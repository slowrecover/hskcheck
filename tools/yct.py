"""YCT (Youth Chinese Test) pages at /yct/, built from data/yct/yctN.tsv.

Each data/yct/yctN.tsv has three columns, word, pinyin and English meaning, one row per word, in
alphabetical order of pinyin. The YCT lists are cumulative: every YCT level contains all the words of
the levels below it (YCT 1: 80 words, 2: 150, 3: 300, 4: 600). Where the syllabus lists one word twice
for two uses (对 and 还 in YCT 4), the file has one row, so YCT 4 has 598 rows. The build stops if a
level is missing a word from the level below.

Outputs:
  yct/index.html                               overview of the four levels
  yct/yct-N-word-list/index.html               the full word list for level N
  yct/yct-N-character-worksheets/index.html    the worksheet maker preset to the characters new at level N

Called from tools/build.py; returns the URLs it wrote so they go into sitemap.xml.
"""
import html

YCT_URL = "/yct/"
LEVELS = (1, 2, 3, 4)
OFFICIAL = {1: 80, 2: 150, 3: 300, 4: 600}
DUPLICATES = {4: "对 and 还"}

LEDE = {
    1: "All 80 words for YCT Level 1, the first level of the Youth Chinese Test for school students, with pinyin and English. "
       "Search by character, pinyin or meaning.",
    2: "All 150 words for YCT Level 2, with pinyin and English. The list includes the 80 words of YCT 1; "
       "tick “Only new words” to see the 70 words added at this level.",
    3: "All 300 words for YCT Level 3, with pinyin and English. The list includes the 150 words of YCT 1 and 2; "
       "tick “Only new words” to see the 150 words added at this level.",
    4: "All 600 words for YCT Level 4, the highest level of the Youth Chinese Test, with pinyin and English. "
       "The list includes the 300 words of YCT 1–3; tick “Only new words” to see the 300 words added at this level.",
}

PROSE = {
    1: [
        "YCT 1 is the starting level of the Youth Chinese Test (<span class=\"zh-inline\">中小学生汉语考试</span>), "
        "the official Chinese test for primary and secondary school students whose first language is not Chinese.",
        "Its 80 words are the ones young learners meet first: numbers one to ten, family members, parts of the face, "
        "pets, simple food and drink, days and dates, and verbs such as <span class=\"zh-inline\">吃</span>, "
        "<span class=\"zh-inline\">喝</span> and <span class=\"zh-inline\">喜欢</span>.",
        "The syllabus lists <span class=\"zh-inline\">这</span>, <span class=\"zh-inline\">那</span> and "
        "<span class=\"zh-inline\">哪</span> together with their place forms <span class=\"zh-inline\">这儿</span>, "
        "<span class=\"zh-inline\">那儿</span> and <span class=\"zh-inline\">哪儿</span>, so those are part of YCT 1 too.",
    ],
    2: [
        "YCT 2 has 150 words: the 80 words of YCT 1 plus 70 new ones. The new words add school things such as "
        "<span class=\"zh-inline\">铅笔</span> and <span class=\"zh-inline\">书包</span>, colours, the weather, "
        "polite phrases such as <span class=\"zh-inline\">对不起</span> and <span class=\"zh-inline\">没关系</span>, "
        "and question words like <span class=\"zh-inline\">怎么</span> and <span class=\"zh-inline\">多少</span>.",
        "This level also brings in the first grammar words beyond the basics: <span class=\"zh-inline\">了</span>, "
        "<span class=\"zh-inline\">呢</span>, <span class=\"zh-inline\">也</span> and <span class=\"zh-inline\">比</span> for comparisons.",
    ],
    3: [
        "YCT 3 doubles the vocabulary to 300 words. Learners can now talk about their day, school and sports, "
        "health, shopping and the weather, and give simple reasons with <span class=\"zh-inline\">因为</span> and "
        "<span class=\"zh-inline\">所以</span>.",
        "New grammar words at this level include <span class=\"zh-inline\">把</span>, <span class=\"zh-inline\">过</span>, "
        "<span class=\"zh-inline\">得</span> and <span class=\"zh-inline\">吧</span>.",
    ],
    4: [
        "YCT 4 is the highest written level, with 600 words: the 300 of YCT 1–3 and 300 new ones. "
        "It covers everyday life in some depth, from travel and hobbies to feelings, school results and the news.",
        "This level adds linked patterns such as <span class=\"zh-inline\">不但……而且……</span>, "
        "<span class=\"zh-inline\">如果……那么……</span> and <span class=\"zh-inline\">一边……一边……</span>, "
        "and grammar words like <span class=\"zh-inline\">被</span>, <span class=\"zh-inline\">着</span> and "
        "<span class=\"zh-inline\">地</span>.",
        "The syllabus lists <span class=\"zh-inline\">对</span> twice (as an adjective and a preposition) and "
        "<span class=\"zh-inline\">还</span> twice (hái and huán). This page shows each once with both uses, "
        "so the table has 598 rows for the 600 syllabus entries.",
    ],
}

