"""HSK 5 (HSK 3.0, 2025 syllabus) word list and character worksheets.

  data/hsk5_words.txt   the 1,600 syllabus entries in order (a word listed twice for two uses appears twice)
  data/hsk5.tsv         word<TAB>pinyin<TAB>English, one row per word (1,595 rows)

Source: the 2025 HSK syllabus (新版HSK考试大纲), via the transcription in hsk-syllabus-vocabulary-parser
(github.com/Punpuf/hsk-syllabus-vocabulary-parser, MIT). Each level of the syllabus first repeats some lower-level
words that gain a new use, then lists its own new words; only the new words are kept here. The same rule gives
this site's HSK 1-4 lists word for word. English meanings are written for this site (CC-CEDICT consulted).

Outputs:
  hsk-5-word-list/index.html
  hsk-5-character-worksheets/index.html   (characters not used in any HSK 1-4 word)

Called from tools/build.py; returns the URLs it wrote.
"""
import html

URL = "/hsk-5-word-list/"
WS_URL = "/hsk-5-character-worksheets/"
OFFICIAL = 1600

LEDE = ("All 1,600 new words for HSK 5 in the HSK 3.0 (New HSK) syllabus, with pinyin and English. Together with HSK 1–4, "
        "that makes 3,600 words. Search by character, pinyin or meaning.")
PROSE = [
    "HSK 5 adds 1,600 words to the 2,000 of HSK 1–4, for 3,600 in total. It is the level where learners read the "
    "news, follow longer talks and discuss work, society and ideas, so abstract words such as "
    "<span class=\"zh-inline\">趋势</span> (trend), <span class=\"zh-inline\">措施</span> (measure) and "
    "<span class=\"zh-inline\">本质</span> (essence) become common.",
    "Everyday modern life is well represented too: <span class=\"zh-inline\">二维码</span> (QR code), "
    "<span class=\"zh-inline\">点赞</span> (to like a post), <span class=\"zh-inline\">直播</span> (livestream) and "
    "<span class=\"zh-inline\">充值</span> (to top up) are all HSK 5 words in the 2025 syllabus.",
    "The syllabus lists <span class=\"zh-inline\">处</span>, <span class=\"zh-inline\">调</span> and "
    "<span class=\"zh-inline\">系</span> twice, once for each reading, and a few words such as "
    "<span class=\"zh-inline\">为</span> (wéi) appear again with a new use. This page shows each word once, "
    "so the table has 1,595 rows for the 1,600 syllabus entries.",
]


def read(root):
    raw = (root / "data" / "hsk5_words.txt").read_text(encoding="utf-8").replace("，", ",")
    words = [w.strip() for w in raw.split(",") if w.strip()]
    if len(words) != OFFICIAL:
        raise SystemExit(f"hsk5_words.txt has {len(words)} entries, expected {OFFICIAL}")
    rows = []
    for i, line in enumerate((root / "data" / "hsk5.tsv").read_text(encoding="utf-8").splitlines(), 1):
        if line.strip():
            parts = [p.strip() for p in line.split("\t")]
            if len(parts) != 3 or not all(parts):
                raise SystemExit(f"hsk5.tsv line {i}: expected word<TAB>pinyin<TAB>meaning")
            rows.append(tuple(parts))
    if [r[0] for r in rows] != list(dict.fromkeys(words)):
        raise SystemExit("hsk5.tsv does not match hsk5_words.txt")
    return words, rows


def new_chars(rows, lower_words):
    known = {c for w in lower_words for c in w}
    out = []
    for w, _, _ in rows:
        for c in w:
            if "一" <= c <= "鿿" and c not in known and c not in out:
                out.append(c)
    return out


