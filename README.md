# Impartial News

A Ground News-style aggregator. It reads free-to-read UK and international outlets, groups articles into stories,
and shows Left, Centre and Right coverage shares, Blindspots and an automated framing check.

* `sources.json`: the outlets, their feeds, and each outlet's Media Bias/Fact Check rating with its URL (checked on 2026-11-12). It also lists the excluded paywalled outlets.
* `aggregator.py`: fetches the feeds with curl, then runs TF-IDF clustering, coverage and blindspot scoring, and the framing heuristic.
* `render.py`: renders the static site into `site/`. All paths are relative, so the site works at any sub-path (for example `/impartial-news/`).
* `refresh.sh`: rebuilds `site/` and `ferret-news-site.zip`. It is safe to run from cron because it uses a lock and swaps the build in atomically.
* `verify_feeds.sh`: checks every feed with curl and writes `feeds_verified.tsv`, which includes the publisher feeds that failed during setup.
* `screenshot.py`: Playwright screenshots of the site served at `http://localhost:8765/impartial-news/`.
* `.github/workflows/pages.yml`: an optional GitHub Actions job that rebuilds every 30 minutes and deploys the site to GitHub Pages.

Setup: `python3 -m venv .venv && .venv/bin/pip install -r requirements.txt && ./refresh.sh`
Hosting: `site/` (or the zip) is plain static HTML/CSS/JS with fonts bundled locally and no external requests.
You can upload it to GitHub Pages, Netlify (drag and drop), Cloudflare Pages or any FTP host.
`404.html` uses `<base href="/impartial-news/">` for GitHub Pages. Change it if you host the site somewhere else.
