#!/usr/bin/env python3
"""Structure checks for the physics flashcards and questions (issue #23).

Run from the repo root:  python3 scripts/check_content_physics.py
Exit code 0 = all checks pass. See also scripts/verify/content_physics.py (answer re-derivation).
"""
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
errors = []
CARD_TYPES = {"basic", "cloze", "order", "match", "occlusion"}
MIN_CARDS, MIN_QUESTIONS = 6, 8


def err(msg):
    errors.append(msg)


def load(rel):
    try:
        return json.loads((ROOT / rel).read_text(encoding="utf-8"))
    except Exception as e:  # noqa: BLE001
        err(f"{rel}: cannot read/parse JSON ({e})")
        return None


def physics_subtopics():
    syl = load("content/syllabus.json")
    for subj in syl["subjects"]:
        if subj["slug"] == "physics":
            return [c["slug"] for t in subj["topics"] for c in t.get("children", [])]
    err("physics not found in syllabus.json")
    return []


def check_svg(rel):
    path = ROOT / "public" / rel
    if not rel.startswith("content/physics/") or not rel.endswith(".svg"):
        err(f"{rel}: visual must be content/physics/<name>.svg")
        return None
    if not path.is_file():
        err(f"{rel}: file does not exist under public/")
        return None
    txt = path.read_text(encoding="utf-8")
    if "viewBox" not in txt:
        err(f"{rel}: no viewBox")
    if re.search(r"<script|<image|<foreignObject", txt, re.I):
        err(f"{rel}: contains script/image/foreignObject")
    if re.search(r"""(?:xlink:)?href\s*=\s*["'](?!#)""", txt):
        err(f"{rel}: external href")
    if re.search(r"""(?:src|url\()\s*=?\s*["']?\s*(?:https?:|//|data:)""", txt, re.I):
        err(f"{rel}: external reference")
    if re.search(r"""<svg[^>]*\s(?:width|height)\s*=\s*["'][^"']*px""", txt):
        err(f"{rel}: px width/height on <svg>")
    if re.search(r"\son\w+\s*=", txt):
        err(f"{rel}: event handler attribute")
    return txt


def words(s):
    return len(re.findall(r"\S+", s))


def check_cards(cards, slugs):
    ids = [c.get("id") for c in cards]
    if ids != [f"physics-{i:04d}" for i in range(1, len(cards) + 1)]:
        err("flashcards: ids are not unique and sequential physics-0001...")
    visual_count = 0
    for c in cards:
        cid = c.get("id")
        if c.get("subtopic") not in slugs:
            err(f"{cid}: unknown subtopic {c.get('subtopic')!r}")
        t = c.get("type")
        if t not in CARD_TYPES:
            err(f"{cid}: bad type {t!r}")
            continue
        if not c.get("front") or not c.get("back"):
            err(f"{cid}: empty front/back")
            continue
        if words(c["front"]) > 25:
            err(f"{cid}: front longer than 25 words")
        if words(c["back"]) > 40:
            err(f"{cid}: back longer than 40 words")
        vis, sk = c.get("visual"), c.get("sketch_prompt")
        if not vis and not sk:
            err(f"{cid}: needs a visual or a sketch_prompt")
        if vis:
            visual_count += 1
            check_svg(vis)
        if t == "cloze" and not re.search(r"\{\{.+?\}\}", c["front"]):
            err(f"{cid}: cloze front has no {{{{...}}}} gap")
        if t == "order":
            items = c.get("items")
            if not isinstance(items, list) or len(items) < 3 or len(set(items)) != len(items):
                err(f"{cid}: order needs >= 3 distinct items")
        if t == "match":
            pairs = c.get("pairs")
            if (not isinstance(pairs, list) or len(pairs) < 3
                    or any(not (isinstance(p, list) and len(p) == 2 and all(p)) for p in pairs)):
                err(f"{cid}: match needs >= 3 [left, right] pairs")
        if t == "occlusion":
            if not vis:
                err(f"{cid}: occlusion needs a visual")
            else:
                txt = check_svg(vis) or ""
                found = re.findall(r'data-label="([^"]+)"', txt)
                listed = [x.strip() for x in c["back"].split(";") if x.strip()]
                if not listed:
                    err(f"{cid}: occlusion back must list the labels separated by ';'")
                for lab in listed:
                    if lab not in found:
                        err(f"{cid}: label {lab!r} not found as data-label in {vis}")
                if len(set(listed)) != len(listed):
                    err(f"{cid}: duplicate labels in back")
                if len(found) < 3:
                    err(f"{cid}: SVG has fewer than 3 data-label elements")
        if t != "order" and "items" in c:
            err(f"{cid}: items only allowed on order cards")
        if t != "match" and "pairs" in c:
            err(f"{cid}: pairs only allowed on match cards")
    share = visual_count / len(cards) if cards else 0
    if share < 0.5:
        err(f"flashcards: only {share:.0%} have a visual (need >= 50%)")
    return share