WS_LEDE = {
    1: "the characters in the YCT 1 words",
    2: "the characters that are new in the YCT 2 words (characters already in YCT 1 are not repeated)",
    3: "the characters that are new in the YCT 3 words (characters already in YCT 1 and 2 are not repeated)",
    4: "the characters that are new in the YCT 4 words (characters already in YCT 1–3 are not repeated)",
}


def read_level(root, n):
    path = root / "data" / "yct" / f"yct{n}.tsv"
    rows = []
    for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        parts = [p.strip() for p in line.split("\t")]
        if len(parts) != 3 or not all(parts):
            raise SystemExit(f"data/yct/yct{n}.tsv line {i}: expected word<TAB>pinyin<TAB>meaning")
        rows.append(tuple(parts))
    words = [r[0] for r in rows]
    if len(set(words)) != len(words):
        raise SystemExit(f"data/yct/yct{n}.tsv lists a word twice")
    expected = OFFICIAL[n] - (2 if n in DUPLICATES else 0)
    if len(rows) != expected:
        raise SystemExit(f"data/yct/yct{n}.tsv has {len(rows)} rows, expected {expected}")
    return rows


def hanzi(word):
    return [c for c in word if "一" <= c <= "鿿"]


def build(root, pages, nav, render, base_css, tpl, site, search_key, worksheet_page):
    levels = {n: read_level(root, n) for n in LEVELS}
    first = {}
    for n in LEVELS:
        words = {r[0] for r in levels[n]}
        if n > 1:
            missing = [w for w, _, _ in levels[n - 1] if w not in words]
            if missing:
                raise SystemExit(f"data/yct/yct{n}.tsv is missing YCT {n - 1} words: {missing}")
        for w, _, _ in levels[n]:
            first.setdefault(w, n)

    urls = []
    wl_css = base_css + (tpl / "wordlist.css").read_text(encoding="utf-8") + (tpl / "yct.css").read_text(encoding="utf-8")
    wl_body = (tpl / "yct_wordlist_body.html").read_text(encoding="utf-8")

    # Characters new at each level, in list order
    seen, level_chars = set(), {}
    for n in LEVELS:
        chars = []
        for w, _, _ in levels[n]:
            for c in hanzi(w):
                if c not in seen:
                    seen.add(c)
                    chars.append(c)
        level_chars[n] = chars

    for n in LEVELS:
        url = f"{YCT_URL}yct-{n}-word-list/"
        rows = []
        for i, (word, pinyin, meaning) in enumerate(levels[n], 1):
            key = html.escape(search_key(word, pinyin, meaning), quote=True)
            lv = first[word]
            rows.append(
                f'          <tr data-k="{key}" data-new="{1 if lv == n else 0}"><td class="n">{i}</td>'
                f'<td class="hz">{html.escape(word)}</td><td class="py">{html.escape(pinyin)}</td>'
                f'<td class="en">{html.escape(meaning)}</td><td class="lv"><span class="lv lv{lv}" title="First in YCT {lv}">{lv}</span></td></tr>'
            )
        toggle = ('<label class="new-toggle"><input type="checkbox" id="only-new"> Only words new at YCT '
                  f'{n}</label>') if n > 1 else ""
        body = (wl_body.replace("__NAV__", nav(pages, YCT_URL))
                .replace("__ROWS__", "\n".join(rows))
                .replace("__PROSE__", "\n".join(f"    <p>{p}</p>" for p in PROSE[n]))
                .replace("__LEDE__", LEDE[n])
                .replace("__NEW_TOGGLE__", toggle)
                .replace("__ROWCOUNT__", str(len(rows)))
                .replace("__COUNT__", str(OFFICIAL[n]))
                .replace("__LEVEL__", str(n)))
        out = render(
            f"YCT {n} Vocabulary List: All {OFFICIAL[n]} Words with Pinyin",
            f"The full YCT {n} vocabulary list: all {OFFICIAL[n]} words of the Youth Chinese Test Level {n} with pinyin and "
            "English meanings. Searchable, free, with printable writing sheets.",
            site + url, wl_css, body,
        )
        target = root / url.strip("/")
        target.mkdir(parents=True, exist_ok=True)
        (target / "index.html").write_text(out, encoding="utf-8")
        urls.append(url)

    # Character worksheets per level
    ws_tpl = (tpl / "worksheet_body.html").read_text(encoding="utf-8")
    ws_css = base_css + (tpl / "worksheet.css").read_text(encoding="utf-8")
    for n in LEVELS:
        url = f"{YCT_URL}yct-{n}-character-worksheets/"
        chars = level_chars[n]
        total = len(chars)
        rows = []
        for i, c in enumerate(chars, 1):
            w = next(e for e in levels[n] if c in e[0])
            rows.append(f'<tr><td class="n">{i}</td><td class="hz">{html.escape(c)}</td>'
                        f'<td class="w"><span class="zh-inline">{html.escape(w[0])}</span> {html.escape(w[1])} '
                        f'<small>{html.escape(w[2])}</small></td></tr>')
        chartable = (f'  <section class="sheet char-table no-print" aria-labelledby="chars-title">\n'
                     f'    <h2 id="chars-title">All {total} characters new at YCT {n}</h2>\n'
                     f'    <div class="table-wrap"><table><thead><tr><th scope="col">#</th><th scope="col">Character</th>'
                     f'<th scope="col">First word in the list</th></tr></thead><tbody>\n'
                     + "\n".join(rows) + "\n    </tbody></table></div>\n  </section>")
        options = [f'<option value="all">All {total} characters</option>']
        for a in range(1, total + 1, 30):
            b = min(a + 29, total)
            options.append(f'<option value="{a}-{b}">Characters {a}–{b}</option>')
        range_html = ('<div class="field"><label for="range">Characters to print</label>'
                      f'<select id="range">{"".join(options)}</select></div>')
        links = []
        for m in LEVELS:
            u = f"{YCT_URL}yct-{m}-character-worksheets/"
            cur = ' aria-current="page"' if m == n else ""
            links.append(f'<a href="{u}"{cur}>YCT {m}</a>')
        level_links = ('<nav class="level-links" aria-label="Character sets"><span>Start from:</span>' + "".join(links)
                       + '<a href="/chinese-character-worksheets/">Any characters</a></nav>')
        prose = [
            f"The YCT syllabus lists words, not single characters. This page takes every character in the YCT {n} words "
            "and lists it once, in the order it first appears in the word list.",
        ]
        if n > 1:
            prose.append("Characters already used at a lower YCT level are left out, so the four pages together cover all "
                         f"{sum(len(v) for v in level_chars.values())} characters in the YCT 1–4 words without repeats.")
        prose.append("Short daily practice works best for children: a row or two per character, then the same sheet again "
                     f'later in the week. Use the sheets alongside the <a href="{YCT_URL}yct-{n}-word-list/">YCT {n} word list</a>.')
        body = worksheet_page(
            ws_tpl, pages, YCT_URL,
            eyebrow="YCT · Youth Chinese Test", chips=[f"Level {n}", f"{total} characters"],
            h1=f"YCT {n} Character Worksheets",
            lede=f"Printable writing practice for {WS_LEDE[n]}, with stroke order, pinyin and tracing boxes. "
                 "Print the whole level, or 30 characters at a time.",
            chars="".join(chars), preset=0, range_html=range_html, sheet_title=f"YCT {n} characters",
            chartable=chartable, about_title="About these characters", prose=prose, links=level_links,
        )
        target = root / url.strip("/")
        target.mkdir(parents=True, exist_ok=True)
        (target / "index.html").write_text(render(
            f"YCT {n} Character Worksheets: Free Printable Stroke Order Sheets",
            f"Free printable Chinese writing worksheets for the {total} characters new at YCT Level {n}, with stroke order, "
            "pinyin, tracing and tian grid boxes. Made for school students and teachers.",
            site + url, ws_css, body), encoding="utf-8")
        urls.append(url)

    # Overview
    rows = []
    for n in LEVELS:
        new = OFFICIAL[n] - (OFFICIAL[n - 1] if n > 1 else 0)
        rows.append(f'<tr><th scope="row">YCT {n}</th><td>{OFFICIAL[n]} <small>({new} new)</small></td>'
                    f'<td><a href="{YCT_URL}yct-{n}-word-list/">Word list</a><br>'
                    f'<a href="{YCT_URL}yct-{n}-character-worksheets/">{len(level_chars[n])} characters to write</a></td></tr>')
    body = ((tpl / "yct_index_body.html").read_text(encoding="utf-8")
            .replace("__NAV__", nav(pages, YCT_URL)).replace("__ROWS__", "\n".join(rows)))
    target = root / YCT_URL.strip("/")
    target.mkdir(parents=True, exist_ok=True)
    (target / "index.html").write_text(render(
        "YCT Vocabulary Lists and Worksheets: Levels 1–4 (Youth Chinese Test)",
        "Free YCT 1–4 vocabulary lists with pinyin and English, and printable character writing worksheets for each level "
        "of the Youth Chinese Test.",
        site + YCT_URL, base_css + (tpl / "wordlist.css").read_text(encoding="utf-8")
        + (tpl / "yct.css").read_text(encoding="utf-8"), body), encoding="utf-8")
    return urls

