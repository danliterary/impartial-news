"""Static HTML renderer for Impartial News. All links are relative so the site works under any sub-path."""
import os, json, shutil, html, re
import themes as TH
from collections import Counter

SIDES = ["left", "center", "right"]
SIDE_NAME = {"left": "Left", "center": "Centre", "right": "Right"}
ABBR = {"bbc":"BBC","guardian":"GDN","independent":"IND","dailymail":"DM","gbnews":"GB","sky":"SKY","reuters":"RTR",
        "ap":"AP","aljazeera":"AJ","cnn":"CNN","npr":"NPR","breitbart":"BB","newstatesman":"NS","express":"EXP",
        "mirror":"MIR","standard":"ES","politicoeu":"POL","dw":"DW","france24":"F24","cbs":"CBS","nypost":"NYP",
        "nationalreview":"NR","washexaminer":"WE","fox":"FOX"}
STEM_LABEL = {"space": "Space", "ai_tech": "AI & Tech", "health": "Health & Medicine", "climate": "Climate & Environment", "science": "Science & Engineering"}
def esc(s): return html.escape(str(s) if s is not None else "", quote=True)

LOGO = ('<svg class="logo-mark" viewBox="0 0 64 64" width="34" height="34" aria-hidden="true"><defs><linearGradient id="in-g" x1="6" y1="0" x2="58" y2="0" gradientUnits="userSpaceOnUse">'
        '<stop offset="0" stop-color="#3b7cf5"/><stop offset=".5" stop-color="#9b6cf0"/><stop offset="1" stop-color="#f0566a"/></linearGradient></defs>'
        '<path d="M5 32C14.5 16 49.5 16 59 32C49.5 48 14.5 48 5 32Z" fill="none" stroke="url(#in-g)" stroke-width="5.5" stroke-linejoin="round"/>'
        '<circle cx="32" cy="32" r="9.5" fill="url(#in-g)"/><circle cx="35.5" cy="28.5" r="3" fill="var(--bg)"/></svg>')

def biasbar(share, counts, big=False):
    segs = []
    for s, cls in (("left", "l"), ("center", "c"), ("right", "r")):
        p = share[s]
        if p <= 0: continue
        lab = f"{SIDE_NAME[s][0]} {p}%" if p >= 14 else (f"{p}%" if p >= 8 else "")
        if big and p >= 20: lab = f"{SIDE_NAME[s]} {p}%"
        segs.append(f'<span class="seg {cls}" style="width:{p}%" title="{SIDE_NAME[s]}: {counts[s]} outlet(s), {p}%">{lab}</span>')
    return f'<div class="biasbar{" big" if big else ""}" role="img" aria-label="Coverage: Left {share["left"]}%, Centre {share["center"]}%, Right {share["right"]}%">{"".join(segs)}</div>'

def badges(story, limit=7):
    out = []
    for a in story["articles"][:limit]:
        out.append(f'<span class="ob {a["bucket"]}" title="{esc(a["name"])} · {SIDE_NAME[a["bucket"]]}">{ABBR.get(a["outlet"], a["name"][:3].upper())}</span>')
    more = len(story["articles"]) - limit
    if more > 0: out.append(f'<span class="ob more">+{more}</span>')
    return "".join(out)

def chips(st):
    c = [f'<span class="chip region">{"UK" if st["region"]=="uk" else "World"}</span>']
    if st.get("stem"):
        t = STEM_LABEL.get((st.get("stem_topics") or [""])[0], "")
        c.append(f'<span class="chip stem">STEM{" · " + esc(t) if t else ""}</span>')
    if st["blindspot_for"]:
        c.append(f'<span class="chip blind {st["blindspot_for"]}" title="At least 70% of covering outlets lean one way">◐ Blindspot for the {SIDE_NAME[st["blindspot_for"]]}</span>')
    return "".join(c)

def sides_block(st):
    rows = []
    for side in SIDES:
        a = next((x for x in st["articles"] if x["bucket"] == side), None)
        if not a: continue
        rows.append(f'<li class="{side}"><span class="sl">{SIDE_NAME[side]}</span><a href="{esc(a["url"])}" target="_blank" rel="noopener">{esc(a["title"])}</a><span class="sn">{esc(a["name"])}</span></li>')
    return f'<div class="how"><h4>How each side headlines it</h4><ul>{"".join(rows)}</ul></div>' if len(rows) > 1 else ""

def card(st, pre="", hero=False):
    cls = "card hero" if hero else "card"
    summ = f'<p class="sum">{esc(st["summary"])}</p>' if st["summary"] and hero else (f'<p class="sum clamp">{esc(st["summary"])}</p>' if st["summary"] else "")
    return f'''<article class="{cls}" data-id="{st["id"]}" data-topics="{" ".join(st.get("stem_topics") or [])}" data-outlets="{" ".join(st["outlets"])}" data-region="{st["region"]}" data-blind="{st["blindspot_for"] or ""}">
 <div class="card-meta">{chips(st)}<time datetime="{st["last_update"]}">Updated {esc(st["last_uk"])}</time></div>
 <h3 class="headline"><a href="{pre}story/{st["id"]}.html">{esc(st["headline"])}</a></h3>
 {summ}
 {biasbar(st["share"], st["counts"], big=hero)}
 {sides_block(st) if hero else ""}
 <div class="card-foot"><div class="badges">{badges(st, 9 if hero else 6)}</div><a class="count" href="{pre}story/{st["id"]}.html">{st["n_outlets"]} sources →</a></div>
</article>'''

ICON_PALETTE = '<svg viewBox="0 0 24 24" width="19" height="19" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 3a9 9 0 1 0 0 18c1.1 0 1.8-.8 1.8-1.8 0-.5-.2-.9-.5-1.2-.3-.3-.5-.8-.5-1.2 0-1 .8-1.8 1.8-1.8H17a4 4 0 0 0 4-4C21 6.6 17 3 12 3z"/><circle cx="7.5" cy="11" r="1.2" fill="currentColor"/><circle cx="10.5" cy="7.2" r="1.2" fill="currentColor"/><circle cx="15" cy="7.4" r="1.2" fill="currentColor"/></svg>'
ICON_SYNC = ('<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
            '<path d="M21 12a9 9 0 0 0-15.45-6.36L3 8"/><path d="M3 3v5h5"/>'
            '<path d="M3 12a9 9 0 0 0 15.45 6.36L21 16"/><path d="M21 21v-5h-5"/></svg>')
