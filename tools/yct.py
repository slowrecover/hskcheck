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
  yct/yct-N-vocabulary-worksheets/index.html   printable vocabulary sheets with answer keys (see tools/yct_ws.py)
  yct/yct-vs-hsk/index.html                    YCT vs HSK word list comparison

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
       "The list includes the 300 words of YCT 1–3; tick “Only new words” to see the words added at this level.",
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
                    f'<a href="{YCT_URL}yct-{n}-vocabulary-worksheets/">Vocabulary worksheets</a><br>'
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
    urls += build_compare(root, lang="en", site=site, render=render, nav_html=nav(pages, YCT_URL),
                          css=base_css + (tpl / "wordlist.css").read_text(encoding="utf-8") + (tpl / "yct.css").read_text(encoding="utf-8"))
    urls += build_vocab_sheets(root, lang="en", site=site, render=render, nav_html=nav(pages, YCT_URL),
                               css=base_css + (tpl / "learn_worksheet.css").read_text(encoding="utf-8"))
    return urls



TH_YCT_URL = "/th/yct/"

TH_LEDE = {
    1: "คำศัพท์ YCT ระดับ 1 ทั้ง 80 คำ ระดับแรกของการสอบภาษาจีนสำหรับนักเรียน พร้อมพินอินและความหมายภาษาไทย "
       "ค้นหาได้ด้วยตัวอักษรจีน พินอิน หรือภาษาไทย",
    2: "คำศัพท์ YCT ระดับ 2 ทั้ง 150 คำ พร้อมพินอินและความหมายภาษาไทย รายการนี้รวมคำศัพท์ 80 คำของ YCT 1 ไว้ด้วย "
       "ติ๊ก “เฉพาะคำใหม่” เพื่อดู 70 คำที่เพิ่มในระดับนี้",
    3: "คำศัพท์ YCT ระดับ 3 ทั้ง 300 คำ พร้อมพินอินและความหมายภาษาไทย รายการนี้รวมคำศัพท์ 150 คำของ YCT 1 และ 2 ไว้ด้วย "
       "ติ๊ก “เฉพาะคำใหม่” เพื่อดู 150 คำที่เพิ่มในระดับนี้",
    4: "คำศัพท์ YCT ระดับ 4 ทั้ง 600 คำ ระดับสูงสุดของการสอบภาษาจีนสำหรับนักเรียน พร้อมพินอินและความหมายภาษาไทย "
       "รายการนี้รวมคำศัพท์ 300 คำของ YCT 1–3 ไว้ด้วย ติ๊ก “เฉพาะคำใหม่” เพื่อดูคำที่เพิ่มในระดับนี้",
}

