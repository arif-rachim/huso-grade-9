#!/usr/bin/env python3
"""Validate content/plan.json (plan v2, issue #33).

Checks: 35 consecutive dates 2026-10-12..2026-11-15; each day's minutes equal the sum of its
blocks; every syllabus subtopic appears in exactly one block's `subtopics` (and nowhere after
2026-11-07); `new_subtopics` of a day equals the union of its blocks' subtopics; phases and
subjects are valid; all text is English (no Indonesian words, no mojibake).

Usage: python3 scripts/check_plan.py
"""
import datetime
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
plan = json.loads((ROOT / "content/plan.json").read_text(encoding="utf-8"))
syl = json.loads((ROOT / "content/syllabus.json").read_text(encoding="utf-8"))

errors = []


def err(msg):
    errors.append(msg)


subtopics = [c["slug"] for s in syl["subjects"] for t in s["topics"] for c in t["children"]]
subject_slugs = {s["slug"] for s in syl["subjects"]}
PHASES = {"intensive", "daily", "weekend", "readiness", "exam"}
SUBJECTS = subject_slugs | {"diagnostic", "mixed", "prep", "exam"}
LAST_NEW = "2026-11-07"

days = plan["days"]
if len(days) != 35:
    err(f"expected 35 days, found {len(days)}")
start = datetime.date(2026, 10, 12)
for i, d in enumerate(days):
    want = (start + datetime.timedelta(days=i)).isoformat()
    if d["date"] != want:
        err(f"day {i}: expected date {want}, found {d['date']}")
    if d["phase"] not in PHASES:
        err(f"{d['date']}: bad phase {d['phase']}")
    if d["subject"] not in SUBJECTS:
        err(f"{d['date']}: bad subject {d['subject']}")
    total = sum(b["minutes"] for b in d["blocks"])
    if total != d["minutes"]:
        err(f"{d['date']}: minutes {d['minutes']} != sum of blocks {total}")

seen = {}
for d in days:
    in_blocks = []
    for b in d["blocks"]:
        for s in b.get("subtopics", []):
            in_blocks.append(s)
            if s not in subtopics:
                err(f"{d['date']}: unknown subtopic {s}")
            if s in seen:
                err(f"{s}: studied twice ({seen[s]} and {d['date']})")
            seen[s] = d["date"]
            if d["date"] > LAST_NEW:
                err(f"{d['date']}: new subtopic {s} after {LAST_NEW}")
    if sorted(in_blocks) != sorted(d.get("new_subtopics", [])):
        err(f"{d['date']}: new_subtopics differs from the blocks' subtopics")
missing = [s for s in subtopics if s not in seen]
if missing:
    err(f"subtopics never studied: {missing}")
if len(subtopics) != 76:
    err(f"syllabus has {len(subtopics)} subtopics, expected 76")

# Language check: English only.
INDONESIAN = set(
    "dan yang untuk dengan tidak adalah jadwal belajar siapkan buat tempel kalender ujian "
    "hari minggu senin selasa rabu kamis jumat sabtu mapel matematika fisika kimia biologi "
    "koreksi salah benar soal pemantapan persiapan tes simulasi sebelum sesudah atau dari "
    "pada ini itu juga sudah akan bisa kerjakan baca gambar catat lembar".split()
)


def strings(o):
    if isinstance(o, str):
        yield o
    elif isinstance(o, dict):
        for k, v in o.items():
            if k != "$comment":
                yield from strings(v)
    elif isinstance(o, list):
        for v in o:
            yield from strings(v)


for text in strings(plan):
    words = set(re.findall(r"[a-z]+", text.lower()))
    bad = words & INDONESIAN
    if bad:
        err(f"Indonesian words {sorted(bad)} in: {text}")
    if "�" in text or "Ã" in text:
        err(f"broken encoding in: {text}")

if errors:
    print("\n".join(errors))
    sys.exit(1)
print(f"OK: {len(days)} days, {len(seen)} subtopics each studied once, last new material {max(seen.values())}")