def build(root, pages, nav, render, base_css, tpl, site, search_key, worksheet_page, lower_words):
    if not (root / "data" / "hsk5.tsv").exists():
        return []
    words, rows = read(root)
    urls = []

    body = (tpl / "wordlist_body.html").read_text(encoding="utf-8")
    old_src = ("<p><b>Source.</b> Words and their order follow the HSK 3.0 Level __LEVEL__ list in the 2025 exam syllabus, "
               "cross-checked against two independently published copies of the list.</p>")
    new_src = ("<p><b>Source.</b> Words and their order follow the HSK 3.0 Level 5 list in the 2025 exam syllabus, as "
               "transcribed by the open hsk-syllabus-vocabulary-parser project; the same transcription matches this "
               "site's HSK 1–4 lists word for word. English meanings are our own.</p>")
    if body.count(old_src) != 1:
        raise SystemExit("hsk5: template source note not found")
    body = body.replace(old_src, new_src)
    trs = []
    for i, (word, pinyin, meaning) in enumerate(rows, 1):
        key = html.escape(search_key(word, pinyin, meaning), quote=True)
        trs.append(f'          <tr data-k="{key}"><td class="n">{i}</td><td class="hz">{html.escape(word)}</td>'
                   f'<td class="py">{html.escape(pinyin)}</td><td class="en">{html.escape(meaning)}</td></tr>')
    body = (body.replace("__NAV__", nav(pages, URL)).replace("__ROWS__", "\n".join(trs))
            .replace("__PROSE__", "\n".join(f"    <p>{p}</p>" for p in PROSE)).replace("__LEDE__", LEDE)
            .replace("__ROWCOUNT__", f"{len(rows):,}").replace("__COUNT__", f"{OFFICIAL:,}").replace("__LEVEL__", "5"))
    out = render("HSK 5 Word List (HSK 3.0, 1600 words)",
                 "All 1,600 HSK 5 words in the HSK 3.0 (New HSK) 2025 syllabus with pinyin and English meanings. "
                 "Searchable and free, with printable writing sheets.",
                 site + URL, base_css + (tpl / "wordlist.css").read_text(encoding="utf-8"), body)
    (root / URL.strip("/")).mkdir(exist_ok=True)
    (root / URL.strip("/") / "index.html").write_text(out, encoding="utf-8")
    urls.append(URL)

    chars = new_chars(rows, lower_words)
    total = len(chars)
    trs = []
    for i, c in enumerate(chars, 1):
        w = next(r for r in rows if c in r[0])
        trs.append(f'<tr><td class="n">{i}</td><td class="hz">{html.escape(c)}</td>'
                   f'<td class="w"><span class="zh-inline">{html.escape(w[0])}</span> {html.escape(w[1])} '
                   f'<small>{html.escape(w[2])}</small></td></tr>')
    chartable = (f'  <section class="sheet char-table no-print" aria-labelledby="chars-title">\n'
                 f'    <h2 id="chars-title">All {total} new characters in the HSK 5 words</h2>\n'
                 f'    <div class="table-wrap"><table><thead><tr><th scope="col">#</th><th scope="col">Character</th>'
                 f'<th scope="col">First word in the list</th></tr></thead><tbody>\n' + "\n".join(trs)
                 + "\n    </tbody></table></div>\n  </section>")
    options = [f'<option value="all">All {total} characters</option>']
    for a in range(1, total + 1, 30):
        b = min(a + 29, total)
        options.append(f'<option value="{a}-{b}">Characters {a}–{b}</option>')
    range_html = ('<div class="field"><label for="range">Characters to print</label>'
                  f'<select id="range">{"".join(options)}</select></div>')
    links = []
    for n in (1, 2, 3, 4, 5):
        u = f"/hsk-{n}-character-worksheets/"
        cur = ' aria-current="page"' if n == 5 else ""
        links.append(f'<a href="{u}"{cur}>HSK {n}</a>')
    links_html = ('<nav class="level-links" aria-label="Character sets"><span>Start from:</span>' + "".join(links)
                  + '<a href="/chinese-character-worksheets/">Any characters</a></nav>')
    body = worksheet_page(
        (tpl / "worksheet_body.html").read_text(encoding="utf-8"), pages, WS_URL,
        eyebrow="New HSK · 2025 syllabus", chips=["Level 5", f"{total} characters"],
        h1="HSK 5 Character Worksheets",
        lede=f"Printable writing practice for the {total} characters that are new in the HSK 5 words of the HSK 3.0 syllabus "
             "(characters already used in HSK 1–4 are not repeated), with stroke order, pinyin and tracing boxes. "
             "Print the whole level, or 30 characters at a time.",
        chars="".join(chars), preset=0, range_html=range_html, sheet_title="HSK 5 characters",
        chartable=chartable, about_title="About these characters",
        prose=["The HSK 3.0 syllabus lists words, not single characters. This page takes every character in the HSK 5 words "
               "that does not appear in any HSK 1–4 word, and lists it once, in the order it first appears in the word list.",
               f'Use these sheets alongside the <a href="{URL}">HSK 5 word list</a>.'],
        links=links_html,
    )
    (root / WS_URL.strip("/")).mkdir(exist_ok=True)
    (root / WS_URL.strip("/") / "index.html").write_text(render(
        "HSK 5 Character Worksheets: Printable Stroke Order Practice (HSK 3.0)",
        f"Free printable writing worksheets for the {total} new characters of HSK 5 in the HSK 3.0 syllabus, "
        "with stroke order, pinyin, tracing and tian grid boxes.",
        site + WS_URL, base_css + (tpl / "worksheet.css").read_text(encoding="utf-8"), body), encoding="utf-8")
    urls.append(WS_URL)
    return urls


