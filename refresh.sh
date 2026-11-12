#!/usr/bin/env bash
# Impartial News: rebuild site/ from live feeds and re-package ferret-news-site.zip.
# Schedule example (every 30 min):  */30 * * * * /workspace/ferret-news/refresh.sh >> /workspace/ferret-news/refresh.log 2>&1
set -euo pipefail
cd "$(dirname "$0")"
exec 9>/tmp/impartial-news.lock
flock -n 9 || { echo "$(date -Is) refresh already running"; exit 0; }
PY=python3; [ -x .venv/bin/python ] && PY=.venv/bin/python
echo "$(date -Is) refresh start"
"$PY" aggregator.py
rm -f ferret-news-site.zip.tmp
"$PY" -c "import shutil; shutil.make_archive('ferret-news-site.build', 'zip', 'site')" && mv ferret-news-site.build.zip ferret-news-site.zip.tmp
mv ferret-news-site.zip.tmp ferret-news-site.zip
"$PY" stage_upload.py
echo "$(date -Is) refresh done"
