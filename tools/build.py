"""Build hskcheck.com from data/ and templates/.

Outputs (written at the repository root):
  index.html                      the level checker
  hsk-N-word-list/index.html      one page per level that has data/hskN.tsv (HSK 4: see tools/hsk4.py)
  chinese-character-worksheets/   the writing worksheet maker
  hsk-N-character-worksheets/     the maker preset to the characters of one level (needs strokes/hskN.json)
  old-hsk-to-new-hsk/index.html   old HSK -> new HSK word gap (needs old-hsk-to-new-hsk/words.json)
  yct/...                         YCT word lists and worksheets (see tools/yct.py)
  hsk-handwriting-characters/     which characters must be written by hand (see tools/handwriting.py)
  mandarin-tone-changes/          written vs spoken tones (see tools/tones.py; data in tones/words.json)
  sitemap.xml                     every page above

Run from anywhere:  python3 tools/build.py
"""
import datetime
import html
import json
import pathlib
import re
import unicodedata

import build_th
import handwriting
import learn
import tones
import hsk4
import yct

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


WS_COPY = {
    1: "the 248 characters used in the HSK 1 words",
    2: "the 123 new characters used in the HSK 2 words (characters already used in HSK 1 are not repeated)",
    3: "the 284 new characters used in the HSK 3 words (characters already used in HSK 1 and 2 are not repeated)",
}


def level_chars(n):
    path = ROOT / "strokes" / f"hsk{n}.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def level_links(current):
    links = []
    for n in LEVELS:
        url = f"/hsk-{n}-character-worksheets/"
        cur = ' aria-current="page"' if url == current else ""
        links.append(f'<a href="{url}"{cur}>HSK {n}</a>')
    cur = ' aria-current="page"' if current == "/chinese-character-worksheets/" else ""
    if (DATA / "hsk4.tsv").exists():
        cur4 = ' aria-current="page"' if current == hsk4.WS_URL else ""
        links.append(f'<a href="{hsk4.WS_URL}"{cur4}>HSK 4</a>')
    links.append(f'<a href="/chinese-character-worksheets/"{cur}>Any characters</a>')
    return '<nav class="level-links" aria-label="Character sets"><span>Start from:</span>' + "".join(links) + "</nav>"


def worksheet_page(tpl, pages, current, *, eyebrow, chips, h1, lede, chars, preset, range_html,
                   sheet_title, chartable, about_title, prose, links=None):
    body = tpl
    for key, value in (
        ("__NAV__", nav(pages, "/chinese-character-worksheets/")),
        ("__EYEBROW__", eyebrow),
        ("__CHIPS__", "".join(f'<span class="chip">{c}</span>' for c in chips)),
        ("__H1__", h1),
        ("__LEDE__", lede),
        ("__LEVEL_LINKS__", level_links(current) if links is None else links),
        ("__CHARS__", html.escape(chars)),
        ("__RANGE__", range_html),
        ("__SHEET_TITLE__", html.escape(sheet_title)),
        ("__CHARTABLE__", chartable),
        ("__ABOUT_TITLE__", about_title),
        ("__PROSE__", "\n".join(f"    <p>{p}</p>" for p in prose)),
        ("__PRESET__", str(preset)),
    ):
        body = body.replace(key, value)
    return body


def nav(pages, current):
    links = []
    for url, label in pages:
        cur = ' aria-current="page"' if url == current else ""
        links.append(f'<a href="{url}"{cur}>{label}</a>')
    return '<nav class="site-nav" aria-label="Site">' + "".join(links) + "</nav>"


PRIVACY_URL = "/privacy/"
ABOUT_URL = "/about/"
SITE_FOOT = (f'\n<footer class="site-foot">hskcheck.com · <a href="{ABOUT_URL}">About</a> · '
             f'<a href="{PRIVACY_URL}">Privacy Policy</a></footer>')


ALTERNATES = build_th.alternates(ROOT, LEVELS)  # English path -> Thai path


def hreflang_links(url):
    path = url[len(SITE):] if url.startswith(SITE) else url
    en = path if path in ALTERNATES else next((e for e, t in ALTERNATES.items() if t == path), None)
    if not en:
        return ""
    return "\n".join([
        f'<link rel="alternate" hreflang="en" href="{SITE}{en}">',
        f'<link rel="alternate" hreflang="th" href="{SITE}{ALTERNATES[en]}">',
        f'<link rel="alternate" hreflang="x-default" href="{SITE}{en}">',
    ])


