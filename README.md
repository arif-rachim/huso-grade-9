# HUSO Grade 9

Preparation for the **Harvard Undergraduate Science Olympiad (HUSO) Round 1**, Sunday 15 Nov 2026,
for a Grade 9 (IB MYP 4) visual learner.

> **Language: everything in this repo is in English** (international exam, English-medium school).

- **Study plan:** GitHub issue #1 (epic) and its sub-issues, also as data in [`content/plan.json`](content/plan.json).
- **Web app:** built with [Renox](https://github.com/arif-rachim/renox) 1.1 (Rust + HTMX + SQLite).
  Spec: [`docs/PROJECT.md`](docs/PROJECT.md). Learning-mechanism design: issue #14. Work list: epic #15.
- **Content:** the official Grade 9–10 syllabus ([`content/syllabus.json`](content/syllabus.json)), sources and
  links to official papers ([`content/sources.json`](content/sources.json)), original flashcards and questions
  (`content/flashcards/`, `content/questions/`), and the visual study material in [`materi/`](materi/).
- **Student profile and parent feedback:** [`docs/STUDENT.md`](docs/STUDENT.md).

## Run the app

Needs Rust 1.94+ and `rnx`:

```bash
cargo install --locked --git https://github.com/arif-rachim/renox --rev 3acc2d1feab8fcb9defa666d15245c314710a609 renox-cli
cp .env.example .env && rnx key:generate
rnx migrate && rnx db:seed
rnx serve        # http://127.0.0.1:3000
```

Tests: `cargo test`. Agents (Claude Code): read `CLAUDE.md`.
