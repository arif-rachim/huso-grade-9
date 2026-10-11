# HUSO Grade 9: project spec for coding agents

Read this together with `AGENTS.md` (how to write Renox code). This file says **what** to build;
`AGENTS.md` says **how**. When they disagree on Renox usage, `AGENTS.md` wins.

## Product in one paragraph

A web app on the family laptop that helps one Grade 9 (IB MYP 4) student prepare for the
**Harvard Undergraduate Science Olympiad (HUSO) Round 1** on **Sunday 15 Nov 2026,
19:30–22:30 WIB**. The student is a **visual learner**. The app shows today's plan, runs
picture-first flashcards with spaced repetition, a question bank with HUSO's scoring, an
automatic error log, a colour-coded syllabus map of mastery, and progress charts. A parent
account sees the same data read-only. The study plan itself lives in GitHub issues #1–#13
and, as data, in `content/plan.json`. The design rationale is issue #14.

## Hard rules

- **UI language: Indonesian (Bahasa Indonesia).** Every user-facing text goes through
  translations in `resources/lang/id.json` (`APP_LOCALE=id`, `APP_FALLBACK_LOCALE=en`).
  Syllabus item names stay in English as in the official syllabus (the exam is in English).
  Code, identifiers, comments, commit messages and tests are in **English**.
- **Time zone:** `APP_TIMEZONE=Asia/Jakarta`. "Today" is the Jakarta date. Read time with
  `renox::db::now()` only (tests use `app.travel`).
- **Device:** a laptop, desktop-first layout (≥ 1024 px), with keyboard shortcuts for the
  repetitive actions (flashcards, answering questions). It must still be usable at 768 px.
- **Visual first.** Every concept, flashcard and explanation should carry a picture
  (an SVG in `public/content/…`) or, when a picture can't be drawn well as SVG, a
  `sketch_prompt` telling the student what to draw on paper. Colour is information: always
  use the subject colours below, never other colours for subjects.
- **Single household.** Exactly two roles: `student` and `parent`. No public sign-up after
  the two accounts exist (see issue "Fondasi").
- **Copyright:** official papers (HUSO, AMC, Physics Bowl, USNCO, USABO, USESO) are stored
  **as links only** (`content/sources.json`). Never copy their questions into the repo.
  Questions in `content/questions/` are **original** (written by an agent or the parent).
- **No JavaScript of our own** unless Renox has no way: use the UI kit tags, htmx and live
  components. No CDN scripts (CSP). No LaTeX: write math with Unicode (x², √2, π, ≤, →, ½).
- Deadline: features marked **P0** must work by **Mon 19 Oct 2026** (the 30‑minute daily
  phase starts). P1 by 1 Nov. P2 is optional.

## Subjects and colours (fixed)

| slug | Name (UI) | Colour | Emoji |
|---|---|---|---|
| `math` | Matematika | `#2563eb` | 🟦 |
| `physics` | Fisika | `#dc2626` | 🟥 |
| `chemistry` | Kimia | `#ca8a04` | 🟨 |
| `biology` | Biologi | `#16a34a` | 🟩 |
| `earth` | Earth Science | `#92400e` | 🟫 |

Define them once as CSS custom properties in `public/app.css` (`--subject-math`, …) and once
in Rust (the `subjects` table, seeded from `content/syllabus.json`). Templates read the colour
from the row, never hard-code it.

## HUSO scoring (must be exact)

- Every question: 5 choices A–E, exactly one correct.
- Raw score per subject = `correct × 1 − wrong × 0.25` (blank = 0). Store **quarter points
  as integers** (`raw_q = 4·correct − wrong`) to avoid floats; show `raw_q / 4` with 2 decimals.
- The real exam converts each subject to a z-score and sums the **best four**. We can't
  compute z-scores (no other students), so the app shows, for a simulation: raw score per
  subject, percent correct per subject, and "total of the best four by percent" with the
  dropped subject named.
- Exam timing: 3 hours, about 36 minutes per subject. Biology ±40 questions, Earth Science
  ±45, Chemistry ±35, Math ±12 (2024 paper).

## Content files (the source of truth; seeded into the database)