def check_questions(qs, slugs):
    ids = [q.get("id") for q in qs]
    if ids != [f"physics-{i:04d}" for i in range(1, len(qs) + 1)]:
        err("questions: ids are not unique and sequential physics-0001...")
    for q in qs:
        qid = q.get("id")
        if q.get("subtopic") not in slugs:
            err(f"{qid}: unknown subtopic {q.get('subtopic')!r}")
        if q.get("difficulty") not in (1, 2, 3):
            err(f"{qid}: difficulty must be 1, 2 or 3")
        if not q.get("stem") or not q.get("explanation"):
            err(f"{qid}: empty stem/explanation")
        ch = q.get("choices")
        if not isinstance(ch, dict) or list(ch.keys()) != list("ABCDE"):
            err(f"{qid}: choices must be exactly A-E")
            continue
        vals = [str(v).strip() for v in ch.values()]
        if any(not v for v in vals) or len(set(vals)) != 5:
            err(f"{qid}: the 5 choices must be non-empty and distinct")
        if q.get("answer") not in ch:
            err(f"{qid}: answer must be one of A-E")
        if q.get("source") != "original":
            err(f"{qid}: source must be 'original'")
        for key in ("visual", "explanation_visual"):
            if q.get(key):
                check_svg(q[key])
        if q.get("difficulty") == 3 and not q.get("explanation_visual") and words(q.get("explanation", "")) < 25:
            err(f"{qid}: difficulty 3 needs an explanation_visual or a step-by-step explanation")
    counts = Counter(q.get("answer") for q in qs)
    if qs and max(counts.values()) / len(qs) > 0.30:
        err("questions: one answer letter exceeds 30%")
    return counts


def main():
    slugs = physics_subtopics()
    fc = load("content/flashcards/physics.json")
    qq = load("content/questions/physics.json")
    if fc is None or qq is None:
        return report()
    for doc, name, key in ((fc, "flashcards", "cards"), (qq, "questions", "questions")):
        if doc.get("version") != 1 or doc.get("subject") != "physics":
            err(f"{name}: needs version 1 and subject 'physics'")
        if not isinstance(doc.get(key), list):
            err(f"{name}: missing {key} list")
            return report()
    cards, qs = fc["cards"], qq["questions"]
    share = check_cards(cards, slugs)
    letters = check_questions(qs, slugs)
    cc = Counter(c["subtopic"] for c in cards)
    qc = Counter(q["subtopic"] for q in qs)
    dc = {s: Counter(q["difficulty"] for q in qs if q["subtopic"] == s) for s in slugs}
    print(f"{'subtopic':45} cards  qs  d1/d2/d3")
    for s in slugs:
        d = dc[s]
        print(f"{s:45} {cc[s]:5} {qc[s]:3}  {d[1]}/{d[2]}/{d[3]}")
        if cc[s] < MIN_CARDS:
            err(f"{s}: only {cc[s]} flashcards (need >= {MIN_CARDS})")
        if qc[s] < MIN_QUESTIONS:
            err(f"{s}: only {qc[s]} questions (need >= {MIN_QUESTIONS})")
        if qc[s] and (d[1] < 1 or d[2] < 1 or d[3] < 1):
            err(f"{s}: needs at least one question of each difficulty")
    td = Counter(q["difficulty"] for q in qs)
    types = Counter(c["type"] for c in cards)
    print(f"total cards={len(cards)} questions={len(qs)} visual share={share:.0%}")
    print("card types:", dict(types), "| difficulty:", dict(sorted(td.items())),
          "| answer letters:", dict(sorted(letters.items())))
    for t in CARD_TYPES:
        if types[t] == 0:
            err(f"no cards of type {t}")
    return report()


def report():
    for e in errors:
        print("FAIL:", e)
    print("OK" if not errors else f"{len(errors)} problem(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