TH_PROSE = {
    1: [
        "YCT 1 เป็นระดับเริ่มต้นของ YCT (<span class=\"zh-inline\">中小学生汉语考试</span>) การสอบวัดระดับภาษาจีนอย่างเป็นทางการ "
        "สำหรับนักเรียนประถมและมัธยมที่ไม่ได้ใช้ภาษาจีนเป็นภาษาแม่",
        "คำศัพท์ 80 คำเป็นคำที่เด็ก ๆ เจอเป็นอันดับแรก ได้แก่ ตัวเลขหนึ่งถึงสิบ สมาชิกในครอบครัว อวัยวะบนใบหน้า สัตว์เลี้ยง "
        "อาหารและเครื่องดื่มง่าย ๆ วันและวันที่ และคำกริยาอย่าง <span class=\"zh-inline\">吃</span> "
        "<span class=\"zh-inline\">喝</span> และ <span class=\"zh-inline\">喜欢</span>",
        "หลักสูตรระบุ <span class=\"zh-inline\">这</span> <span class=\"zh-inline\">那</span> และ "
        "<span class=\"zh-inline\">哪</span> พร้อมรูปที่หมายถึงสถานที่ คือ <span class=\"zh-inline\">这儿</span> "
        "<span class=\"zh-inline\">那儿</span> และ <span class=\"zh-inline\">哪儿</span> คำเหล่านี้จึงอยู่ใน YCT 1 ด้วย",
    ],
    2: [
        "YCT 2 มีคำศัพท์ 150 คำ คือ 80 คำของ YCT 1 บวกคำใหม่อีก 70 คำ คำใหม่ได้แก่ ของใช้ในโรงเรียนอย่าง "
        "<span class=\"zh-inline\">铅笔</span> และ <span class=\"zh-inline\">书包</span> สี สภาพอากาศ "
        "คำสุภาพอย่าง <span class=\"zh-inline\">对不起</span> และ <span class=\"zh-inline\">没关系</span> "
        "และคำถามอย่าง <span class=\"zh-inline\">怎么</span> และ <span class=\"zh-inline\">多少</span>",
        "ระดับนี้ยังเริ่มมีคำไวยากรณ์ที่มากกว่าพื้นฐาน ได้แก่ <span class=\"zh-inline\">了</span> "
        "<span class=\"zh-inline\">呢</span> <span class=\"zh-inline\">也</span> และ <span class=\"zh-inline\">比</span> "
        "สำหรับการเปรียบเทียบ",
    ],
    3: [
        "YCT 3 เพิ่มคำศัพท์เป็นสองเท่า รวมเป็น 300 คำ ผู้เรียนเริ่มเล่าเรื่องในแต่ละวัน โรงเรียน กีฬา สุขภาพ การซื้อของ "
        "และสภาพอากาศได้ และให้เหตุผลง่าย ๆ ด้วย <span class=\"zh-inline\">因为</span> และ <span class=\"zh-inline\">所以</span>",
        "คำไวยากรณ์ใหม่ในระดับนี้ได้แก่ <span class=\"zh-inline\">把</span> <span class=\"zh-inline\">过</span> "
        "<span class=\"zh-inline\">得</span> และ <span class=\"zh-inline\">吧</span>",
    ],
    4: [
        "YCT 4 เป็นระดับสูงสุดของข้อสอบข้อเขียน มีคำศัพท์ 600 คำ คือ 300 คำของ YCT 1–3 และคำใหม่อีก 300 คำ "
        "ครอบคลุมชีวิตประจำวันได้ลึกขึ้น ตั้งแต่การท่องเที่ยวและงานอดิเรก ไปจนถึงความรู้สึก ผลการเรียน และข่าว",
        "ระดับนี้เพิ่มรูปประโยคที่ใช้เป็นคู่ เช่น <span class=\"zh-inline\">不但……而且……</span> "
        "<span class=\"zh-inline\">如果……那么……</span> และ <span class=\"zh-inline\">一边……一边……</span> "
        "รวมถึงคำไวยากรณ์อย่าง <span class=\"zh-inline\">被</span> <span class=\"zh-inline\">着</span> และ "
        "<span class=\"zh-inline\">地</span>",
        "หลักสูตรระบุ <span class=\"zh-inline\">对</span> ไว้สองครั้ง (คำคุณศัพท์และคำบุพบท) และ "
        "<span class=\"zh-inline\">还</span> ไว้สองครั้ง (hái และ huán) หน้านี้แสดงแต่ละคำเพียงครั้งเดียวพร้อมทั้งสองความหมาย "
        "ตารางจึงมี 598 แถวสำหรับ 600 รายการในหลักสูตร",
    ],
}


def read_thai(root, n, rows):
    path = root / "data" / "th" / "yct" / f"yct{n}_th.tsv"
    if not path.exists():
        return None
    th = []
    for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        parts = [p.strip() for p in line.split("\t")]
        if len(parts) != 2 or not parts[1]:
            raise SystemExit(f"data/th/yct/yct{n}_th.tsv line {i}: expected word<TAB>Thai meaning")
        th.append(parts)
    if [w for w, _ in th] != [r[0] for r in rows]:
        raise SystemExit(f"data/th/yct/yct{n}_th.tsv does not match data/yct/yct{n}.tsv word for word")
    return [m for _, m in th]


def has_thai(root):
    return all((root / "data" / "th" / "yct" / f"yct{n}_th.tsv").exists() for n in LEVELS)


def alternates(root):
    if not has_thai(root):
        return {}
    pairs = {YCT_URL: TH_YCT_URL}
    pairs.update({f"{YCT_URL}yct-{n}-word-list/": f"{TH_YCT_URL}yct-{n}-word-list/" for n in LEVELS})
    pairs[YCT_URL + COMPARE] = TH_YCT_URL + COMPARE
    pairs.update({f"{YCT_URL}yct-{n}-vocabulary-worksheets/": f"{TH_YCT_URL}yct-{n}-vocabulary-worksheets/" for n in LEVELS})
    return pairs


