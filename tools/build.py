"""Build hskcheck.com from data/ and templates/.

Outputs (written at the repository root):
  index.html                      the level checker
  hsk-N-word-list/index.html      one page per level that has data/hskN.tsv
  sitemap.xml                     every page above

Run from anywhere:  python3 tools/build.py
"""
import datetime
import html
import json
import pathlib
import unicodedata

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
TPL = ROOT / "templates"
SITE = "https://hskcheck.com"
LEVELS = (1, 2, 3)

LEVEL_COPY = {
    1: {
        "lede": "All 300 words for HSK 1 in the HSK 3.0 (New HSK) syllabus, with pinyin and English. Search by character, pinyin or meaning.",
        "prose": [
            "HSK 1 is the first of the nine HSK 3.0 levels. Its 300 words cover numbers, family, time, food, places and the most common verbs, enough for short everyday exchanges.",
            "Every later level builds on this list: HSK 2 adds 200 words for a total of 500, and HSK 3 adds 500 more for a total of 1,000.",
            "A few entries are easy to miss because the syllabus lists words, not characters. <span class=\"zh-inline\">杯子</span> (cup) is on the list, but the measure word <span class=\"zh-inline\">杯</span> is not, so <span class=\"zh-inline\">一杯茶</span> is above HSK 1.",
        ],
    },
    2: {
        "lede": "All 200 new words for HSK 2 in the HSK 3.0 (New HSK) syllabus, with pinyin and English. Together with HSK 1, that makes 500 words. Search by character, pinyin or meaning.",
        "prose": [
            "HSK 2 adds 200 words to the 300 of HSK 1. They cover directions, transport, shopping, weather, health and simple feelings, plus the grammar words that link ideas, such as <span class=\"zh-inline\">因为</span>, <span class=\"zh-inline\">所以</span> and <span class=\"zh-inline\">虽然</span>.",
            "The syllabus lists <span class=\"zh-inline\">过</span> and <span class=\"zh-inline\">花</span> twice, once for each main use. This page shows each of them once with both meanings, so the table has 198 rows.",
            "Some HSK 1 characters return here in new words or new uses: <span class=\"zh-inline\">点</span> as in ordering food, and the particles <span class=\"zh-inline\">得</span> and <span class=\"zh-inline\">地</span>.",
        ],
    },
    3: {
        "lede": "All 500 new words for HSK 3 in the HSK 3.0 (New HSK) syllabus, with pinyin and English. Together with HSK 1 and 2, that makes 1,000 words. Search by character, pinyin or meaning.",
        "prose": [
            "HSK 3 doubles the vocabulary, adding 500 words to reach 1,000 in total. This is the level where learners start to handle everyday topics in some depth: school and work, travel, health, the weather and seasons, and their own opinions.",
            "Several familiar characters come back with a new reading or meaning. <span class=\"zh-inline\">还</span> is read huán (to give back), <span class=\"zh-inline\">长</span> is read zhǎng (to grow), and <span class=\"zh-inline\">只</span> is read zhī as a measure word for animals.",
            "The syllabus lists <span class=\"zh-inline\">得</span> twice, for dé (to get) and děi (to have to). This page shows it once with both readings, so the table has 499 rows.",
        ],
    },
}


def read_words(n):
    raw = (DATA / f"hsk{n}_words.txt").read_text(encoding="utf-8").replace("，", ",")
    return [w.strip() for w in raw.split(",") if w.strip()]


def level_table():
    """Word -> lowest level, plus 儿化 variants without the final 儿."""
    table = {}
    for n in LEVELS:
        for w in read_words(n):
            table.setdefault(w, n)
    for w, n in list(table.items()):
        if len(w) >= 3 and w.endswith("儿"):
            table.setdefault(w[:-1], n)
    return table


def read_tsv(n):
    path = DATA / f"hsk{n}.tsv"
    if not path.exists():
        return None
    entries = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        word, pinyin, meaning = line.split("\t")
        entries.append((word.strip(), pinyin.strip(), meaning.strip()))
    expected = list(dict.fromkeys(read_words(n)))
    got = [e[0] for e in entries]
    if got != expected:
        missing = [w for w in expected if w not in got]
        extra = [w for w in got if w not in expected]
        raise SystemExit(f"hsk{n}.tsv does not match hsk{n}_words.txt; missing={missing} extra={extra}")
    return entries


def _squash(s):
    """Lowercase, drop tone marks, spaces and apostrophes (mirrors the page's search normaliser)."""
    s = "".join(c for c in unicodedata.normalize("NFD", s.lower()) if not unicodedata.combining(c))
    for ch in " '’-":
        s = s.replace(ch, "")
    return s


