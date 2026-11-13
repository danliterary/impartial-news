"""Impartial News colour themes: one source of truth for the CSS, the selector panel and the no-flash head script.
Each theme sets a full palette, including a tinted page, a coloured accent used in the header, and bias colours
(left/centre/right) tuned so the bias bar stays legible (checked by check_themes.py, WCAG contrast >= 4.5 for
segment labels). Existing theme keys are stable; saved values keep working."""

THEMES = [
 # id, name, description, group, scheme, vars
 ("paper", "Paper", "Warm off-white, the house style", "light", "light", dict(
   bg="#f6f4ef", surface="#ffffff", surface2="#f0ede6", ink="#14161b", ink2="#4a4f59", ink3="#6b707a", line="#e3dfd6",
   left="#2a62d6", centre="#cfc8ba", right="#c9333a", centre_ink="#2f2c26", left_ink="#ffffff", right_ink="#ffffff",
   accent="#14161b", accent_ink="#f6f4ef")),
 ("porcelain", "Porcelain", "Cool white and cobalt", "light", "light", dict(
   bg="#f7f9fc", surface="#ffffff", surface2="#edf1f8", ink="#0f1a2e", ink2="#43506a", ink3="#66728a", line="#dbe2ee",
   left="#1f56c8", centre="#c9d0dc", right="#c42f3c", centre_ink="#232b3a", left_ink="#ffffff", right_ink="#ffffff",
   accent="#1e4c9e", accent_ink="#ffffff")),
 ("sepia", "Sepia", "Aged paper, easy on the eyes", "light", "light", dict(
   bg="#f3ead7", surface="#fbf5e8", surface2="#ede2c9", ink="#2b2115", ink2="#584833", ink3="#76644b", line="#dfd0b1",
   left="#2753ab", centre="#cbbb98", right="#b2342b", centre_ink="#33291a", left_ink="#ffffff", right_ink="#ffffff",
   accent="#6b3f18", accent_ink="#fff6e8")),
 ("newsprint", "Newsprint", "Grey broadsheet", "light", "light", dict(
   bg="#ecebe7", surface="#f9f9f7", surface2="#e2e1dc", ink="#111111", ink2="#3b3b3b", ink3="#5f5f5f", line="#d2d1cb",
   left="#2a57b5", centre="#bdbcb5", right="#b83434", centre_ink="#1e1e1e", left_ink="#ffffff", right_ink="#ffffff",
   accent="#111111", accent_ink="#f9f9f7")),
 ("harbour", "Harbour", "Open-water blue", "colour", "light", dict(
   bg="#e7f1fb", surface="#f5f9fd", surface2="#d4e5f5", ink="#0e2138", ink2="#3a516a", ink3="#4d6480", line="#c3d6ea",
   left="#1a4fb3", centre="#b4c6da", right="#c42f3c", centre_ink="#1a2838", left_ink="#ffffff", right_ink="#ffffff",
   accent="#155a8a", accent_ink="#ffffff")),
 ("lagoon", "Lagoon", "Clear teal", "colour", "light", dict(
   bg="#e5f4f2", surface="#f4fbfa", surface2="#d0eae6", ink="#0c2c2a", ink2="#3a5856", ink3="#4d6c6a", line="#bddcd7",
   left="#1a54b8", centre="#b0cfc9", right="#c42f3c", centre_ink="#16302c", left_ink="#ffffff", right_ink="#ffffff",
   accent="#0c5f5b", accent_ink="#ffffff")),
 ("celadon", "Celadon", "Soft green-grey", "colour", "light", dict(
   bg="#ecf1ed", surface="#f9fbf9", surface2="#e0e9e3", ink="#13221c", ink2="#3d5249", ink3="#5d7067", line="#d0dcd4",
   left="#245ec2", centre="#c1cdc5", right="#c03a3d", centre_ink="#1f2e27", left_ink="#ffffff", right_ink="#ffffff",
   accent="#1f6b4a", accent_ink="#ffffff")),
 ("meadow", "Meadow", "Fresh leaf green", "colour", "light", dict(
   bg="#e8f4e6", surface="#f5fbf4", surface2="#d4ead0", ink="#142616", ink2="#3a553c", ink3="#4e6c50", line="#b9d6b6",
   left="#1a54b8", centre="#b4ceb4", right="#c42f3c", centre_ink="#1a2e1a", left_ink="#ffffff", right_ink="#ffffff",
   accent="#1d6a32", accent_ink="#ffffff")),
 ("flax", "Flax", "Pale straw", "colour", "light", dict(
   bg="#f6f3dc", surface="#fcfaf0", surface2="#ebe6c4", ink="#2a2710", ink2="#55522e", ink3="#6a663c", line="#d9d4a8",
   left="#2453ad", centre="#cfc89a", right="#b2342b", centre_ink="#2a2710", left_ink="#ffffff", right_ink="#ffffff",
   accent="#5c6b16", accent_ink="#ffffff")),
 ("harvest", "Harvest", "Ripe gold", "colour", "light", dict(
   bg="#f8efd4", surface="#fdf8e9", surface2="#f0e0b4", ink="#2c2108", ink2="#5c4a22", ink3="#726033", line="#e4d09a",
   left="#2453ad", centre="#d4c292", right="#b2342b", centre_ink="#2c2108", left_ink="#ffffff", right_ink="#ffffff",
   accent="#8a5410", accent_ink="#ffffff")),
 ("marigold", "Marigold", "Warm orange", "colour", "light", dict(
   bg="#fbecdd", surface="#fff6ec", surface2="#f5dcc0", ink="#311c0c", ink2="#5e3d28", ink3="#75553c", line="#e8c8a6",
   left="#1f53b0", centre="#e0c4a0", right="#b32e28", centre_ink="#311c0c", left_ink="#ffffff", right_ink="#ffffff",
   accent="#b04a10", accent_ink="#ffffff")),
 ("garnet", "Garnet", "Deep red", "colour", "light", dict(
   bg="#f8ecec", surface="#fdf6f6", surface2="#f0d8d8", ink="#2e1214", ink2="#5c3538", ink3="#745054", line="#e3c4c4",
   left="#1f53b0", centre="#e0c4c4", right="#a81e28", centre_ink="#2e1214", left_ink="#ffffff", right_ink="#ffffff",
   accent="#9b1c28", accent_ink="#ffffff")),
 ("blush", "Blush", "Rose pink", "colour", "light", dict(
   bg="#fbeff3", surface="#fff7f9", surface2="#f4dde5", ink="#2c121c", ink2="#5a3544", ink3="#725260", line="#e8c9d4",
   left="#1f53b0", centre="#e4c5d0", right="#b42a48", centre_ink="#2c121c", left_ink="#ffffff", right_ink="#ffffff",
   accent="#a32e5c", accent_ink="#ffffff")),
 ("lilac", "Lilac", "Pale lavender", "colour", "light", dict(
   bg="#f5f2fa", surface="#ffffff", surface2="#ece6f5", ink="#1b1530", ink2="#4a4262", ink3="#6b6385", line="#e0d9ec",
   left="#2459cc", centre="#cdc6da", right="#c4304a", centre_ink="#2a2340", left_ink="#ffffff", right_ink="#ffffff",
   accent="#5b3396", accent_ink="#ffffff")),
 ("heather", "Heather", "Moorland purple", "colour", "light", dict(
   bg="#f3eef8", surface="#faf7fd", surface2="#e5dcf2", ink="#221530", ink2="#4c3a5e", ink3="#665276", line="#d4c6e6",
   left="#2453ad", centre="#d0c2e0", right="#c4304a", centre_ink="#221530", left_ink="#ffffff", right_ink="#ffffff",
   accent="#6a2d8a", accent_ink="#ffffff")),
 ("walnut", "Walnut", "Warm brown", "colour", "light", dict(
   bg="#f3ebe1", surface="#faf5ef", surface2="#e6d6c6", ink="#2a1c12", ink2="#584634", ink3="#6e5a46", line="#d8c4b0",
   left="#1f53b0", centre="#d4c0a8", right="#b2342b", centre_ink="#2a1c12", left_ink="#ffffff", right_ink="#ffffff",
   accent="#7a4520", accent_ink="#ffffff")),
 ("ink", "Ink", "Deep charcoal, the house dark", "dark", "dark", dict(
   bg="#0d0f13", surface="#161920", surface2="#1d2129", ink="#eef0f4", ink2="#b3b8c2", ink3="#8a909b", line="#272b34",
   left="#4d8af7", centre="#8d8778", right="#f0565b", centre_ink="#0d0f13", left_ink="#08111f", right_ink="#1a0607",
   accent="#eef0f4", accent_ink="#0d0f13")),
 ("midnight", "Midnight", "Navy night", "dark", "dark", dict(
   bg="#0a1222", surface="#111b30", surface2="#18243c", ink="#e8eefb", ink2="#aab6cf", ink3="#8291ad", line="#22304a",
   left="#5b95ff", centre="#8b94a8", right="#ff6b70", centre_ink="#0a1222", left_ink="#06101f", right_ink="#1f0608",
   accent="#8bb0ff", accent_ink="#0a1222")),
 ("thicket", "Thicket", "Forest green", "dark", "dark", dict(
   bg="#0c1610", surface="#152019", surface2="#1c2a21", ink="#e8f0e9", ink2="#a8bdb0", ink3="#7e9586", line="#2a3d30",
   left="#5b95ff", centre="#8aa090", right="#ff6b70", centre_ink="#0c1610", left_ink="#06101f", right_ink="#1f0608",
   accent="#8fd49a", accent_ink="#0c1610")),
 ("damson", "Damson", "Deep purple", "dark", "dark", dict(
   bg="#140e1c", surface="#1d1628", surface2="#271f36", ink="#efe8f8", ink2="#b7a8cc", ink3="#8e819f", line="#3a3150",
   left="#6b9cff", centre="#9a8cb0", right="#ff6b70", centre_ink="#140e1c", left_ink="#06101f", right_ink="#1f0608",
   accent="#c9a0f0", accent_ink="#140e1c")),
 ("claret", "Claret", "Burgundy wine", "dark", "dark", dict(
   bg="#1a0c10", surface="#251318", surface2="#301c22", ink="#f6e8eb", ink2="#c9a8b0", ink3="#a07f88", line="#3d242b",
   left="#6b9cff", centre="#b09098", right="#ff7a80", centre_ink="#1a0c10", left_ink="#06101f", right_ink="#1f0608",
   accent="#f0a0aa", accent_ink="#1a0c10")),
 ("graphite", "Graphite", "Neutral dark grey", "dark", "dark", dict(
   bg="#18191b", surface="#212225", surface2="#2a2c30", ink="#ececec", ink2="#bbbbbf", ink3="#8f8f95", line="#34363a",
   left="#5a92f5", centre="#9a968c", right="#f06368", centre_ink="#141414", left_ink="#06101f", right_ink="#1d0607",
   accent="#ececec", accent_ink="#18191b")),
 ("black", "True Black", "OLED black", "dark", "dark", dict(
   bg="#000000", surface="#0b0b0c", surface2="#151517", ink="#f2f2f2", ink2="#b8b8b8", ink3="#8c8c8c", line="#232325",
   left="#4f8cff", centre="#8f8a80", right="#ff5a5f", centre_ink="#000000", left_ink="#000000", right_ink="#000000",
   accent="#f2f2f2", accent_ink="#000000")),
 ("hc-light", "High contrast", "Maximum legibility, light", "access", "light", dict(
   bg="#ffffff", surface="#ffffff", surface2="#ececec", ink="#000000", ink2="#111111", ink3="#2b2b2b", line="#000000",
   left="#0035a8", centre="#d6d6d6", right="#a8001a", centre_ink="#000000", left_ink="#ffffff", right_ink="#ffffff",
   accent="#000000", accent_ink="#ffffff")),
 ("hc-dark", "High contrast dark", "Maximum legibility, dark", "access", "dark", dict(
   bg="#000000", surface="#000000", surface2="#1a1a1a", ink="#ffffff", ink2="#f2f2f2", ink3="#d6d6d6", line="#ffffff",
   left="#6aa8ff", centre="#e6e6e6", right="#ff7b7b", centre_ink="#000000", left_ink="#000000", right_ink="#000000",
   accent="#ffffff", accent_ink="#000000")),
]
DEFAULT_LIGHT, DEFAULT_DARK = "paper", "ink"
GROUPS = [("light", "Light"), ("colour", "Colour"), ("dark", "Dark"), ("access", "Accessibility")]
DEFAULT_FONT, DEFAULT_SIZE = "default", "11"
SIZES = ["9", "10", "11", "12", "14", "16", "18", "20", "22", "24", "26", "28"]
SIZE_MIGRATE = {"90": "10", "100": "11", "112.5": "12", "125": "14"}
FONT_MIGRATE = {"serif": "gelasio", "sans": "inter", "system": "default"}
# id, label, group, css stack; lazy is True when the family is not already in style.css
FONT_GROUPS = [
    ("sans", "Sans serif", [
        ("mako", "Mako", "Mako, Inter, sans-serif", False),
        ("carlito", "Carlito (Calibri)", "Carlito, Calibri, sans-serif", True),
        ("arimo", "Arimo (Arial)", "Arimo, Arial, sans-serif", True),
        ("inter", "Inter", "Inter, system-ui, sans-serif", False),
        ("roboto", "Roboto", "Roboto, sans-serif", True),
        ("open-sans", "Open Sans", '"Open Sans", sans-serif', True),
        ("lato", "Lato", "Lato, sans-serif", True),
        ("source-sans-3", "Source Sans 3", '"Source Sans 3", sans-serif', True),
        ("noto-sans", "Noto Sans", '"Noto Sans", sans-serif', True),
        ("montserrat", "Montserrat", "Montserrat, sans-serif", True),
        ("atkinson", "Atkinson Hyperlegible", '"Atkinson Hyperlegible", sans-serif', True),
        ("opendyslexic", "OpenDyslexic", "OpenDyslexic, sans-serif", True),
    ]),
    ("serif", "Serif", [
        ("caladea", "Caladea (Cambria)", "Caladea, Cambria, serif", True),
        ("tinos", "Tinos (Times New Roman)", 'Tinos, "Times New Roman", serif', True),
        ("gelasio", "Gelasio (Georgia)", "Gelasio, Georgia, serif", True),
        ("newsreader", "Newsreader", "Newsreader, Georgia, serif", False),
        ("noto-serif", "Noto Serif", '"Noto Serif", serif', True),
        ("merriweather", "Merriweather", "Merriweather, serif", True),
        ("lora", "Lora", "Lora, serif", True),
        ("libre-baskerville", "Libre Baskerville", '"Libre Baskerville", serif', True),
        ("eb-garamond", "EB Garamond", '"EB Garamond", serif', True),
        ("pt-serif", "PT Serif", '"PT Serif", serif', True),
    ]),
    ("mono", "Monospace", [
        ("cousine", "Cousine (Courier New)", 'Cousine, "Courier New", monospace', True),
        ("jetbrains-mono", "JetBrains Mono", '"JetBrains Mono", ui-monospace, monospace', True),
        ("source-code-pro", "Source Code Pro", '"Source Code Pro", ui-monospace, monospace', True),
    ]),
    ("display", "Display", [
        ("playfair-display", "Playfair Display", '"Playfair Display", serif', True),
        ("oswald", "Oswald", "Oswald, sans-serif", True),
    ]),
]
FONTS = [("default", "Site default (Mako)", None, None, False)] + [
    (fid, label, gid, stack, lazy) for gid, _, items in FONT_GROUPS for fid, label, stack, lazy in items
]
LAZY_FONTS = [fid for fid, *_, lazy in FONTS if lazy]
SCHEME = {t[0]: t[4] for t in THEMES}