def build_th(*, root, tpl, site, css, render, nav, font_link, foot, search_key, thai_key, ws_css=None):
    """Thai word list pages at /th/yct/. The Thai worksheet pages are built by tools/worksheets_th.py."""
    if not has_thai(root):
        return []
    levels = {n: read_level(root, n) for n in LEVELS}
    first = {}
    for n in LEVELS:
        for w, _, _ in levels[n]:
            first.setdefault(w, n)
    urls = []
    wl_body = (tpl / "th" / "yct_wordlist_body.html").read_text(encoding="utf-8")
    for n in LEVELS:
        thai = read_thai(root, n, levels[n])
        url = f"{TH_YCT_URL}yct-{n}-word-list/"
        rows = []
        for i, ((word, pinyin, en), th) in enumerate(zip(levels[n], thai), 1):
            key = html.escape(search_key(word, pinyin, en) + "|" + thai_key(th), quote=True)
            lv = first[word]
            rows.append(
                f'          <tr data-k="{key}" data-new="{1 if lv == n else 0}"><td class="n">{i}</td>'
                f'<td class="hz">{html.escape(word)}</td><td class="py">{html.escape(pinyin)}</td>'
                f'<td class="en">{html.escape(th)}</td><td class="lv"><span class="lv lv{lv}" title="YCT {lv}">{lv}</span></td></tr>'
            )
        toggle = (f'<label class="new-toggle"><input type="checkbox" id="only-new"> เฉพาะคำใหม่ของ YCT {n}</label>'
                  if n > 1 else "")
        body = (wl_body.replace("__NAV__", nav(TH_YCT_URL))
                .replace("__ROWS__", "\n".join(rows))
                .replace("__PROSE__", "\n".join(f"    <p>{p}</p>" for p in TH_PROSE[n]))
                .replace("__LEDE__", TH_LEDE[n])
                .replace("__NEW_TOGGLE__", toggle)
                .replace("__ROWCOUNT__", str(len(rows)))
                .replace("__COUNT__", str(OFFICIAL[n]))
                .replace("__LEVEL__", str(n)))
        out = render(
            f"คำศัพท์ YCT {n} ครบ {OFFICIAL[n]} คำ พร้อมพินอินและคำแปลไทย",
            f"คำศัพท์ YCT ระดับ {n} ทั้ง {OFFICIAL[n]} คำ พร้อมพินอินและความหมายภาษาไทย ค้นหาได้ ฟรี "
            "พร้อมแบบฝึกเขียนตัวอักษรจีนที่พิมพ์ได้",
            site + url, css, body, font_link, lang="th", foot=foot,
        )
        target = root / url.strip("/")
        target.mkdir(parents=True, exist_ok=True)
        (target / "index.html").write_text(out, encoding="utf-8")
        urls.append(url)

    seen, new_chars = set(), {}
    for n in LEVELS:
        count = 0
        for w, _, _ in levels[n]:
            for c in hanzi(w):
                if c not in seen:
                    seen.add(c)
                    count += 1
        new_chars[n] = count
    rows = []
    for n in LEVELS:
        new = OFFICIAL[n] - (OFFICIAL[n - 1] if n > 1 else 0)
        rows.append(f'<tr><th scope="row">YCT {n}</th><td>{OFFICIAL[n]} <small>(ใหม่ {new})</small></td>'
                    f'<td><a href="{TH_YCT_URL}yct-{n}-word-list/">คำศัพท์</a><br>'
                    f'<a href="{TH_YCT_URL}yct-{n}-vocabulary-worksheets/">แบบฝึกหัดคำศัพท์</a><br>'
                    f'<a href="{TH_YCT_URL}yct-{n}-character-worksheets/">แบบฝึกเขียน {new_chars[n]} ตัว</a></td></tr>')
    body = ((tpl / "th" / "yct_index_body.html").read_text(encoding="utf-8")
            .replace("__NAV__", nav(TH_YCT_URL)).replace("__ROWS__", "\n".join(rows)))
    target = root / TH_YCT_URL.strip("/")
    target.mkdir(parents=True, exist_ok=True)
    (target / "index.html").write_text(render(
        "คำศัพท์ YCT 1–4 และแบบฝึกเขียน พร้อมคำแปลไทย ฟรี",
        "คำศัพท์ YCT ระดับ 1–4 พร้อมพินอินและความหมายภาษาไทย และแบบฝึกคัดตัวอักษรจีนที่พิมพ์ได้ฟรีสำหรับแต่ละระดับ "
        "เหมาะสำหรับนักเรียน ครู และผู้ปกครอง",
        site + TH_YCT_URL, css, body, font_link, lang="th", foot=foot), encoding="utf-8")
    urls.insert(0, TH_YCT_URL)
    urls += build_compare(root, lang="th", site=site, render=render, css=css, nav_html=nav(TH_YCT_URL),
                          font_link=font_link, foot=foot)
    if ws_css:
        urls += build_vocab_sheets(root, lang="th", site=site, render=render, css=ws_css, nav_html=nav(TH_YCT_URL),
                                   font_link=font_link, foot=foot)
    return urls


