#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

if [[ ! -x ".venv-build/bin/python" ]]; then
    python3 -m venv .venv-build
fi

".venv-build/bin/python" -m pip install --upgrade pip
".venv-build/bin/python" -m pip install -r requirements-build.txt
".venv-build/bin/python" -m PyInstaller --noconfirm --clean --onedir --windowed --name NexusCRM --specpath build --workpath build/work --distpath dist --collect-all googleapiclient --collect-all google_auth_oauthlib --collect-all google.auth --collect-all google.oauth2 --hidden-import google_auth_httplib2 --collect-all httplib2 main.py

echo "Build complete: dist/NexusCRM.app"