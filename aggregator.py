#!/usr/bin/env python3
"""Impartial News aggregator: fetch feeds -> cluster stories -> score bias coverage -> render static site."""
import json, re, subprocess, html, os, sys, shutil, hashlib, time, math
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
from concurrent.futures import ThreadPoolExecutor
from collections import Counter, defaultdict
from urllib.parse import urlparse
import feedparser, numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer, ENGLISH_STOP_WORDS
from sklearn.cluster import AgglomerativeClustering
from sklearn.metrics.pairwise import cosine_similarity
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

ROOT = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.join(ROOT, "site")
UK = ZoneInfo("Europe/London")
SITE_NAME = "Impartial News"
MAX_AGE_H = 36            # only articles published in the last N hours
SIM_THRESHOLD = 0.20      # average-linkage cosine similarity needed to join a story
MERGE_THRESHOLD = 0.3   # centroid cosine similarity for merging split clusters
BLINDSPOT_SHARE = 0.70    # >= this share of outlets from one side
BLINDSPOT_MIN = 3         # minimum distinct outlets
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130 Safari/537.36"
SIDES = ["left", "center", "right"]
SIDE_NAME = {"left": "Left", "center": "Centre", "right": "Right"}

def log(*a): print(*a, file=sys.stderr, flush=True)
def esc(s): return html.escape(s or "", quote=True)
def clean(s):
    s = re.sub(r"<[^>]+>", " ", s or ""); s = html.unescape(s)
    return re.sub(r"\s+", " ", s).strip()

# ---------------------------------------------------------------- fetch
def fetch_feed(src, feed):
    rec, arts = _fetch_feed(src, feed)
    if not rec["ok"]:
        time.sleep(3); rec, arts = _fetch_feed(src, feed); rec["retried"] = True
    return rec, arts

def _fetch_feed(src, feed):
    rec = {"outlet": src["id"], "url": feed["url"], "via": feed.get("via"), "section": feed["section"]}
    t0 = time.time()
    try:
        # curl is used (not requests) because some publishers reject Python's TLS/HTTP fingerprint
        tmpf = f"/tmp/impartial_{hashlib.md5(feed['url'].encode()).hexdigest()}.xml"
        p = subprocess.run(["curl", "-sL", "--compressed", "-m", "25", "--retry", "1", "-A", UA, "-H", "Accept: application/rss+xml, application/xml, text/xml, */*",
                            "-o", tmpf, "-w", "%{http_code}", feed["url"]], capture_output=True, text=True, timeout=60)
        code = int(p.stdout.strip() or 0)
        rec["http"] = code
        content = open(tmpf, "rb").read() if os.path.exists(tmpf) else b""
        if os.path.exists(tmpf): os.remove(tmpf)
        fp = feedparser.parse(content)
        entries = fp.entries if code == 200 else []
        rec["items"] = len(entries)
        rec["ok"] = code == 200 and len(entries) > 0
        if not rec["ok"]: rec["error"] = f"HTTP {code}, {len(entries)} items"
    except Exception as e:
        rec.update(ok=False, http=None, items=0, error=str(e)[:200]); entries = []
    rec["ms"] = int((time.time() - t0) * 1000)
    arts = []
    dom = urlparse(src["homepage"]).netloc.replace("www.", "")
    now = datetime.now(timezone.utc)
    for e in entries:
        title = clean(e.get("title"))
        link = e.get("link") or ""
        if not title or not link: continue
        if feed.get("via") == "Google News":
            srcurl = (e.get("source") or {}).get("href", "")
            if dom.split(".")[0] not in srcurl: continue
            title = re.sub(r"\s+[-–|]\s+[^-–|]{2,40}$", "", title)
            summary = ""
        else:
            summary = clean(e.get("summary") or e.get("description"))[:500]
        tp = e.get("published_parsed") or e.get("updated_parsed")
        if not tp: continue
        dt = datetime(*tp[:6], tzinfo=timezone.utc)
        max_age = STEM_MAX_AGE_H if feed["section"] == "stem" else MAX_AGE_H
        if dt > now + timedelta(hours=1) or now - dt > timedelta(hours=max_age): continue
        arts.append({"outlet": src["id"], "title": title, "summary": summary, "url": link,
                     "published": dt.isoformat(), "section": feed["section"], "via": feed.get("via")})
    return rec, arts