# YCT vs HSK comparison --------------------------------------------------------------------------------

COMPARE = "yct-vs-hsk/"


def hsk_levels(root):
    """Word -> lowest HSK 3.0 level (1-9), from the old-to-new HSK data (levels 1-3 come from data/hskN.tsv)."""
    import json
    lv = {}
    for name in ("words.json", "words-7-9.json"):
        path = root / "old-hsk-to-new-hsk" / name
        if path.exists():
            for w in json.loads(path.read_text(encoding="utf-8"))["w"]:
                lv.setdefault(w[0], w[3])
    for w, n in list(lv.items()):
        if len(w) >= 3 and w.endswith("儿"):
            lv.setdefault(w[:-1], n)
    return lv


def hsk_level_of(word, lv):
    """The HSK level where the YCT word is listed as a word, or None. Paired patterns take their later part."""
    if word in lv:
        return lv[word]
    if word.endswith("儿") and word[:-1] in lv:
        return lv[word[:-1]]
    parts = [p for p in word.split("……") if p]
    if len(parts) > 1 and all(p in lv for p in parts):
        return max(lv[p] for p in parts)
    return None


def comparison(root):
    lv = hsk_levels(root)
    if not lv:
        return None
    hsk = {}
    for n in (1, 2, 3):
        hsk[n] = [line.split("\t")[0] for line in (root / "data" / f"hsk{n}.tsv").read_text(encoding="utf-8").splitlines()
                  if line.strip()]
    out = {}
    for n in LEVELS:
        rows = read_level(root, n)
        words = {r[0] for r in rows}
        levels = [hsk_level_of(r[0], lv) for r in rows]
        out[n] = {
            "rows": rows, "levels": levels, "total": len(rows),
            "h1": levels.count(1), "h2": levels.count(2), "h3": levels.count(3),
            "h46": sum(1 for x in levels if x and 4 <= x <= 6), "h79": sum(1 for x in levels if x and x >= 7),
            "none": levels.count(None),
            "covers": [sum(1 for w in hsk[k] if w in words or w + "儿" in words or (w.endswith("儿") and w[:-1] in words))
                       for k in (1, 2, 3)],
            "hsk_sizes": [len(hsk[k]) for k in (1, 2, 3)],
        }
    return out


def pct(a, b):
    return f"{round(100 * a / b)}%"


