"""Renders brand PNGs (favicon-32, apple-touch-icon, og.png) from static/favicon.svg using headless Chrome."""
import pathlib
from playwright.sync_api import sync_playwright
S = pathlib.Path(__file__).parent / "static"
svg = (S / "favicon.svg").read_text()
import base64
def f64(n): return "data:font/woff2;base64," + base64.b64encode((S / "fonts" / n).read_bytes()).decode()
mark = svg.replace('<rect width="64" height="64" rx="15" fill="#12141a"/>', '')
og = f'''<html><head><style>
@font-face{{font-family:N;font-weight:700;src:url({f64('newsreader-v26-latin-700.woff2')})}}
@font-face{{font-family:I;font-weight:600;src:url({f64('inter-v20-latin-600.woff2')})}}
@font-face{{font-family:I;font-weight:800;src:url({f64('inter-v20-latin-800.woff2')})}}
body{{margin:0;width:1200px;height:630px;background:radial-gradient(90% 120% at 85% 10%,#2a1f4a 0%,#12141a 55%);color:#eef0f4;font-family:I;display:flex;flex-direction:column;justify-content:center;padding:0 96px;box-sizing:border-box}}
.row{{display:flex;align-items:center;gap:30px}} .m svg{{width:150px;height:150px}}
h1{{font:700 104px/1 N;letter-spacing:-.02em;margin:0}} h1 span{{font:800 30px I;letter-spacing:.18em;background:#eef0f4;color:#12141a;padding:8px 14px;border-radius:10px;vertical-align:26px;margin-left:16px}}
p{{font:600 34px/1.35 I;color:#b3b8c2;margin:44px 0 0;max-width:900px}}
.bar{{margin-top:46px;height:14px;width:560px;border-radius:7px;background:linear-gradient(90deg,#3b7cf5,#9b6cf0,#f0566a)}}
</style></head><body><div class="row"><div class="m">{mark}</div><h1>Impartial<span>NEWS</span></h1></div>
<p>Every side of every story: see who is covering it, and who isn't.</p><div class="bar"></div></body></html>'''
with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox"])
    for name, size in [("favicon-32.png", 32), ("apple-touch-icon.png", 180)]:
        pg = b.new_page(viewport={"width": size, "height": size})
        pg.set_content(f'<body style="margin:0">{svg.replace("<svg ", f"<svg width=\"{size}\" height=\"{size}\" ", 1)}</body>')
        pg.screenshot(path=str(S / name), omit_background=True)
    pg = b.new_page(viewport={"width": 1200, "height": 630})
    pg.set_content(og); pg.evaluate("document.fonts.ready"); pg.wait_for_timeout(600)
    print(pg.evaluate("Array.from(document.fonts).map(f=>f.family+':'+f.status).join(', ')"))
    pg.screenshot(path=str(S / "og.png"))
    b.close()
print("brand assets written")