# ---------------------------------------------------------------- lexicons
STEM_TOPICS = {
 "space": r"NASA|ESA|SpaceX|Blue Origin|rockets?|astronauts?|orbit(al|ing)?|Mars|Martian|moon|lunar|asteroids?|comets?|galax(y|ies)|telescopes?|satellites?|planets?|exoplanets?|Hubble|James Webb|black holes?|solar system|cosmic|spacecraft|Artemis|ISS|space station",
 "ai_tech": r"AI|A\.I\.|artificial intelligence|chatbots?|ChatGPT|OpenAI|Anthropic|Gemini|Nvidia|Microsoft|Google|Apple|iPhone|Android|Meta|semiconductors?|microchips?|chipmakers?|AI chips?|software|cyber ?attacks?|cybersecurity|hack(ers?|ed|ing)?|data breach|smartphones?|algorithms?|robots?|robotics|quantum|outages?|social media|TikTok|crypto|bitcoin|Tesla|data cent(re|er)s?|tech giants?",
 "health": r"vaccines?|cancers?|tumou?rs?|diseases?|virus(es)?|viral infection|medical|medicine|clinical trials?|dementia|Alzheimer'?s|genes?|genetic|DNA|brain|obesity|weight-loss|Ozempic|Wegovy|diabetes|bird flu|pandemic|antibiotics?|heart attack|surgeons?|surgery|prostate|screening",
 "climate": r"climate|emissions|carbon|net zero|global warming|COP\d+|fossil fuels?|renewables?|solar power|solar panels?|wind farms?|wildlife|species|extinct(ion)?|biodiversity|oceans?|glaciers?|sea ice|pollution|deforestation|coral|environmental",
 "science": r"scientists?|researchers?|study finds|new study|physic(s|ists?)|chemistry|chemists?|mathematic(s|ians?)|engineer(s|ing)|archaeolog(y|ists?|ical)|fossils?|dinosaurs?|evolution|fusion|laborator(y|ies)|Nobel|experiments?|peer-reviewed|journal Nature",
}
STEM_RE = {k: re.compile(r"\b(" + v + r")\b", re.I) for k, v in STEM_TOPICS.items()}
STEM_LABEL = {"space": "Space", "ai_tech": "AI & Tech", "health": "Health & Medicine", "climate": "Climate & Environment", "science": "Science & Engineering"}
STEM_MAX_AGE_H = 60       # science/tech section feeds move slower, so they get a longer window

def stem_info(items):
    """items: list of articles. Returns (is_stem, [topics]). Needs science/tech-section feeds or keywords in headlines."""
    hits = Counter(); stemmy = 0; sec = 0; title_hit = 0
    for a in items:
        th = {k for k, r in STEM_RE.items() if r.search(a["title"])}
        sh = {k for k, r in STEM_RE.items() if len(r.findall(a["summary"])) >= 2}
        if a["section"] == "stem": sec += 1
        if th: title_hit += 1
        if a["section"] == "stem" or th: stemmy += 1
        for k in th: hits[k] += 2
        for k in sh: hits[k] += 1
    n = len(items)
    is_stem = bool(hits) and stemmy / n >= 0.5 and (sec >= 1 or title_hit / n >= 0.5)
    return is_stem, [k for k, c in hits.most_common(2) if c >= max(2, n * 0.4)]

