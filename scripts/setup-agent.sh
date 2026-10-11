#!/usr/bin/env bash
# Prepares a fresh (cloud) session: installs the `rnx` CLI at the Renox revision pinned in
# Cargo.toml and creates .env. Safe to run repeatedly. Used by the SessionStart hook.
set -euo pipefail
cd "$(dirname "$0")/.."

rev=$(sed -n 's/^renox = .*rev = "\([0-9a-f]*\)".*/\1/p' Cargo.toml)
if ! command -v rnx >/dev/null 2>&1; then
  echo "Installing rnx (renox-cli @ ${rev:-main})…"
  cargo install --locked --git https://github.com/arif-rachim/renox ${rev:+--rev "$rev"} renox-cli >/dev/null 2>&1 \
    || echo "WARN: rnx install failed; run: cargo install --locked --git https://github.com/arif-rachim/renox --rev $rev renox-cli"
fi

if [ ! -f .env ]; then
  cp .env.example .env
  command -v rnx >/dev/null 2>&1 && rnx key:generate >/dev/null 2>&1 || true
fi
echo "Ready: rnx $(rnx --version 2>/dev/null | awk '{print $2}'), .env present. See CLAUDE.md and docs/PROJECT.md."