# Thai ------------------------------------------------------------------------------------------------------------
# Same pattern as tools/hsk4.py: data/th/hsk5_th.tsv (word<TAB>Thai) follows data/hsk5.tsv row for row. It may be
# written in batches; the Thai HSK 5 pages are built only once it covers every word.

TH_URL = "/th/hsk-5-word-list/"
TH_WS_URL = "/th/hsk-5-character-worksheets/"
TH_LEDE = ("คำศัพท์ใหม่ของ HSK 5 ทั้ง 1,600 คำ ตามหลักสูตร HSK 3.0 (HSK ใหม่) พร้อมพินอินและความหมายภาษาไทย "
           "รวมกับ HSK 1–4 เป็น 3,600 คำ ค้นหาได้ด้วยตัวอักษรจีน พินอิน หรือภาษาไทย")
TH_PROSE = [
    "HSK 5 เพิ่มคำศัพท์อีก 1,600 คำจาก 2,000 คำของ HSK 1–4 รวมเป็น 3,600 คำ ระดับนี้ผู้เรียนอ่านข่าว ฟังการพูดที่ยาวขึ้น "
    "และพูดคุยเรื่องงาน สังคม และความคิด คำนามธรรมอย่าง <span class=\"zh-inline\">趋势</span> (แนวโน้ม) "
    "<span class=\"zh-inline\">措施</span> (มาตรการ) และ <span class=\"zh-inline\">本质</span> (แก่นแท้) จึงพบบ่อยขึ้น",
    "คำในชีวิตสมัยใหม่ก็มีมาก เช่น <span class=\"zh-inline\">二维码</span> (คิวอาร์โค้ด) "
    "<span class=\"zh-inline\">点赞</span> (กดไลก์) <span class=\"zh-inline\">直播</span> (ไลฟ์สด) และ "
    "<span class=\"zh-inline\">充值</span> (เติมเงิน) ล้วนเป็นคำศัพท์ HSK 5 ในหลักสูตรปี 2025",
    "หลักสูตรระบุ <span class=\"zh-inline\">处</span> <span class=\"zh-inline\">调</span> และ "
    "<span class=\"zh-inline\">系</span> ไว้สองครั้งตามเสียงอ่าน และมีบางคำ เช่น <span class=\"zh-inline\">为</span> (wéi) "
    "ที่ปรากฏซ้ำพร้อมการใช้งานใหม่ หน้านี้แสดงแต่ละคำเพียงครั้งเดียว ตารางจึงมี 1,595 แถวสำหรับ 1,600 รายการในหลักสูตร",
]