def css():
    out = ["/* generated from themes.py, do not edit by hand */"]
    for tid, name, _, _, scheme, v in THEMES:
        dark = scheme == "dark"
        sh = ("0 1px 2px rgba(0,0,0,.4),0 8px 28px -14px rgba(0,0,0,.7)", "0 2px 4px rgba(0,0,0,.4),0 20px 44px -16px rgba(0,0,0,.85)") if dark else \
             ("0 1px 2px rgba(20,22,27,.05),0 6px 24px -12px rgba(20,22,27,.18)", "0 2px 4px rgba(20,22,27,.06),0 18px 40px -18px rgba(20,22,27,.32)")
        if tid.startswith("hc"): sh = ("none", "0 0 0 2px var(--ink)")
        sel = f'html[data-theme="{tid}"]' + (",:root" if tid == DEFAULT_LIGHT else "")
        out.append(f'{sel}{{--bg:{v["bg"]};--surface:{v["surface"]};--surface2:{v["surface2"]};--ink:{v["ink"]};--ink2:{v["ink2"]};--ink3:{v["ink3"]};--line:{v["line"]};'
                   f'--left:{v["left"]};--centre:{v["centre"]};--right:{v["right"]};--centre-ink:{v["centre_ink"]};--left-ink:{v["left_ink"]};--right-ink:{v["right_ink"]};'
                   f'--accent:{v["accent"]};--accent-ink:{v["accent_ink"]};--shadow:{sh[0]};--shadow-h:{sh[1]};color-scheme:{scheme}}}')
    out.append('html[data-theme^="hc"] .card,html[data-theme^="hc"] .art,html[data-theme^="hc"] .filterbar,html[data-theme^="hc"] .dist,html[data-theme^="hc"] .framing{border-width:2px}')
    out.append('html[data-theme^="hc"] a:not(.see-all):not(.brand){text-decoration:underline;text-underline-offset:3px}')
    out.append('html[data-theme^="hc"] .biasbar{outline:2px solid var(--ink);outline-offset:1px}')
    for fid, label, gid, stack, lazy in FONTS:
        if fid == "default":
            continue
        out.append(f'html[data-font="{fid}"]{{--serif:{stack};--sans:{stack}}}')
        out.append(f'html[data-font="{fid}"] #ap-font,html[data-font="{fid}"] [data-font-pick="{fid}"]{{font-family:{stack}}}')
    return "\n".join(out) + "\n"

