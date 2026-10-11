# Writing content (flashcards, questions, SVG diagrams)

> **Read `docs/STUDENT.md` first**: student profile and parent feedback (visual learner; use the
> student's interests — cooking, Valorant, swimming — for hooks, analogies and ~40 % of word
> problems). It overrides the style rules below where they differ.

Shared rules for the content issues ("Konten 1–5"). The JSON formats are in
`docs/PROJECT.md` → "Content files". Each content issue only adds files under
`content/flashcards/`, `content/questions/` and `public/content/<subject>/`; it never changes Rust code.

## Files and ids

- `content/flashcards/<subject>.json`, ids `<subject>-0001`, `<subject>-0002`, … (4 digits, never reused).
- `content/questions/<subject>.json`, ids `<subject>-0001`, … (separate sequence from flashcards).
- `public/content/<subject>/<descriptive-kebab-name>.svg`, referenced as `content/<subject>/<name>.svg`.
- Every card and question names a **subtopic** slug from `content/syllabus.json` (level 2, e.g.
  `biology.cell.division`). Every subtopic of the subject must be covered.

## Language and style

- **Questions in English** (the exam is in English). Flashcard `back` and question `explanation`
  may be Indonesian, with the English term in parentheses: "inti sel (nucleus)".
- Math with Unicode: x², x³, √2, π, ≤, ≥, ≠, ½, ·, →, Δ, θ, °. **No LaTeX.**
- Five choices A–E, exactly one correct, all different, similar length. Distractors come from
  real mistakes (wrong sign, forgot a case, unit slip, swapped terms), never jokes.
- Difficulty mix per subtopic ≈ 40 % `1` (quick: definition, unit, one step), 40 % `2`
  (typical: two steps), 20 % `3` (hard: several steps or a trap).
- **Original only.** Never copy or lightly reword questions from HUSO, AMC, Physics Bowl, USNCO,
  USABO, USESO or textbooks. Their *style* is the target, not their text. `source` is always
  `"original"`.

## Flashcards for a visual learner

- At least **50 %** of cards have a `visual` SVG; the rest have a `sketch_prompt` that tells
  the student exactly what to draw ("Gambar sel tumbuhan, beri label 6 organel: …").
- Prefer `occlusion` for labelled diagrams, `order` for processes and sequences (≥ 3 items),
  `match` for pairs to memorise (≥ 3 pairs), `cloze` for formulas and definitions, `basic`
  for the rest.
- One idea per card. Front ≤ 25 words. Back ≤ 40 words.
- Each formula the student must know by heart is a card (the exam gives constants, not formulas).

## SVG rules

- `viewBox` set, no `width`/`height` in px (the app scales it), readable at 320 px wide.
- Colours: the subject colour (math `#2563eb`, physics `#dc2626`, chemistry `#ca8a04`,
  biology `#16a34a`, earth `#92400e`) plus greys (`#111827`, `#6b7280`, `#d1d5db`) and white.
  A light tint of the subject colour (opacity 0.15) for fills.
- Text as `<text>` with `font-family="sans-serif"` and `font-size` ≥ 12 (in viewBox units at
  a ~400-wide viewBox). No embedded fonts, images, `<script>`, `<foreignObject>` or external
  `href`.
- For `occlusion`, each hideable label is a `<g data-label="name">` (or a `<text data-label=…>`)
  and the card's `back` lists the names in the same order.
- Hand-written, simple and clean: arrows, axes, boxes, labels. Accuracy beats beauty
  (correct number of heart chambers, correct order of atmospheric layers, correct graph shape).
- Re-use a diagram in several cards and explanations instead of drawing near-duplicates.

## Verifying (mandatory)

1. After writing each question, **solve it again from scratch without looking at the key**.
   If your answer differs or two choices could be right, fix the question.
2. Check every number in explanations (units, significant figures, arithmetic).
3. Run `cargo test --test content` until green (ids, subtopics, choices, answer, SVG paths).
4. Count coverage per subtopic with a small script and paste the table in the PR:

   ```bash
   python3 - <<'PY'
   import json, collections, sys
   s = sys.argv[1] if len(sys.argv) > 1 else "biology"
   c = collections.Counter(x["subtopic"] for x in json.load(open(f"content/flashcards/{s}.json"))["cards"])
   q = collections.Counter(x["subtopic"] for x in json.load(open(f"content/questions/{s}.json"))["questions"])
   for t in sorted(set(c) | set(q)): print(f"{t:45} cards={c[t]:3} questions={q[t]:3}")
   PY
   ```
5. If the app's flashcard/practice pages exist, `rnx content:import` and look at a few cards and
   questions in `rnx serve`; describe what you checked in the PR.

## Working in batches

Large JSON files are easier to get right in batches: write one topic (its subtopics) at a time,
run the content test, commit, continue. One PR per subject issue.