HEAD_SCRIPT = TH.head_script()

def appearance_panel():
    groups = []
    for gid, gname in TH.GROUPS:
        sw = []
        for tid, name, desc, grp, scheme, v in TH.THEMES:
            if grp != gid: continue
            style = f"--b:{v['bg']};--s:{v['surface']};--i:{v['ink']};--a:{v['accent']};--l:{v['left']};--c:{v['centre']};--r:{v['right']};--ln:{v['line']}"
            sw.append(f'<button type="button" class="sw" data-theme-pick="{tid}" data-scheme="{scheme}" aria-pressed="false" title="{esc(name)}: {esc(desc)}">'
                      f'<span class="sw-chip" style="{style}" aria-hidden="true"><span class="sw-aa">Aa</span><span class="sw-bar"><i></i><i></i><i></i></span></span>'
                      f'<span class="sw-name">{esc(name)}</span></button>')
        groups.append(f'<p class="ap-sub">{gname}</p><div class="sw-grid">{"".join(sw)}</div>')
    default_label = next(label for fid, label, *_ in TH.FONTS if fid == "default")
    font_items = [f'<button type="button" class="ap-font-opt" role="option" data-font-pick="default" aria-selected="false" id="ap-font-default" style="font-family:Mako, Inter, sans-serif">{esc(default_label)}</button>']
    for gid, gname, items in TH.FONT_GROUPS:
        font_items.append(f'<p class="ap-font-g" role="presentation">{esc(gname)}</p>')
        for fid, label, stack, lazy in items:
            font_items.append(
                f'<button type="button" class="ap-font-opt" role="option" data-font-pick="{fid}" aria-selected="false" id="ap-font-{fid}" style="font-family:{stack}">{esc(label)}</button>'
            )
    size_opts = "".join(
        f'<option value="{n}">{"11 pt (default)" if n==TH.DEFAULT_SIZE else n+" pt"}</option>' for n in TH.SIZES
    )
    return f'''<div class="appearance">
  <button class="appearance-btn" type="button" id="appearance-btn" aria-expanded="false" aria-controls="appearance-panel" title="Theme, typeface and text size">{ICON_PALETTE}<span class="sr">Reader settings: colour theme, typeface and text size</span></button>
  <div class="appearance-panel" id="appearance-panel" role="dialog" aria-modal="false" aria-labelledby="ap-title" hidden>
   <div class="ap-head"><p class="ap-title" id="ap-title">Reader settings</p><button type="button" class="ap-reset" data-ap-reset title="Back to Match system, default typeface, 11 pt">Restore default</button></div>
   <p class="ap-label">Colour theme</p>
   <button type="button" class="ap-auto" data-theme-pick="auto" aria-pressed="false"><span class="ap-auto-dot" aria-hidden="true"></span>Match system <small>Paper by day, Ink at night</small></button>
   {"".join(groups)}
   <p class="ap-label" id="ap-font-label">Typeface</p>
   <div class="ap-font" id="ap-font-wrap">
    <div class="ap-font-list" id="ap-font" role="listbox" aria-labelledby="ap-font-label">{"".join(font_items)}</div>
   </div>
   <p class="ap-label" id="ap-size-label">Text size</p>
   <div class="ap-size-step" id="ap-size" role="group" aria-labelledby="ap-size-label">
    <button type="button" class="ap-size-btn" data-size-step="-1" aria-label="Smaller text">−</button>
    <select class="ap-size-select" id="ap-size-select" aria-label="Text size in points">{size_opts}</select>
    <button type="button" class="ap-size-btn" data-size-step="1" aria-label="Larger text">+</button>
   </div>
   <p class="ap-note">Saved on this device. Typefaces are self-hosted open fonts, so they look the same on every device. Bias colours are tuned in every theme so the Left, Centre and Right bar stays readable.</p>
  </div>
 </div>'''