def render(title, description, url, css, body, head_extra="", lang="en", foot=None):
    page = (TPL / "layout.html").read_text(encoding="utf-8")
    head_extra = "\n".join(x for x in (hreflang_links(url), head_extra) if x)
    for key, value in (
        ("__LANG__", lang),
        ("__TITLE__", html.escape(title)),
        ("__DESCRIPTION__", html.escape(description)),
        ("__URL__", url),
        ("__HEAD_EXTRA__", head_extra),
        ("__CSS__", css),
        ("__BODY__", body + (SITE_FOOT if foot is None else foot)),
    ):
        page = page.replace(key, value)
    return page


MW_URL = "/chinese-measure-words/"
HAN_RUN = re.compile(r"[㐀-鿿，。：！？]+")
FOURTH_TONE = set("àèìòùǜ")


def read_classifiers():
    table = {}
    for line in (DATA / "classifiers.tsv").read_text(encoding="utf-8").splitlines():
        if line.strip():
            mw, pinyin, use = line.split("\t")
            table[mw] = (pinyin, use)
    return table


def read_measure_words(classifiers):
    entries = []
    seen = set()
    for i, line in enumerate((DATA / "measure_words.tsv").read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        parts = line.split("\t")
        if len(parts) == 4:
            parts.append("")  # note column is optional
        if len(parts) != 5:
            raise SystemExit(f"measure_words.tsv line {i}: expected 5 columns, got {len(parts)}")
        word, pinyin, meaning, mws, note = (p.strip() for p in parts)
        if word in seen:
            raise SystemExit(f"measure_words.tsv line {i}: {word} listed twice")
        seen.add(word)
        mws = [m for m in mws.split(",") if m]
        unknown = [m for m in mws if m not in classifiers]
        if unknown:
            raise SystemExit(f"measure_words.tsv line {i}: {word} uses {unknown}, not in classifiers.tsv")
        if not mws and not note:
            raise SystemExit(f"measure_words.tsv line {i}: {word} has no measure word, so it needs a note")
        entries.append((word, pinyin, meaning, mws, note))
    return entries


def yi_before(pinyin):
    """一 is read yí before a fourth tone, yì before the other tones."""
    return "yí" if any(c in FOURTH_TONE for c in pinyin.split()[0]) else "yì"


def zh_spans(text):
    """Escape a note and wrap its Chinese in zh-inline spans."""
    return HAN_RUN.sub(lambda m: f'<span class="zh-inline">{m.group(0)}</span>', html.escape(text))


def build_measure_words(pages, base_css):
    classifiers = read_classifiers()
    entries = read_measure_words(classifiers)
    levels = level_table()
    used = {m for e in entries for m in e[3]}
    unused = [m for m in classifiers if m not in used]
    if unused:
        raise SystemExit(f"classifiers.tsv lists measure words no noun uses: {unused}")

    data, rows, by_mw = [], [], {m: [] for m in classifiers}
    for word, pinyin, meaning, mws, note in entries:
        items = []
        for m in mws:
            mpy = classifiers[m][0]
            items.append({"c": m, "ex": f"一{m}{word}", "expy": f"{yi_before(mpy)} {mpy} {pinyin}"})
            by_mw[m].append(word)
        keys = [_squash(pinyin), _squash(unicodedata.normalize("NFD", pinyin.lower()).replace("ü", "v"))]
        data.append({"w": word, "p": pinyin, "en": meaning, "lv": levels.get(word), "m": items,
                     "note": zh_spans(note) if note else "", "keys": keys})
        if mws:
            first = classifiers[mws[0]][0]
            others = "、".join(mws[1:])
            mw_cell = f"{mws[0]} <small>{html.escape(first)}</small>" + (f" <small>also {others}</small>" if others else "")
        else:
            mw_cell = "<small>none needed</small>"
        key = html.escape(search_key(word, pinyin, meaning) + "|" + "".join(mws), quote=True)
        rows.append(
            f'          <tr data-w="{html.escape(word)}" data-k="{key}"><td class="hz"><b>{html.escape(word)}</b>'
            f'<span>{html.escape(pinyin)}</span></td><td class="en">{html.escape(meaning)}</td><td class="mw">{mw_cell}</td></tr>'
        )

    mw_json = {m: {"p": p, "e": use} for m, (p, use) in classifiers.items()}
    index = []
    for m, (p, use) in classifiers.items():
        nouns = "、".join(f'<a href="#{html.escape(w)}">{html.escape(w)}</a>' for w in by_mw[m])
        index.append(
            f'      <div><dt>{m}<span>{html.escape(p)}</span></dt><dd><span class="use">{html.escape(use)}</span>'
            f'<span class="nouns">{nouns}</span></dd></div>'
        )

    body = (TPL / "measure_body.html").read_text(encoding="utf-8")
    body = (body.replace("__NAV__", nav(pages, MW_URL))
            .replace("__ROWS__", "\n".join(rows))
            .replace("__INDEX__", "\n".join(index))
            .replace("__NOUNCOUNT__", str(len(entries)))
            .replace("__MWCOUNT__", str(len(classifiers)))
            .replace("__DATA_JSON__", json.dumps(data, ensure_ascii=False, separators=(",", ":")))
            .replace("__MW_JSON__", json.dumps(mw_json, ensure_ascii=False, separators=(",", ":"))))
    ld = json.dumps({
        "@context": "https://schema.org", "@type": "WebApplication", "name": "Chinese Measure Word Finder",
        "url": SITE + MW_URL, "applicationCategory": "EducationalApplication", "operatingSystem": "Any",
        "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"},
        "description": "Find the right Chinese measure word for a noun, with pinyin, examples and HSK levels.",
    }, ensure_ascii=False)
    out = render(
        "Chinese Measure Word Finder: Which Measure Word for a Noun?",
        f"Find the right Chinese measure word (量词) for {len(entries)} common nouns. Search in Chinese, pinyin or English, "
        "with examples and HSK 3.0 levels. Free.",
        SITE + MW_URL,
        base_css + (TPL / "measure.css").read_text(encoding="utf-8"),
        body,
        f'<script type="application/ld+json">{ld}</script>',
    )
    target = ROOT / MW_URL.strip("/")
    target.mkdir(exist_ok=True)
    (target / "index.html").write_text(out, encoding="utf-8")


