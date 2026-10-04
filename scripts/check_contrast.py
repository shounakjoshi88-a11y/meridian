"""Check the Meridian palette against WCAG contrast ratios.

Taught concepts: Lab 1 arithmetic, Lab 2 string formatting, loops, dicts.
Run:  python scripts/check_contrast.py
"""

import colorsys


def hsl_to_rgb(h, s, l):
    """Convert HSL (h in degrees, s and l as 0-100) to 0-255 RGB."""
    r, g, b = colorsys.hls_to_rgb(h / 360.0, l / 100.0, s / 100.0)
    return (r * 255, g * 255, b * 255)


def parse(token):
    """Parse an hsl(210 24% 97%) string into an RGB tuple."""
    body = token[token.index("(") + 1:token.index(")")].strip()

    if "/" in body:
        body = body.split("/")[0].strip()

    parts = body.replace("%", "").split()
    h = float(parts[0])
    s = float(parts[1])
    l = float(parts[2])

    return hsl_to_rgb(h, s, l)


def relative_luminance(rgb):
    """WCAG relative luminance."""

    def channel(value):
        c = value / 255.0
        if c <= 0.03928:
            return c / 12.92
        return ((c + 0.055) / 1.055) ** 2.4

    r, g, b = [channel(v) for v in rgb]
    return (0.2126 * r) + (0.7152 * g) + (0.0722 * b)


def contrast_ratio(fg, bg):
    """WCAG contrast ratio between two RGB colours."""
    l1 = relative_luminance(fg)
    l2 = relative_luminance(bg)

    lighter = max(l1, l2)
    darker = min(l1, l2)

    return (lighter + 0.05) / (darker + 0.05)


LIGHT = {
    "bg": "hsl(210 24% 97%)",
    "surface": "hsl(200 30% 99.4%)",
    "surface-sunken": "hsl(210 22% 94.5%)",
    "text": "hsl(215 32% 12%)",
    "text-2": "hsl(215 16% 34%)",
    "text-muted": "hsl(215 14% 40%)",
    "accent": "hsl(174 64% 22%)",
    "accent-hover": "hsl(174 66% 18%)",
    "on-accent": "hsl(170 30% 98%)",
    "caution": "hsl(28 72% 34%)",
    "alarm": "hsl(6 68% 42%)",
    "ok": "hsl(166 50% 27%)",
    "border": "hsl(214 18% 88%)",
    "border-strong": "hsl(214 16% 54%)",
}

DARK = {
    "bg": "hsl(215 28% 8.5%)",
    "surface": "hsl(215 24% 12.5%)",
    "surface-sunken": "hsl(215 22% 10.5%)",
    "text": "hsl(210 20% 93%)",
    "text-2": "hsl(213 14% 70%)",
    "text-muted": "hsl(213 12% 57%)",
    "accent": "hsl(172 44% 52%)",
    "accent-hover": "hsl(172 48% 60%)",
    "on-accent": "hsl(200 40% 7%)",
    "caution": "hsl(36 74% 60%)",
    "alarm": "hsl(8 76% 63%)",
    "ok": "hsl(166 44% 54%)",
    "border": "hsl(214 16% 22%)",
    "border-strong": "hsl(214 12% 52%)",
}

# (foreground, background, minimum ratio, what it is used for)
BODY_MIN = 4.5
LARGE_MIN = 3.0

CHECKS = [
    ("text", "bg", BODY_MIN, "body text on canvas"),
    ("text", "surface", BODY_MIN, "body text on surface"),
    ("text", "surface-sunken", BODY_MIN, "body text on sunken"),
    ("text-2", "bg", BODY_MIN, "secondary text on canvas"),
    ("text-2", "surface", BODY_MIN, "secondary text on surface"),
    ("text-muted", "bg", BODY_MIN, "muted text on canvas"),
    ("text-muted", "surface", BODY_MIN, "muted text on surface"),
    ("text-muted", "surface-sunken", BODY_MIN, "muted text on sunken"),
    ("accent", "surface", BODY_MIN, "accent link on surface"),
    ("accent", "bg", BODY_MIN, "accent link on canvas"),
    ("on-accent", "accent", BODY_MIN, "button label on accent"),
    ("on-accent", "accent-hover", BODY_MIN, "button label hover"),
    ("caution", "bg", LARGE_MIN, "caution text, large"),
    ("caution", "surface", LARGE_MIN, "caution text on surface"),
    ("alarm", "bg", LARGE_MIN, "alarm text, large"),
    ("alarm", "surface", LARGE_MIN, "alarm text on surface"),
    ("ok", "surface", LARGE_MIN, "ok text on surface"),
    ("border-strong", "surface", LARGE_MIN, "input border, UI component"),
    ("border", "bg", 1.2, "hairline divider, decorative only"),
]


def run(name, palette):
    print("=" * 64)
    print(name)
    print("=" * 64)

    failures = []

    for fg_key, bg_key, minimum, description in CHECKS:
        fg = parse(palette[fg_key])
        bg = parse(palette[bg_key])
        ratio = contrast_ratio(fg, bg)

        ok = ratio >= minimum
        mark = "ok  " if ok else "FAIL"

        if not ok:
            failures.append((description, ratio, minimum))

        print(f"[{mark}] {ratio:5.2f}:1  (min {minimum})  {description}")

    return failures


def main():
    all_failures = run("LIGHT MODE", LIGHT)
    print()
    all_failures += run("DARK MODE", DARK)

    print()
    if all_failures:
        print(f"{len(all_failures)} contrast failures:")
        for description, ratio, minimum in all_failures:
            print(f"  {description}: {ratio:.2f} below {minimum}")
        return 1

    print("all contrast checks pass")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())