def sync_control(meta):
    built = esc(meta.get("built_utc") or "")
    built_uk = esc(meta.get("built_uk") or "")
    feeds_ok = int(meta.get("feeds_ok") or 0)
    feeds_total = int(meta.get("feeds_total") or 0)
    pods_ok = int(meta.get("podcast_feeds_ok") or 0)
    pods_total = int(meta.get("podcast_feeds_total") or 0)
    episodes = int(meta.get("podcasts") or 0)
    token_new = "https://github.com/settings/personal-access-tokens/new"
    actions = "https://github.com/danliterary/impartial-news/actions/workflows/pages.yml"
    return f'''<div class="sync" id="sync-root" data-built="{built}" data-built-uk="{built_uk}" data-feeds-ok="{feeds_ok}" data-feeds-total="{feeds_total}" data-podcasts-ok="{pods_ok}" data-podcasts-total="{pods_total}" data-episodes="{episodes}">
  <button class="sync-btn" type="button" id="sync-btn" aria-expanded="false" aria-controls="sync-panel" title="Sync and refresh sources">{ICON_SYNC}<span class="sync-label">Sync</span><span class="sr">Sync and refresh sources</span></button>
  <div class="sync-panel" id="sync-panel" role="dialog" aria-modal="false" aria-labelledby="sync-title" hidden>
   <div class="sync-head"><p class="sync-title" id="sync-title">Sync sources</p></div>
   <p class="sync-meta">Last synced <time id="sync-built" datetime="{built}">{built_uk}</time><span id="sync-rel"></span></p>
   <p class="sync-status" id="sync-status" role="status" aria-live="polite"><span class="sync-dot" id="sync-dot" data-state="idle"></span><span id="sync-status-text">Idle</span></p>
   <div class="sync-actions">
    <button type="button" class="sync-action" id="sync-check">Check for updates</button>
    <button type="button" class="sync-action primary" id="sync-now">Sync all sources now</button>
   </div>
   <p class="sync-note">Feeds also refresh automatically every 30 minutes. A full sync re-reads every news and podcast feed on GitHub Actions, then this page reloads when the new build is live.</p>
   <div class="sync-howto" id="sync-howto">
    <p class="ap-label">Run a fresh scrape now</p>
    <ol>
     <li>Paste a fine-grained GitHub token with <b>Actions: Read and write</b> on <code>danliterary/impartial-news</code>. It is stored only in this browser and sent only to api.github.com.
      <form class="sync-token-form" id="sync-token-form">
       <label class="sr" for="sync-token">Fine-grained GitHub token</label>
       <input class="sync-token-input" id="sync-token" type="password" name="token" autocomplete="off" spellcheck="false" placeholder="github_pat_…">
       <button type="submit" class="sync-action">Save on this device</button>
      </form>
      <a class="sync-ext" href="{token_new}" target="_blank" rel="noopener">Create a token on GitHub</a>
     </li>
     <li>Or start the same job on GitHub: <a class="sync-ext" href="{actions}" target="_blank" rel="noopener">Run on GitHub Actions</a></li>
    </ol>
   </div>
   <div class="sync-token-ok" id="sync-token-ok" hidden>
    <p>A token is saved on this device. “Sync all sources now” starts the official GitHub Actions workflow.</p>
    <button type="button" class="sync-text-btn" id="sync-forget">Remove saved token</button>
    <a class="sync-ext" href="{actions}" target="_blank" rel="noopener">Open the workflow on GitHub</a>
   </div>
  </div>
 </div>'''

APPEARANCE = None


def page(title, body, meta, pre="", active="", desc="Every side of every story — news from across the spectrum with bias and blindspot indicators."):
    nav = [("index.html","Top stories","top"),("blindspots.html","Blindspots","blind"),("uk.html","UK","uk"),
           ("world.html","World","world"),("stem.html","STEM","stem"),("podcasts.html","Podcasts","podcasts"),
           ("sources.html","Sources","sources"),("about.html","Methodology","about")]
    navh = "".join(f'<a href="{pre}{h}" class="{"on" if k==active else ""}">{t}</a>' for h,t,k in nav)
    global APPEARANCE
    if APPEARANCE is None: APPEARANCE = appearance_panel()
    return f'''<!doctype html>
<html lang="en-GB" data-assets="{pre}assets/" data-built="{esc(meta.get("built_utc") or "")}">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<meta name="theme-color" content="#0f1115">
<link rel="icon" href="{pre}assets/favicon.svg" type="image/svg+xml">
<link rel="icon" href="{pre}assets/favicon-32.png" sizes="32x32" type="image/png">
<link rel="apple-touch-icon" href="{pre}assets/apple-touch-icon.png">
<meta property="og:site_name" content="Impartial News">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:type" content="website">
<meta property="og:image" content="https://danliterary.github.io/impartial-news/assets/og.png">
<meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:image" content="https://danliterary.github.io/impartial-news/assets/og.png">
<link rel="stylesheet" href="{pre}assets/style.css">
<link rel="stylesheet" href="{pre}assets/themes.css">
{HEAD_SCRIPT}
</head>
<body>
<header class="masthead">
 <div class="wrap mast-row">
  <a class="brand" href="{pre}index.html">{LOGO}<span class="wordmark">Impartial<span>News</span></span></a>
  <div class="mast-right"><span class="updated">Updated {esc(meta["built_uk"])}</span>
  <div class="mast-tools">{sync_control(meta)}
  {APPEARANCE}</div></div>
 </div>
 <nav class="wrap nav" aria-label="Sections">{navh}</nav>
</header>
<main class="wrap">
{body}
</main>
<footer class="site-foot"><div class="wrap">
 <div class="foot-brand">{LOGO}<strong>Impartial News</strong></div>
 <p>Headlines and links belong to their publishers; we link to the original articles. Bias ratings are taken from Media Bias/Fact Check and shown per outlet — they describe outlets, not individual articles. Blindspot and framing indicators are automated heuristics. <a href="{pre}about.html">How this works</a>.</p>
 <p class="small">Built {esc(meta["built_uk"])} · {meta["feeds_ok"]}/{meta["feeds_total"]} feeds · {meta["articles"]} articles · {meta["stories"]} stories{(" · " + str(meta["podcasts"]) + " podcast episodes") if meta.get("podcasts") else ""}</p>
</div></footer>
<div class="sync-toast" id="sync-toast" hidden role="status" aria-live="polite"></div>
<script src="{pre}assets/app.js"></script>
</body></html>'''

def filterbar(sources, stories, extra=""):
    used = Counter(o for s in stories for o in s["outlets"])
    opts = "".join(f'<option value="{k}">{esc(v["name"])} ({SIDE_NAME[v["bucket"]]}) · {used.get(k,0)}</option>'
                   for k, v in sorted(sources.items(), key=lambda kv: kv[1]["name"]) if used.get(k))
    return f'''<div class="filterbar">
 <label class="sel"><span>Outlet</span><select id="f-outlet"><option value="">All outlets</option>{opts}</select></label>
 <div class="seg-toggle" id="f-side" role="group" aria-label="Filter by coverage">
  <button data-v="" class="on">All</button><button data-v="blind">Blindspots</button><button data-v="multi">Covered by all sides</button>
 </div>
 {extra}<span class="fcount" id="f-count"></span>
</div>'''

def statstrip(meta):
    return f'''<section class="stats">
 <div><b>{meta["stories"]}</b><span>stories</span></div>
 <div><b>{meta["articles"]}</b><span>articles</span></div>
 <div><b>{meta["feeds_ok"]}</b><span>live feeds</span></div>
 <div><b>{meta["blindspots"]}</b><span>blindspots</span></div>
</section>'''

