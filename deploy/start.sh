#!/usr/bin/env bash
# Starts Huso. The first time it also creates .env with a fresh secret key.
set -e
cd "$(dirname "$0")"
if [ ! -f .env ]; then
  cp env.example .env
  key="base64:$(head -c 32 /dev/urandom | base64)"
  sed -i.bak "s|^APP_KEY=.*|APP_KEY=$key|" .env && rm -f .env.bak
  echo "Created .env with a new APP_KEY."
fi
mkdir -p storage
exec ./huso serve