def compare_body(data, lang, nav_html, thai=None):
    th = lang == "th"
    T = (lambda en, t: t) if th else (lambda en, t: en)
    rows = []
    for n in LEVELS:
        d = data[n]
        upto3 = d["h1"] + d["h2"] + d["h3"]
        rows.append(f'<tr><th scope="row">YCT {n}</th><td>{d["total"]}</td><td>{d["h1"]}</td><td>{d["h2"]}</td>'
                    f'<td>{d["h3"]}</td><td>{d["h46"] + d["h79"]}</td><td>{d["none"]}</td>'
                    f'<td><b>{pct(upto3, d["total"])}</b></td></tr>')
    cover = []
    for n in LEVELS:
        d = data[n]
        cells = "".join(f'<td>{c} / {s}</td>' for c, s in zip(d["covers"], d["hsk_sizes"]))
        cover.append(f'<tr><th scope="row">YCT {n}</th>{cells}<td><b>{sum(d["covers"])} / {sum(d["hsk_sizes"])}</b></td></tr>')
    d4 = data[4]
    above = [(r, l) for r, l in zip(d4["rows"], d4["levels"]) if l and l >= 4]
    above.sort(key=lambda x: (x[1], x[0][1]))
    meaning = {r[0]: m for r, m in zip(d4["rows"], thai)} if thai else {}
    arows = "\n".join(
        f'<tr><td class="hz">{html.escape(r[0])}</td><td class="py">{html.escape(r[1])}</td>'
        f'<td class="en">{html.escape(meaning.get(r[0], r[2]))}</td><td>HSK {l}</td></tr>' for r, l in above)
    none = [r for r, l in zip(d4["rows"], d4["levels"]) if l is None]
    none_html = "、".join(f'<span class="zh-inline">{html.escape(r[0])}</span>' for r in none)
    y4_upto3 = d4["h1"] + d4["h2"] + d4["h3"]
    y3 = data[3]
    wl = (lambda n: f"{TH_YCT_URL}yct-{n}-word-list/") if th else (lambda n: f"{YCT_URL}yct-{n}-word-list/")
    hskwl = (lambda n: f"/th/hsk-{n}-word-list/") if th else (lambda n: f"/hsk-{n}-word-list/")
    summary = T(
        f"Most YCT words are HSK 1–3 words: {pct(y3['h1'] + y3['h2'] + y3['h3'], y3['total'])} of YCT 3 and "
        f"{pct(y4_upto3, d4['total'])} of YCT 4. But YCT 4, the top level, covers only {sum(d4['covers'])} of the "
        f"{sum(d4['hsk_sizes'])} different words in HSK 1–3. In vocabulary, YCT 1–2 are mostly HSK 1 words, YCT 3 reaches "
        "into HSK 2 and 3, and YCT 4 spreads across HSK 1–3 without covering any of them completely.",
        f"คำศัพท์ YCT ส่วนใหญ่เป็นคำศัพท์ HSK 1–3 คือ {pct(y3['h1'] + y3['h2'] + y3['h3'], y3['total'])} ของ YCT 3 และ "
        f"{pct(y4_upto3, d4['total'])} ของ YCT 4 แต่ YCT 4 ซึ่งเป็นระดับสูงสุด ครอบคลุมคำศัพท์เพียง {sum(d4['covers'])} คำ "
        f"จาก {sum(d4['hsk_sizes'])} คำที่ไม่ซ้ำกันของ HSK 1–3 ในแง่คำศัพท์ YCT 1–2 ส่วนใหญ่เป็นคำศัพท์ HSK 1 YCT 3 เริ่มเข้าไปใน HSK 2 และ 3 "
        "ส่วน YCT 4 กระจายอยู่ใน HSK 1–3 แต่ไม่ครอบคลุมระดับใดครบทั้งหมด")
    return f"""<div class="wrap">
  <header>
    {nav_html}
    <div class="eyebrow"><span>{T("YCT · HSK 3.0", "YCT · HSK 3.0")}</span><span class="chip">{T("Word list comparison", "เปรียบเทียบคำศัพท์")}</span></div>
    <h1>{T("YCT vs HSK: Which HSK Level Is Each YCT Level?", "YCT เทียบกับ HSK: YCT แต่ละระดับเท่ากับ HSK ระดับไหน")}</h1>
    <p class="lede">{summary}</p>
  </header>

  <section class="sheet" aria-labelledby="t1">
    <h2 id="t1">{T("Where the YCT words sit in HSK 3.0", "คำศัพท์ YCT อยู่ใน HSK 3.0 ระดับไหน")}</h2>
    <p class="lede">{T("Each YCT word is counted at the lowest HSK 3.0 level that lists it.", "นับคำศัพท์ YCT แต่ละคำตามระดับ HSK 3.0 ที่ต่ำที่สุดที่มีคำนั้นอยู่")}</p>
    <div class="levels-wrap"><table class="levels">
      <thead><tr><th scope="col">YCT</th><th scope="col">{T("Words", "คำ")}</th><th scope="col">HSK 1</th><th scope="col">HSK 2</th><th scope="col">HSK 3</th><th scope="col">HSK 4–6</th><th scope="col">{T("Not an HSK word", "ไม่ใช่คำใน HSK")}</th><th scope="col">{T("HSK 1–3", "HSK 1–3")}</th></tr></thead>
      <tbody>
{chr(10).join(rows)}
      </tbody>
    </table></div>
  </section>

  <section class="sheet" aria-labelledby="t2">
    <h2 id="t2">{T("How much of HSK each YCT level covers", "YCT แต่ละระดับครอบคลุมคำศัพท์ HSK ได้แค่ไหน")}</h2>
    <p class="lede">{T("The other way round: how many words of each HSK level are already in the YCT list.", "มองกลับกัน: คำศัพท์ของ HSK แต่ละระดับมีอยู่ในรายการ YCT แล้วกี่คำ")}</p>
    <div class="levels-wrap"><table class="levels">
      <thead><tr><th scope="col">YCT</th><th scope="col">HSK 1</th><th scope="col">HSK 2</th><th scope="col">HSK 3</th><th scope="col">HSK 1–3</th></tr></thead>
      <tbody>
{chr(10).join(cover)}
      </tbody>
    </table></div>
  </section>

  <section class="prose" aria-labelledby="t3">
    <h2 id="t3">{T("What this means", "หมายความว่าอย่างไร")}</h2>
    <p>{T("A student who passes YCT 4 knows a good part of the HSK 1–3 vocabulary, but not all of it. Moving on to the HSK, the quickest path is to learn the HSK 1–3 words that are not in the YCT list, rather than starting HSK 1 from scratch.",
          "นักเรียนที่สอบผ่าน YCT 4 รู้คำศัพท์ HSK 1–3 ไปมากพอสมควร แต่ไม่ครบทั้งหมด ถ้าจะต่อไปสอบ HSK วิธีที่เร็วที่สุดคือเรียนคำศัพท์ HSK 1–3 ส่วนที่ไม่อยู่ใน YCT แทนที่จะเริ่ม HSK 1 ใหม่ตั้งแต่ต้น")}</p>
    <p>{T("The YCT is written for children, so its list includes words the HSK leaves for later, such as animals, sports and single-character colours like <span class=\"zh-inline\">红</span> and <span class=\"zh-inline\">黄</span>, and a few everyday phrases that the HSK does not list as separate words. Those are shown below.",
          "YCT ออกแบบมาสำหรับเด็ก รายการคำศัพท์จึงมีคำที่ HSK เก็บไว้ในระดับสูงกว่า เช่น สัตว์ กีฬา และชื่อสีแบบตัวเดียวอย่าง <span class=\"zh-inline\">红</span> และ <span class=\"zh-inline\">黄</span> รวมถึงวลีในชีวิตประจำวันบางคำที่ HSK ไม่ได้นับเป็นคำแยก ดูรายการด้านล่าง")}</p>
    <p>{T("This page compares word lists only. The YCT and the HSK are different exams with their own formats, and there is no official equivalence between their levels.",
          "หน้านี้เปรียบเทียบเฉพาะรายการคำศัพท์ YCT และ HSK เป็นการสอบคนละแบบ มีรูปแบบข้อสอบของตัวเอง และไม่มีการเทียบระดับอย่างเป็นทางการระหว่างกัน")}</p>
  </section>

  <section class="sheet" aria-labelledby="t4">
    <h2 id="t4">{T(f"The {len(above)} YCT 4 words above HSK 3", f"คำศัพท์ YCT 4 จำนวน {len(above)} คำที่สูงกว่า HSK 3")}</h2>
    <div class="table-wrap"><table class="words-table">
      <thead><tr><th scope="col">{T("Word", "คำ")}</th><th scope="col">{T("Pinyin", "พินอิน")}</th><th scope="col">{T("Meaning", "ความหมาย")}</th><th scope="col">HSK</th></tr></thead>
      <tbody>
{arows}
      </tbody>
    </table></div>
    <p class="lede">{T(f"Not listed as separate words in HSK 3.0 ({len(none)}): ", f"ไม่ได้อยู่ใน HSK 3.0 ในฐานะคำแยก ({len(none)} คำ): ")}{none_html}</p>
  </section>

  <section class="sheet" aria-labelledby="t5">
    <h2 id="t5">{T("Word lists", "รายการคำศัพท์")}</h2>
    <div class="cta"><a class="button ghost" href="{wl(1)}">YCT 1</a><a class="button ghost" href="{wl(2)}">YCT 2</a><a class="button ghost" href="{wl(3)}">YCT 3</a><a class="button ghost" href="{wl(4)}">YCT 4</a><a class="button ghost" href="{hskwl(1)}">HSK 1</a><a class="button ghost" href="{hskwl(2)}">HSK 2</a><a class="button ghost" href="{hskwl(3)}">HSK 3</a></div>
  </section>

  <footer class="notes">
    <p><b>{T("Method.", "วิธีนับ")}</b> {T("YCT words follow the official YCT syllabus. HSK levels follow the HSK 3.0 (2025) word lists: levels 1–3 from this site's cross-checked lists, levels 4–9 from complete-hsk-vocabulary. A word counts as an HSK word only if the HSK list has it as written (a final 儿 may be dropped); phrases such as 打篮球 are not split into parts. Paired patterns such as 一边……一边…… are counted at the level of their parts.",
        "คำศัพท์ YCT เป็นไปตามหลักสูตร YCT อย่างเป็นทางการ ระดับ HSK เป็นไปตามรายการคำศัพท์ HSK 3.0 (2025) ระดับ 1–3 จากรายการที่เว็บไซต์นี้ตรวจทานแล้ว ระดับ 4–9 จาก complete-hsk-vocabulary คำหนึ่งจะนับเป็นคำ HSK ก็ต่อเมื่อรายการ HSK มีคำนั้นตรงตามที่เขียน (ตัด 儿 ท้ายคำได้) วลีอย่าง 打篮球 จะไม่ถูกแยกเป็นส่วน ๆ ส่วนรูปประโยคคู่อย่าง 一边……一边…… นับตามระดับของส่วนประกอบ")}</p>
  </footer>
</div>"""


