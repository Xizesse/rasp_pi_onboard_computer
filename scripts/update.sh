#!/usr/bin/env bash
# update.sh: if GitHub has a newer release than the one running, deploy it
set -euo pipefail

BASE=/opt/piobc
REPO=$BASE/repo

git -C "$REPO" fetch --tags --quiet
LATEST=$(git -C "$REPO" tag --sort=-v:refname | head -n1)
CURRENT=$(basename "$(readlink "$BASE/current")")

if [ "$LATEST" = "$CURRENT" ]; then
    echo "up to date ($CURRENT)"
else
    echo "updating $CURRENT -> $LATEST"
    "$BASE/bin/deploy.sh" "$LATEST"
fi
