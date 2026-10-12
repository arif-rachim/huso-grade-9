#!/usr/bin/env python3
"""Structural checks for the Earth Science content (issue #26).

Run from anywhere:  python3 scripts/check_content_earth.py
Exit code 0 = all good, 1 = at least one error.

Checks
- both JSON files are valid, version 1, subject "earth"
- ids are unique and sequential (earth-0001, earth-0002, ...)
- every subtopic slug exists in content/syllabus.json and ALL earth subtopics are covered
- per subtopic: >= 6 flashcards, >= 8 questions, >= 40% of questions are simple/typical/hard mix sanity
- questions: 5 distinct non-empty choices A-E, answer in A-E, explanation present,
  source "original", no answer letter above 30%
- cards: type-specific fields (order items >= 3, match pairs >= 3, cloze has {{..}},
  occlusion visual exists and every label in `back` is a data-label in the SVG)
- every card has a visual or a sketch_prompt; at least 50% have a visual file
- referenced visuals exist on disk (and are under public/)
- SVG safety: viewBox, no script/image/foreignObject/external href/on* attributes
"""
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
errors = []
warnings = []


def err(msg):
    errors.append(msg)


def load(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:  # noqa: BLE001
        err(f"{path}: invalid JSON: {e}")
        return None


def earth_subtopics():
    syl = load(ROOT / "content" / "syllabus.json")
    slugs = []

    def walk(node):
        if isinstance(node, dict):
            if str(node.get("slug", "")).startswith("earth.") and node.get("slug", "").count(".") == 2:
                slugs.append(node["slug"])
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)

    walk(syl)
    return sorted(set(slugs))


def check_svg(rel):
    """Return the set of data-label values, and report safety errors."""
    p = ROOT / "public" / rel
    if not p.is_file():
        err(f"missing visual file: {rel}")
        return set()
    txt = p.read_text(encoding="utf-8")
    if not rel.endswith(".svg"):
        err(f"visual is not an SVG: {rel}")
        return set()
    if not re.search(r"<svg[^>]*\sviewBox=\"[^\"]+\"", txt):
        err(f"{rel}: no viewBox")
    m = re.search(r"<svg\b[^>]*>", txt)
    if m and re.search(r"\s(width|height)=\"\d", m.group(0)):
        err(f"{rel}: <svg> has fixed width/height")
    for bad in ("<script", "<image", "<foreignObject", "<iframe", "<style", "<use"):
        if bad.lower() in txt.lower():
            err(f"{rel}: forbidden element {bad}")
    if re.search(r"\son[a-z]+\s*=", txt):
        err(f"{rel}: event handler attribute")
    for m in re.finditer(r"""(?:xlink:)?href\s*=\s*["']([^"']*)["']""", txt):
        err(f"{rel}: href found ({m.group(1)})")
    if re.search(r"url\(\s*[\"']?(?!#)", txt):
        err(f"{rel}: external url() reference")
    if "http://" in txt.replace("http://www.w3.org/2000/svg", "") or "https://" in txt:
        err(f"{rel}: external URL in file")
    for m in re.finditer(r"font-size=\"([\d.]+)\"", txt):
        if float(m.group(1)) < 12:
            err(f"{rel}: font-size {m.group(1)} < 12")
            break
    allowed = {"#92400e", "#111827", "#6b7280", "#d1d5db", "#ffffff", "none"}
    for m in re.finditer(r"(?:fill|stroke)=\"(#[0-9a-fA-F]{3,6}|none)\"", txt):
        if m.group(1).lower() not in allowed:
            err(f"{rel}: colour {m.group(1)} is outside the palette")
            break
    return set(re.findall(r'data-label="([^"]+)"', txt))