def main():
    base_css = (TPL / "base.css").read_text(encoding="utf-8")
    pages = [("/", "Level Checker")]
    word_lists = {}
    for n in LEVELS:
        entries = read_tsv(n)
        if entries:
            word_lists[n] = entries
            pages.append((f"/hsk-{n}-word-list/", f"HSK {n} Words"))
    if (DATA / "hsk4.tsv").exists():
        pages.append((hsk4.URL, "HSK 4 Words"))
    pages.append(("/chinese-character-worksheets/", "Writing Sheets"))
    pages.append((handwriting.URL, "Handwriting"))
    pages.append((tones.URL, "Tone Changes"))
    pages.append((MW_URL, "Measure Words"))
    upgrade_data = ROOT / "old-hsk-to-new-hsk" / "words.json"
    if upgrade_data.exists():
        pages.append(("/old-hsk-to-new-hsk/", "Old → New HSK"))
    if any((DATA / "learn").glob("*.json")):
        pages.append((learn.LEARN_URL, "Grammar"))
    pages.append((yct.YCT_URL, "YCT"))
    if ALTERNATES:
        pages.append((build_th.TH_URL, "ภาษาไทย"))
    extra_urls = []

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

    # Worksheet maker and one preset page per level
    ws_tpl = (TPL / "worksheet_body.html").read_text(encoding="utf-8")
    ws_css = base_css + (TPL / "worksheet.css").read_text(encoding="utf-8")
    url = "/chinese-character-worksheets/"
    ld = json.dumps({
        "@context": "https://schema.org", "@type": "WebApplication", "name": "Chinese Character Worksheet Maker",
        "url": SITE + url, "applicationCategory": "EducationalApplication", "operatingSystem": "Any",
        "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"},
        "description": "Make printable Chinese handwriting worksheets with stroke order, tracing and tian or mi grids.",
    }, ensure_ascii=False)
    body = worksheet_page(
        ws_tpl, pages, url,
        eyebrow="Free · printable", chips=[],
        h1='<span class="zh">字帖</span>Chinese Character Worksheet Maker',
        lede="Make a printable handwriting sheet for any Chinese characters: stroke order, a model character, "
             "tracing and empty practice boxes on a tian or mi grid. Or start from the characters of an HSK 3.0 level.",
        chars="你好我爱学中文", preset=0, range_html="", sheet_title="Chinese writing practice", chartable="",
        about_title="How to use the worksheets",
        prose=[
            "Start each character with the stroke order strip: the newest stroke is shown in black and earlier strokes in grey. "
            "Then write over the grey tracing characters, and fill the empty boxes from memory.",
            "A tian (<span class=\"zh-inline\">田</span>) grid splits each box into four, and a mi (<span class=\"zh-inline\">米</span>) grid adds the diagonals. "
            "Both help you place each part of a character, which matters more than speed when you are starting out.",
            "Writing a character a few times on several days works better than filling a whole page in one sitting. "
            "Print one or two rows per character, and come back to the same sheet later in the week.",
        ],
    )
    (ROOT / "chinese-character-worksheets").mkdir(exist_ok=True)
    (ROOT / "chinese-character-worksheets" / "index.html").write_text(render(
        "Chinese Character Worksheet Maker: Free Printable Tian Zi Ge Sheets",
        "Make free printable Chinese character worksheets with stroke order, pinyin, tracing and tian or mi grid boxes. "
        "Type any characters or start from an HSK 3.0 level.",
        SITE + url, ws_css, body, f'<script type="application/ld+json">{ld}</script>'), encoding="utf-8")

    for n in LEVELS:
        chars = level_chars(n)
        if not chars or n not in word_lists:
            continue
        url = f"/hsk-{n}-character-worksheets/"
        total = len(chars)
        order = list(chars)
        rows = []
        for i, c in enumerate(order, 1):
            first = next((e for e in word_lists[n] if c in e[0]), None)
            word = (f'<span class="zh-inline">{html.escape(first[0])}</span> {html.escape(first[1])} '
                    f'<small>{html.escape(first[2])}</small>') if first else ""
            rows.append(f'<tr><td class="n">{i}</td><td class="hz">{html.escape(c)}</td>'
                        f'<td class="py">{html.escape(" / ".join(chars[c]["p"]))}</td><td class="w">{word}</td></tr>')
        chartable = (f'  <section class="sheet char-table no-print" aria-labelledby="chars-title">\n'
                     f'    <h2 id="chars-title">All {total} characters in the HSK {n} words</h2>\n'
                     f'    <div class="table-wrap"><table><thead><tr><th scope="col">#</th><th scope="col">Character</th>'
                     f'<th scope="col">Pinyin</th><th scope="col">First word in the list</th></tr></thead><tbody>\n'
                     + "\n".join(rows) + "\n    </tbody></table></div>\n  </section>")
        options = ['<option value="all">All ' + str(total) + " characters</option>"]
        for a in range(1, total + 1, 30):
            b = min(a + 29, total)
            options.append(f'<option value="{a}-{b}">Characters {a}–{b}</option>')
        range_html = ('<div class="field"><label for="range">Characters to print</label>'
                      f'<select id="range">{"".join(options)}</select></div>')
        prose = [
            f"The HSK 3.0 syllabus lists words, not single characters. This page takes every character that appears in the HSK {n} words "
            "and lists it once, in the order it first appears in the word list.",
        ]
        if n > 1:
            prose.append("Characters already used at a lower level are left out, so the three levels together cover all 655 characters "
                         "in the HSK 1–3 words without repeats.")
        prose.append("The HSK 3.0 standard also includes its own character list, which may differ slightly from this set. "
                     f'Use these sheets to practise writing the words you are learning, alongside the <a href="/hsk-{n}-word-list/">HSK {n} word list</a>.')
        body = worksheet_page(
            ws_tpl, pages, url,
            eyebrow="New HSK · 2025 syllabus", chips=[f"Level {n}", f"{total} characters"],
            h1=f"HSK {n} Character Worksheets",
            lede=f"Printable writing practice for {WS_COPY[n]} of the HSK 3.0 syllabus, with stroke order, pinyin and tracing boxes. "
                 "Print the whole level, or 30 characters at a time.",
            chars="".join(order), preset=n, range_html=range_html, sheet_title=f"HSK {n} characters",
            chartable=chartable, about_title="About these characters", prose=prose,
        )
        (ROOT / url.strip("/")).mkdir(exist_ok=True)
        (ROOT / url.strip("/") / "index.html").write_text(render(
            f"HSK {n} Character Worksheets: Printable Stroke Order Practice (HSK 3.0)",
            f"Free printable writing worksheets for {WS_COPY[n].split(' (')[0]} of the HSK 3.0 syllabus, "
            "with stroke order, pinyin, tracing and tian grid boxes.",
            SITE + url, ws_css, body), encoding="utf-8")
        extra_urls.append(url)

    build_measure_words(pages, base_css)
    # Old HSK -> new HSK
    if upgrade_data.exists():
        url = "/old-hsk-to-new-hsk/"
        words = json.loads(upgrade_data.read_text(encoding="utf-8"))
        oc = words["oc"]
        old4 = set("".join(oc[1:5]))
        gap = [x for x in words["w"] if x[3] <= 4 and not (x[4] and x[4] <= 4)]
        hard = sum(1 for x in gap if any(c not in old4 for c in x[0] if "\u4e00" <= c <= "\u9fff"))
        total4 = sum(1 for x in words["w"] if x[3] <= 4)
        example = (f"New HSK 1–4 has {total4:,} words. Someone who studied all of old HSK 1–4 has met "
                   f"{total4 - len(gap):,} of them, so {len(gap):,} are still to learn. {hard:,} of those use at least one character "
                   "that never appeared in the old HSK 1–4 words.")
        ld = json.dumps({
            "@context": "https://schema.org", "@type": "WebApplication", "name": "Old HSK to New HSK Word Gap",
            "url": SITE + url, "applicationCategory": "EducationalApplication", "operatingSystem": "Any",
            "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"},
            "description": "See which HSK 3.0 words and characters you still need after studying the old HSK 2.0.",
        }, ensure_ascii=False)
        body = (TPL / "upgrade_body.html").read_text(encoding="utf-8")
        body = body.replace("__NAV__", nav(pages, url)).replace("__EXAMPLE__", example)
        (ROOT / "old-hsk-to-new-hsk" / "index.html").write_text(render(
            "Old HSK to New HSK: Which HSK 3.0 Words You Still Need",
            "Studied the old HSK 2.0? Pick your old level and your new HSK 3.0 target to see only the words and characters "
            "you have not learned yet. Free, with Anki and Pleco export.",
            SITE + url, base_css + (TPL / "upgrade.css").read_text(encoding="utf-8"), body,
            f'<script type="application/ld+json">{ld}</script>'), encoding="utf-8")

    # Handwriting characters
    extra_urls += handwriting.build(ROOT, pages, nav, render, base_css, TPL, SITE)

    # Tone changes
    extra_urls += tones.build(ROOT, pages, nav, render, base_css, TPL, SITE)


    # HSK 4 word list and worksheets
    extra_urls += hsk4.build(ROOT, pages, nav, render, base_css, TPL, SITE, search_key, worksheet_page,
                             [w for n in LEVELS for w in read_words(n)])

    # YCT word lists and worksheets
    extra_urls += yct.build(ROOT, pages, nav, render, base_css, TPL, SITE, search_key, worksheet_page)

    # Grammar explainers
    extra_urls += learn.build(pages, nav, render, base_css, TPL, SITE)

    # Privacy policy
    today = datetime.date.today().isoformat()
    body = (TPL / "privacy_body.html").read_text(encoding="utf-8")
    body = body.replace("__NAV__", nav(pages, PRIVACY_URL)).replace("__UPDATED__", today)
    target = ROOT / PRIVACY_URL.strip("/")
    target.mkdir(exist_ok=True)
    (target / "index.html").write_text(render(
        "Privacy Policy | hskcheck.com",
        "How hskcheck.com handles your data: the tools run in your browser, and the site may show Google ads that use cookies.",
        SITE + PRIVACY_URL, base_css, body), encoding="utf-8")
    extra_urls.append(PRIVACY_URL)

    # About
    body = (TPL / "about_body.html").read_text(encoding="utf-8").replace("__NAV__", nav(pages, ABOUT_URL))
    target = ROOT / ABOUT_URL.strip("/")
    target.mkdir(exist_ok=True)
    (target / "index.html").write_text(render(
        "About hskcheck.com: Free HSK 3.0 and YCT Tools",
        "About hskcheck.com: free word lists, grammar explanations, worksheets and tools for HSK 3.0 and YCT learners "
        "and teachers, in English and Thai. How the content is made and where the data comes from.",
        SITE + ABOUT_URL, base_css, body), encoding="utf-8")
    extra_urls.append(ABOUT_URL)

    # Thai pages
    extra_urls += build_th.build(root=ROOT, tpl=TPL, site=SITE, base_css=base_css, render=render,
                                 word_lists=word_lists, level_table=level_table, search_key=search_key,
                                 read_words=read_words,
                                 measure=dict(read_classifiers=read_classifiers, read_measure_words=read_measure_words,
                                              yi_before=yi_before, zh_spans=zh_spans, squash=_squash))

    # Sitemap
    urls = "\n".join(
        f"  <url>\n    <loc>{SITE}{u}</loc>\n    <lastmod>{today}</lastmod>\n  </url>"
        for u in dict.fromkeys([u for u, _ in pages] + extra_urls)
    )
    (ROOT / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + urls + "\n</urlset>\n",
        encoding="utf-8",
    )
    print("built:", ", ".join(dict.fromkeys([u for u, _ in pages] + extra_urls)))


if __name__ == "__main__":
    main()
