#!/usr/bin/env python3
"""Structural checks for the biology flashcards and questions (issue #25).

Usage: python3 scripts/check_content_biology.py      (exit code 0 = all good, 1 = problems)
"""
import collections
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
errors, warnings = [], []


def err(msg):
    errors.append(msg)


def warn(msg):
    warnings.append(msg)


def load(rel):
    try:
        return json.loads((ROOT / rel).read_text(encoding="utf-8"))
    except Exception as e:  # noqa: BLE001
        err(f"{rel}: cannot read JSON: {e}")
        return None


syllabus = load("content/syllabus.json")
subtopics = []
for s in syllabus["subjects"]:
    if s["slug"] == "biology":
        for t in s["topics"]:
            subtopics += [c["slug"] for c in t.get("children", [])]
if len(subtopics) != 16:
    err(f"expected 16 biology subtopics in syllabus.json, found {len(subtopics)}")

cards_doc = load("content/flashcards/biology.json")
qs_doc = load("content/questions/biology.json")
cards = cards_doc["cards"] if cards_doc else []
questions = qs_doc["questions"] if qs_doc else []

for doc, name in ((cards_doc, "flashcards"), (qs_doc, "questions")):
    if doc and (doc.get("version") != 1 or doc.get("subject") != "biology"):
        err(f"{name}: version must be 1 and subject 'biology'")


# ---------- SVG safety
def check_svg(rel, where):
    p = ROOT / "public" / rel
    if not p.is_file():
        err(f"{where}: visual not found on disk: {rel}")
        return None
    s = p.read_text(encoding="utf-8")
    if not s.lstrip().startswith("<svg"):
        err(f"{rel}: must start with <svg")
    if "viewBox=" not in s.split(">", 1)[0]:
        err(f"{rel}: <svg> has no viewBox")
    head = s.split(">", 1)[0]
    if re.search(r'\s(width|height)="\d+(px)?"', head):
        err(f"{rel}: <svg> must not have fixed width/height")
    for bad in ("<script", "<image", "<foreignObject", "<iframe", "javascript:", "onload=", "onclick=", "@import", "<style"):
        if bad.lower() in s.lower():
            err(f"{rel}: forbidden content {bad!r}")
    if re.search(r'(xlink:)?href\s*=', s):
        err(f"{rel}: href is not allowed (no external or internal links)")
    if re.search(r'(https?:)?//[a-z]', re.sub(r'xmlns="http://www.w3.org/2000/svg"', "", s)):
        err(f"{rel}: external URL found")
    for fs in re.findall(r'font-size="([\d.]+)"', s):
        if float(fs) < 12:
            err(f"{rel}: font-size {fs} < 12")
    bad_colors = set(re.findall(r'(?:fill|stroke)="(#[0-9a-fA-F]{3,6})"', s)) - {
        "#16a34a", "#111827", "#6b7280", "#d1d5db", "#ffffff", "#bbe5c8", "#f0fdf4"}
    if bad_colors:
        warn(f"{rel}: colors outside the palette: {sorted(bad_colors)}")
    return s


checked_svgs = {}


def svg_text(rel, where):
    if rel not in checked_svgs:
        checked_svgs[rel] = check_svg(rel, where)
    return checked_svgs[rel]


# ---------- flashcards
ids = [c.get("id") for c in cards]
if ids != [f"biology-{i:04d}" for i in range(1, len(cards) + 1)]:
    err("flashcard ids must be unique and sequential: biology-0001, biology-0002, ...")
TYPES = {"basic", "cloze", "order", "match", "occlusion"}
for c in cards:
    cid = c.get("id")
    for f in ("subtopic", "type", "front", "back"):
        if not c.get(f):
            err(f"{cid}: missing {f}")
    if c.get("subtopic") not in subtopics:
        err(f"{cid}: unknown subtopic {c.get('subtopic')}")
    t = c.get("type")
    if t not in TYPES:
        err(f"{cid}: bad type {t}")
    if not c.get("visual") and not c.get("sketch_prompt"):
        err(f"{cid}: needs a visual or a sketch_prompt")
    if len(c.get("front", "").split()) > 25:
        err(f"{cid}: front longer than 25 words")
    if len(c.get("back", "").split()) > 40:
        err(f"{cid}: back longer than 40 words")
    if c.get("visual"):
        svg_text(c["visual"], cid)
    if t == "order":
        items = c.get("items") or []
        if len(items) < 3 or len(set(items)) != len(items):
            err(f"{cid}: order needs >= 3 distinct items")
    if t == "match":
        pairs = c.get("pairs") or []
        if len(pairs) < 3 or any(len(p) != 2 or not p[0] or not p[1] for p in pairs):
            err(f"{cid}: match needs >= 3 [left, right] pairs")
        elif len({p[0] for p in pairs}) != len(pairs) or len({p[1] for p in pairs}) != len(pairs):
            err(f"{cid}: match pairs must have distinct lefts and rights")
    if t == "cloze" and not re.search(r"\{\{.+?\}\}", c.get("front", "")):
        err(f"{cid}: cloze front needs a {{{{gap}}}}")
    if t == "occlusion":
        if not c.get("visual"):
            err(f"{cid}: occlusion needs a visual")
        else:
            s = svg_text(c["visual"], cid) or ""
            labels = list(dict.fromkeys(re.findall(r'data-label="([^"]+)"', s)))
            back = [x.strip() for x in c["back"].split(",")]
            if not labels:
                err(f"{cid}: svg has no data-label elements")
            elif back != labels:
                err(f"{cid}: back must list the svg's data-labels in order: {labels} vs {back}")

