#!/usr/bin/env bash
# Verifies every podcast feed in podcasts.json for a recent public audio enclosure.
cd "$(dirname "$0")"
PY=python3
[[ -x .venv/bin/python ]] && PY=.venv/bin/python
$PY - << 'PY'
import json, os, time, hashlib, subprocess, re, html
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed
import feedparser

ROOT = os.path.dirname(os.path.abspath("podcasts.json"))
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130 Safari/537.36"
cfg = json.load(open("podcasts.json"))
shows = cfg["podcasts"]

def upgrade(url):
    if url and "open.live.bbc.co.uk/mediaselector" in url:
        if url.startswith("http://"):
            url = "https://" + url[len("http://"):]
        url = url.replace("/proto/http/", "/proto/https/")
    return url

def audio_of(entry):
    sec = entry.get("ppg_enclosuresecure") or {}
    if isinstance(sec, dict) and sec.get("url"):
        return upgrade(sec["url"])
    for enc in entry.get("enclosures") or []:
        href = enc.get("href") or enc.get("url") or ""
        typ = (enc.get("type") or "").lower()
        if href and (typ.startswith("audio") or re.search(r"\.(mp3|m4a|aac)(\?|$)", href, re.I)):
            return upgrade(href)
    return None

def probe(url):
    p = subprocess.run(["curl","-sL","-m","18","-A",UA,"-r","0-1023","-o","/tmp/impartial_pod_probe.bin",
                        "-w","%{http_code}\t%{content_type}",url], capture_output=True, text=True, timeout=25)
    code = 0; typ = ""
    if p.stdout:
        parts = p.stdout.strip().split("\t", 1)
        try: code = int(parts[0] or 0)
        except: code = 0
        typ = parts[1] if len(parts)>1 else ""
    head = open("/tmp/impartial_pod_probe.bin","rb").read(16) if os.path.exists("/tmp/impartial_pod_probe.bin") else b""
    is_audio = head.startswith(b"ID3") or (len(head)>=2 and head[0]==0xff and (head[1]&0xe0)==0xe0) or b"ftyp" in head or "audio" in typ.lower() or "mpeg" in typ.lower()
    return code, typ, is_audio

def check(show):
    url = show["feed"]
    tmpf = f"/tmp/impartial_podv_{hashlib.md5(url.encode()).hexdigest()}.xml"
    p = subprocess.run(["curl","-sL","--compressed","-m","25","-A",UA,"-o",tmpf,"-w","%{http_code}\t%{size_download}",url],
                       capture_output=True, text=True, timeout=45)
    http, nbytes = 0, 0
    if p.stdout:
        a, _, b = p.stdout.strip().partition("\t")
        http = int(a or 0); nbytes = int(b or 0)
    content = open(tmpf,"rb").read() if os.path.exists(tmpf) else b""
    fp = feedparser.parse(content)
    enc = 0; latest = ""; audio_ok = ""
    for e in fp.entries[:8]:
        href = audio_of(e)
        if href: enc += 1
        tp = e.get("published_parsed") or e.get("updated_parsed")
        if tp and not latest:
            latest = datetime(*tp[:6], tzinfo=timezone.utc).isoformat()
            if href:
                code, typ, ok = probe(href)
                audio_ok = f"{'OK' if ok and code in (200,206) else 'FAIL'} {code} {typ}"
    st = "OK" if http==200 and enc>0 else "FAIL"
    return show["id"], http, nbytes, len(fp.entries), enc, st, latest, audio_ok, url

rows = []
with ThreadPoolExecutor(8) as ex:
    futs = [ex.submit(check, s) for s in shows]
    for f in as_completed(futs):
        rows.append(f.result())
rows.sort(key=lambda r: r[0])
now = datetime.now(timezone.utc).isoformat(timespec="seconds")
with open("podcasts_verified.tsv","w") as out:
    out.write("checked_at\tshow\thttp\tbytes\titems\tenclosures\tstatus\tlatest\taudio_probe\turl\n")
    for r in rows:
        out.write("\t".join(str(x) for x in (now,)+r) + "\n")
        print(f"{r[5]:4} {r[0]:22} http={r[1]} items={r[3]} enc={r[4]} latest={r[6]} audio={r[7]}")
print("wrote podcasts_verified.tsv")
PY