def legend():
    return '<div class="legend"><span><i class="l"></i>Left</span><span><i class="c"></i>Centre</span><span><i class="r"></i>Right</span><a href="about.html">share of outlets covering the story, by MBFC rating</a></div>'

def list_page(title, intro, stories, sources, meta, active, hero=True, empty="No stories in this section right now.", after_hero="", head_extra="", bar_extra=""):
    body = [f'<section class="page-head">{head_extra}<h1>{esc(title)}</h1><p>{intro}</p>{legend()}</section>', filterbar(sources, stories, bar_extra)]
    if not stories:
        body.append(f'<p class="empty">{empty}</p>')
    else:
        if hero:
            body.append('<div class="hero-row">' + card(stories[0], hero=True) +
                        '<div class="side-list">' + "".join(card(s) for s in stories[1:3]) + '</div></div>')
            body.append(after_hero)
            rest = stories[3:]
        else:
            rest = stories
        body.append('<div class="grid">' + "".join(card(s) for s in rest) + '</div>')
    body.append('<p class="empty hidden" id="f-empty">No stories match this filter.</p>')
    return "\n".join(body)


REGION_NAME = {"uk": "UK", "us": "US", "world": "World", "stem": "STEM"}
LEAN_NAME = {"left": "Left", "center": "Centre", "right": "Right", "unrated": "Unrated"}

def lean_chip(ep):
    bucket = ep.get("bucket") or "unrated"
    label = ep.get("bias_label") or LEAN_NAME.get(bucket, "Unrated")
    if bucket == "unrated":
        return '<span class="chip lean unrated" title="No published Media Bias/Fact Check rating was found for this show">Unrated</span>'
    applies = ep.get("rating_applies_to") or ""
    note = ep.get("rating_note") or ""
    title = f"{label} · MBFC"
    if applies == "outlet": title += " rating of the parent outlet"
    elif applies == "host": title += " journalist rating of the host"
    if note: title += " — " + note
    cls = "proscience" if label == "Pro-Science" else bucket
    return f'<span class="chip lean {cls}" title="{esc(title)}">{esc(label)}</span>'

def pod_card(ep, compact=False):
    dur = f'<span class="pod-dur">{esc(ep["duration"])}</span>' if ep.get("duration") else ""
    notes = f'<a class="pod-notes" href="{esc(ep["url"])}" target="_blank" rel="noopener">Show notes</a>' if ep.get("url") else ""
    player = (f'<audio class="pod-audio" controls preload="none" controlslist="nodownload">'
              f'<source src="{esc(ep["audio"])}" type="{esc(ep.get("audio_type") or "audio/mpeg")}">'
              f'Your browser cannot play this audio. <a href="{esc(ep["audio"])}">Open the episode</a>.</audio>')
    region = REGION_NAME.get(ep.get("region"), ep.get("region") or "")
    hosts = f'<span class="pod-hosts">{esc(ep["hosts"])}</span>' if ep.get("hosts") and not compact else ""
    summ = f'<p class="sum clamp">{esc(ep["summary"])}</p>' if ep.get("summary") and not compact else ""
    cls = "pod-card compact" if compact else "pod-card"
    show_href = ep.get("homepage") or ep.get("url") or "podcasts.html"
    return (
        f'<article class="{cls}" data-id="{ep["id"]}" data-show="{esc(ep["show_id"])}" data-region="{esc(ep.get("region") or "")}" data-bucket="{esc(ep.get("bucket") or "unrated")}">'
        f'<div class="card-meta"><span class="chip region">{esc(region)}</span>{lean_chip(ep)}{dur}<time datetime="{ep["published"]}">{esc(ep["published_uk"])}</time></div>'
        f'<p class="pod-show"><a href="{esc(show_href)}" target="_blank" rel="noopener">{esc(ep["show"])}</a> <span class="pod-outlet">{esc(ep["outlet"])}</span></p>'
        f'<h3 class="headline">{esc(ep["title"])}</h3>'
        f'{hosts}{summ}{player}'
        f'<div class="card-foot">{notes}</div></article>'
    )

def podcasts_strip(episodes, meta):
    if not episodes: return ""
    cards = "".join(pod_card(ep, compact=True) for ep in episodes[:6])
    n = meta.get("podcasts", len(episodes))
    shows = meta.get("podcast_shows", 0)
    kicker = "Listen · UK · US · World · STEM"
    return (
        f'<section class="pod-strip" aria-labelledby="pod-h">'
        f'<div class="stem-head"><div><span class="kicker pod-kicker">{kicker}</span>'
        f'<h2 id="pod-h"><a href="podcasts.html">Latest News Podcasts</a></h2>'
        f'<p>{n} recent episode{"s" if n!=1 else ""} from {shows} show{"s" if shows!=1 else ""}, with a built-in player and the same lean labels used on the stories.</p></div>'
        f'<a class="see-all" href="podcasts.html">See all podcasts <span>→</span></a></div>'
        f'<div class="pod-grid">{cards}</div></section>'
    )