def main():
    subs = earth_subtopics()
    if len(subs) != 17:
        err(f"expected 17 earth subtopics in syllabus.json, found {len(subs)}")

    fc = load(ROOT / "content" / "flashcards" / "earth.json")
    qs = load(ROOT / "content" / "questions" / "earth.json")
    if fc is None or qs is None:
        return report()
    for name, d in (("flashcards", fc), ("questions", qs)):
        if d.get("version") != 1 or d.get("subject") != "earth":
            err(f"{name}: need version 1 and subject 'earth'")
    cards = fc.get("cards", [])
    questions = qs.get("questions", [])

    # ids
    for name, items in (("card", cards), ("question", questions)):
        ids = [x.get("id") for x in items]
        if len(set(ids)) != len(ids):
            err(f"{name} ids are not unique")
        for i, x in enumerate(ids, 1):
            if x != f"earth-{i:04d}":
                err(f"{name} id {x!r} should be earth-{i:04d}")
                break

    # cards
    svg_labels = {}
    visual_count = 0
    for c in cards:
        cid = c.get("id")
        for k in ("subtopic", "type", "front", "back", "visual", "sketch_prompt", "tags"):
            if k not in c:
                err(f"{cid}: missing field {k}")
        if c.get("subtopic") not in subs:
            err(f"{cid}: unknown subtopic {c.get('subtopic')!r}")
        t = c.get("type")
        if t not in ("basic", "cloze", "order", "match", "occlusion"):
            err(f"{cid}: bad type {t!r}")
        if not str(c.get("front", "")).strip() or not str(c.get("back", "")).strip():
            err(f"{cid}: empty front/back")
        if len(str(c.get("front", "")).split()) > 25:
            err(f"{cid}: front is longer than 25 words")
        if len(str(c.get("back", "")).split()) > 40 and t not in ("order", "match", "occlusion"):
            err(f"{cid}: back is longer than 40 words")
        if not c.get("visual") and not c.get("sketch_prompt"):
            err(f"{cid}: needs a visual or a sketch_prompt")
        if c.get("visual"):
            visual_count += 1
            if c["visual"] not in svg_labels:
                svg_labels[c["visual"]] = check_svg(c["visual"])
        if t == "cloze" and not re.search(r"\{\{.+?\}\}", c.get("front", "")):
            err(f"{cid}: cloze front has no {{{{..}}}} gap")
        if t == "order":
            items = c.get("items")
            if not isinstance(items, list) or len(items) < 3 or len(set(items)) != len(items):
                err(f"{cid}: order needs >= 3 distinct items")
        if t == "match":
            pairs = c.get("pairs")
            if not isinstance(pairs, list) or len(pairs) < 3 or any(not (isinstance(p, list) and len(p) == 2 and all(p)) for p in pairs):
                err(f"{cid}: match needs >= 3 [left, right] pairs")
            elif len({p[0] for p in pairs}) != len(pairs):
                err(f"{cid}: match has duplicate left items")
        if t == "occlusion":
            if not c.get("visual"):
                err(f"{cid}: occlusion needs a visual")
            else:
                labels = [x.strip() for x in c["back"].split(",") if x.strip()]
                if not labels:
                    err(f"{cid}: occlusion back lists no labels")
                for lab in labels:
                    if lab not in svg_labels[c["visual"]]:
                        err(f"{cid}: label {lab!r} is not a data-label in {c['visual']}")
    if cards and visual_count / len(cards) < 0.5:
        err(f"only {visual_count}/{len(cards)} cards have a visual (need >= 50%)")

    # questions
    for q in questions:
        qid = q.get("id")
        for k in ("subtopic", "difficulty", "stem", "visual", "choices", "answer", "explanation", "explanation_visual", "source"):
            if k not in q:
                err(f"{qid}: missing field {k}")
        if q.get("subtopic") not in subs:
            err(f"{qid}: unknown subtopic {q.get('subtopic')!r}")
        if q.get("difficulty") not in (1, 2, 3):
            err(f"{qid}: difficulty must be 1, 2 or 3")
        if q.get("source") != "original":
            err(f"{qid}: source must be 'original'")
        ch = q.get("choices", {})
        if sorted(ch) != list("ABCDE"):
            err(f"{qid}: choices must be exactly A-E")
        else:
            vals = [str(ch[k]).strip() for k in "ABCDE"]
            if any(not v for v in vals):
                err(f"{qid}: empty choice")
            if len({v.lower() for v in vals}) != 5:
                err(f"{qid}: choices are not 5 distinct texts")
        if q.get("answer") not in list("ABCDE"):
            err(f"{qid}: answer must be A-E")
        if not str(q.get("explanation", "")).strip() or not str(q.get("stem", "")).strip():
            err(f"{qid}: empty stem or explanation")
        for key in ("visual", "explanation_visual"):
            if q.get(key):
                if q[key] not in svg_labels:
                    svg_labels[q[key]] = check_svg(q[key])

    # coverage
    cc = Counter(c.get("subtopic") for c in cards)
    qc = Counter(q.get("subtopic") for q in questions)
    dc = {s: Counter(q["difficulty"] for q in questions if q.get("subtopic") == s) for s in subs}
    print(f"{'subtopic':40} cards  questions  d1/d2/d3")
    for s in subs:
        print(f"{s:40} {cc[s]:5} {qc[s]:10}  {dc[s][1]}/{dc[s][2]}/{dc[s][3]}")
        if cc[s] < 6:
            err(f"{s}: only {cc[s]} cards (need >= 6)")
        if qc[s] < 8:
            err(f"{s}: only {qc[s]} questions (need >= 8)")
        if dc[s][3] < 1 or dc[s][1] < 2 or dc[s][2] < 2:
            err(f"{s}: difficulty mix {dc[s][1]}/{dc[s][2]}/{dc[s][3]} is too lopsided")

    # answer letter balance
    letters = Counter(q.get("answer") for q in questions)
    for L in "ABCDE":
        share = letters[L] / max(len(questions), 1)
        print(f"answer {L}: {letters[L]} ({share:.0%})")
        if share > 0.30:
            err(f"answer letter {L} is {share:.0%} of all answers (max 30%)")
    dd = Counter(q.get("difficulty") for q in questions)
    print(f"cards={len(cards)} questions={len(questions)} with_visual={visual_count} difficulty={dict(sorted(dd.items()))}")
    return report()


def report():
    for w in warnings:
        print("WARN:", w)
    if errors:
        print(f"\n{len(errors)} error(s):")
        for e in errors:
            print(" -", e)
        return 1
    print("\nOK: all Earth Science content checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
