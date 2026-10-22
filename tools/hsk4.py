"""HSK 4 (HSK 3.0, 2025 syllabus) word list and character worksheets.

  data/hsk4_words.txt   the 1,000 syllabus entries in order (a word listed twice for two uses appears twice)
  data/hsk4.tsv         word<TAB>pinyin<TAB>English, one row per word (997 rows)

Source: the 2025 HSK syllabus (新版HSK考试大纲, 2025-11), via the transcription in hsk-3.0-vocabulary-dataset, which
matches this site's HSK 1-3 lists word for word; cross-checked against complete-hsk-vocabulary (972 of the 1,000
entries are in both; the other 25 are words the second source lists at a lower level or lacks).

HSK 4 is kept out of build.LEVELS for now, so the level checker still covers HSK 1-3 only.

Outputs:
  hsk-4-word-list/index.html
  hsk-4-character-worksheets/index.html   (characters not used in any HSK 1-3 word)

Called from tools/build.py; returns the URLs it wrote.
"""
import html

URL = "/hsk-4-word-list/"
WS_URL = "/hsk-4-character-worksheets/"
OFFICIAL = 1000

LEDE = ("All 1,000 new words for HSK 4 in the HSK 3.0 (New HSK) syllabus, with pinyin and English. Together with HSK 1–3, "
        "that makes 2,000 words. Search by character, pinyin or meaning.")
PROSE = [
    "HSK 4 doubles the vocabulary again, adding 1,000 words to reach 2,000 in total. It is the level where learners move "
    "from everyday survival Chinese to work, study and social life: applying for jobs, talking about the news, travel "
    "plans, feelings and opinions.",
    "Many HSK 4 words are built from characters you already know, such as <span class=\"zh-inline\">网友</span> "
    "(online friend) from <span class=\"zh-inline\">网</span> and <span class=\"zh-inline\">友</span>. Modern words "
    "like <span class=\"zh-inline\">扫码</span> (to scan a QR code), <span class=\"zh-inline\">线上</span> (online) and "
    "<span class=\"zh-inline\">动车</span> (bullet train) are new in the 2025 syllabus.",
    "The syllabus lists <span class=\"zh-inline\">重</span>, <span class=\"zh-inline\">空</span> and "
    "<span class=\"zh-inline\">生</span> twice, once for each reading or use. This page shows each of them once, so the "
    "table has 997 rows for the 1,000 syllabus entries.",
]