def podcasts_page(episodes, shows, meta, podcast_status=None):
    back = '<a class="backlink" href="index.html">← Back to all news</a>'
    intro = (
        "English-language news and current-affairs podcasts from across the spectrum, plus a short STEM list. "
        "Each episode has a built-in player. Lean labels come from Media Bias/Fact Check: usually the parent outlet, "
        "and never an invented rating. Shows without a published MBFC page are marked Unrated."
    )
    filt = (
        '<div class="filterbar" id="p-filters">'
        '<div class="seg-toggle" id="p-region" role="group" aria-label="Filter by region">'
        '<button type="button" data-v="" class="on">All</button>'
        '<button type="button" data-v="uk">UK</button>'
        '<button type="button" data-v="us">US</button>'
        '<button type="button" data-v="world">World</button>'
        '<button type="button" data-v="stem">STEM</button></div>'
        '<div class="seg-toggle" id="p-side" role="group" aria-label="Filter by lean">'
        '<button type="button" data-v="" class="on">All leans</button>'
        '<button type="button" data-v="left">Left</button>'
        '<button type="button" data-v="center">Centre</button>'
        '<button type="button" data-v="right">Right</button>'
        '<button type="button" data-v="unrated">Unrated</button></div>'
        '<span class="fcount" id="p-count"></span></div>'
    )
    cards = "".join(pod_card(ep) for ep in episodes) if episodes else '<p class="empty">No recent podcast episodes in this build.</p>'
    rows = []
    status = {s["show"]: s for s in (podcast_status or [])}
    order = {"left": 0, "center": 1, "right": 2, "unrated": 3}
    for s in sorted(shows or [], key=lambda x: (order.get(x.get("bucket"), 9), x["name"])):
        st = status.get(s["id"], {})
        kept = st.get("kept")
        kept_s = f"{kept} episode{'s' if kept!=1 else ''} in this build" if kept is not None else ""
        if s.get("rating_status") == "published" and s.get("rating_url"):
            who = {"outlet": "parent outlet", "host": "host", "show": "show"}.get(s.get("rating_applies_to") or "outlet", "outlet")
            rating = f'<a href="{esc(s["rating_url"])}" target="_blank" rel="noopener">{esc(s["bias_label"])}</a> <small>MBFC, {esc(who)}</small>'
        else:
            rating = '<em class="est">No published MBFC rating</em>'
        hostbit = (" · " + esc(s["hosts"])) if s.get("hosts") else ""
        rows.append(
            f'<tr><td><a href="{esc(s["homepage"])}" target="_blank" rel="noopener">{esc(s["name"])}</a>'
            f'<small>{esc(s["outlet"])}{hostbit}</small></td>'
            f'<td>{esc(REGION_NAME.get(s["region"], s["region"]))}</td>'
            f'<td>{rating}</td><td class="small">{esc(kept_s)}</td></tr>'
        )
    table = ""
    if rows:
        table = (
            '<section class="prose pod-shows"><h2>Shows we follow</h2>'
            '<p>Every show below has a public RSS feed with playable audio enclosures. Subscriber-only or paywalled feeds were not added.</p>'
            '<div class="table-wrap"><table class="src"><thead><tr><th>Show</th><th>Region</th><th>MBFC rating</th><th>This build</th></tr></thead>'
            f'<tbody>{("".join(rows))}</tbody></table></div></section>'
        )
    body = (
        f'<section class="page-head">{back}<h1>Podcasts</h1><p>{intro}</p>'
        f'<p class="legend"><span><i class="l"></i>Left</span><span><i class="c"></i>Centre, including MBFC Pro-Science</span><span><i class="r"></i>Right</span>'
        f'<a href="about.html#podcasts">How podcast ratings work</a></p></section>'
        f'{filt}<div class="pod-list">{cards}</div>'
        f'<p class="empty hidden" id="p-empty">No episodes match this filter.</p>'
        f'{table}<p class="back-foot"><a class="backlink" href="index.html">← Back to all news</a></p>'
    )
    return page("Podcasts — Impartial News", body, meta, active="podcasts",
                desc="Free English-language news and current-affairs podcasts, with lean labels and a built-in player.")


def stem_strip(stem, meta):
    if not stem: return ""
    cards = "".join(card(x) for x in stem[:6])
    topics = Counter(t for x in stem for t in x["stem_topics"])
    tl = "".join(f'<a class="tchip" href="stem.html?topic={k}">{esc(STEM_LABEL[k])} <b>{c}</b></a>' for k, c in topics.most_common())
    return f'''<section class="stem-strip" aria-labelledby="stem-h">
 <div class="stem-head">
  <div><span class="kicker">Science · Technology · Engineering · Maths</span><h2 id="stem-h"><a href="stem.html">STEM</a></h2>
  <p>{len(stem)} science and technology stories, with the same bias bars and blindspot checks.</p></div>
  <a class="see-all" href="stem.html">See all STEM news <span>→</span></a>
 </div>
 <div class="stem-topics">{tl}</div>
 <div class="stem-grid">{cards}</div>
</section>'''

def stem_page(stem, sources, meta):
    topics = Counter(t for x in stem for t in x["stem_topics"])
    chips_ = '<div class="seg-toggle" id="f-topic" role="group" aria-label="Filter by STEM topic"><button data-v="" class="on">All topics</button>' + "".join(
        f'<button data-v="{k}">{esc(STEM_LABEL[k])} <small>{topics.get(k,0)}</small></button>' for k in STEM_LABEL if topics.get(k)) + '</div>'
    back = '<a class="backlink" href="index.html">← Back to all news</a>'
    body = list_page("STEM", "Science, technology, health and environment stories, grouped and scored like the rest of Impartial News. STEM stories also appear in Top stories.",
                     stem, sources, meta, "stem", head_extra=back, bar_extra=chips_, empty="No STEM stories in this build.")
    body += '<p class="back-foot"><a class="backlink" href="index.html">← Back to all news</a></p>'
    return page("STEM — Impartial News", body, meta, active="stem")

