import sys
from playwright.sync_api import sync_playwright
tag = sys.argv[1]; base = "http://localhost:8765/impartial-news/"; out = "/workspace/ferret-news/shots/"
with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox"])
    pg = b.new_page(viewport={"width": 1100, "height": 300}, device_scale_factor=2)
    pg.goto(base + "index.html", wait_until="networkidle")
    for theme, tid in [("light", "paper"), ("dark", "ink")]:
        pg.evaluate(f"document.documentElement.dataset.theme='{tid}';document.documentElement.dataset.scheme='{theme}'"); pg.wait_for_timeout(500)
        pg.screenshot(path=f"{out}logo-{tag}-masthead-{theme}.png", clip={"x": 0, "y": 0, "width": 1100, "height": 130})
    fav = b.new_page(viewport={"width": 360, "height": 140}, device_scale_factor=2)
    fav.set_content(f'''<body style="margin:0;display:flex;gap:18px;padding:22px;background:#f1f1f1"><img src="{base}assets/favicon.svg" width="96" height="96"><img src="{base}assets/favicon.svg" width="32" height="32"><img src="{base}assets/favicon.svg" width="16" height="16"><div style="background:#111;padding:10px;border-radius:8px;display:flex;gap:10px;align-items:center"><img src="{base}assets/favicon.svg" width="64" height="64"><img src="{base}assets/favicon.svg" width="16" height="16"></div></body>''')
    fav.wait_for_timeout(500); fav.screenshot(path=f"{out}logo-{tag}-favicon.png")
    b.close()
print("ok")