def read(root):
    raw = (root / "data" / "hsk4_words.txt").read_text(encoding="utf-8").replace("，", ",")
    words = [w.strip() for w in raw.split(",") if w.strip()]
    if len(words) != OFFICIAL:
        raise SystemExit(f"hsk4_words.txt has {len(words)} entries, expected {OFFICIAL}")
    rows = []
    for i, line in enumerate((root / "data" / "hsk4.tsv").read_text(encoding="utf-8").splitlines(), 1):
        if line.strip():
            parts = [p.strip() for p in line.split("\t")]
            if len(parts) != 3 or not all(parts):
                raise SystemExit(f"hsk4.tsv line {i}: expected word<TAB>pinyin<TAB>meaning")
            rows.append(tuple(parts))
    if [r[0] for r in rows] != list(dict.fromkeys(words)):
        raise SystemExit("hsk4.tsv does not match hsk4_words.txt")
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
    if not (root / "data" / "hsk4.tsv").exists():
        return []
    words, rows = read(root)
    urls = []

    body = (tpl / "wordlist_body.html").read_text(encoding="utf-8")
    swaps = [
        ('<h2 id="cta-title">Check a text against HSK __LEVEL__</h2>', '<h2 id="cta-title">Practise writing the HSK __LEVEL__ characters</h2>'),
        ('<p class="lede">Paste any Chinese text into the level checker. Words above HSK __LEVEL__ are marked in red, so you can see at once whether a text fits.</p>',
         '<p class="lede">Print free handwriting sheets for the characters that are new at HSK 4, with stroke order, pinyin and tracing boxes.</p>'),
        ('<a class="button" href="/#hsk__LEVEL__">Open the level checker</a><a class="button ghost" href="/hsk-__LEVEL__-character-worksheets/">Print writing worksheets</a>',
         '<a class="button" href="/hsk-__LEVEL__-character-worksheets/">Print writing worksheets</a><a class="button ghost" href="/hsk-3-word-list/">HSK 3 word list</a>'),
        ("cross-checked against two independently published copies of the list.",
         "cross-checked against an independently published copy of the list."),
    ]
    for a, b in swaps:
        if body.count(a) != 1:
            raise SystemExit(f"hsk4: template text not found: {a[:50]}")
        body = body.replace(a, b)
    trs = []
    for i, (word, pinyin, meaning) in enumerate(rows, 1):
        key = html.escape(search_key(word, pinyin, meaning), quote=True)
        trs.append(f'          <tr data-k="{key}"><td class="n">{i}</td><td class="hz">{html.escape(word)}</td>'
                   f'<td class="py">{html.escape(pinyin)}</td><td class="en">{html.escape(meaning)}</td></tr>')
    body = (body.replace("__NAV__", nav(pages, URL)).replace("__ROWS__", "\n".join(trs))
            .replace("__PROSE__", "\n".join(f"    <p>{p}</p>" for p in PROSE)).replace("__LEDE__", LEDE)
            .replace("__ROWCOUNT__", str(len(rows))).replace("__COUNT__", str(OFFICIAL)).replace("__LEVEL__", "4"))
    out = render("HSK 4 Word List (HSK 3.0, 1000 words)",
                 "All 1,000 HSK 4 words in the HSK 3.0 (New HSK) 2025 syllabus with pinyin and English meanings. "
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
                 f'    <h2 id="chars-title">All {total} new characters in the HSK 4 words</h2>\n'
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
    for n in (1, 2, 3, 4):
        u = f"/hsk-{n}-character-worksheets/"
        cur = ' aria-current="page"' if n == 4 else ""
        links.append(f'<a href="{u}"{cur}>HSK {n}</a>')
    links_html = ('<nav class="level-links" aria-label="Character sets"><span>Start from:</span>' + "".join(links)
                  + '<a href="/chinese-character-worksheets/">Any characters</a></nav>')
    body = worksheet_page(
        (tpl / "worksheet_body.html").read_text(encoding="utf-8"), pages, WS_URL,
        eyebrow="New HSK · 2025 syllabus", chips=["Level 4", f"{total} characters"],
        h1="HSK 4 Character Worksheets",
        lede=f"Printable writing practice for the {total} characters that are new in the HSK 4 words of the HSK 3.0 syllabus "
             "(characters already used in HSK 1–3 are not repeated), with stroke order, pinyin and tracing boxes. "
             "Print the whole level, or 30 characters at a time.",
        chars="".join(chars), preset=0, range_html=range_html, sheet_title="HSK 4 characters",
        chartable=chartable, about_title="About these characters",
        prose=["The HSK 3.0 syllabus lists words, not single characters. This page takes every character in the HSK 4 words "
               "that does not appear in any HSK 1–3 word, and lists it once, in the order it first appears in the word list.",
               f'Use these sheets alongside the <a href="{URL}">HSK 4 word list</a>.'],
        links=links_html,
    )
    (root / WS_URL.strip("/")).mkdir(exist_ok=True)
    (root / WS_URL.strip("/") / "index.html").write_text(render(
        "HSK 4 Character Worksheets: Printable Stroke Order Practice (HSK 3.0)",
        f"Free printable writing worksheets for the {total} new characters of HSK 4 in the HSK 3.0 syllabus, "
        "with stroke order, pinyin, tracing and tian grid boxes.",
        site + WS_URL, base_css + (tpl / "worksheet.css").read_text(encoding="utf-8"), body), encoding="utf-8")
    urls.append(WS_URL)
    return urls


# Thai ------------------------------------------------------------------------------------------------------------

TH_URL = "/th/hsk-4-word-list/"
TH_WS_URL = "/th/hsk-4-character-worksheets/"
TH_LEDE = ("คำศัพท์ใหม่ของ HSK 4 ทั้ง 1,000 คำ ตามหลักสูตร HSK 3.0 (HSK ใหม่) พร้อมพินอินและความหมายภาษาไทย "
           "รวมกับ HSK 1–3 เป็น 2,000 คำ ค้นหาได้ด้วยตัวอักษรจีน พินอิน หรือภาษาไทย")
TH_PROSE = [
    "HSK 4 เพิ่มคำศัพท์เป็นสองเท่าอีกครั้ง คือเพิ่มอีก 1,000 คำ รวมเป็น 2,000 คำ ระดับนี้ผู้เรียนก้าวจากภาษาจีนในชีวิตประจำวัน "
    "ไปสู่การทำงาน การเรียน และการเข้าสังคม เช่น การสมัครงาน การพูดถึงข่าว แผนการเดินทาง ความรู้สึก และความคิดเห็น",
    "คำศัพท์ HSK 4 หลายคำประกอบจากตัวอักษรที่คุณรู้อยู่แล้ว เช่น <span class=\"zh-inline\">网友</span> (เพื่อนออนไลน์) "
    "จาก <span class=\"zh-inline\">网</span> และ <span class=\"zh-inline\">友</span> ส่วนคำสมัยใหม่อย่าง "
    "<span class=\"zh-inline\">扫码</span> (สแกนคิวอาร์โค้ด) <span class=\"zh-inline\">线上</span> (ออนไลน์) และ "
    "<span class=\"zh-inline\">动车</span> (รถไฟความเร็วสูง) เป็นคำใหม่ในหลักสูตรปี 2025",
    "หลักสูตรระบุ <span class=\"zh-inline\">重</span> <span class=\"zh-inline\">空</span> และ "
    "<span class=\"zh-inline\">生</span> ไว้สองครั้งตามเสียงอ่านหรือการใช้งาน หน้านี้แสดงแต่ละคำเพียงครั้งเดียว "
    "ตารางจึงมี 997 แถวสำหรับ 1,000 รายการในหลักสูตร",
]


def read_thai(root, rows):
    """Thai meanings from data/th/hsk4_th.tsv (word<TAB>Thai), in the order of data/hsk4.tsv.

    The file may be incomplete while it is being written in batches: it must then be an exact prefix of the word list,
    and the Thai pages are only built once every word has a meaning. Returns the list of meanings or None."""
    path = root / "data" / "th" / "hsk4_th.tsv"
    if not path.exists():
        return None
    th = []
    for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if line.strip():
            parts = [p.strip() for p in line.split("\t")]
            if len(parts) != 2 or not parts[1]:
                raise SystemExit(f"data/th/hsk4_th.tsv line {i}: expected word<TAB>Thai meaning")
            th.append(parts)
    words = [r[0] for r in rows]
    if [w for w, _ in th] != words[:len(th)]:
        bad = next(i for i, (w, _) in enumerate(th) if i >= len(words) or w != words[i])
        raise SystemExit(f"data/th/hsk4_th.tsv line {bad + 1}: {th[bad][0]} is out of order; expected "
                         f"{words[bad] if bad < len(words) else 'end of file'}")
    return [m for _, m in th] if len(th) == len(words) else None


def th_alternates(root):
    if not (root / "data" / "hsk4.tsv").exists():
        return {}
    _, rows = read(root)
    if read_thai(root, rows) is None:
        return {}
    return {URL: TH_URL, WS_URL: TH_WS_URL}


def build_th(*, root, tpl, site, render, nav, font_link, foot, wl_css, ws_css, search_key, thai_key, lower_words):
    import worksheets_th
    if not (root / "data" / "hsk4.tsv").exists():
        return []
    _, rows = read(root)
    thai = read_thai(root, rows)
    if thai is None:
        return []
    urls = []
    body = (tpl / "th" / "wordlist_body.html").read_text(encoding="utf-8")
    swaps = [
        ('<h2 id="cta-title">ตรวจข้อความเทียบกับ HSK __LEVEL__</h2>', '<h2 id="cta-title">ฝึกเขียนตัวอักษร HSK __LEVEL__</h2>'),
        ('<a class="button" href="/th/#hsk__LEVEL__">เปิดเครื่องมือตรวจระดับ</a><a class="button ghost" href="/th/hsk-__LEVEL__-character-worksheets/">แบบฝึกเขียนตัวอักษร</a>',
         '<a class="button" href="/th/hsk-__LEVEL__-character-worksheets/">แบบฝึกเขียนตัวอักษร</a><a class="button ghost" href="/th/hsk-3-word-list/">คำศัพท์ HSK 3</a>'),
        ("และตรวจทานกับสำเนารายการที่เผยแพร่อย่างอิสระอีกสองแหล่ง", "และตรวจทานกับสำเนารายการที่เผยแพร่อย่างอิสระอีกหนึ่งแหล่ง"),
    ]
    for a, b in swaps:
        if body.count(a) != 1:
            raise SystemExit(f"hsk4 (th): template text not found: {a[:50]}")
        body = body.replace(a, b)
    import re
    body = re.sub(r'(<h2 id="cta-title">.*?</h2>\s*<p class="lede">).*?(</p>)',
                  r"\1พิมพ์แบบฝึกคัดตัวอักษรจีนสำหรับตัวอักษรใหม่ของ HSK 4 ได้ฟรี มีลำดับขีด พินอิน และช่องให้เขียนตาม\2",
                  body, count=1, flags=re.S)
    trs = []
    for i, ((word, pinyin, en), th) in enumerate(zip(rows, thai), 1):
        key = html.escape(search_key(word, pinyin, en) + "|" + thai_key(th), quote=True)
        trs.append(f'          <tr data-k="{key}"><td class="n">{i}</td><td class="hz">{html.escape(word)}</td>'
                   f'<td class="py">{html.escape(pinyin)}</td><td class="en">{html.escape(th)}</td></tr>')
    body = (body.replace("__NAV__", nav(TH_URL)).replace("__ROWS__", "\n".join(trs))
            .replace("__PROSE__", "\n".join(f"    <p>{p}</p>" for p in TH_PROSE)).replace("__LEDE__", TH_LEDE)
            .replace("__ROWCOUNT__", str(len(rows))).replace("__COUNT__", str(OFFICIAL)).replace("__LEVEL__", "4"))
    target = root / TH_URL.strip("/")
    target.mkdir(parents=True, exist_ok=True)
    (target / "index.html").write_text(render(
        f"คำศัพท์ HSK 4 (HSK 3.0) {OFFICIAL} คำ พร้อมคำแปลภาษาไทย",
        f"คำศัพท์ HSK 4 ทั้ง {OFFICIAL:,} คำ ตามหลักสูตร HSK 3.0 (HSK ใหม่) ปี 2025 พร้อมพินอินและความหมายภาษาไทย ค้นหาได้ ฟรี",
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
        chips=["ระดับ 4", f"{total} ตัว"], h1="แบบฝึกเขียนตัวอักษร HSK 4",
        lede=f"แบบฝึกเขียนตัวอักษรใหม่ของ HSK 4 (ไม่ซ้ำกับ HSK 1–3) ทั้ง {total} ตัว มีลำดับขีด พินอิน และช่องให้เขียนตาม "
             "พิมพ์ได้ทั้งระดับหรือครั้งละ 30 ตัว",
        links=worksheets_th.links_html(TH_WS_URL, [1, 2, 3, 4]), chars="".join(chars), preset=0,
        range_html=worksheets_th.range_select(total), sheet_title="ตัวอักษร HSK 4",
        chartable=worksheets_th.char_table(f"ตัวอักษรใหม่ทั้งหมด {total} ตัวในคำศัพท์ HSK 4", trs),
        about_title="เกี่ยวกับตัวอักษรชุดนี้",
        prose=["หลักสูตร HSK 3.0 กำหนดเป็นคำศัพท์ ไม่ใช่ตัวอักษรเดี่ยว หน้านี้นำตัวอักษรทุกตัวในคำศัพท์ HSK 4 ที่ไม่เคยปรากฏในคำศัพท์ "
               "HSK 1–3 มาแสดงตัวละครั้งเดียว ตามลำดับที่ปรากฏครั้งแรกในรายการคำศัพท์",
               f'ใช้แบบฝึกนี้คู่กับ<a href="{TH_URL}">คำศัพท์ HSK 4</a>'],
    )
    target = root / TH_WS_URL.strip("/")
    target.mkdir(parents=True, exist_ok=True)
    (target / "index.html").write_text(render(
        "แบบฝึกเขียนตัวอักษรจีน HSK 4 พิมพ์ได้ฟรี พร้อมลำดับขีด",
        f"แบบฝึกคัดตัวอักษรจีน HSK 4 ({total} ตัว) ตามหลักสูตร HSK 3.0 พิมพ์ได้ฟรี มีลำดับขีด พินอิน ตัวจาง ๆ ให้เขียนตาม และตาราง 田",
        site + TH_WS_URL, ws_css, body, font_link, lang="th", foot=foot), encoding="utf-8")
    urls.append(TH_WS_URL)
    return urls
