# 🔬 HUSO Grade 9

**Preparation for the Harvard Undergraduate Science Olympiad (HUSO) Round 1: a 5-week study plan and a study web app for a Grade 9 visual learner.**

![Rust 1.94+](https://img.shields.io/badge/rust-1.94%2B-orange) ![Renox 1.1](https://img.shields.io/badge/renox-1.1-blue) ![status](https://img.shields.io/badge/status-work%20in%20progress-yellow)

> **Language: everything in this repo is English** (international exam, English-medium school).

## About the project

The student is in Grade 9 (IB MYP 4), a **visual learner** who likes cooking, Valorant and swimming. The goal is a good score in HUSO Round 1. Every study material, question and flashcard is picture-first and uses those three themes ([`docs/STUDENT.md`](docs/STUDENT.md)).

| | |
|---|---|
| **Exam** | Sunday **15 Nov 2026**, 19:30–22:30 WIB (16:30 UAE / 18:00 IST) |
| **Format** | Online, 3 hours, 5 subjects (Mathematics, Physics, Chemistry, Biology, Earth Science), multiple choice A–E |
| **Scoring** | +1 correct, −0.25 wrong, 0 blank; the best 4 subjects count |
| **Registration** | Deadline **31 Oct 2026** ([#2](../../issues/2): confirm eligibility first) |

## What is in the repo

| Part | Location | Notes |
|---|---|---|
| Study plan | issues [#1](../../issues/1)–[#13](../../issues/13), [`content/plan.json`](content/plan.json), [`docs/CURRICULUM.md`](docs/CURRICULUM.md) | 35 days, every subtopic studied once by 7 Nov |
| Learning design | [#14](../../issues/14) | why the plan and the app work the way they do |
| Visual study material | [`materi/`](materi/) (one folder per subject) | one illustrated page per subtopic + a printable cheat sheet |
| Flashcards and questions | `content/flashcards/`, `content/questions/`, `public/content/` (SVG) | original, never copied from official papers |
| Web app | epic [#15](../../issues/15), `src/`, `resources/`, `migrations/` | Renox (Rust + HTMX) |
| Documents | [`docs/PROJECT.md`](docs/PROJECT.md), [`docs/CONTENT.md`](docs/CONTENT.md), [`docs/MATERI.md`](docs/MATERI.md), [`CLAUDE.md`](CLAUDE.md), [`AGENTS.md`](AGENTS.md) | spec, writing rules, agent rules |

## The study plan at a glance

| Phase | Dates | Daily time | Goal |
|---|---|---|---|
| Intensive (school holiday) | 12–18 Oct | 4 hours | diagnostic test, then the first pass over every subject |
| Routine | 19 Oct – 14 Nov | 30 min on school days, 2 h on weekends | finish all 76 subtopics by 7 Nov, readiness exam 8 Nov, remedial 9–13 Nov |
| Exam day | 15 Nov | 3 hours | HUSO Round 1 |

Nine visual-learning principles drive the plan: dual coding (picture and words), redrawing a mind map from memory, colour coding per subject, flashcards with spaced repetition, retrieval practice, an error log, videos and simulations, Pomodoro blocks, and a wall tracker.

## Subject colours

| Slug | Subject | Colour | |
|---|---|---|---|
| `math` | Mathematics | `#2563eb` | 🟦 |
| `physics` | Physics | `#dc2626` | 🟥 |
| `chemistry` | Chemistry | `#ca8a04` | 🟨 |
| `biology` | Biology | `#16a34a` | 🟩 |
| `earth` | Earth Science | `#92400e` | 🟫 |

## Web app

Stack: [Renox](https://github.com/arif-rachim/renox) 1.1 (Rust + Axum + HTMX + Alpine.js + SQLite), one binary, English UI.

| Feature | Issue | Priority | Status |
|---|---|---|---|
| Foundation: layout, navigation, accounts, countdown | [#16](../../issues/16) | P0 | ✅ |
| Content model and seeder | [#17](../../issues/17) | P0 | ✅ |
| Today page | [#18](../../issues/18) | P0 | 🚧 |
| Illustrated flashcards (Leitner) | [#19](../../issues/19) | P0 | 🚧 |
| Question bank with HUSO scoring | [#20](../../issues/20) | P0 | 🚧 |
| Error log | [#21](../../issues/21) | P0 | ⏳ |
| 35-day plan and tracker | [#27](../../issues/27) | P1 | ⏳ |
| Syllabus map | [#28](../../issues/28) | P1 | ⏳ |
| Progress charts | [#29](../../issues/29) | P1 | ⏳ |
| Parent dashboard | [#30](../../issues/30) | P1 | ⏳ |
| Materials page and READY status | [#39](../../issues/39) | P1 | ⏳ |
| "Redraw from memory" canvas | [#31](../../issues/31) | P2 | ⏳ |

## Running the app

Needs Rust 1.94+ and a C compiler.

```bash
cargo install --locked --git https://github.com/arif-rachim/renox --rev 3acc2d1feab8fcb9defa666d15245c314710a609 renox-cli
cp .env.example .env && rnx key:generate
rnx migrate && rnx db:seed     # creates both accounts and loads content/*.json
rnx serve                      # http://127.0.0.1:3000
```

Accounts (change the passwords in `.env` first if the laptop is shared):

| Role | Email | Password |
|---|---|---|
| Student | `student@huso.local` | `study123` |
| Parent (read-only dashboard) | `parent@huso.local` | `study123` |

Other commands: `cargo test`, `rnx content:import` (reload `content/*.json` after editing, `--check` only validates), `rnx build` (a single release binary in `dist/`, for the family laptop).

## How to contribute

- **All work starts from a GitHub issue.** One issue = one branch `feat/issue-N-…` = one PR with `Closes #N`.
- Labels: `epic` (a group of issues), `app` (web app), `content` (flashcards/questions), `materi` (study material), `docs`, `plan`, `P0`/`P1`/`P2` (priority), `ready-for-agent` (can be picked up), `qa`.
- AI agents: read [`CLAUDE.md`](CLAUDE.md), then [`AGENTS.md`](AGENTS.md) and [`docs/PROJECT.md`](docs/PROJECT.md); content follows [`docs/CONTENT.md`](docs/CONTENT.md) and materials follow [`docs/MATERI.md`](docs/MATERI.md).

## Copyright

Official papers (HUSO, AMC, Physics Bowl, USNCO, USABO, USESO) are **linked, never copied** ([`content/sources.json`](content/sources.json)). Every question in this repo is original.

## Official sources

- HUSO: <https://www.husoscience.org/>
- Past papers, syllabus and registration links: [`content/sources.json`](content/sources.json)
