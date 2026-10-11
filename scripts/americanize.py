#!/usr/bin/env python3
"""Normalize British spellings to American English in materi/**/*.md and public/content/**/*.svg.
Usage: python3 scripts/americanize.py   (idempotent; prints the files it changed)"""
import pathlib, re
ROOT = pathlib.Path(__file__).resolve().parent.parent
RULES = [(r"colour", "color"), (r"Colour", "Color"), (r"centre", "center"), (r"Centre", "Center"),
         (r"metre", "meter"), (r"neighbour", "neighbor"), (r"Neighbour", "Neighbor"), (r"favour", "favor"),
         (r"labelled(?!by)", "labeled"), (r"Labelled", "Labeled"), (r"\bgrey\b", "gray"), (r"\bGrey\b", "Gray"),
         (r"\bmaths\b", "math"), (r"\bMaths\b", "Math"), (r"litre", "liter"), (r"programme", "program"),
         (r"analyse", "analyze"), (r"practise", "practice"), (r"\bwhilst\b", "while"), (r"\brices\b", "kinds of rice")]
files = list((ROOT / "materi").rglob("*.md")) + list((ROOT / "public/content").rglob("*.svg")) + [ROOT / "README.md"]
for f in files:
    t = f.read_text(); o = t
    for a, b in RULES: t = re.sub(a, b, t)
    if t != o:
        f.write_text(t); print("changed", f.relative_to(ROOT))