UK_RE = re.compile(r"\b(UK|U\.K\.|Britain|British|England|English|Scotland|Scottish|Wales|Welsh|Northern Ireland|London|Manchester|Birmingham|Liverpool|Leeds|Glasgow|Edinburgh|Cardiff|Belfast|Bristol|Westminster|Downing Street|No 10|Starmer|Reeves|Badenoch|Farage|Reform UK|Labour|Tory|Tories|Conservatives?|Lib Dems?|SNP|NHS|Ofsted|Ofcom|Ofgem|Met Police|Scotland Yard|Home Office|Treasury|Bank of England|Commons|Lords|King Charles|Prince William|Princess of Wales|Royal Family|Premier League|council tax|HMRC|DWP|BBC)\b")
LOADED = set("""slams slammed blasts blasted rips ripped destroys destroyed torches eviscerates savages lashes lashed
chaos chaotic meltdown fury furious outrage outraged outrageous shock shocking shocked horror horrific brutal disgrace disgraceful
scandal bombshell crisis catastrophe catastrophic disaster disastrous humiliating humiliation humiliated
radical extremist extremists far-right far-left leftist leftists woke marxist socialist fascist regime thugs mob invasion invaders
illegal illegals migrants swarm flood flooding betrayal betrayed traitor elite elites globalist propaganda censorship hoax
slaughter massacre genocide atrocity apartheid terror terrorist terrorists militants occupation crackdown
explosive dramatic stunning staggering astonishing jaw-dropping incredible war warns threat threatens backlash row feud""".split())
STOP = set(ENGLISH_STOP_WORDS) | {"says","say","said","new","just","year","years","day","week","amid","after","over","us","uk","live","latest","update","updates","video","watch","news","report"}
VADER = SentimentIntensityAnalyzer()

def words(t): return [w for w in re.findall(r"[a-z][a-z'\-]+", t.lower())]

def framing(story_arts, bucket):
    by = defaultdict(list)
    for a in story_arts: by[bucket[a["outlet"]]].append(a["title"])
    if not by["left"] or not by["right"]:
        return None
    out = {"sides": {}}
    for side in SIDES:
        hs = by.get(side) or []
        if not hs: continue
        sent = float(np.mean([VADER.polarity_scores(h)["compound"] for h in hs]))
        ws = [w for h in hs for w in words(h)]
        loaded = Counter(w for w in ws if w in LOADED)
        out["sides"][side] = {"n": len(hs), "tone": round(sent, 2),
                              "loaded": [w for w, _ in loaded.most_common(5)],
                              "loaded_rate": round(sum(loaded.values()) / max(1, len(hs)), 2)}
    lw = Counter(w for h in by["left"] for w in set(words(h)) if w not in STOP and len(w) > 3)
    rw = Counter(w for h in by["right"] for w in set(words(h)) if w not in STOP and len(w) > 3)
    out["left_only"] = [w for w, _ in lw.most_common() if w not in rw][:5]
    out["right_only"] = [w for w, _ in rw.most_common() if w not in lw][:5]
    L, R = out["sides"]["left"], out["sides"]["right"]
    def tone(v): return "negative" if v <= -0.25 else "positive" if v >= 0.25 else "neutral"
    bits = []
    d = R["tone"] - L["tone"]
    if abs(d) >= 0.2:
        neg = "Right" if d < 0 else "Left"
        bits.append(f"{neg}-leaning headlines are more negative in tone (average {L['tone']:+.2f} left vs {R['tone']:+.2f} right, on a −1 to +1 scale).")
    else:
        bits.append(f"Headline tone is similar across sides ({tone(L['tone'])} left, {tone(R['tone'])} right).")
    if L["loaded"] or R["loaded"]:
        parts = []
        if L["loaded"]: parts.append("left: " + ", ".join(f"“{w}”" for w in L["loaded"]))
        if R["loaded"]: parts.append("right: " + ", ".join(f"“{w}”" for w in R["loaded"]))
        bits.append("Loaded or emotive words — " + "; ".join(parts) + ".")
    if out["left_only"] or out["right_only"]:
        parts = []
        if out["left_only"]: parts.append("only left headlines mention " + ", ".join(f"“{w}”" for w in out["left_only"][:4]))
        if out["right_only"]: parts.append("only right headlines mention " + ", ".join(f"“{w}”" for w in out["right_only"][:4]))
        bits.append("Emphasis: " + "; ".join(parts) + ".")
    out["note"] = " ".join(bits)
    return out

