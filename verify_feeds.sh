#!/usr/bin/env bash
# Verifies every feed in sources.json with curl; writes feeds_verified.tsv
cd "$(dirname "$0")"
UA="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130 Safari/537.36"
out=feeds_verified.tsv; echo -e "checked_at\toutlet\thttp\tbytes\titems\tstatus\turl" > "$out"
python3 -c "import json;[print(s['id']+'\t'+f['url']) for s in json.load(open('sources.json'))['sources'] for f in s['feeds']]" |
while IFS=$'\t' read id url; do
  tmp=$(mktemp)
  res=$(curl -sL --compressed -m 25 -A "$UA" -o "$tmp" -w "%{http_code}\t%{size_download}" "$url")
  items=$(grep -o -E "<item[ >]|<entry[ >]" "$tmp" | wc -l); rm -f "$tmp"
  code=${res%%$'\t'*}; st=FAIL; [[ "$code" == 200 && $items -gt 0 ]] && st=OK
  echo -e "$(date -Is)\t$id\t$res\t$items\t$st\t$url" >> "$out"
done
# Also record the outlet feeds that were tried during setup and did not work
cat failed_feeds_setup.tsv >> "$out" 2>/dev/null
cut -f2-7 "$out" | cut -c1-150
