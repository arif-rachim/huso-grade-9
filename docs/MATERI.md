# Writing the learning material (`materi/<subject>/*.md`)

For the issues "Materi 1–5" (#34–#38). Read first: `docs/STUDENT.md` (the student, parent
feedback, theme bank), `docs/CONTENT.md` (SVG rules, originality). The **reference example** is
`materi/math/algebra-polynomials.md`: copy its structure, tone and level of detail.

## What a subtopic file is
One Markdown file per subtopic (`materi/<subject>/<topic>-<subtopic>.md`) that a Grade 9 visual
learner can read in ~12 minutes, redraw from memory, and test with 5 questions. It must work
**printed from GitHub** and later inside the app, so: plain Markdown, relative links, no HTML
except `<details>`.

### Exact template (the linter `scripts/check_materi.py` enforces it)
```text
# {emoji} {Nama subtopik}  ·  `{slug}`
> 📅 Dipelajari: {tanggal} · ⏱️ Baca ±12 menit · 📋 Silabus: {poin silabus, Inggris, dipisah koma}

{HOOK: 2–3 kalimat dengan emoji tema 🍳 / 🎮 / 🏊 dalam judul "## 🏊 Mulai dari …"}

## 🖼️ Gambaran besar
![alt](../../public/content/{subject}/{name}.svg)
## 💡 Konsep inti            (max 6 numbered points, bold keywords)
## 🧮 Contoh bergaya HUSO    (1–2 MCQ examples in English, numbered solution steps)
## ⚠️ Jebakan umum           (2–4 bullets)
## ✏️ Gambar dari ingatan    (what to draw + 4–6 checkbox items)
## 🎥 Tonton / coba          (1–3 links: "- [Title](url) — channel · 6:42 · what to watch for")
## ✅ Cek Paham (5 soal)     (**1.** … (A) … (B) … (C) … (D) … (E) …, in English)
<details><summary>Kunci & pembahasan</summary>   (lines "1. **(C) 11.** explanation", Indonesian)
</details>
```
The hook section goes between the `>` line and `## 🖼️ Gambaran besar`. The image line **must start
with `!`**.

## Writing rules
- **Indonesian, simple, friendly, "kamu"**; English terms in parentheses on first use. Short
  sentences. Bold the keyword in each point. Math in Unicode (x², √, π, ≤, ½, Σ, →), no LaTeX.
- **Hook from the student's world** (cooking 🍳, Valorant 🎮, swimming 🏊), rotate themes across the
  files of a subject. The hook must lead naturally into the concept and come back in the example
  or a Cek Paham question. Add **"Bedanya:"** when an analogy is not exact.
- Valorant: names/mechanics only (agents, abilities, rounds, sides, credits, economy). **Never
  state real game numbers as facts** (credit prices, bonuses change): write "misalkan" and use
  simple made-up numbers. No official art/logos; draw simple shapes yourself.
- **Stay inside the official syllabus items** of the subtopic (`content/syllabus.json`); go deep,
  not wide. Level: AMC 10 style for maths (examples may reach AMC 10 #10–15 difficulty,
  Cek Paham difficulty 1–2), HUSO difficulty (see the Materi issue of the subject).
- At least **1 theme-based question in Cek Paham** and the worked examples may be themed. The
  theme must not change the maths/science.
- Questions are **original** (never copy HUSO/AMC/USABO/USNCO/USESO/Physics Bowl). Five options
  (A)–(E), one correct, plausible distractors that come from real mistakes; vary the position
  of the correct letter across the 5 questions (no letter used more than twice).

## Diagrams (SVG)
- File names: `public/content/<subject>/<topic>-<what>.svg` (kebab-case, unique per subtopic;
  reuse an existing one if it fits, e.g. `pascal-triangle.svg`). Rules in `docs/CONTENT.md`:
  `viewBox` set, **no width/height**, no script/image/external href, labels as `<text>` ≥ 12 px,
  subject colour (maths `#2563eb`, tints with `fill-opacity`) + greys, white background rect.
- Generate numbers/coordinates with a small Python script instead of by hand when they matter
  (Pascal rows, polygon vertices, circle points); an inaccurate diagram is worse than none.
- **Look at every SVG you make:**
  `CH=$(ls /opt/pw-browsers/chromium*/chrome-linux*/chrome | head -1); "$CH" --headless --no-sandbox --disable-gpu --screenshot=/tmp/x.png --window-size=440,356 file://$PWD/public/content/math/NAME.svg`
  then open `/tmp/x.png` with the Read tool. Fix overlapping text, cut-off labels, wrong shapes.

## Videos and links
- 1–3 links per file, ≤ 12 min each. Find with `python3 scripts/ytfind.py search "query"`
  (prints url | channel | length | title) and verify with `python3 scripts/ytfind.py check URL`.
  Prefer: Khan Academy, Art of Problem Solving, 3Blue1Brown, The Organic Chemistry Tutor,
  CrashCourse, Amoeba Sisters, Professor Dave Explains, Flipping Physics, PhET, GeoGebra,
  Desmos, Stellarium Web. The title must really be about this subtopic. Never guess a URL.
- Interactive tools (GeoGebra/Desmos/PhET) are welcome when they fit; open the page and make
  sure the link works (`check`).

## Checking your work (all required)
1. `python3 scripts/verify/<subject>_<file>.py` — **write this script yourself** for each file:
   it recomputes **every worked example and every Cek Paham answer independently** (plain
   Python, `fractions`, brute force, `itertools`) and `assert`s the stated answer and the key
   distractor reasoning. It must print `OK <n> checks`. Do **not** derive the check from the
   same reasoning chain as the key; compute by brute force/simulation when possible.
2. `python3 scripts/check_materi.py --links materi/<subject>/<your files>` must print `OK`.
3. Re-read the file as the student: any sentence a 14-year-old would stumble on? Any term used
   before it is explained? Fix it.
4. Look at your SVGs rendered (see above).

## Workflow
- Branch `feat/issue-N-materi-<subject>`; do not push to `main` directly. Deadlines per file are in
  the issue table; merge in batches by deadline.
- Add only your files: `materi/<subject>/…`, `public/content/<subject>/…`,
  `scripts/verify/<subject>_….py`.
- Also write `materi/<subject>/README.md` (index table in schedule order with dates and links)
  and `materi/<subject>/lembar-ringkas.md` (1–2 printable pages: formulas/tables only, minimal
  prose, colour-coded with emoji).