def read_thai(root, rows):
    """Thai meanings from data/th/hsk5_th.tsv (word<TAB>Thai), in the order of data/hsk5.tsv.

    The file may be incomplete while it is being written in batches: it must then be an exact prefix of the word list,
    and the Thai pages are only built once every word has a meaning. Returns the list of meanings or None."""
    path = root / "data" / "th" / "hsk5_th.tsv"
    if not path.exists():
        return None
    th = []
    for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if line.strip():
            parts = [p.strip() for p in line.split("\t")]
            if len(parts) != 2 or not parts[1]:
                raise SystemExit(f"data/th/hsk5_th.tsv line {i}: expected word<TAB>Thai meaning")
            th.append(parts)
    words = [r[0] for r in rows]
    if [w for w, _ in th] != words[:len(th)]:
        bad = next(i for i, (w, _) in enumerate(th) if i >= len(words) or w != words[i])
        raise SystemExit(f"data/th/hsk5_th.tsv line {bad + 1}: {th[bad][0]} is out of order; expected "
                         f"{words[bad] if bad < len(words) else 'end of file'}")
    return [m for _, m in th] if len(th) == len(words) else None


def thai_meanings(root):
    """The complete Thai meanings and rows, or (None, rows) while the Thai file is unfinished."""
    if not (root / "data" / "hsk5.tsv").exists():
        return None, []
    _, rows = read(root)
    return read_thai(root, rows), rows


def th_alternates(root):
    thai, _ = thai_meanings(root)
    if thai is None:
        return {}
    return {URL: TH_URL, WS_URL: TH_WS_URL}