def build_compare(root, *, lang, site, render, css, nav_html, font_link="", foot=None):
    data = comparison(root)
    if not data:
        return []
    th = lang == "th"
    thai = read_thai(root, 4, data[4]["rows"]) if th else None
    url = (TH_YCT_URL if th else YCT_URL) + COMPARE
    body = compare_body(data, lang, nav_html, thai)
    d4, d3 = data[4], data[3]
    if th:
        title = "YCT เทียบกับ HSK: YCT แต่ละระดับเท่ากับ HSK ระดับไหน"
        desc = (f"เปรียบเทียบคำศัพท์ YCT 1–4 กับ HSK 3.0: YCT 4 ครอบคลุมคำศัพท์ HSK 1–3 {sum(d4['covers'])} จาก "
                f"{sum(d4['hsk_sizes'])} คำ พร้อมรายการคำที่สูงกว่า HSK 3")
        kw = dict(lang="th", foot=foot)
    else:
        title = "YCT vs HSK: Which HSK Level Is Each YCT Level?"
        desc = (f"YCT 1–4 compared with HSK 3.0, word by word: YCT 4 covers {sum(d4['covers'])} of the "
                f"{sum(d4['hsk_sizes'])} HSK 1–3 words. With the YCT 4 words above HSK 3.")
        kw = {}
    target = root / url.strip("/")
    target.mkdir(parents=True, exist_ok=True)
    (target / "index.html").write_text(render(title, desc, site + url, css, body, font_link, **kw), encoding="utf-8")
    return [url]


def build_vocab_sheets(root, *, lang, site, render, css, nav_html, font_link="", foot=None):
    """Printable vocabulary worksheets, one page per level (see tools/yct_ws.py)."""
    import yct_ws
    levels = {n: read_level(root, n) for n in LEVELS}
    first = {}
    for n in LEVELS:
        for w, _, _ in levels[n]:
            first.setdefault(w, n)
    th = lang == "th"
    base = TH_YCT_URL if th else YCT_URL
    t = yct_ws.T[lang]
    urls = []
    for n in LEVELS:
        url = f"{base}yct-{n}-vocabulary-worksheets/"
        thai = read_thai(root, n, levels[n]) if th else None
        body, sets, words = yct_ws.page(n, lang, levels[n], first, thai, site, nav_html,
                                        f"{base}yct-{n}-character-worksheets/", url)
        kw = dict(lang="th", foot=foot) if th else {}
        target = root / url.strip("/")
        target.mkdir(parents=True, exist_ok=True)
        (target / "index.html").write_text(render(
            t["doc_title"].format(n=n), t["doc_desc"].format(n=n, sets=sets, words=words), site + url,
            css + yct_ws.CSS, body, font_link, **kw), encoding="utf-8")
        urls.append(url)
    return urls