# ---------------------------------------------------------------- clustering
def cluster(arts):
    texts = [(a["title"] + ". ") * 2 + a["summary"] for a in arts]
    vec = TfidfVectorizer(stop_words=list(STOP), sublinear_tf=True, ngram_range=(1, 2), min_df=1, max_df=0.3,
                          token_pattern=r"(?u)\b[a-zA-Z][a-zA-Z\-']+\b")
    X = vec.fit_transform(texts)
    S = cosine_similarity(X)
    D = np.clip(1 - S, 0, 2)
    model = AgglomerativeClustering(n_clusters=None, metric="precomputed", linkage="average",
                                    distance_threshold=1 - SIM_THRESHOLD)
    labels = model.fit_predict(D)
    groups = defaultdict(list)
    for i, l in enumerate(labels): groups[l].append(i)
    groups = list(groups.values())
    # second pass: merge clusters whose centroids are very similar (same story split by wording)
    C = np.vstack([np.asarray(X[g].mean(axis=0)) for g in groups])
    C = C / np.maximum(np.linalg.norm(C, axis=1, keepdims=True), 1e-9)
    CS = C @ C.T
    parent = list(range(len(groups)))
    def find(x):
        while parent[x] != x: parent[x] = parent[parent[x]]; x = parent[x]
        return x
    ii, jj = np.where(np.triu(CS, 1) >= MERGE_THRESHOLD)
    for a, b in zip(ii, jj): parent[find(a)] = find(b)
    merged = defaultdict(list)
    for k, g in enumerate(groups): merged[find(k)].extend(g)
    return list(merged.values()), S

# ---------------------------------------------------------------- build
def fmt_uk(iso, with_date=True):
    dt = datetime.fromisoformat(iso).astimezone(UK)
    return dt.strftime("%-d %b, %H:%M %Z") if with_date else dt.strftime("%H:%M %Z")

