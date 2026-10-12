# QA report: independent check of the AI-written content (issue #40)

Reviewer: second agent (not the content authors). Scope: content on `main` at `6df8767`.

## Method

1. **Questions, blind solve.** For each subject a random sample (Python `random.seed(40)`) was printed as
   stem + choices only (no `answer`, no `explanation`). Each question was solved from scratch (arithmetic
   re-checked in my head or with Python), the choice written down, and only then compared with the key by script.
2. **Extra hard-question pass.** A further 12 difficulty-3 questions (seed 41, not in the first sample) were
   blind-solved for Math, Physics and Chemistry, where a wrong key is most likely.
3. **Flashcards.** 20 random cards per subject (seed 40) were read for factual accuracy. For all 76 `occlusion`
   cards a script compared the labels in `back` with the `data-label` attributes of the SVG.
4. **Materials.** For 3 files per subject (+ the files that carry the author-flagged facts) only the
   "Common traps" section and the "Check your understanding" questions and keys were read, and every question was
   re-solved.
5. **Repo checks.** `scripts/check_content_<subject>.py` for all five subjects and `scripts/check_materi.py` pass.

## Sample sizes

| Item | Math | Physics | Biology | Chemistry | Earth | Total |
|---|---|---|---|---|---|---|
| Questions blind-solved (main sample) | 30/120 | 30/88 | 30/131 | 35/142 | 35/157 | 160 |
| Extra difficulty-3 questions | 12 | 12 | - | 12 | - | 36 |
| Flashcards read | 20/110 | 20/88 | 20/118 | 20/122 | 20/132 | 100 |
| Occlusion cards checked against SVG (all) | | | | | | 76 |
| Materials files (traps + check questions) | 3 | 3 | 3 (+ tissues) | 3 | 4 | 16 |

Material files read: math `algebra-polynomials`, `geometry-triangles`, `number-theory-modular`; physics `mechanics-shm`,
`thermodynamics-laws`, `electromagnetism-circuits`; biology `anatomy-immune`, `cell-photosynthesis`, `anatomy-nervous`
(plus the relevant lines of `anatomy-tissues`, `anatomy-circulatory`); chemistry `analytical-acid-base`,
`physical-thermo`, `organic-reactions`; earth `astronomy-solar-system`, `astronomy-sphere`, `geosphere-rocks`,
`atmosphere-fronts` (plus the Bowen section of `geosphere-geochemistry`).
That is 16 files with every key line re-derived (80 material questions).

## Result

**No confirmed errors.** All 196 blind-solved questions matched the key (160 + 36). All 100 sampled flashcards are
factually correct, all 76 occlusion cards list exactly the labels that exist in their SVG, and all re-solved
material questions and traps are correct. Nothing was edited in `content/` or `materi/`.

## Findings table

| id | issue | severity | fixed |
|---|---|---|---|
| earth-0073 | Stem says "the water table roughly follows the land surface" and asks which well is deeper. Key A (hilltop well is deeper) is correct (the water table is a smoothed copy of the relief, so it lies deeper under hills), but a student may read "follows the surface" as "same depth". Wording could say "is a smoothed copy of the land surface". | low (wording) | no (not an error) |
| earth-0080 | "Most likely found together": A (quartz + muscovite) is the best answer and the explanation is right; B (olivine + quartz) is rare in nature but not impossible. Acceptable for "most likely". | low (note) | no |
| materi/chemistry/organic-reactions Q5 | "Cooking oil" decolorizing bromine water assumes an unsaturated oil (olive, sunflower). A mostly saturated oil (coconut, palm kernel) would react slowly. Fine for the intended lesson. | low (note) | no |
| biology-0124 | Amoeba is keyed to Protista, which is right; the distractor "Monera" belongs to the older five-kingdom scheme. Consistent with the syllabus if the syllabus uses Protista. | info | no |
| physics-0015 | Key 37 N is the rounded 36.75 N; no other option is within rounding, so no ambiguity. | info | no |

No finding needed a fix, so no ids or checks were touched (all `check_content_*.py` and `check_materi.py` still pass).

## Facts with a single or weak source that deserve a human spot-check

These were flagged by the authors; my re-check from general knowledge is in brackets. A parent or teacher should
confirm them with a textbook.

Biology
- **Lymph composition** (lymph is mostly white blood cells/lymphocytes, no red cells; "lymph nodes filter germs and
  contain white blood cells"; `biology-0114`, circulatory page). [Consistent with standard texts.]
- **Destarching time** ("dark for a day or two", `cell-photosynthesis`). [Textbooks say 24-48 h; some plants need
  longer, and the exam would only expect "kept in the dark".]
- **Ligament = bone to bone, tendon = muscle to bone** (`anatomy-tissues`). [Correct, standard school definition.]
- **Blinking and coughing as reflexes handled "lower in the brain"** (`anatomy-nervous`). [Correct: brainstem. Cough is
  partly voluntary too. The page already hedges.]

Earth
- **Polaris "about the 50th brightest"** (`astronomy-sphere`). [Apparent magnitude 1.98 puts it around 48th-50th
  depending on the list; "about" is safe. Distance "about 430 ly" is within the quoted 430-445 ly.]
- **Oort cloud "about 2,000 to 100,000 AU"** (`astronomy-solar-system`). [Sources give inner edge 2,000-5,000 AU and
  outer edge 50,000-200,000 AU; the numbers are a reasonable middle.]
- **Voyager crossings**: Voyager 1 into interstellar space in 2012, Voyager 2 in 2018. [Correct (Aug 2012, Nov 2018).]
- **Bowen series coexistence question** (`earth-0080`). [Key is the best answer; see the finding above.]

Other items worth a quick look by a human (not wrong, but convention-dependent)
- Gas molar volume 22.4 L at "STP (0 °C, 1 atm)" (chemistry cards): current IUPAC STP uses 1 bar (22.7 L); the
  HUSO/school convention of 22.4 L is fine but the exam may state the molar volume.
- Mohs hardness of a copper coin (3.5) and steel knife (5.5) in `geosphere-geochemistry`: common field-test values,
  coin hardness varies from 3 to 3.5.
- Hurricane wind threshold "over 119 km/h" on `earth-0030`'s SVG: correct for hurricane/typhoon (74 mph).

## Limits of this review

- 196 of 638 questions (31%) were blind-solved; the remainder were only covered by the authors' own check scripts.
  The sampled error rate was 0/196, so a residual error rate above about 1.5% in the whole bank is unlikely (95%
  confidence), but not impossible, especially in the unsampled difficulty-1/2 earth and biology fact questions.
- Videos/links and the visual rendering of the SVGs were not opened in a browser; only SVG labels were parsed.
- Reading the materials was limited to "Common traps" and "Check your understanding", as requested; the "Core
  ideas" text of the unsampled 61 files was not reviewed.
