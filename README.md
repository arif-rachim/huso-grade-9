# HUSO Grade 9

Persiapan **Harvard Undergraduate Science Olympiad (HUSO) Round 1**, Minggu 15 Nov 2026,
untuk siswa Grade 9 (IB MYP 4), visual learner.

- **Rencana belajar:** GitHub issue #1 (epic) dan #2–#13 (harian/mingguan), juga sebagai data di
  [`content/plan.json`](content/plan.json).
- **Aplikasi web:** dibangun dengan [Renox](https://github.com/arif-rachim/renox) 1.1 (Rust + HTMX +
  SQLite). Spesifikasi: [`docs/PROJECT.md`](docs/PROJECT.md). Desain mekanisme belajar: issue #14.
  Daftar pekerjaan: epic #15.
- **Konten:** silabus resmi Grade 9–10 ([`content/syllabus.json`](content/syllabus.json)), sumber &
  link soal resmi ([`content/sources.json`](content/sources.json)), flashcard & soal orisinal
  (`content/flashcards/`, `content/questions/`).

## Menjalankan aplikasi

Butuh Rust 1.94+ dan `rnx`:

```bash
cargo install --locked --git https://github.com/arif-rachim/renox --rev 3acc2d1feab8fcb9defa666d15245c314710a609 renox-cli
cp .env.example .env && rnx key:generate
rnx migrate && rnx db:seed
rnx serve        # http://127.0.0.1:3000
```

Tes: `cargo test`. Agen (Claude Code): baca `CLAUDE.md`.
