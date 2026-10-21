"""Mandarin tone change checker, built to /mandarin-tone-changes/.

The page loads tones/words.json (made by tools/make_tone_data.py) and works out the spoken
tones in the browser: third tone before third tone, 一 and 不.
"""
import json

URL = "/mandarin-tone-changes/"


def build(root, pages, nav, render, base_css, tpl, site):
    if not (root / "tones" / "words.json").exists():
        raise SystemExit("tones/words.json is missing: run tools/make_tone_data.py first")
    body = (tpl / "tones_body.html").read_text(encoding="utf-8").replace("__NAV__", nav(pages, URL))
    description = "See how Mandarin tones change in speech: third tone sandhi, 一 and 不, for any Chinese text."
    ld = json.dumps({
        "@context": "https://schema.org", "@type": "WebApplication", "name": "Mandarin Tone Change Checker",
        "url": site + URL, "applicationCategory": "EducationalApplication", "operatingSystem": "Any",
        "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"},
        "description": description,
    }, ensure_ascii=False)
    out = render(
        "Mandarin Tone Change Checker: Third Tone Sandhi, 一 and 不 (变调)",
        "Paste Chinese text to see pinyin as written and as actually spoken. Shows third tone sandhi and the "
        "tone changes of 一 (yī) and 不 (bù), with each change explained. Free.",
        site + URL,
        base_css + (tpl / "checker.css").read_text(encoding="utf-8") + (tpl / "tones.css").read_text(encoding="utf-8"),
        body,
        f'<script type="application/ld+json">{ld}</script>',
    )
    target = root / URL.strip("/")
    target.mkdir(exist_ok=True)
    (target / "index.html").write_text(out, encoding="utf-8")
    return [URL]
