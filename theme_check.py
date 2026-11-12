"""Loads every page in every theme; checks console errors, failed requests, no-flash head script, prefers-color-scheme default,
bias-bar label contrast as rendered; saves shots/theme-<id>.png and shots/theme-selector-open.png."""
import json, glob, os, sys
sys.path.insert(0, os.path.dirname(__file__))
from themes import THEMES, FONTS, SIZES, LAZY_FONTS, DEFAULT_SIZE, FONT_MIGRATE, SIZE_MIGRATE
from playwright.sync_api import sync_playwright
BASE = "http://localhost:8765/impartial-news/"
SITE = "/workspace/ferret-news/site"
story = sorted(glob.glob(SITE + "/story/*.html"))
pages = ["index.html", "blindspots.html", "uk.html", "world.html", "stem.html", "sources.html", "about.html", "404.html"] + \
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
    for path, shot_9, shot_28 in [("index.html", "size-9.png", "size-28.png"), ("stem.html", None, None), ("about.html", None, None)]:
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