def build_th(*, root, tpl, site, render, nav, font_link, foot, wl_css, ws_css, search_key, thai_key, lower_words):
    import re
    import worksheets_th
    thai, rows = thai_meanings(root)
    if thai is None:
        return []
    urls = []
    body = (tpl / "th" / "wordlist_body.html").read_text(encoding="utf-8")
    swaps = [
        ('<h2 id="cta-title">ตรวจข้อความเทียบกับ HSK __LEVEL__</h2>', '<h2 id="cta-title">ฝึกเขียนตัวอักษร HSK __LEVEL__</h2>'),
        ('<a class="button" href="/th/#hsk__LEVEL__">เปิดเครื่องมือตรวจระดับ</a><a class="button ghost" href="/th/hsk-__LEVEL__-character-worksheets/">แบบฝึกเขียนตัวอักษร</a>',
         '<a class="button" href="/th/hsk-__LEVEL__-character-worksheets/">แบบฝึกเขียนตัวอักษร</a><a class="button ghost" href="/th/hsk-4-word-list/">คำศัพท์ HSK 4</a>'),
        ("และตรวจทานกับสำเนารายการที่เผยแพร่อย่างอิสระอีกสองแหล่ง",
         "ตามการถอดความของโครงการเปิด hsk-syllabus-vocabulary-parser ซึ่งตรงกับรายการ HSK 1–4 ของเว็บไซต์นี้ทุกคำ"),
    ]
    for a, b in swaps:
        if body.count(a) != 1:
            raise SystemExit(f"hsk5 (th): template text not found: {a[:50]}")
        body = body.replace(a, b)
    body = re.sub(r'(<h2 id="cta-title">.*?</h2>\s*<p class="lede">).*?(</p>)',
                  r"\1พิมพ์แบบฝึกคัดตัวอักษรจีนสำหรับตัวอักษรใหม่ของ HSK 5 ได้ฟรี มีลำดับขีด พินอิน และช่องให้เขียนตาม\2",
                  body, count=1, flags=re.S)
    trs = []
    for i, ((word, pinyin, en), th) in enumerate(zip(rows, thai), 1):
        key = html.escape(search_key(word, pinyin, en) + "|" + thai_key(th), quote=True)
        trs.append(f'          <tr data-k="{key}"><td class="n">{i}</td><td class="hz">{html.escape(word)}</td>'
                   f'<td class="py">{html.escape(pinyin)}</td><td class="en">{html.escape(th)}</td></tr>')
    body = (body.replace("__NAV__", nav(TH_URL)).replace("__ROWS__", "\n".join(trs))
            .replace("__PROSE__", "\n".join(f"    <p>{p}</p>" for p in TH_PROSE)).replace("__LEDE__", TH_LEDE)
            .replace("__ROWCOUNT__", f"{len(rows):,}").replace("__COUNT__", f"{OFFICIAL:,}").replace("__LEVEL__", "5"))
    target = root / TH_URL.strip("/")
    target.mkdir(parents=True, exist_ok=True)
    (target / "index.html").write_text(render(
        f"คำศัพท์ HSK 5 (HSK 3.0) {OFFICIAL} คำ พร้อมคำแปลภาษาไทย",
        f"คำศัพท์ HSK 5 ทั้ง {OFFICIAL:,} คำ ตามหลักสูตร HSK 3.0 (HSK ใหม่) ปี 2025 พร้อมพินอินและความหมายภาษาไทย ค้นหาได้ ฟรี",
        site + TH_URL, wl_css, body, font_link, lang="th", foot=foot), encoding="utf-8")
    urls.append(TH_URL)

    chars = new_chars(rows, lower_words)
    total = len(chars)
    entries = list(zip(rows, thai))
    trs = []
    for i, c in enumerate(chars, 1):
        (w, p, _), th = next(e for e in entries if c in e[0][0])
        trs.append(f'<tr><td class="n">{i}</td><td class="hz">{html.escape(c)}</td>'
                   f'<td class="w">{worksheets_th.word_cell(w, p, th)}</td></tr>')
    body = worksheets_th.fill(
        worksheets_th.thai_template(tpl), nav=nav(worksheets_th.TH_WS_URL), eyebrow="HSK ใหม่ · หลักสูตรปี 2025",
        chips=["ระดับ 5", f"{total} ตัว"], h1="แบบฝึกเขียนตัวอักษร HSK 5",
        lede=f"แบบฝึกเขียนตัวอักษรใหม่ของ HSK 5 (ไม่ซ้ำกับ HSK 1–4) ทั้ง {total} ตัว มีลำดับขีด พินอิน และช่องให้เขียนตาม "
             "พิมพ์ได้ทั้งระดับหรือครั้งละ 30 ตัว",
        links=worksheets_th.links_html(TH_WS_URL, [1, 2, 3, 4, 5]), chars="".join(chars), preset=0,
        range_html=worksheets_th.range_select(total), sheet_title="ตัวอักษร HSK 5",
        chartable=worksheets_th.char_table(f"ตัวอักษรใหม่ทั้งหมด {total} ตัวในคำศัพท์ HSK 5", trs),
        about_title="เกี่ยวกับตัวอักษรชุดนี้",
        prose=["หลักสูตร HSK 3.0 กำหนดเป็นคำศัพท์ ไม่ใช่ตัวอักษรเดี่ยว หน้านี้นำตัวอักษรทุกตัวในคำศัพท์ HSK 5 ที่ไม่เคยปรากฏในคำศัพท์ "
               "HSK 1–4 มาแสดงตัวละครั้งเดียว ตามลำดับที่ปรากฏครั้งแรกในรายการคำศัพท์",
               f'ใช้แบบฝึกนี้คู่กับ<a href="{TH_URL}">คำศัพท์ HSK 5</a>'],
    )
    target = root / TH_WS_URL.strip("/")
    target.mkdir(parents=True, exist_ok=True)
    (target / "index.html").write_text(render(
        "แบบฝึกเขียนตัวอักษรจีน HSK 5 พิมพ์ได้ฟรี พร้อมลำดับขีด",
        f"แบบฝึกคัดตัวอักษรจีน HSK 5 ({total} ตัว) ตามหลักสูตร HSK 3.0 พิมพ์ได้ฟรี มีลำดับขีด พินอิน ตัวจาง ๆ ให้เขียนตาม และตาราง 田",
        site + TH_WS_URL, ws_css, body, font_link, lang="th", foot=foot), encoding="utf-8")
    urls.append(TH_WS_URL)
    return urls