def build():
    cfg = json.load(open(os.path.join(ROOT, "sources.json")))
    sources = {s["id"]: s for s in cfg["sources"]}
    bucket = {k: v["bucket"] for k, v in sources.items()}
    jobs = [(s, f) for s in cfg["sources"] for f in s["feeds"]]
    with ThreadPoolExecutor(12) as ex:
        results = list(ex.map(lambda sf: fetch_feed(*sf), jobs))
    feed_status = [r for r, _ in results]
    arts, seen = [], set()
    for _, a_list in results:
        for a in a_list:
            key = (a["outlet"], a["url"].split("?")[0] if a["via"] is None else a["url"])
            tkey = (a["outlet"], a["title"].lower())
            if key in seen or tkey in seen: continue
            seen.add(key); seen.add(tkey); arts.append(a)
    ok = sum(r["ok"] for r in feed_status)
    log(f"feeds ok {ok}/{len(feed_status)}; articles {len(arts)}")
    groups, S = cluster(arts)
    stories = []
    for g in groups:
        outlets = sorted({arts[i]["outlet"] for i in g})
        if len(outlets) < 2: continue
        # centroid relevance
        cen = S[np.ix_(g, g)].mean(axis=1)
        order = [g[j] for j in np.argsort(-cen)]
        best_per_outlet = {}
        for i in order:
            best_per_outlet.setdefault(arts[i]["outlet"], i)
        counts = Counter(bucket[o] for o in outlets)
        n = len(outlets)
        share = {s: counts.get(s, 0) / n for s in SIDES}
        # headline: most central article, preferring centre-rated outlets
        cands = [i for i in order if bucket[arts[i]["outlet"]] == "center"] or order
        head = arts[cands[0]]
        times = sorted(arts[i]["published"] for i in g)
        blind = None
        if n >= BLINDSPOT_MIN:
            if share["left"] >= BLINDSPOT_SHARE: blind = "right"   # blindspot FOR the right
            elif share["right"] >= BLINDSPOT_SHARE: blind = "left"
        txt = " ".join(arts[i]["title"] + " " + arts[i]["summary"] for i in g)
        uk_hits = sum(1 for i in g if UK_RE.search(arts[i]["title"] + " " + arts[i]["summary"]))
        uk_sec = sum(1 for i in g if arts[i]["section"] == "uk")
        uk_outlets = sum(1 for o in outlets if sources[o]["country"] == "UK") / n
        region = "uk" if (uk_hits / len(g) >= 0.4 or uk_sec / len(g) >= 0.5 or (uk_outlets >= 0.8 and uk_hits >= 1)) else "world"
        items = []
        for o, i in sorted(best_per_outlet.items(), key=lambda kv: arts[kv[1]]["published"]):
            a = arts[i]
            items.append({"outlet": o, "name": sources[o]["name"], "bucket": bucket[o], "title": a["title"],
                          "summary": a["summary"][:300], "url": a["url"], "published": a["published"],
                          "time_uk": fmt_uk(a["published"]), "via": a["via"]})
        is_stem, topics = stem_info([arts[i] for i in g])
        fr = framing([arts[best_per_outlet[o]] for o in outlets], bucket)
        sid = hashlib.sha1((head["title"] + times[0]).encode()).hexdigest()[:10]
        summary = next((arts[i]["summary"] for i in order if len(arts[i]["summary"]) > 60), "")
        stories.append({"id": sid, "headline": head["title"], "headline_outlet": sources[head["outlet"]]["name"],
                        "summary": summary[:280], "n_outlets": n, "n_articles": len(g),
                        "counts": {s: counts.get(s, 0) for s in SIDES},
                        "share": {s: round(share[s] * 100) for s in SIDES},
                        "blindspot_for": blind, "region": region, "stem": is_stem, "stem_topics": topics if is_stem else [],
                        "first_seen": times[0], "last_update": times[-1],
                        "first_uk": fmt_uk(times[0]), "last_uk": fmt_uk(times[-1]),
                        "outlets": outlets, "articles": items, "framing": fr,
                        "estimated_ratings": [o for o in outlets if sources[o]["rating_status"] != "published"]})
    now = datetime.now(timezone.utc)
    def score(s):
        age = (now - datetime.fromisoformat(s["last_update"])).total_seconds() / 3600
        return s["n_outlets"] + 0.15 * min(s["n_articles"], 20) - 0.08 * age
    stories.sort(key=score, reverse=True)
    meta = {"site": SITE_NAME, "built_utc": now.isoformat(), "built_uk": now.astimezone(UK).strftime("%-d %B %Y, %H:%M %Z"),
            "feeds_ok": ok, "feeds_total": len(feed_status), "articles": len(arts), "stories": len(stories),
            "blindspots": sum(1 for s in stories if s["blindspot_for"]),
            "blind_for_left": sum(1 for s in stories if s["blindspot_for"] == "left"),
            "blind_for_right": sum(1 for s in stories if s["blindspot_for"] == "right"),
            "uk": sum(1 for s in stories if s["region"] == "uk"), "stem": sum(1 for s in stories if s["stem"]), "world": sum(1 for s in stories if s["region"] == "world"),
            "params": {"max_age_h": MAX_AGE_H, "sim_threshold": SIM_THRESHOLD, "merge_threshold": MERGE_THRESHOLD, "stem_max_age_h": STEM_MAX_AGE_H, "blindspot_share": BLINDSPOT_SHARE, "blindspot_min": BLINDSPOT_MIN}}
    import render
    render.render_site(SITE, ROOT, meta, stories, sources, cfg["_meta"], feed_status, STEM_LABEL)
    json.dump({"meta": meta, "feeds": feed_status}, open(os.path.join(ROOT, "last_build.json"), "w"), indent=1)
    log(json.dumps(meta))
    return meta

if __name__ == "__main__":
    build()
