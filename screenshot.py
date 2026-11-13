import sys, asyncio
from playwright.sync_api import sync_playwright
base = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8765/impartial-news/"
out = "/workspace/ferret-news/"
with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox"])
    errs = []
    pg = b.new_page(viewport={"width": 1366, "height": 900}, device_scale_factor=1)
    pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
    pg.on("requestfailed", lambda r: errs.append("FAILED " + r.url))
    pg.on("response", lambda r: errs.append(f"{r.status} {r.url}") if r.status >= 400 else None)
    pg.goto(base + "index.html", wait_until="networkidle"); pg.wait_for_timeout(500)
    pg.screenshot(path=out + "screenshot.png", full_page=False)
    pg.screenshot(path=out + "shots/front-full.png", full_page=True)
    pg.evaluate("document.documentElement.dataset.theme='ink';document.documentElement.dataset.scheme='dark'"); pg.wait_for_timeout(600)
    pg.screenshot(path=out + "shots/front-dark.png")
    pg.evaluate("document.documentElement.dataset.theme='paper';document.documentElement.dataset.scheme='light'")
    for name in ["blindspots", "sources", "about", "uk", "stem", "podcasts"]:
        pg.goto(base + name + ".html", wait_until="networkidle"); pg.screenshot(path=out + f"shots/{name}.png")
    pg.goto(base + "index.html", wait_until="networkidle")
    href = pg.eval_on_selector(".card.hero .headline a", "a=>a.getAttribute('href')")
    pg.goto(base + href, wait_until="networkidle"); pg.screenshot(path=out + "shots/story.png", full_page=True)
    m = b.new_page(viewport={"width": 390, "height": 844}, device_scale_factor=2, is_mobile=True)
    m.goto(base + "index.html", wait_until="networkidle"); m.screenshot(path=out + "shots/mobile.png")
    print("errors:", errs)
    b.close()
