#!/usr/bin/env python3
"""Lint the Chemistry flashcards and questions (issue #24).

    python3 scripts/check_content_chemistry.py

Checks (exit code 1 if anything fails; prints the per-subtopic count table):
  * both JSON files are valid, version 1, subject "chemistry"; ids unique and sequential (chemistry-0001, ...)
  * every subtopic slug exists in content/syllabus.json and ALL 17 chemistry subtopics are covered
    (>= 6 cards and >= 8 questions each, at least one difficulty-3 question)
  * questions: 5 distinct non-empty choices A-E, answer in A-E, explanation present, difficulty 1-3,
    source "original", no answer letter above 30 %, organic questions <= 20 %, difficulty mix per subtopic
  * cards: type-specific fields (order items >= 3, match pairs >= 3, cloze has {{..}}, occlusion visual exists and has
    data-label elements that match the labels listed in `back`), every card has a visual or a sketch_prompt,
    >= 50 % of cards have a visual, front <= 25 words, back <= 40 words
  * every referenced SVG exists under public/, has a viewBox, no width/height in px, no script / image /
    foreignObject / external href
"""
import collections
import json
import pathlib
import re
import sys
import xml.dom.minidom

ROOT = pathlib.Path(__file__).resolve().parent.parent
errors = []

def err(msg):
    errors.append(msg)

def load(path):
    try:
        return json.loads((ROOT / path).read_text(encoding="utf-8"))
    except Exception as e:  # noqa: BLE001
        err(f"{path}: cannot read JSON: {e}")
        return None

syl = load("content/syllabus.json")
SUBS = [c["slug"] for s in syl["subjects"] if s["slug"] == "chemistry" for t in s["topics"] for c in t["children"]]
cards_doc = load("content/flashcards/chemistry.json")
qs_doc = load("content/questions/chemistry.json")
if cards_doc is None or qs_doc is None:
    print("\n".join(errors))
    sys.exit(1)

for name, doc, key in (("flashcards", cards_doc, "cards"), ("questions", qs_doc, "questions")):
    if doc.get("version") != 1 or doc.get("subject") != "chemistry":
        err(f"{name}: needs version 1 and subject 'chemistry'")
cards, qs = cards_doc["cards"], qs_doc["questions"]

def check_ids(items, what):
    ids = [x.get("id") for x in items]
    if len(set(ids)) != len(ids):
        err(f"{what}: duplicate ids")
    for i, x in enumerate(items, 1):
        if x.get("id") != f"chemistry-{i:04d}":
            err(f"{what}: id {x.get('id')} should be chemistry-{i:04d} (ids must be sequential)")
            break

check_ids(cards, "flashcards")
check_ids(qs, "questions")

# ---------------------------------------------------------------- SVG helpers
svg_cache = {}

def svg_info(visual):
    """Return the set of data-label values of a visual, or None if the file is unusable. Reports problems once."""
    if visual in svg_cache:
        return svg_cache[visual]
    path = ROOT / "public" / visual
    labels = None
    if not visual.startswith("content/chemistry/cards-") or not visual.endswith(".svg"):
        err(f"{visual}: visual must be content/chemistry/cards-<name>.svg")
    elif not path.is_file():
        err(f"{visual}: file not found under public/")
    else:
        raw = path.read_text(encoding="utf-8")
        try:
            dom = xml.dom.minidom.parseString(raw.encode("utf-8"))
            root = dom.documentElement
            if root.tagName != "svg":
                err(f"{visual}: root element is not <svg>")
            if not root.getAttribute("viewBox"):
                err(f"{visual}: missing viewBox")
            labels = {e.getAttribute("data-label") for e in dom.getElementsByTagName("*") if e.hasAttribute("data-label")}
        except Exception as e:  # noqa: BLE001
            err(f"{visual}: SVG is not well formed: {e}")
        if re.search(r"<script|<image|<foreignObject|xlink:href|\bhref\s*=\s*[\"']\s*(https?:|//|data:|javascript:)|javascript:|\son\w+\s*=", raw, re.I):
            err(f"{visual}: unsafe content (script / image / foreignObject / external href / event handler)")
        if re.search(r"<svg[^>]*\s(width|height)\s*=", raw):
            err(f"{visual}: <svg> must not have width/height (use viewBox)")
        if re.search(r"https?://(?!www\.w3\.org/)", raw):
            err(f"{visual}: external URL inside SVG")
    svg_cache[visual] = labels
    return labels

# ---------------------------------------------------------------- questions
q_by_sub = collections.defaultdict(list)
for q in qs:
    qid = q.get("id", "?")
    sub = q.get("subtopic")
    if sub not in SUBS:
        err(f"{qid}: unknown subtopic {sub!r}")
    q_by_sub[sub].append(q)
    ch = q.get("choices")
    if not isinstance(ch, dict) or list(ch) != list("ABCDE"):
        err(f"{qid}: choices must be exactly A-E")
        continue
    vals = [str(v).strip() for v in ch.values()]
    if any(not v for v in vals):
        err(f"{qid}: empty choice")
    if len(set(vals)) != 5:
        err(f"{qid}: choices are not 5 distinct texts")
    if q.get("answer") not in list("ABCDE"):
        err(f"{qid}: answer must be A-E")
    if not str(q.get("stem", "")).strip() or not str(q.get("explanation", "")).strip():
        err(f"{qid}: stem and explanation are required")
    if q.get("difficulty") not in (1, 2, 3):
        err(f"{qid}: difficulty must be 1, 2 or 3")
    if q.get("source") != "original":
        err(f"{qid}: source must be 'original'")
    for k in ("visual", "explanation_visual"):
        if q.get(k):
            svg_info(q[k])