def search_key(word, pinyin, meaning):
    decomposed = unicodedata.normalize("NFD", pinyin.lower())
    v_form = _squash(decomposed.replace("ü", "v"))  # lets "nv" find nǚ
    return "|".join([word, _squash(pinyin), v_form, _squash(meaning)])


def nav(pages, current):
    links = []
    for url, label in pages:
        cur = ' aria-current="page"' if url == current else ""
        links.append(f'<a href="{url}"{cur}>{label}</a>')
    return '<nav class="site-nav" aria-label="Site">' + "".join(links) + "</nav>"


def render(title, description, url, css, body, head_extra=""):
    page = (TPL / "layout.html").read_text(encoding="utf-8")
    for key, value in (
        ("__TITLE__", html.escape(title)),
        ("__DESCRIPTION__", html.escape(description)),
        ("__URL__", url),
        ("__HEAD_EXTRA__", head_extra),
        ("__CSS__", css),
        ("__BODY__", body),
    ):
        page = page.replace(key, value)
    return page


def main():
    base_css = (TPL / "base.css").read_text(encoding="utf-8")
    pages = [("/", "Level Checker")]
    word_lists = {}
    for n in LEVELS:
        entries = read_tsv(n)
        if entries:
            word_lists[n] = entries
            pages.append((f"/hsk-{n}-word-list/", f"HSK {n} Words"))

    # Level checker
    ld = json.dumps({
        "@context": "https://schema.org", "@type": "WebApplication", "name": "HSK 3.0 Level Checker",
        "url": SITE + "/", "applicationCategory": "EducationalApplication", "operatingSystem": "Any",
        "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"},
        "description": "Paste Chinese text and see which words are above your HSK 3.0 level.",
    }, ensure_ascii=False)
    body = (TPL / "checker_body.html").read_text(encoding="utf-8")
    body = body.replace("__NAV__", nav(pages, "/"))
    body = body.replace("__LEVELS_JSON__", json.dumps(level_table(), ensure_ascii=False, separators=(",", ":")))
    out = render(
        "HSK 3.0 Level Checker",
        "Paste Chinese text and see which words are above your HSK 3.0 level. Free, instant, works in your browser.",
        SITE + "/",
        base_css + (TPL / "checker.css").read_text(encoding="utf-8"),
        body,
        f'<script type="application/ld+json">{ld}</script>',
    )
    (ROOT / "index.html").write_text(out, encoding="utf-8")

    # Word list pages
    wl_body = (TPL / "wordlist_body.html").read_text(encoding="utf-8")
    wl_css = base_css + (TPL / "wordlist.css").read_text(encoding="utf-8")
    for n, entries in word_lists.items():
        rows = []
        for i, (word, pinyin, meaning) in enumerate(entries, 1):
            key = html.escape(search_key(word, pinyin, meaning), quote=True)
            rows.append(
                f'          <tr data-k="{key}"><td class="n">{i}</td><td class="hz">{html.escape(word)}</td>'
                f'<td class="py">{html.escape(pinyin)}</td><td class="en">{html.escape(meaning)}</td></tr>'
            )
        copy = LEVEL_COPY.get(n, {})
        prose = "\n".join(f"    <p>{p}</p>" for p in copy.get("prose", []))
        official = len(read_words(n))  # syllabus entries, counting repeated words once per use
        body = (wl_body.replace("__NAV__", nav(pages, f"/hsk-{n}-word-list/"))
                .replace("__ROWS__", "\n".join(rows))
                .replace("__PROSE__", prose)
                .replace("__LEDE__", copy.get("lede", ""))
                .replace("__ROWCOUNT__", str(len(entries)))
                .replace("__COUNT__", str(official))
                .replace("__LEVEL__", str(n)))
        url = f"{SITE}/hsk-{n}-word-list/"
        out = render(
            f"HSK {n} Word List (HSK 3.0, {official} words)",
            f"All {official} HSK {n} words in the HSK 3.0 (New HSK) syllabus with pinyin and English meanings. Searchable and free.",
            url, wl_css, body,
        )
        target = ROOT / f"hsk-{n}-word-list"
        target.mkdir(exist_ok=True)
        (target / "index.html").write_text(out, encoding="utf-8")

    # Sitemap
    today = datetime.date.today().isoformat()
    urls = "\n".join(
        f"  <url>\n    <loc>{SITE}{u}</loc>\n    <lastmod>{today}</lastmod>\n  </url>" for u, _ in pages
    )
    (ROOT / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + urls + "\n</urlset>\n",
        encoding="utf-8",
    )
    print("built:", ", ".join(u for u, _ in pages))


if __name__ == "__main__":
    main()
