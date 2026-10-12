# Deploying Huso

This folder is everything the app needs: the program (`huso`, one file with all pages and pictures inside)
and the database (`storage/app.db`) that already holds the whole syllabus, the 35-day plan, 76 lessons,
570 flashcards, 638 questions and the two accounts.

## Run it

Pick the archive for your computer from the release (`linux-x86_64`, `macos-arm64` or `windows-x86_64`).

```bash
# Linux and macOS
tar xzf huso-VERSION-PLATFORM.tar.gz && cd huso-VERSION-PLATFORM
./start.sh            # first run creates .env with a fresh APP_KEY, then serves on http://127.0.0.1:3000
```

```powershell
# Windows (PowerShell): tar -xzf huso-VERSION-windows-x86_64.tar.gz, open the folder, then
powershell -ExecutionPolicy Bypass -File .\start.ps1
```

On macOS the first start may be blocked because the program is not signed: run `xattr -d com.apple.quarantine huso` once.

Open <http://127.0.0.1:3000> and log in:

| Role | Email | Password |
|---|---|---|
| Student | `student@huso.local` | `study123` |
| Parent (read-only dashboard) | `parent@huso.local` | `study123` |

**Change both passwords first** (Account page, top right) if the app is reachable by anyone else.

## On a server

1. Copy the folder to `/opt/huso`, edit `.env`: `APP_URL` (your public address) and `APP_HOST=0.0.0.0` (or keep `127.0.0.1` behind a proxy on the same machine).
2. Production mode sends cookies over HTTPS only (except on 127.0.0.1): put a proxy with HTTPS in front (for example Caddy: `huso.example.com { reverse_proxy 127.0.0.1:3000 }`).
3. Run it as a service with `huso.service` (systemd).

## Your data

Everything the student does (ticks, reviews, answers, errors, drawings) is stored in `storage/app.db` and `storage/app/`. Back up the `storage/` folder (copy it while the app is stopped, or use `sqlite3 storage/app.db ".backup backup.db"`).

## New content later

The content in the database comes from the repository files (`content/`, `materi/`). To load new content, use the source repository: `rnx content:import`, then copy the new `storage/app.db` here. Do not overwrite `storage/app.db` after the student has started studying, unless you want to lose progress.

## Other commands

`./huso help` lists them (`migrate`, `db:seed`, `route:list`, ...).
