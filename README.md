# Impartial News

A Ground News-style aggregator. It reads free-to-read UK and international outlets, groups articles into stories,
and shows Left, Centre and Right coverage shares, Blindspots and an automated framing check.

* `sources.json`: the outlets, their feeds, and each outlet's Media Bias/Fact Check rating with its URL (checked on 2026-11-12). It also lists the excluded paywalled outlets.
* `podcasts.json`: free English-language news, current-affairs and STEM podcasts, each with a public RSS feed and a Media Bias/Fact Check rating (or an explicit Unrated note when no published page was found).
* `aggregator.py`: fetches the news feeds with curl, then runs TF-IDF clustering, coverage and blindspot scoring, and the framing heuristic. It also fetches the podcast feeds and keeps recent episodes that have a public audio enclosure.
* `render.py`: renders the static site into `site/`. All paths are relative, so the site works at any sub-path (for example `/impartial-news/`).
* `refresh.sh`: rebuilds `site/` and `ferret-news-site.zip`. It is safe to run from cron because it uses a lock and swaps the build in atomically.
* `verify_feeds.sh`: checks every feed with curl and writes `feeds_verified.tsv`, which includes the publisher feeds that failed during setup.
* `verify_podcasts.sh`: checks every podcast RSS feed for recent playable audio enclosures and writes `podcasts_verified.tsv` and `failed_podcasts_setup.tsv`.
* `themes.py`: the 25 colour themes (light, a range of hues, dark and high-contrast), the self-hosted typeface list and the 9–28 pt text-size scale. It generates `assets/themes.css`, the reader-settings panel and the inline script that applies the saved theme, typeface and size before the page first draws, so there is no flash.
* `static/fonts`: self-hosted OFL typefaces (latin woff2) and their licence files. They load only when a typeface is chosen, so unused families stay off the default page. Mako is the site default for every heading and body line, and is bundled in the main stylesheet with Inter (the fallback) and Newsreader.
* `check_themes.py`: WCAG contrast check for the bias-bar labels and text in every theme.
* `theme_check.py`: Playwright test of every page in every theme (console errors, saved choice, prefers-color-scheme default, no flash). It also takes the `shots/theme-*.png` screenshots.
* `make_brand.py`: renders `favicon-32.png`, `apple-touch-icon.png` and `og.png` from `static/favicon.svg`.
* `stage_upload.py`: run by `refresh.sh`. It copies the site to `upload/impartial-news/` and writes `upload/MANIFEST.json`, which lists every file with its sha256 and what changed since the last staging.
* `logo_shots.py`: before and after screenshots of the logo.
* `screenshot.py`: Playwright screenshots of the site served at `http://localhost:8765/impartial-news/`.
* `.github/workflows/pages.yml`: an optional GitHub Actions job that rebuilds every 30 minutes and deploys the site to GitHub Pages.

Setup: `python3 -m venv .venv && .venv/bin/pip install -r requirements.txt && ./refresh.sh`
Hosting: `site/` (or the zip) is plain static HTML/CSS/JS with fonts bundled locally and no external requests.
You can upload it to GitHub Pages, Netlify (drag and drop), Cloudflare Pages or any FTP host.
`404.html` uses `<base href="/impartial-news/">` for GitHub Pages. Change it if you host the site somewhere else.