All under `content/`. JSON, UTF-8, 2-space indent. A Rust test validates every file
(issue "Model konten & seeder"). Ids are stable strings: never renumber.

- `content/syllabus.json`: `subjects[] → topics[] → children[]` (subtopics) `→ items[]`.
  Slugs are dotted paths: `biology.cell.division`. **Subtopic** is the unit whose mastery
  is tracked; 76 subtopics in total.
- `content/plan.json`: 35 `days` (2026‑10‑12 … 2026‑11‑15), each with `date`, `phase`
  (`intensive` | `daily` | `exam`), `minutes`, `subject` (a subject slug or `diagnostic`,
  `mixed`, `review`, `prep`, `exam`), `title`, `issue` (GitHub issue number), `blocks[]`
  (`label`, `minutes`, `tasks[]` strings).
- `content/sources.json`: official links, past papers (links + question counts), practice
  and visual resources per subject.
- `content/flashcards/<subject>.json` (written by the content issues):

  ```json
  {
    "version": 1,
    "subject": "biology",
    "cards": [
      {
        "id": "biology-0001",
        "subtopic": "biology.anatomy.circulatory",
        "type": "basic",
        "front": "Which heart chamber pumps blood to the whole body?",
        "back": "The left ventricle (thickest wall) → aorta.",
        "visual": "content/biology/heart-chambers.svg",
        "sketch_prompt": null,
        "tags": ["diagram"]
      }
    ]
  }
  ```

  `type`: `basic` (front/back), `cloze` (`front` contains `{{…}}` gaps), `order` (`items[]`
  in the right order; shown shuffled), `match` (`pairs[]` of `[left, right]`),
  `occlusion` (`visual` is an SVG whose elements with `data-label="…"` are hidden one at a
  time; `back` lists the labels). `visual` is a path under `public/`; at least one of
  `visual` or `sketch_prompt` is set on every card. Front/back are in **English**
  (international exam, English-medium school; see `docs/STUDENT.md`).
- `content/questions/<subject>.json`:

  ```json
  {
    "version": 1,
    "subject": "physics",
    "questions": [
      {
        "id": "physics-0001",
        "subtopic": "physics.mechanics.kinematics",
        "difficulty": 1,
        "stem": "A car accelerates uniformly from rest to 20 m/s in 5 s. How far does it travel?",
        "visual": null,
        "choices": { "A": "20 m", "B": "40 m", "C": "50 m", "D": "80 m", "E": "100 m" },
        "answer": "C",
        "explanation": "x = ½·(v₀+v)·t = ½·20·5 = 50 m.",
        "explanation_visual": "content/physics/vt-graph-area.svg",
        "source": "original"
      }
    ]
  }
  ```

  Questions and explanations are in **English** (like the exam).
  `difficulty`: 1 = HUSO's quick opening questions, 2 = typical, 3 = hard (AMC 10 #15+,
  USNCO National). Each question must be checked by solving it independently before commit.
- SVGs: `public/content/<subject>/<name>.svg`, `viewBox` set, no external refs, no scripts,
  readable at 320 px wide, use the subject colour plus greys. Labels as `<text>`.

## Domain model (tables)

Names are a guide; keep them unless a Renox convention says otherwise. All rows that belong to
the student carry `user_id`.