def story_page(st, sources, meta):
    cols = []
    for side in SIDES:
        arts = [a for a in st["articles"] if a["bucket"] == side]
        items = "".join(f'''<li class="art"><div class="art-head"><span class="ob {a["bucket"]}">{ABBR.get(a["outlet"], a["name"][:3].upper())}</span>
<span class="art-src">{esc(a["name"])}{' <em class="est">rating estimated</em>' if sources[a["outlet"]]["rating_status"]!="published" else ""}</span><time datetime="{a["published"]}">{esc(a["time_uk"])}</time></div>
<a class="art-title" href="{esc(a["url"])}" target="_blank" rel="noopener">{esc(a["title"])}</a>
{f'<p class="art-sum">{esc(a["summary"])}</p>' if a["summary"] else ""}
{'<span class="via">Link via Google News</span>' if a["via"] else ""}</li>''' for a in arts)
        cols.append(f'''<section class="col {side}"><h2><i class="{side[0]}"></i>{SIDE_NAME[side]} <span>{len(arts)}</span></h2>
<ul>{items or '<li class="none">No outlets rated '+SIDE_NAME[side]+' covered this story in the current window.</li>'}</ul></section>''')
    fr = st["framing"]
    if fr:
        rows = "".join(f'<tr><th>{SIDE_NAME[s]}</th><td>{v["n"]}</td><td>{v["tone"]:+.2f}</td><td>{", ".join(v["loaded"]) or "—"}</td></tr>'
                       for s, v in fr["sides"].items())
        frh = f'''<section class="framing"><div class="fr-head"><h2>Framing check</h2><span class="auto">Automated heuristic</span></div>
<p>{esc(fr["note"])}</p>
<table><thead><tr><th>Side</th><th>Headlines</th><th>Avg tone</th><th>Loaded words</th></tr></thead><tbody>{rows}</tbody></table>
<p class="small">Tone is the mean VADER sentiment score of headlines (−1 very negative … +1 very positive). Loaded words come from a fixed list of emotive terms. This compares wording only; it cannot judge accuracy or intent. <a href="../about.html#framing">Method</a></p></section>'''
    else:
        frh = '<section class="framing"><div class="fr-head"><h2>Framing check</h2><span class="auto">Automated heuristic</span></div><p>Needs at least one left- and one right-rated headline to compare; not available for this story.</p></section>'
    blind = ""
    if st["blindspot_for"]:
        other = "right" if st["blindspot_for"] == "left" else "left"
        blind = f'<div class="blind-banner {st["blindspot_for"]}"><b>Blindspot for the {SIDE_NAME[st["blindspot_for"]]}</b> — {st["share"][other]}% of the {st["n_outlets"]} outlets covering this story are rated {SIDE_NAME[other]}. Readers who mainly follow {SIDE_NAME[st["blindspot_for"]].lower()}-leaning outlets may not have seen it.</div>'
    body = f'''<p class="crumb"><a href="../index.html">← All stories</a></p>
<article class="story">
 <div class="card-meta">{chips(st)}<time>First seen {esc(st["first_uk"])} · updated {esc(st["last_uk"])}</time></div>
 <h1 class="story-h">{esc(st["headline"])}</h1>
 <p class="hl-credit">Headline as published by {esc(st["headline_outlet"])}</p>
 {f'<p class="lede">{esc(st["summary"])}</p>' if st["summary"] else ""}
 <div class="dist"><div class="dist-head"><h2>Coverage by bias</h2><span>{st["n_outlets"]} outlets · {st["n_articles"]} articles</span></div>
 {biasbar(st["share"], st["counts"], big=True)}
 <div class="dist-nums"><span><i class="l"></i>Left {st["counts"]["left"]}</span><span><i class="c"></i>Centre {st["counts"]["center"]}</span><span><i class="r"></i>Right {st["counts"]["right"]}</span></div></div>
 {blind}
 {frh}
 <div class="cols">{"".join(cols)}</div>
</article>'''
    return page(f'{st["headline"]} — Impartial News', body, meta, pre="../", active="", desc=st["summary"][:150] if st["summary"] else st["headline"])

def sources_page(sources, smeta, feed_status, stories, meta):
    used = Counter(o for s in stories for o in s["outlets"])
    fs = {}
    for f in feed_status: fs.setdefault(f["outlet"], []).append(f)
    rows = []
    for side in SIDES:
        for k, v in sorted(sources.items(), key=lambda kv: kv[1]["name"]):
            if v["bucket"] != side: continue
            feeds = fs.get(k, [])
            okc = sum(f["ok"] for f in feeds)
            via = " · via Google News" if any(f.get("via") for f in feeds) else ""
            status = f'<span class="pill {"ok" if okc==len(feeds) else "warn" if okc else "bad"}">{okc}/{len(feeds)} feeds{via}</span>'
            rating = (f'<a href="{esc(v["rating_url"])}" target="_blank" rel="noopener">{esc(v["bias_label"])}</a><small>{esc(v["rating_source"])}, checked {esc(smeta["rating_checked"])}</small>'
                      if v["rating_status"] == "published" else f'{esc(v["bias_label"])} <em class="est">estimated</em>')
            rows.append(f'<tr><td><span class="ob {side}">{ABBR.get(k,k[:3].upper())}</span> <a href="{esc(v["homepage"])}" target="_blank" rel="noopener">{esc(v["name"])}</a><small>{esc(v["country"])}</small></td><td><span class="side-tag {side}">{SIDE_NAME[side]}</span></td><td>{rating}</td><td>{esc(v["factual_reporting"])}</td><td>{status}</td><td><a href="index.html?outlet={k}">{used.get(k,0)} stories</a></td></tr>')
    cnt = Counter(v["bucket"] for v in sources.values())
    excl = ", ".join(sorted(smeta.get("excluded_paywalled", {}).keys()))
    failed = [f for f in feed_status if not f["ok"]]
    failh = "".join(f'<li><b>{esc(sources[f["outlet"]]["name"])}</b> — <code>{esc(f["url"][:90])}</code> — {esc(f.get("error",""))}</li>' for f in failed) or "<li>None in this build.</li>"
    body = f'''<section class="page-head"><h1>Sources</h1><p>{len(sources)} free-to-read outlets: {cnt["left"]} rated left, {cnt["center"]} centre and {cnt["right"]} right. Paywalled or hard-metered outlets are deliberately excluded so every link opens for free. News and current-affairs podcasts are listed separately on the <a href="podcasts.html">Podcasts</a> page.</p>{legend()}</section>
<div class="table-wrap"><table class="src"><thead><tr><th>Outlet</th><th>Bucket</th><th>Published rating</th><th>Factual (MBFC)</th><th>Feed status (this build)</th><th>In build</th></tr></thead><tbody>{"".join(rows)}</tbody></table></div>
<section class="prose"><h2>Feeds that failed in this build</h2><ul>{failh}</ul>
<p class="small">Publisher feeds that failed when the site was set up (for example CNN's and the New Statesman's own RSS) are replaced with Google News site-search feeds for that publisher; those links pass through Google News before reaching the article. Excluded as paywalled/metered: {esc(excl)}.</p></section>'''
    return page("Sources — Impartial News", body, meta, active="sources")

