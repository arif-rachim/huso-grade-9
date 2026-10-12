# Huso v0.1.1: ready-to-deploy files

New in 0.1.1: visitors can look around and study **without logging in** (Today, Plan, Materials, Syllabus, Flashcards, Practice menu).
Login is only asked when answering questions or saving anything.

| File | What it is |
|---|---|
| `huso-0.1.1-linux-x86_64.tar.gz` | The program (Linux, x86-64) **and** the ready-made database, with start script and `DEPLOY.md` |
| `huso-0.1.1-app.db` | The database alone (SQLite): syllabus, 35-day plan, 76 lessons, 570 flashcards, 638 questions, the two accounts |
| `SHA256SUMS` | Checksums of the two files |

## Quick start

```bash
curl -LO https://github.com/arif-rachim/huso-grade-9/raw/release/v0.1.1/huso-0.1.1-linux-x86_64.tar.gz
tar xzf huso-0.1.1-linux-x86_64.tar.gz && cd huso-0.1.1-linux-x86_64
./start.sh        # http://127.0.0.1:3000
```

Login `student@huso.local` or `parent@huso.local`, password `study123`: **change both after the first login.**

macOS and Windows: run **Actions > Release > Run workflow** with the tag of a release (for example `0.1.1`) to attach archives
for Linux, macOS and Windows plus the database to that release. This branch is only a download location; the source code is on `main`.