| Table | Key fields |
|---|---|
| `subjects` | `slug` (unique), `name`, `color`, `emoji`, `position` |
| `topics` | `slug` (unique), `subject_id`, `parent_id` (null for topic, set for subtopic), `name`, `items` (JSON text), `position` |
| `plan_days` | `date` (unique), `phase`, `minutes`, `subject` (text slug), `title`, `issue` |
| `plan_tasks` | `plan_day_id`, `block_label`, `block_minutes`, `label`, `position` |
| `task_checks` | `user_id`, `plan_task_id`, `checked_at` (unique per user+task) |
| `study_sessions` | `user_id`, `date`, `minutes`, `subject` , `note` |
| `flashcards` | `key` (the JSON id, unique), `topic_id`, `type`, `front`, `back`, `visual`, `sketch_prompt`, `payload` (JSON for items/pairs), `origin` (`content`/`manual`) |
| `card_states` | `user_id`, `flashcard_id`, `box` (1–5), `due_on` (date), `reviews`, `lapses`, `last_grade` |
| `card_reviews` | `user_id`, `flashcard_id`, `grade` (`again`/`hard`/`good`/`easy`), `reviewed_at`, `box_before`, `box_after` |
| `questions` | `key` (unique), `topic_id`, `difficulty`, `stem`, `visual`, `choice_a`…`choice_e`, `answer`, `explanation`, `explanation_visual`, `source` |
| `attempts` | `user_id`, `mode` (`topic`/`sprint`/`mixed`/`simulation`/`errors`), `started_at`, `finished_at`, `time_limit_secs`, `subject` (nullable) |
| `answers` | `attempt_id`, `question_id`, `choice` (nullable = blank), `is_correct`, `guessed`, `seconds` |
| `error_entries` | `user_id`, `answer_id` (nullable), `external_log_id` (nullable), `topic_id`, `cause` (`concept`/`calculation`/`misread`/`rushed`/`guess`), `note`, `photo` (upload path), `box`, `due_on`, `resolved_at` |
| `external_logs` | `user_id`, `date`, `source` (e.g. `huso-2024-r1`, `amc10`), `subject`, `topic_id` (nullable), `correct`, `wrong`, `blank`, `minutes`, `note` |

Leitner boxes (flashcards and error entries): box 1 = every day, 2 = every 2 days,
3 = every 4 days, 4 = every 7 days, 5 = every 14 days. `again` → box 1; `hard` → same box;
`good` → box + 1; `easy` → box + 2 (max 5). `due_on = today + interval(box)`. New cards start in
box 1, due today. Cap new cards at 20 per day.

**Mastery of a subtopic** (0–100, or "not started"), used by the syllabus map:
`round(100 × (0.6 × question accuracy over the last 14 days + 0.4 × share of its cards in box ≥ 3))`,
where a guessed correct answer counts as half correct. With fewer than 3 answers and no
reviewed cards: "not started". Colours: not started = grey, < 40 red, 40–69 yellow, ≥ 70 green.

## Modules (one Renox module each, under `src/app/`)

| Module | Routes (names) | Issue |
|---|---|---|
| `home` | `/` → redirect to `/today` when logged in | Fondasi |
| `content` | none (seeder + models + `content:import` command) | Model konten & seeder |
| `today` | `/today` (`today.index`) | Halaman Hari Ini |
| `plan` | `/plan` (`plan.index`), `/plan/{date}` (`plan.show`) | Jadwal & tracker |
| `flashcards` | `/flashcards` (`flashcards.index`), `/flashcards/review` (`flashcards.review`), CRUD for manual cards | Flashcard |
| `practice` | `/practice` (`practice.index`), `/practice/{attempt}` (`practice.show`), `/practice/{attempt}/result` (`practice.result`) | Bank soal |
| `errors` | `/errors` (`errors.index`), `/errors/review` (`errors.review`) | Error log |
| `syllabus` | `/syllabus` (`syllabus.index`), `/syllabus/{slug}` (`syllabus.show`) | Peta silabus |
| `progress` | `/progress` (`progress.index`), `/progress/log` (`progress.log`) | Progres |
| `parent` | `/parent` (`parent.index`), `require_role("parent")` | Dashboard orang tua |

Navigation (top `<rx-navbar>`): Hari Ini · Jadwal · Flashcard · Latihan · Error Log · Silabus ·
Progres (· Orang Tua for the parent). Show a countdown "H‑N menuju HUSO" in the navbar.

## Definition of done (every issue)

1. The acceptance criteria in the issue are met and each has a test in `tests/` (Renox
   `TestApp`; use `app.travel` for dates).
2. `cargo fmt`, `cargo clippy --all-targets -- -D warnings`, `cargo test`, `rnx db:check`,
   `rnx view:check` all pass.
3. New texts are in `resources/lang/id.json`.
4. Tried in the browser with `rnx serve` at 1280 px wide; describe what you checked in the PR.
5. One PR per issue, branch `feat/issue-N-short-name` from the default branch, body with `Closes #N`.

## Running it

```bash
cp .env.example .env && rnx key:generate
rnx migrate && rnx db:seed     # loads content/*.json and the two accounts
rnx serve                       # http://127.0.0.1:3000
```
