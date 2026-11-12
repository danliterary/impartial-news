"""Checks WCAG contrast of bias-bar labels and body text for every theme."""
from themes import THEMES
def lum(h):
    h = h.lstrip("#"); r, g, b = [int(h[i:i+2], 16) / 255 for i in (0, 2, 4)]
    f = lambda c: c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b)
def cr(a, b):
    la, lb = sorted([lum(a), lum(b)], reverse=True); return (la + 0.05) / (lb + 0.05)
bad = 0
for tid, *_, v in THEMES:
    rows = {"left label": cr(v["left"], v["left_ink"]), "centre label": cr(v["centre"], v["centre_ink"]), "right label": cr(v["right"], v["right_ink"]),
            "body text": cr(v["ink"], v["surface"]), "muted text": cr(v["ink3"], v["surface"]),
            "left vs right": cr(v["left"], v["right"]), "left text on surface": cr(v["left"], v["surface"]), "right text on surface": cr(v["right"], v["surface"]),
            "accent badge": cr(v["accent"], v["accent_ink"]), "accent on surface": cr(v["accent"], v["surface"])}
    need = {"left label": 4.5, "centre label": 4.5, "right label": 4.5, "body text": 7, "muted text": 4.5, "left vs right": 1.0, "left text on surface": 3, "right text on surface": 3,
            "accent badge": 4.5, "accent on surface": 4.5}
    fails = [f"{k} {x:.2f}" for k, x in rows.items() if x < need[k]]
    bad += bool(fails)
    print(f"{tid:10s} " + "  ".join(f"{k.split()[0][:5]}={x:.1f}" for k, x in rows.items()) + ("   FAIL: " + ", ".join(fails) if fails else "   ok"))
raise SystemExit(1 if bad else 0)
