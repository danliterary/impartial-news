"""Loads every page in every theme; checks console errors, failed requests, no-flash head script, prefers-color-scheme default,
bias-bar label contrast as rendered; saves shots/theme-<id>.png and shots/theme-selector-open.png."""
import json, glob, os, sys
sys.path.insert(0, os.path.dirname(__file__))
from themes import THEMES, FONTS, SIZES, LAZY_FONTS, DEFAULT_SIZE, FONT_MIGRATE, SIZE_MIGRATE
from playwright.sync_api import sync_playwright
BASE = "http://localhost:8765/impartial-news/"
SITE = "/workspace/ferret-news/site"
story = sorted(glob.glob(SITE + "/story/*.html"))
pages = ["index.html", "blindspots.html", "uk.html", "world.html", "stem.html", "podcasts.html", "sources.html", "about.html", "404.html"] + \
        ["story/" + os.path.basename(p) for p in story[:3]]
problems = []
def lum(rgb):
    f = lambda c: c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = [f(x / 255) for x in rgb]; return 0.2126 * r + 0.7152 * g + 0.0722 * b
def parse(c):
    import re; return [int(float(x)) for x in re.findall(r"[\d.]+", c)[:3]]
with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox"])
    for tid, name, *_ in THEMES:
        ctx = b.new_context(viewport={"width": 1366, "height": 900})
        ctx.add_init_script(f"try{{if(!sessionStorage.getItem('seeded')){{localStorage.setItem('in-theme','{tid}');sessionStorage.setItem('seeded','1')}}}}catch(e){{}}")
        pg = ctx.new_page()
        errs = []
        pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
        pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.on("response", lambda r: errs.append(f"{r.status} {r.url}") if r.status >= 400 and not r.url.endswith("404.html") else None)
        for path in pages:
            pg.goto(BASE + path, wait_until="networkidle")
            got = pg.evaluate("document.documentElement.dataset.theme")
            if got != tid: problems.append(f"{tid} {path}: data-theme={got}")
            # rendered contrast of bias segment labels
            if not pg.query_selector("#sync-btn"):
                problems.append(f"{tid} {path}: missing #sync-btn")
            sb = pg.query_selector("#sync-btn")
            if sb:
                fg, bg = sb.evaluate("e=>[getComputedStyle(e).color,getComputedStyle(e).backgroundColor]")
                la, lb = sorted([lum(parse(fg)), lum(parse(bg))], reverse=True); c = (la + .05) / (lb + .05)
                if c < 4.5: problems.append(f"{tid} {path}: sync button contrast {c:.2f} ({fg} on {bg})")
            for seg in pg.query_selector_all(".biasbar .seg")[:6]:
                fg, bg = seg.evaluate("e=>[getComputedStyle(e).color,getComputedStyle(e).backgroundColor]")
                la, lb = sorted([lum(parse(fg)), lum(parse(bg))], reverse=True); c = (la + .05) / (lb + .05)
                if c < 4.5: problems.append(f"{tid} {path}: segment contrast {c:.2f} ({fg} on {bg})")
        for e in errs: problems.append(f"{tid}: {e}")
        pg.goto(BASE + "index.html", wait_until="networkidle"); pg.wait_for_timeout(300)
        pg.screenshot(path=f"/workspace/ferret-news/shots/theme-{tid}.png")
        if tid == "paper":
            pg.click("#appearance-btn"); pg.wait_for_timeout(300)
            pg.screenshot(path="/workspace/ferret-news/shots/theme-selector-open.png")
            # interaction test: pick sepia, 14 pt, Lora, then reload -> persisted
            pg.click('[data-theme-pick="sepia"]'); pg.click('[data-font-pick="lora"]'); pg.select_option("#ap-size-select", "14")
            pg.reload(wait_until="networkidle")
            st = pg.evaluate("[document.documentElement.dataset.theme,document.documentElement.dataset.font,document.documentElement.dataset.size,localStorage.getItem('in-theme'),localStorage.getItem('in-font'),localStorage.getItem('in-size')]")
            if st != ["sepia", "lora", "14", "sepia", "lora", "14"]: problems.append(f"persist failed: {st}")
            pg.keyboard.press("Escape")
        ctx.close()
    # no-flash: block app.js entirely; head script alone must apply theme before first paint
    for scheme, want in [("dark", "ink"), ("light", "paper")]:
        ctx = b.new_context(color_scheme=scheme); pg = ctx.new_page()
        pg.route("**/app.js", lambda r: r.abort())
        pg.goto(BASE + "stem.html", wait_until="domcontentloaded")
        got = pg.evaluate("[document.documentElement.dataset.theme, document.documentElement.dataset.scheme]")
        if got != [want, scheme]: problems.append(f"prefers-color-scheme {scheme}: {got}")
        ctx.close()
    ctx = b.new_context(color_scheme="dark"); ctx.add_init_script("try{localStorage.setItem('in-theme','sepia')}catch(e){}")
    pg = ctx.new_page(); pg.route("**/app.js", lambda r: r.abort()); pg.goto(BASE + "index.html", wait_until="domcontentloaded")
    if pg.evaluate("document.documentElement.dataset.theme") != "sepia": problems.append("saved theme not applied by head script")
    # legacy value from the old toggle
    ctx2 = b.new_context(); ctx2.add_init_script("try{localStorage.setItem('in-theme','dark')}catch(e){}")
    pg2 = ctx2.new_page(); pg2.goto(BASE + "index.html", wait_until="domcontentloaded")
    if pg2.evaluate("document.documentElement.dataset.theme") != "ink": problems.append("legacy 'dark' not migrated")
    # legacy font and size values from the previous four-option / S-M-L-XL controls
    for oldv, want in [("serif","gelasio"),("sans","inter"),("system", None)]:
        ctxm = b.new_context(); ctxm.add_init_script(f"try{{localStorage.setItem('in-font','{oldv}')}}catch(e){{}}")
        pgm = ctxm.new_page(); pgm.route("**/app.js", lambda r: r.abort())
        pgm.goto(BASE + "index.html", wait_until="domcontentloaded")
        got = pgm.evaluate("document.documentElement.dataset.font || null")
        if got != want: problems.append(f"legacy font {oldv!r} -> {got!r}, expected {want!r}")
        ctxm.close()
    for oldv, want in [("90","10"),("100", None),("112.5","12"),("125","14")]:
        ctxm = b.new_context(); ctxm.add_init_script(f"try{{localStorage.setItem('in-size','{oldv}')}}catch(e){{}}")
        pgm = ctxm.new_page(); pgm.route("**/app.js", lambda r: r.abort())
        pgm.goto(BASE + "index.html", wait_until="domcontentloaded")
        got = pgm.evaluate("document.documentElement.dataset.size || null")
        if got != want: problems.append(f"legacy size {oldv!r} -> {got!r}, expected {want!r}")
        ctxm.close()
    # no-flash for a saved typeface and size (head script only)
    ctxf = b.new_context(); ctxf.add_init_script("try{localStorage.setItem('in-font','merriweather');localStorage.setItem('in-size','18')}catch(e){}")
    pgf = ctxf.new_page(); pgf.route("**/app.js", lambda r: r.abort())
    pgf.goto(BASE + "index.html", wait_until="domcontentloaded")
    got = pgf.evaluate("[document.documentElement.dataset.font, document.documentElement.dataset.size, !!document.getElementById('in-font-merriweather')]")
    if got != ["merriweather", "18", True]: problems.append(f"head script font/size: {got}")
    ctxf.close()

    # typeface and size sweep
    ctxs = b.new_context(viewport={"width": 1366, "height": 900})
    pgs = ctxs.new_page()
    ferrs = []
    pgs.on("console", lambda m: ferrs.append(m.text) if m.type == "error" else None)
    pgs.on("pageerror", lambda e: ferrs.append(str(e)))
    pgs.on("response", lambda r: ferrs.append(f"{r.status} {r.url}") if r.status >= 400 and not r.url.endswith("404.html") else None)
    pgs.goto(BASE + "index.html", wait_until="networkidle")
    pgs.click("#appearance-btn"); pgs.wait_for_timeout(400)
    pgs.locator("#ap-font").scroll_into_view_if_needed(); pgs.wait_for_timeout(800)
    pgs.screenshot(path="/workspace/ferret-news/shots/fonts-panel.png")
    for fid, *_ in FONTS:
        pgs.click(f'[data-font-pick="{fid}"]')
        pgs.wait_for_timeout(40)
        got = pgs.evaluate("document.documentElement.dataset.font || 'default'")
        if got != fid: problems.append(f"font pick {fid}: data-font={got}")
        if fid in LAZY_FONTS and not pgs.evaluate(f"!!document.getElementById('in-font-{fid}')"):
            problems.append(f"font css not loaded: {fid}")
    pgs.click('[data-font-pick="default"]')
    for path, shot_9, shot_28 in [("index.html", "size-9.png", "size-28.png"), ("stem.html", None, None), ("podcasts.html", None, None), ("about.html", None, None)]:
        pgs.goto(BASE + path, wait_until="networkidle")
        if path == "index.html":
            pgs.click("#appearance-btn"); pgs.wait_for_timeout(200)
        pgs.locator("#ap-size-select").select_option("9", force=True)
        if path == "index.html":
            pgs.keyboard.press("Escape"); pgs.wait_for_timeout(200)
            pgs.screenshot(path="/workspace/ferret-news/shots/size-9.png")
        fs9 = pgs.evaluate("getComputedStyle(document.documentElement).fontSize")
        overflow9 = pgs.evaluate("document.documentElement.scrollWidth > window.innerWidth + 2")
        if overflow9: problems.append(f"{path} overflows at 9 pt")
        pgs.click("#appearance-btn"); pgs.locator("#ap-size-select").select_option("28", force=True)
        if path == "index.html":
            pgs.keyboard.press("Escape"); pgs.wait_for_timeout(200)
            pgs.screenshot(path="/workspace/ferret-news/shots/size-28.png")
        fs28 = pgs.evaluate("getComputedStyle(document.documentElement).fontSize")
        overflow28 = pgs.evaluate("document.documentElement.scrollWidth > window.innerWidth + 2")
        if overflow28: problems.append(f"{path} overflows at 28 pt")
        # 28 must be substantially larger than 9 (15px * 28/11 vs 15px * 9/11)
        try:
            if float(fs28.replace("px","")) <= float(fs9.replace("px","")) * 2:
                problems.append(f"{path} size scale too small: 9={fs9} 28={fs28}")
        except Exception as e:
            problems.append(f"{path} font-size parse {fs9} {fs28} {e}")
        pgs.keyboard.press("Escape")
    for e in ferrs: problems.append(f"font/size: {e}")
    ctxs.close()

    # mobile panel + size 28
    m = b.new_page(viewport={"width": 390, "height": 844}, device_scale_factor=2, is_mobile=True)
    m.goto(BASE + "index.html", wait_until="networkidle"); m.click("#appearance-btn"); m.wait_for_timeout(300)
    m.screenshot(path="/workspace/ferret-news/shots/theme-selector-open-mobile.png")
    m.locator("#ap-size-select").select_option("28", force=True); m.keyboard.press("Escape"); m.wait_for_timeout(200)
    if m.evaluate("document.documentElement.scrollWidth > window.innerWidth + 4"):
        problems.append("mobile overflows at 28 pt")

    # ---- Sync button and popover ----
    import json as _json
    def _lum_ok(page, sel, minc, label):
        el = page.query_selector(sel)
        if not el:
            problems.append(f"sync: missing {sel} for {label}")
            return
        fg, bg = el.evaluate("e=>[getComputedStyle(e).color,getComputedStyle(e).backgroundColor]")
        # allow transparent/empty backgrounds by walking up
        if bg in ("rgba(0, 0, 0, 0)", "transparent"):
            bg = el.evaluate("e=>{let n=e;while(n){const b=getComputedStyle(n).backgroundColor;if(b&&b!=='rgba(0, 0, 0, 0)'&&b!=='transparent')return b;n=n.parentElement}return getComputedStyle(document.body).backgroundColor}")
        la, lb = sorted([lum(parse(fg)), lum(parse(bg))], reverse=True)
        c = (la + .05) / (lb + .05)
        if c < minc:
            problems.append(f"sync {label}: contrast {c:.2f} for {sel} ({fg} on {bg})")

    def mock_sync(page, status=None, runs=None, jobs=None, dispatch_status=204):
        st = status or {
            "generated_at": "2026-11-13T00:28:22+00:00",
            "generated_at_uk": "13 November 2026, 00:28 GMT",
            "stories": 239, "articles": 2517, "feeds_ok": 121, "feeds_total": 121,
            "podcasts_ok": 25, "podcasts_total": 25, "episodes": 70,
        }
        rs = runs if runs is not None else {"workflow_runs": [{
            "id": 101, "status": "completed", "conclusion": "success",
            "created_at": "2026-11-13T00:20:00Z", "run_started_at": "2026-11-13T00:20:01Z",
            "name": "Build and deploy Impartial News",
        }]}
        jb = jobs if jobs is not None else {"jobs": [
            {"name": "build", "status": "completed", "conclusion": "success"},
            {"name": "deploy", "status": "completed", "conclusion": "success"},
        ]}
        def _ok(body):
            payload = _json.dumps(body)
            def handler(route, request=None):
                route.fulfill(status=200, content_type="application/json", body=payload)
            return handler
        def _dispatch(route, request=None, ds=dispatch_status):
            route.fulfill(status=ds, body="")
        page.route("**/status.json**", _ok(st))
        page.route("https://api.github.com/repos/danliterary/impartial-news/actions/workflows/pages.yml/runs**", _ok(rs))
        page.route("https://api.github.com/repos/danliterary/impartial-news/actions/runs/**/jobs**", _ok(jb))
        page.route("https://api.github.com/repos/danliterary/impartial-news/actions/workflows/pages.yml/dispatches", _dispatch)

    # button present on every key page (unmocked open is avoided here)
    ctxp = b.new_context(viewport={"width": 1366, "height": 900})
    pgp = ctxp.new_page()
    for path in ["index.html", "uk.html", "world.html", "stem.html", "podcasts.html",
                 "blindspots.html", "sources.html", "about.html", "404.html"] + \
                ["story/" + __import__("os").path.basename(p) for p in story[:3]]:
        pgp.goto(BASE + path, wait_until="networkidle")
        if not pgp.query_selector("#sync-btn") or not pgp.query_selector("#sync-panel"):
            problems.append(f"sync control missing on {path}")
        if pgp.evaluate("document.getElementById('sync-panel') && !document.getElementById('sync-panel').hidden"):
            problems.append(f"sync panel should start closed on {path}")
    ctxp.close()

    serrs = []
    ctxs2 = b.new_context(viewport={"width": 1366, "height": 900})
    pgs2 = ctxs2.new_page()
    pgs2.on("console", lambda m: serrs.append("console:"+m.text) if m.type == "error" else None)
    pgs2.on("pageerror", lambda e: serrs.append("page:"+str(e)))
    mock_sync(pgs2)
    pgs2.goto(BASE + "index.html", wait_until="networkidle")
    pgs2.wait_for_timeout(200)
    pgs2.screenshot(path="/workspace/ferret-news/shots/sync-button.png")
    pgs2.click("#sync-btn")
    pgs2.wait_for_timeout(400)
    if pgs2.evaluate("document.getElementById('sync-btn').getAttribute('aria-expanded')") != "true":
        problems.append("sync: aria-expanded not true after open")
    if pgs2.evaluate("document.getElementById('sync-panel').hidden"):
        problems.append("sync: panel stayed hidden after click")
    # default: no token, howto visible
    if pgs2.evaluate("document.getElementById('sync-howto').hidden"):
        problems.append("sync: howto hidden without a token")
    if not pgs2.evaluate("document.getElementById('sync-token-ok').hidden"):
        problems.append("sync: token-ok visible without a token")
    pgs2.wait_for_timeout(200)
    pgs2.screenshot(path="/workspace/ferret-news/shots/sync-popover.png")
    # overflow with panel open
    if pgs2.evaluate("document.documentElement.scrollWidth > window.innerWidth + 2"):
        problems.append("desktop overflows with sync popover open")
    # contrast of popover copy on Paper
    for sel, minc, lab in [("#sync-title", 4.5, "title"), ("#sync-status-text", 4.5, "status"),
                            (".sync-note", 4.5, "note"), ("#sync-check", 4.5, "check btn"),
                            ("#sync-now", 4.5, "sync now btn")]:
        _lum_ok(pgs2, sel, minc, "paper "+lab)
    # Escape closes and restores focus
    pgs2.keyboard.press("Escape")
    pgs2.wait_for_timeout(150)
    if not pgs2.evaluate("document.getElementById('sync-panel').hidden"):
        problems.append("sync: Escape did not close the panel")
    if pgs2.evaluate("document.activeElement && document.activeElement.id") != "sync-btn":
        problems.append("sync: focus did not return to the button after Escape")
    # reopen, click outside closes
    pgs2.click("#sync-btn"); pgs2.wait_for_timeout(200)
    pgs2.mouse.click(40, 700)
    pgs2.wait_for_timeout(150)
    if not pgs2.evaluate("document.getElementById('sync-panel').hidden"):
        problems.append("sync: click outside did not close the panel")
    # appearance and sync are mutually exclusive
    pgs2.click("#sync-btn"); pgs2.wait_for_timeout(150)
    pgs2.click("#appearance-btn"); pgs2.wait_for_timeout(150)
    if not pgs2.evaluate("document.getElementById('sync-panel').hidden"):
        problems.append("sync: panel stayed open after opening reader settings")
    pgs2.keyboard.press("Escape")
    for e in serrs: problems.append(f"sync paper: {e}")
    ctxs2.close()

    # token saved: howto hides, dispatch updates status
    posted = []
    ctxt = b.new_context(viewport={"width": 1366, "height": 900})
    ctxt.add_init_script("try{localStorage.setItem('in-gh-token','github_pat_TEST_TOKEN')}catch(e){}")
    pgt = ctxt.new_page()
    mock_sync(pgt, runs={"workflow_runs": []})
    # override dispatch to record the POST
    def on_dispatch(route):
        posted.append({"method": route.request.method, "has_auth": "authorization" in {k.lower():v for k,v in route.request.headers.items()}})
        body = route.request.post_data or ""
        posted[-1]["body"] = body
        route.fulfill(status=204, body="")
    pgt.unroute("https://api.github.com/repos/danliterary/impartial-news/actions/workflows/pages.yml/dispatches")
    pgt.route("https://api.github.com/repos/danliterary/impartial-news/actions/workflows/pages.yml/dispatches", on_dispatch)
    pgt.goto(BASE + "index.html", wait_until="networkidle")
    pgt.click("#sync-btn"); pgt.wait_for_timeout(300)
    if not pgt.evaluate("document.getElementById('sync-howto').hidden"):
        problems.append("sync: howto still visible with a saved token")
    if pgt.evaluate("document.getElementById('sync-token-ok').hidden"):
        problems.append("sync: token-ok hidden with a saved token")
    pgt.click("#sync-now"); pgt.wait_for_timeout(400)
    if not posted:
        problems.append("sync: dispatch was not sent")
    else:
        if posted[0]["method"] != "POST":
            problems.append(f"sync: dispatch method {posted[0]['method']}")
        if not posted[0]["has_auth"]:
            problems.append("sync: dispatch missing Authorization")
        if "main" not in (posted[0].get("body") or ""):
            problems.append("sync: dispatch body missing ref main")
    txt = pgt.evaluate("document.getElementById('sync-status-text').textContent")
    if "Queued" not in (txt or "") and "Starting" not in (txt or "") and "progress" not in (txt or "").lower() and "Fetching" not in (txt or ""):
        problems.append(f"sync: unexpected status after dispatch: {txt!r}")
    ctxt.close()

    # in-progress run shows fetching copy
    ctxi = b.new_context(viewport={"width": 1366, "height": 900})
    pgi = ctxi.new_page()
    mock_sync(pgi, runs={"workflow_runs": [{
        "id": 202, "status": "in_progress", "conclusion": None,
        "created_at": "2026-11-13T01:00:00Z", "name": "Build and deploy Impartial News",
    }]}, jobs={"jobs": [
        {"name": "build", "status": "in_progress", "conclusion": None},
        {"name": "deploy", "status": "queued", "conclusion": None},
    ]})
    pgi.goto(BASE + "stem.html", wait_until="networkidle")
    pgi.click("#sync-btn"); pgi.wait_for_timeout(500)
    txt = pgi.evaluate("document.getElementById('sync-status-text').textContent")
    if "Fetching" not in (txt or "") and "Queued" not in (txt or "") and "Syncing" not in (txt or ""):
        problems.append(f"sync: in-progress status {txt!r}")
    ctxi.close()

    # newer status.json triggers a reload
    ctxn = b.new_context(viewport={"width": 1366, "height": 900})
    pgn = ctxn.new_page()
    mock_sync(pgn, status={
        "generated_at": "2026-11-13T12:00:00+00:00",
        "generated_at_uk": "13 November 2026, 12:00 GMT",
        "stories": 240, "articles": 2600, "feeds_ok": 121, "feeds_total": 121,
        "podcasts_ok": 25, "podcasts_total": 25, "episodes": 70,
    })
    pgn.goto(BASE + "about.html", wait_until="networkidle")
    # force an older page timestamp so the mock status looks newer
    pgn.evaluate("document.documentElement.dataset.built='2026-11-13T00:28:22+00:00';var r=document.getElementById('sync-root'); if(r) r.dataset.built='2026-11-13T00:28:22+00:00'")
    with pgn.expect_navigation(timeout=8000):
        pgn.click("#sync-btn")
    if "sync=" not in pgn.url:
        problems.append(f"sync: expected reload with cache-bust param, got {pgn.url}")
    ctxn.close()

    # high-contrast popover contrast + no overflow
    for tid in ("ink", "hc-light", "hc-dark"):
        ctxh = b.new_context(viewport={"width": 1366, "height": 900})
        ctxh.add_init_script(f"try{{localStorage.setItem('in-theme','{tid}')}}catch(e){{}}")
        pgh = ctxh.new_page()
        mock_sync(pgh)
        pgh.goto(BASE + "index.html", wait_until="networkidle")
        pgh.click("#sync-btn"); pgh.wait_for_timeout(250)
        for sel, minc, lab in [("#sync-title", 4.5, "title"), ("#sync-status-text", 4.5, "status"),
                                (".sync-note", 4.5, "note"), ("#sync-check", 4.5, "check"),
                                ("#sync-now", 4.5, "now")]:
            _lum_ok(pgh, sel, minc, f"{tid} {lab}")
        if pgh.evaluate("document.documentElement.scrollWidth > window.innerWidth + 2"):
            problems.append(f"{tid} overflows with sync popover open")
        ctxh.close()

    # mobile layout
    m2 = b.new_page(viewport={"width": 390, "height": 844}, device_scale_factor=2, is_mobile=True)
    m2e = []
    m2.on("console", lambda m: m2e.append(m.text) if m.type == "error" else None)
    m2.on("pageerror", lambda e: m2e.append(str(e)))
    mock_sync(m2)
    m2.goto(BASE + "index.html", wait_until="networkidle")
    m2.click("#sync-btn"); m2.wait_for_timeout(350)
    if m2.evaluate("document.getElementById('sync-panel').hidden"):
        problems.append("sync: mobile panel did not open")
    if m2.evaluate("document.documentElement.scrollWidth > window.innerWidth + 4"):
        problems.append("mobile overflows with sync popover open")
    box = m2.evaluate("""() => {
      const p=document.getElementById('sync-panel');
      const r=p.getBoundingClientRect();
      return {left:r.left,right:r.right,top:r.top,bottom:r.bottom,dw:window.innerWidth,dh:window.innerHeight};
    }""")
    if box["left"] < -1 or box["right"] > box["dw"] + 1 or box["top"] < -1:
        problems.append(f"sync mobile panel off-screen: {box}")
    m2.screenshot(path="/workspace/ferret-news/shots/sync-mobile.png")
    m2.keyboard.press("Escape")
    m2.wait_for_timeout(150)
    if not m2.evaluate("document.getElementById('sync-panel').hidden"):
        problems.append("sync: Escape did not close the mobile panel")
    for e in m2e: problems.append(f"sync mobile: {e}")

    m.screenshot(path="/workspace/ferret-news/shots/size-28-mobile.png")
    b.close()