# ---------- questions
qids = [q.get("id") for q in questions]
if qids != [f"biology-{i:04d}" for i in range(1, len(questions) + 1)]:
    err("question ids must be unique and sequential: biology-0001, ...")
for q in questions:
    qid = q.get("id")
    if q.get("subtopic") not in subtopics:
        err(f"{qid}: unknown subtopic {q.get('subtopic')}")
    if q.get("difficulty") not in (1, 2, 3):
        err(f"{qid}: difficulty must be 1, 2 or 3")
    if not q.get("stem") or not q.get("explanation"):
        err(f"{qid}: needs a stem and an explanation")
    ch = q.get("choices") or {}
    if list(ch.keys()) != list("ABCDE"):
        err(f"{qid}: choices must be exactly A-E")
    vals = [str(v).strip() for v in ch.values()]
    if len(set(vals)) != 5 or any(not v for v in vals):
        err(f"{qid}: the 5 choices must be non-empty and distinct")
    if q.get("answer") not in list("ABCDE"):
        err(f"{qid}: answer must be A-E")
    if q.get("source") != "original":
        err(f"{qid}: source must be 'original'")
    for k in ("visual", "explanation_visual"):
        if q.get(k):
            svg_text(q[k], qid)
    lens = [len(v) for v in vals]
    if lens and max(lens) > 4 * max(min(lens), 12) + 20:
        warn(f"{qid}: choice lengths are very uneven ({min(lens)}..{max(lens)})")

# ---------- coverage and mix
cc = collections.Counter(c["subtopic"] for c in cards)
qc = collections.Counter(q["subtopic"] for q in questions)
for st in subtopics:
    if cc[st] < 6:
        err(f"{st}: only {cc[st]} flashcards (need >= 6)")
    if qc[st] < 8:
        err(f"{st}: only {qc[st]} questions (need >= 8)")
    d = collections.Counter(q["difficulty"] for q in questions if q["subtopic"] == st)
    if d[1] < 2 or d[2] < 2 or d[3] < 1:
        err(f"{st}: difficulty mix too thin: {dict(d)}")
    types = {c["type"] for c in cards if c["subtopic"] == st}
    if len(types) < 2:
        warn(f"{st}: flashcards use only one type")

n_visual = sum(1 for c in cards if c.get("visual"))
if cards and n_visual / len(cards) < 0.6:
    err(f"only {n_visual}/{len(cards)} cards have a visual (biology target >= 60%)")
tc = collections.Counter(c["type"] for c in cards)
if tc["occlusion"] < 8 or tc["order"] < 6:
    err(f"too few occlusion/order cards: {dict(tc)}")

letters = collections.Counter(q["answer"] for q in questions)
for l, n in letters.items():
    if n / len(questions) > 0.30:
        err(f"answer letter {l} used {n}/{len(questions)} times (> 30%)")
dd = collections.Counter(q["difficulty"] for q in questions)
for k, lo, hi in ((1, 0.30, 0.50), (2, 0.30, 0.50), (3, 0.12, 0.28)):
    share = dd[k] / max(len(questions), 1)
    if not lo <= share <= hi:
        err(f"difficulty {k} share {share:.0%} outside {lo:.0%}-{hi:.0%}")

themed = re.compile(r"\b(cook|chef|kitchen|recipe|bread|dough|basil|salad|swimmer|swim|pool|team|round|agent|player|coach|captain|mint|stock|pan|banana|dinner|pasta|egg|mould)\b", re.I)
n_theme = sum(1 for q in questions if themed.search(q["stem"]))
if questions and n_theme / len(questions) < 0.35:
    err(f"only {n_theme}/{len(questions)} questions look themed (target about 40%)")

used = {c["visual"] for c in cards if c.get("visual")} | {q[k] for q in questions for k in ("visual", "explanation_visual") if q.get(k)}
on_disk = {f"content/biology/{p.name}" for p in (ROOT / "public/content/biology").glob("cards-*.svg")}
for u in sorted(on_disk - used):
    warn(f"unused svg: {u}")
for p in sorted(on_disk):
    svg_text(p, p)
if len(on_disk) < 20:
    err(f"only {len(on_disk)} cards-*.svg diagrams (need >= 20)")

print(f"cards={len(cards)} questions={len(questions)} svgs={len(on_disk)} visual_cards={n_visual} themed={n_theme}")
print("letters:", dict(sorted(letters.items())), "difficulty:", dict(sorted(dd.items())), "types:", dict(tc))
for st in subtopics:
    print(f"  {st:40} cards={cc[st]:3} questions={qc[st]:3}")
for w in warnings:
    print("WARN", w)
for e in errors:
    print("ERROR", e)
print("OK" if not errors else f"FAILED: {len(errors)} problem(s)")
sys.exit(1 if errors else 0)