def head_script():
    """Inline, render-blocking: applies the saved theme/font/size before first paint (no flash)."""
    import json
    cfg = json.dumps({
        "s": SCHEME, "l": DEFAULT_LIGHT, "d": DEFAULT_DARK,
        "f": [fid for fid, *_ in FONTS],
        "z": SIZES, "zd": DEFAULT_SIZE, "zm": SIZE_MIGRATE, "fm": FONT_MIGRATE,
        "lazy": LAZY_FONTS,
    }, separators=(",", ":"))
    return ("<script>(function(c){var d=document.documentElement,g=function(k){try{return localStorage.getItem(k)}catch(e){return null}};"
            "var t=g('in-theme');if(t==='light')t=c.l;if(t==='dark')t=c.d;"
            "if(!t||!c.s[t]){t=(window.matchMedia&&matchMedia('(prefers-color-scheme: dark)').matches)?c.d:c.l;d.setAttribute('data-theme-auto','1')}"
            "d.setAttribute('data-theme',t);d.setAttribute('data-scheme',c.s[t]);"
            "var f=g('in-font');if(c.fm[f])f=c.fm[f];"
            "if(f&&f!=='default'&&c.f.indexOf(f)>-1){d.setAttribute('data-font',f);"
            "if(c.lazy.indexOf(f)>-1){var a=d.getAttribute('data-assets')||'assets/',l=document.createElement('link');"
            "l.rel='stylesheet';l.href=a+'fonts/'+f+'.css';l.id='in-font-'+f;(document.head||d).appendChild(l)}}"
            "var z=g('in-size');if(c.zm[z])z=c.zm[z];"
            "if(z&&z!==c.zd&&c.z.indexOf(z)>-1)d.setAttribute('data-size',z);"
            f"}})({cfg});</script>")