def about_page(meta, smeta, sources):
    p = meta["params"]
    cnt = Counter(v["bucket"] for v in sources.values())
    body = f'''<section class="page-head"><h1>Methodology</h1><p>What Impartial News measures, where the ratings come from, and the limits of the heuristics.</p></section>
<section class="prose">
<h2>What this is</h2>
<p>Impartial News gathers headlines from {len(sources)} free-to-read UK and international news outlets across the political spectrum, groups articles that report the same story, and shows <b>who is covering it</b>. It does not write or rewrite news: every headline is the publisher's own, and every source link goes to the original article.</p>
<h2>Where bias ratings come from</h2>
<p>Each outlet's lean is taken from its page on <a href="https://mediabiasfactcheck.com/" target="_blank" rel="noopener">Media Bias/Fact Check</a> (MBFC), checked on {esc(smeta["rating_checked"])}. Every rating links to its source on the <a href="sources.html">Sources</a> page. MBFC's five labels are grouped into three buckets:</p>
<ul><li><b>Left</b> = MBFC “Left” or “Left-Center”</li><li><b>Centre</b> = MBFC “Least Biased”</li><li><b>Right</b> = MBFC “Right-Center” or “Right”</li></ul>
<p>AllSides and Ad Fontes Media also publish ratings, but their pages could not be retrieved for checking when this site was built, so none of their ratings are cited here. If an outlet has no published rating, it is shown as <em class="est">estimated</em> wherever it appears. In the current list every outlet has a published MBFC rating. Ratings describe an outlet's overall editorial lean, not any single article, and other raters may place some outlets differently.</p>
<h2>Grouping articles into stories</h2>
<p>Articles from the last {p["max_age_h"]} hours are converted to TF-IDF vectors (headline weighted twice, plus the feed summary) and grouped by average-linkage clustering with a cosine-similarity threshold of {p["sim_threshold"]}. A second pass merges clusters whose average vectors have a cosine similarity of at least {p.get("merge_threshold", 0.3)}, which catches one story split by different wording. A story needs at least two different outlets. Matching text is imperfect: occasionally two related stories merge, or one story splits in two.</p>
<h2>The bias bar</h2>
<p>The bar shows the share of <b>distinct outlets</b> covering a story in each bucket, not the number of articles, so one outlet publishing five pieces still counts once. The source pool has {cnt["left"]} left, {cnt["center"]} centre and {cnt["right"]} right outlets. Because the centre group is smaller, centre shares are naturally lower.</p>
<h2 id="blindspot">Blindspots (selective emphasis)</h2>
<p>A story is flagged as a <b>Blindspot</b> when it is covered by at least {p["blindspot_min"]} outlets and at least {int(p["blindspot_share"]*100)}% of them sit on one side. “Blindspot for the Right” means mostly left-rated outlets are covering it, so readers of right-leaning media may be missing it, and the reverse for “Blindspot for the Left”. This measures coverage <i>in the feeds we read</i> during the window. An outlet may have covered the story in a section without an RSS feed, or outside the window.</p>
<h2 id="framing">Framing check (automated heuristic)</h2>
<p>For stories with both left- and right-rated coverage, we compare headline wording across sides using: (1) the average <a href="https://github.com/cjhutto/vaderSentiment" target="_blank" rel="noopener">VADER</a> sentiment score of the headlines; (2) counts of words from a fixed list of loaded or emotive terms, such as “slams”, “chaos” or “regime”; and (3) words that appear in one side's headlines but not the other's. It is a crude signal. It does not understand sarcasm, quotation or context, and it cannot judge whether coverage is accurate. Treat it as a prompt to read across the spectrum, not as a verdict.</p>
<h2 id="stem">STEM</h2>
<p>A story is tagged STEM when at least half of its articles either come from a publisher's science, technology or environment feed or contain science and technology keywords. Its topic (Space, AI &amp; Tech, Health &amp; Medicine, Climate &amp; Environment, Science &amp; Engineering) comes from the same keyword lists. Science and technology feeds use a {p.get("stem_max_age_h", 60)}-hour window because those stories move more slowly. STEM stories stay in Top stories as well as appearing on the <a href="stem.html">STEM page</a>.</p>
<h2 id="podcasts">Podcasts</h2>
<p>The <a href="podcasts.html">Podcasts</a> page lists recent episodes from a fixed set of free, English-language news, current-affairs and STEM shows. Each episode is played in the page with a standard HTML5 audio player; we do not host the audio files. A compact “Latest News Podcasts” strip also appears on the front page. A show is included only when its public RSS feed returns a playable audio enclosure (MP3 or similar). Subscriber-only, Wondery+ or other paywalled feeds are skipped, as are shows whose parent news site is already excluded as paywalled, even if the podcast audio itself is free.</p>
<p>Lean labels use the same Media Bias/Fact Check source as the rest of the site. If a show has no MBFC page of its own, the parent outlet’s published rating is used and the badge says so. The Megyn Kelly Show uses Megyn Kelly’s journalist rating, which is also labelled. If no published page is found for the show, the host or a clear parent outlet, the show is marked <em class="est">Unrated</em> — a lean is never invented. MBFC’s “Pro-Science” label is shown as published and is grouped with Centre in the filter. Daily shows use a window of about three to four days; weekly and STEM shows use up to 21 days, and each show contributes at most three episodes in a build.</p>
<h2>Exclusions and limits</h2>
<p>Paywalled or hard-metered outlets are excluded, including the FT, The Times, The Telegraph, the WSJ, the New York Times, the Washington Post, The Economist and The Spectator. Some publishers do not offer a working RSS feed. For those, which are Reuters, AP, CNN and the New Statesman, a Google News search feed restricted to the publisher's domain is used and marked “via Google News”. Times are shown in UK time ({esc(meta["built_uk"].split(", ")[-1].split(" ")[-1])}).</p>
<h2>Refresh</h2>
<p>The site is regenerated from the feeds every 30 minutes. The <b>Sync</b> button in the header checks whether a newer build is already live and reloads the page if it is. If you save a fine-grained GitHub token in your own browser — Actions: Read and write on the <code>danliterary/impartial-news</code> repository, stored only on this device — Sync can also start a fresh scrape of every news and podcast feed now, then reload the page when that build is live. You can start the same job from the <a href="https://github.com/danliterary/impartial-news/actions/workflows/pages.yml" target="_blank" rel="noopener">Actions tab on GitHub</a>. This build: {esc(meta["built_uk"])}, from {meta["feeds_ok"]} of {meta["feeds_total"]} feeds{(" and " + str(meta["podcast_feeds_ok"]) + " of " + str(meta["podcast_feeds_total"]) + " podcast feeds") if meta.get("podcast_feeds_total") else ""}.</p>
</section>'''
    return page("Methodology — Impartial News", body, meta, active="about")

