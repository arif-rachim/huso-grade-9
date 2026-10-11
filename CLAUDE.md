@AGENTS.md
@docs/PROJECT.md

## Working on an issue in this repo

- Start from a GitHub issue labelled `ready-for-agent`. Read the whole issue, its parent epic
  (#15 for the app, #1 for the study plan) and the files it names before writing code.
- Respect the issue's "Depends on": don't start an issue whose dependencies are still open.
- Branch `feat/issue-N-short-name` from the up-to-date default branch; one PR per issue with `Closes #N`.
- Content issues follow docs/CONTENT.md; they only add files under `content/` and `public/content/`
  and must pass `cargo test --test content`.
- **Any learning material or question** (issues Materi, Konten, QA) must follow
  `docs/STUDENT.md` (student profile + parent feedback: visual, simple, themes cooking / Valorant /
  swimming). Record new parent feedback in its "Log feedback" section.