letters = collections.Counter(q.get("answer") for q in qs)
for letter, n in letters.items():
    if n / len(qs) > 0.30:
        err(f"answer letter {letter} is used {n}/{len(qs)} times (> 30 %)")
organic = sum(1 for q in qs if str(q.get("subtopic", "")).startswith("chemistry.organic."))
if organic / len(qs) > 0.20:
    err(f"organic questions are {organic}/{len(qs)} = {organic / len(qs):.0%} (> 20 %)")

# ---------------------------------------------------------------- cards
TYPES = {"basic", "cloze", "order", "match", "occlusion"}
c_by_sub = collections.defaultdict(list)
with_visual = 0
for c in cards:
    cid = c.get("id", "?")
    sub = c.get("subtopic")
    if sub not in SUBS:
        err(f"{cid}: unknown subtopic {sub!r}")
    c_by_sub[sub].append(c)
    t = c.get("type")
    if t not in TYPES:
        err(f"{cid}: unknown type {t!r}")
    front, back = str(c.get("front", "")).strip(), str(c.get("back", "")).strip()
    if not front or not back:
        err(f"{cid}: front and back are required")
    if len(front.split()) > 25:
        err(f"{cid}: front has {len(front.split())} words (max 25)")
    if len(back.split()) > 40:
        err(f"{cid}: back has {len(back.split())} words (max 40)")
    if not c.get("visual") and not c.get("sketch_prompt"):
        err(f"{cid}: needs a visual or a sketch_prompt")
    if c.get("visual"):
        with_visual += 1
    labels = svg_info(c["visual"]) if c.get("visual") else None
    if not isinstance(c.get("tags"), list):
        err(f"{cid}: tags must be a list")
    if t == "order":
        items = c.get("items")
        if not isinstance(items, list) or len(items) < 3 or len(set(items)) != len(items):
            err(f"{cid}: order card needs >= 3 distinct items")
    elif t == "match":
        pairs = c.get("pairs")
        if not isinstance(pairs, list) or len(pairs) < 3 or any(not (isinstance(p, list) and len(p) == 2 and all(p)) for p in pairs):
            err(f"{cid}: match card needs >= 3 [left, right] pairs")
    elif t == "cloze":
        if not re.search(r"\{\{.+?\}\}", front):
            err(f"{cid}: cloze front needs a {{{{gap}}}}")
    elif t == "occlusion":
        if not c.get("visual"):
            err(f"{cid}: occlusion card needs a visual")
        elif labels is not None:
            want = [x.strip() for x in back.split(",") if x.strip()]
            if not want:
                err(f"{cid}: occlusion back must list the labels separated by commas")
            for w in want:
                if w not in labels:
                    err(f"{cid}: label {w!r} is not a data-label in {c['visual']} (has {sorted(labels)})")
    if t != "occlusion" and c.get("items") and t != "order":
        err(f"{cid}: items only belong on order cards")

if cards and with_visual / len(cards) < 0.50:
    err(f"only {with_visual}/{len(cards)} cards have a visual (< 50 %)")

# ---------------------------------------------------------------- coverage table
print(f"{'subtopic':45} cards  visual  questions  difficulty 1/2/3")
for s in SUBS:
    cs, qq = c_by_sub.get(s, []), q_by_sub.get(s, [])
    diff = [sum(1 for q in qq if q.get("difficulty") == d) for d in (1, 2, 3)]
    vis = sum(1 for c in cs if c.get("visual"))
    print(f"{s:45} {len(cs):5} {vis:7} {len(qq):10}  {diff}")
    if len(cs) < 6:
        err(f"{s}: only {len(cs)} cards (need >= 6)")
    if len(qq) < 8:
        err(f"{s}: only {len(qq)} questions (need >= 8)")
    if qq and diff[2] == 0:
        err(f"{s}: no difficulty-3 question")
    if cs and vis / len(cs) < 0.5:
        print(f"  note: {s} has {vis}/{len(cs)} cards with a visual (the rest have a sketch_prompt)")
for s in set(c_by_sub) | set(q_by_sub):
    if s not in SUBS:
        err(f"unknown subtopic in content: {s}")
print(f"\ntotal: {len(cards)} cards ({with_visual} with a visual = {with_visual / len(cards):.0%}), "
      f"{len(qs)} questions, organic {organic}/{len(qs)} = {organic / len(qs):.0%}, "
      f"answer letters {dict(sorted(letters.items()))}")

if errors:
    print(f"\n{len(errors)} problem(s):")
    for e in errors:
        print(" -", e)
    sys.exit(1)
print("OK")