def page404(*a, **k):
    # GitHub Pages serves 404.html at any missing URL, so pin links to the project root.
    return page(*a, **k).replace("<head>", '<head>\n<base href="/impartial-news/">', 1)

def render_site(SITE, ROOT, meta, stories, sources, smeta, feed_status, stem_labels=None, episodes=None, podcast_shows=None, podcast_status=None):
    if stem_labels: STEM_LABEL.update(stem_labels)
    stem = [s for s in stories if s.get("stem")]
    tmp = SITE + ".tmp"
    shutil.rmtree(tmp, ignore_errors=True)
    os.makedirs(os.path.join(tmp, "story")); os.makedirs(os.path.join(tmp, "data"))
    shutil.copytree(os.path.join(ROOT, "static"), os.path.join(tmp, "assets"))
    open(os.path.join(tmp, "assets", "themes.css"), "w").write(TH.css())
    W = lambda name, s: open(os.path.join(tmp, name), "w", encoding="utf-8").write(s)
    top = stories[:60]
    W("index.html", page("Impartial News — every side of every story",
        statstrip(meta) + list_page("Top stories", "The most widely covered stories right now, ranked by how many outlets are reporting them.", top, sources, meta, "top", after_hero=stem_strip(stem, meta) + podcasts_strip(episodes or [], meta)), meta, active="top"))
    W("stem.html", stem_page(stem, sources, meta))
    W("podcasts.html", podcasts_page(episodes or [], podcast_shows or [], meta, podcast_status))
    bl = [s for s in stories if s["blindspot_for"] == "left"]
    br = [s for s in stories if s["blindspot_for"] == "right"]
    fb = lambda lst: "".join(card(s) for s in lst) or '<p class="empty">None in this build.</p>'
    W("blindspots.html", page("Blindspots — Impartial News", f'''<section class="page-head"><h1>Blindspots</h1><p>Stories covered mainly by one side of the spectrum: at least {meta["params"]["blindspot_min"]} outlets, and {int(meta["params"]["blindspot_share"]*100)}% or more of them on one side. <a href="about.html#blindspot">How this is calculated</a>.</p>{legend()}</section>
{filterbar(sources, bl+br)}
<div class="blind-cols"><section><h2 class="bh left">Blindspot for the Left <span>{len(bl)}</span></h2><p class="bsub">Covered mostly by right-rated outlets.</p><div class="stack">{fb(bl)}</div></section>
<section><h2 class="bh right">Blindspot for the Right <span>{len(br)}</span></h2><p class="bsub">Covered mostly by left-rated outlets.</p><div class="stack">{fb(br)}</div></section></div><p class="empty hidden" id="f-empty">No stories match this filter.</p>''', meta, active="blind"))
    uk = [s for s in stories if s["region"] == "uk"]; wd = [s for s in stories if s["region"] == "world"]
    W("uk.html", page("UK — Impartial News", list_page("UK", "Stories about Britain, ranked by breadth of coverage.", uk, sources, meta, "uk"), meta, active="uk"))
    W("world.html", page("World — Impartial News", list_page("World", "International stories, ranked by breadth of coverage.", wd, sources, meta, "world"), meta, active="world"))
    W("sources.html", sources_page(sources, smeta, feed_status, stories, meta))
    W("about.html", about_page(meta, smeta, sources))
    for st in stories:
        W(os.path.join("story", st["id"] + ".html"), story_page(st, sources, meta))
    json.dump({"meta": meta, "stories": stories}, open(os.path.join(tmp, "data", "stories.json"), "w"), ensure_ascii=False)
    json.dump(feed_status, open(os.path.join(tmp, "data", "feeds_status.json"), "w"), indent=1)
    json.dump({"episodes": episodes or [], "shows": podcast_shows or [], "status": podcast_status or []},
              open(os.path.join(tmp, "data", "podcasts.json"), "w"), ensure_ascii=False)
    status = {
        "generated_at": meta.get("built_utc"),
        "generated_at_uk": meta.get("built_uk"),
        "stories": meta.get("stories"),
        "articles": meta.get("articles"),
        "feeds_ok": meta.get("feeds_ok"),
        "feeds_total": meta.get("feeds_total"),
        "podcasts_ok": meta.get("podcast_feeds_ok"),
        "podcasts_total": meta.get("podcast_feeds_total"),
        "episodes": meta.get("podcasts"),
    }
    json.dump(status, open(os.path.join(tmp, "assets", "status.json"), "w"), indent=1, ensure_ascii=False)
    W(".nojekyll", "")
    W("404.html", page404("Not found — Impartial News", '<section class="page-head"><h1>Story not found</h1><p>Stories roll off after about a day and a half. <a href="index.html">Back to the latest</a>.</p></section>', meta))
    old = SITE + ".old"
    shutil.rmtree(old, ignore_errors=True)
    if os.path.exists(SITE): os.rename(SITE, old)
    os.rename(tmp, SITE)
    shutil.rmtree(old, ignore_errors=True)
