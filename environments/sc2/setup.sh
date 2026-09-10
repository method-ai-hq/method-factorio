#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"
if [[ ! -x local/sc2/.venv/bin/python ]]; then
  uv venv --python 3.10 local/sc2/.venv
fi
uv pip sync --python local/sc2/.venv/bin/python environments/sc2/requirements.lock
mkdir -p local/sc2/downloads local/sc2/Maps
archive=local/sc2/downloads/mini_games.zip
curl -fL --retry 2 -o "$archive" https://github.com/google-deepmind/pysc2/releases/download/v1.0/mini_games.zip
printf '%s  %s\n' 53fe151be42f943454ef65ef5909e9a6e8d254abbd44f80ef5ae1f03a6361db5 "$archive" | shasum -a 256 -c -
unzip -oq "$archive" -d local/sc2/Maps
local/sc2/.venv/bin/python environments/sc2/control.py offline
printf '\nNext: install StarCraft II through Battle.net, then run the doctor command in environments/sc2/README.md.\n'
