#!/usr/bin/env python3
"""Validate content/flashcards/<subject>.json and content/questions/<subject>.json (default subject: math).

Usage: python3 scripts/check_content_math.py [subject]
Exit code 0 when everything passes, 1 otherwise. Rules follow docs/PROJECT.md and docs/CONTENT.md.
"""
import collections
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
subject = sys.argv[1] if len(sys.argv) > 1 else "math"
errors = []
notes = []


def err(msg):
    errors.append(msg)


def load(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:  # noqa: BLE001
        err(f"{path.name}: cannot read JSON: {e}")
        return None


syllabus = load(ROOT / "content" / "syllabus.json")
subtopics = []
for s in syllabus["subjects"]:
    if s["slug"] == subject:
        for t in s["topics"]:
            for ch in t.get("children", []):
                subtopics.append(ch["slug"])
if not subtopics:
    err(f"no subtopics found for subject {subject} in syllabus.json")

cards_doc = load(ROOT / "content" / "flashcards" / f"{subject}.json")
qs_doc = load(ROOT / "content" / "questions" / f"{subject}.json")

SVG_BAD = [r"<script", r"<image", r"<foreignObject", r"<[^>]*\son\w+\s*=", r"<[^>]*href\s*=\s*[\"'](?!#)", r"javascript:", r"@import", r"url\(\s*[\"']?https?:"]
checked_svgs = {}


def check_svg(rel, who):
    """rel is like content/math/x.svg (a path under public/). Returns the list of data-label values."""
    if rel in checked_svgs:
        return checked_svgs[rel]
    path = ROOT / "public" / rel
    if not path.is_file():
        err(f"{who}: visual {rel} does not exist")
        checked_svgs[rel] = []
        return []
    txt = path.read_text(encoding="utf-8")
    if "<svg" not in txt or not re.search(r"<svg[^>]*\sviewBox=\"[^\"]+\"", txt):
        err(f"{rel}: missing <svg> or viewBox")
    if re.search(r"<svg[^>]*\s(width|height)=\"\d+px\"", txt):
        err(f"{rel}: px width/height on <svg>")
    for pat in SVG_BAD:
        if re.search(pat, txt, re.I):
            err(f"{rel}: unsafe SVG content matches {pat}")
    labels = re.findall(r'data-label="([^"]+)"', txt)
    try:
        import xml.dom.minidom as md
        md.parseString(txt.encode("utf-8"))
    except Exception as e:  # noqa: BLE001
        err(f"{rel}: not well-formed XML: {e}")
    checked_svgs[rel] = labels
    return labels


# ------------------------------------------------------------------ flashcards
if cards_doc:
    cards = cards_doc.get("cards", [])
    if cards_doc.get("version") != 1 or cards_doc.get("subject") != subject:
        err("flashcards: version must be 1 and subject must match")
    ids = [c.get("id") for c in cards]
    if len(set(ids)) != len(ids):
        err("flashcards: duplicate ids")
    if ids != [f"{subject}-{i + 1:04d}" for i in range(len(cards))]:
        err("flashcards: ids are not sequential from 0001")
    per_sub = collections.Counter()
    with_visual = 0
    types = collections.Counter()
    for c in cards:
        cid = c.get("id")
        per_sub[c.get("subtopic")] += 1
        if c.get("subtopic") not in subtopics:
            err(f"{cid}: unknown subtopic {c.get('subtopic')}")
        t = c.get("type")
        types[t] += 1
        if t not in ("basic", "cloze", "order", "match", "occlusion"):
            err(f"{cid}: bad type {t}")
        for f in ("front", "back"):
            if not isinstance(c.get(f), str) or not c[f].strip():
                err(f"{cid}: empty {f}")
        if len(c.get("front", "").split()) > 25:
            err(f"{cid}: front longer than 25 words")
        if len(c.get("back", "").split()) > 40:
            err(f"{cid}: back longer than 40 words")
        if not c.get("visual") and not c.get("sketch_prompt"):
            err(f"{cid}: needs a visual or a sketch_prompt")
        if c.get("visual"):
            with_visual += 1
        if not isinstance(c.get("tags"), list):
            err(f"{cid}: tags must be a list")
        labels = check_svg(c["visual"], cid) if c.get("visual") else []
        if t == "cloze":
            gaps = re.findall(r"\{\{.+?\}\}", c.get("front", ""))
            if not gaps:
                err(f"{cid}: cloze front has no {{{{…}}}} gap")
        if t == "order":
            if not isinstance(c.get("items"), list) or len(c["items"]) < 3:
                err(f"{cid}: order needs items (>= 3)")
            elif len(set(c["items"])) != len(c["items"]):
                err(f"{cid}: duplicate order items")
        if t == "match":
            p = c.get("pairs")
            if not isinstance(p, list) or len(p) < 3 or any(not (isinstance(x, list) and len(x) == 2) for x in p):
                err(f"{cid}: match needs pairs (>= 3 of [left, right])")
            else:
                if len({x[0] for x in p}) != len(p) or len({x[1] for x in p}) != len(p):
                    err(f"{cid}: duplicate match sides")
        if t == "occlusion":
            if not c.get("visual"):
                err(f"{cid}: occlusion needs a visual")
            elif not labels:
                err(f"{cid}: occlusion SVG has no data-label elements")
            else:
                for lab in labels:
                    if lab not in c["back"]:
                        err(f"{cid}: back does not list label '{lab}'")
    for st in subtopics:
        n = per_sub.get(st, 0)
        if n < 6:
            err(f"flashcards: {st} has only {n} cards (need >= 6)")
    if cards and with_visual / len(cards) < 0.5:
        err(f"flashcards: only {with_visual}/{len(cards)} cards have a visual (need >= 50%)")
    notes.append(f"flashcards: {len(cards)} cards, {with_visual} with visual, types {dict(types)}")

# ------------------------------------------------------------------ questions
if qs_doc:
    qs = qs_doc.get("questions", [])
    if qs_doc.get("version") != 1 or qs_doc.get("subject") != subject:
        err("questions: version must be 1 and subject must match")
    ids = [q.get("id") for q in qs]
    if len(set(ids)) != len(ids):
        err("questions: duplicate ids")
    if ids != [f"{subject}-{i + 1:04d}" for i in range(len(qs))]:
        err("questions: ids are not sequential from 0001")
    per_sub = collections.Counter()
    diffs = collections.defaultdict(collections.Counter)
    letters = collections.Counter()
    stems = set()
    for q in qs:
        qid = q.get("id")
        per_sub[q.get("subtopic")] += 1
        if q.get("subtopic") not in subtopics:
            err(f"{qid}: unknown subtopic {q.get('subtopic')}")
        d = q.get("difficulty")
        if d not in (1, 2, 3):
            err(f"{qid}: difficulty must be 1, 2 or 3")
        diffs[q.get("subtopic")][d] += 1
        ch = q.get("choices")
        if not isinstance(ch, dict) or list(ch.keys()) != list("ABCDE"):
            err(f"{qid}: choices must be exactly A-E")
        else:
            vals = [str(v).strip() for v in ch.values()]
            if len(set(vals)) != 5 or any(not v for v in vals):
                err(f"{qid}: choices must be 5 distinct non-empty texts")
        if q.get("answer") not in list("ABCDE"):
            err(f"{qid}: answer must be A-E")
        letters[q.get("answer")] += 1
        if not q.get("stem", "").strip() or not q.get("explanation", "").strip():
            err(f"{qid}: empty stem or explanation")
        if q.get("stem") in stems:
            err(f"{qid}: duplicate stem")
        stems.add(q.get("stem"))
        if q.get("source") != "original":
            err(f"{qid}: source must be 'original'")
        for key in ("visual", "explanation_visual"):
            if q.get(key):
                check_svg(q[key], qid)
    for st in subtopics:
        n = per_sub.get(st, 0)
        if n < 8:
            err(f"questions: {st} has only {n} questions (need >= 8)")
        dc = diffs[st]
        if n and not (dc[1] >= 2 and dc[2] >= 2 and dc[3] >= 1):
            err(f"questions: {st} difficulty mix {dict(dc)} is off (want about 40/40/20)")
    if qs:
        worst = max(letters.values()) / len(qs)
        if worst > 0.30:
            err(f"questions: correct-letter distribution is skewed {dict(letters)}")
        notes.append(f"questions: {len(qs)} questions, letters {dict(sorted(letters.items()))}")
        themed = sum(1 for q in qs if re.search(r"Valorant|swim|pool|lane|bak|cook|recipe|pizza|oven|kitchen|sandwich|cookie|pantry|pepper|yeast|sourdough|pan\b|tray|soup|fondant|lemon|agent|round|spike", q["stem"], re.I))
        notes.append(f"questions with a theme keyword in the stem: {themed}/{len(qs)} ({themed * 100 // len(qs)}%)")

# all cards-* SVGs of the subject must be safe even if unused
for p in sorted((ROOT / "public" / "content" / subject).glob("cards-*.svg")):
    check_svg(f"content/{subject}/{p.name}", p.name)

for n in notes:
    print(n)
if errors:
    print(f"\n{len(errors)} problem(s):")
    for e in errors:
        print(" -", e)
    sys.exit(1)
print("OK: all content checks passed")