# contact sheet of every theme
from PIL import Image, ImageDraw, ImageFont
SHOT = "/workspace/ferret-news/shots"
cols, cell_w, cell_h, cap, pad = 5, 400, 250, 28, 12
rows_n = (len(THEMES) + cols - 1) // cols
W = cols * cell_w + (cols + 1) * pad
H = rows_n * (cell_h + cap) + (rows_n + 1) * pad + 36
sheet = Image.new("RGB", (W, H), "#1a1c20")
draw = ImageDraw.Draw(sheet)
try:
    font_t = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 18)
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
except Exception:
    font_t = font = ImageFont.load_default()
draw.text((pad, 10), "Impartial News — colour themes", fill="#f2f2f2", font=font_t)
for i, (tid, name, *_) in enumerate(THEMES):
    r, c = divmod(i, cols)
    x = pad + c * (cell_w + pad)
    y = 36 + pad + r * (cell_h + cap + pad)
    im = Image.open(f"{SHOT}/theme-{tid}.png").convert("RGB")
    # crop the masthead and first stories so the tint and header accent are visible
    crop_h = int(im.width * cell_h / cell_w)
    im = im.crop((0, 0, im.width, min(im.height, crop_h))).resize((cell_w, cell_h), Image.Resampling.LANCZOS)
    sheet.paste(im, (x, y))
    draw.rectangle((x, y, x + cell_w, y + cell_h), outline="#3a3d44")
    draw.text((x, y + cell_h + 6), name, fill="#e8e8ea", font=font)
sheet.save(f"{SHOT}/theme-grid.png")
print("wrote", f"{SHOT}/theme-grid.png", sheet.size)

print(f"pages x themes: {len(pages)} x {len(THEMES)}")
print("PROBLEMS:" if problems else "no problems", *problems[:40], sep="\n")
