#!/usr/bin/env bash
# deploy.sh <tag>: install one release of piobc and switch to it
set -euo pipefail

TAG="$1"
BASE=/opt/piobc
REPO=$BASE/repo
DEST=$BASE/releases/$TAG

git -C "$REPO" fetch --tags --quiet

if [ ! -d "$DEST" ]; then
    TMP="$DEST.tmp"
    rm -rf "$TMP" && mkdir -p "$TMP"
    git -C "$REPO" archive "$TAG" | tar -x -C "$TMP"
    python3 -m venv "$TMP/.venv"
    "$TMP/.venv/bin/pip" install --quiet -r "$TMP/requirements.txt"
    mv "$TMP" "$DEST"
fi

ln -sfn "$DEST" "$BASE/current"
sudo systemctl restart monitor.service lcd.service
echo "deployed $TAG"
