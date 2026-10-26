"""Thai versions of the character worksheet pages.

Outputs:
  th/chinese-character-worksheets/              the worksheet maker in Thai
  th/hsk-N-character-worksheets/                preset to the characters of HSK N (needs strokes/hskN.json)
  th/yct/yct-N-character-worksheets/            preset to the characters new at YCT N

The Thai page is the English template (templates/worksheet_body.html) with its interface text swapped for
Thai, so the two never drift apart: the build stops if an English string to be replaced is not found.

Called from tools/build_th.py; returns the URLs it wrote.
"""
import html
import json
import pathlib

import yct

TH_WS_URL = "/th/chinese-character-worksheets/"
_ROOT = pathlib.Path(__file__).resolve().parent.parent

# English text in templates/worksheet_body.html -> Thai. Every key must occur in the template.
UI = [
    ('aria-label="Worksheet settings"', 'aria-label="ตั้งค่าแบบฝึกเขียน"'),
    ('<label for="chars">Characters</label>', '<label for="chars">ตัวอักษร</label>'),
    ("Type or paste any Chinese text. Each character is used once, in order.",
     "พิมพ์หรือวางข้อความภาษาจีนอะไรก็ได้ ตัวอักษรแต่ละตัวจะใช้เพียงครั้งเดียวตามลำดับ"),
    ("<legend>Grid</legend>", "<legend>ตาราง</legend>"),
    ("<span>田 Tian</span>", "<span>田 เทียน</span>"),
    ("<span>米 Mi</span>", "<span>米 หมี่</span>"),
    ("<span>Plain</span>", "<span>ช่องเปล่า</span>"),
    ("<legend>Tracing</legend>", "<legend>ตัวจาง ๆ ให้เขียนตาม</legend>"),
    ("<span>None</span>", "<span>ไม่มี</span>"),
    ("<span>Full row</span>", "<span>ทั้งแถว</span>"),
    ("<legend>Rows per character</legend>", "<legend>จำนวนแถวต่อตัวอักษร</legend>"),
    ("<legend>Show</legend>", "<legend>แสดง</legend>"),
    ("checked> Stroke order</label>", "checked> ลำดับขีด</label>"),
    ("checked> Pinyin</label>", "checked> พินอิน</label>"),
    (">Print or save as PDF</button>", ">พิมพ์หรือบันทึกเป็น PDF</button>"),
    ('href="/chinese-character-tracing/" data-base="/chinese-character-tracing/">Trace them on screen</a>',
     'href="/th/chinese-character-tracing/" data-base="/th/chinese-character-tracing/">ฝึกเขียนตามรอยบนจอ</a>'),
    ('aria-label="Worksheet preview"', 'aria-label="ตัวอย่างแบบฝึกเขียน"'),
    ("Name ______________________ &nbsp; Date ____________", "ชื่อ ______________________ &nbsp; วันที่ ____________"),
    ("Free worksheets and the HSK level checker at hskcheck.com", "แบบฝึกเขียนตัวอักษรจีนฟรีที่ hskcheck.com/th/"),
    ("<p><b>Printing.</b> Use your browser's print dialog to print or to save the sheet as a PDF. "
     "Choose A4 or US Letter; the grid is sized to fit both.</p>",
     "<p><b>การพิมพ์</b> ใช้หน้าต่างพิมพ์ของเบราว์เซอร์เพื่อพิมพ์ หรือบันทึกเป็นไฟล์ PDF เลือกกระดาษ A4 หรือ US Letter "
     "ก็ได้ ตารางมีขนาดพอดีทั้งสองแบบ</p>"),
    ("<p><b>Stroke data.</b> Stroke outlines and pinyin come from",
     "<p><b>ข้อมูลลำดับขีด</b> รูปขีดและพินอินมาจาก"),
    ("(Arphic Public License and GNU LGPL, see <a href=\"/strokes/LICENSE.md\">licence</a>). "
     "Stroke order follows mainland China standards for simplified characters.</p>",
     "(Arphic Public License และ GNU LGPL ดู<a href=\"/strokes/LICENSE.md\" hreflang=\"en\">สัญญาอนุญาต</a>) "
     "ลำดับขีดเป็นไปตามมาตรฐานตัวอักษรจีนตัวย่อของจีนแผ่นดินใหญ่</p>"),
    ('n + (n === 1 ? " stroke" : " strokes")', 'n + " ขีด"'),
    ('status.textContent = chars.length ? "Loading…" : "";', 'status.textContent = chars.length ? "กำลังโหลด…" : "";'),
    ('"Could not load stroke data. Check your connection and try again."',
     '"โหลดข้อมูลลำดับขีดไม่สำเร็จ ตรวจสอบอินเทอร์เน็ตแล้วลองใหม่อีกครั้ง"'),
    ('ok.length + (ok.length === 1 ? " character" : " characters")', 'ok.length + " ตัว"'),
    ('"no stroke data for "', '"ไม่มีข้อมูลลำดับขีดของ "'),
    ('"Type some Chinese characters above."', '"พิมพ์ตัวอักษรจีนในช่องด้านบน"'),
]


def thai_template(tpl):
    body = (tpl / "worksheet_body.html").read_text(encoding="utf-8")
    for en, th in UI:
        if en not in body:
            raise SystemExit(f"worksheets_th: English text not found in templates/worksheet_body.html: {en[:60]}")
        body = body.replace(en, th)
    return body


def fill(body, *, nav, eyebrow, chips, h1, lede, links, chars, preset, range_html, sheet_title, chartable,
         about_title, prose):
    for key, value in (
        ("__NAV__", nav),
        ("__EYEBROW__", eyebrow),
        ("__CHIPS__", "".join(f'<span class="chip">{c}</span>' for c in chips)),
        ("__H1__", h1),
        ("__LEDE__", lede),
        ("__LEVEL_LINKS__", links),
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


def range_select(total):
    options = [f'<option value="all">ทั้งหมด {total} ตัว</option>']
    for a in range(1, total + 1, 30):
        b = min(a + 29, total)
        options.append(f'<option value="{a}-{b}">ตัวที่ {a}–{b}</option>')
    return ('<div class="field"><label for="range">ตัวอักษรที่จะพิมพ์</label>'
            f'<select id="range">{"".join(options)}</select></div>')


def char_table(title, rows):
    return (f'  <section class="sheet char-table no-print" aria-labelledby="chars-title">\n'
            f'    <h2 id="chars-title">{title}</h2>\n'
            f'    <div class="table-wrap"><table><thead><tr><th scope="col">#</th><th scope="col">ตัวอักษร</th>'
            f'<th scope="col">คำแรกในรายการ</th></tr></thead><tbody>\n'
            + "\n".join(rows) + "\n    </tbody></table></div>\n  </section>")


def word_cell(word, pinyin, th):
    return (f'<span class="zh-inline">{html.escape(word)}</span> {html.escape(pinyin)} '
            f'<small>{html.escape(th)}</small>')


def links_html(current, hsk_levels):
    items = [(f"/th/hsk-{n}-character-worksheets/", f"HSK {n}") for n in hsk_levels]
    if 4 not in hsk_levels and (_ROOT / "data" / "th" / "hsk4_th.tsv").exists():
        import hsk4
        if hsk4.th_alternates(_ROOT):
            items.append((hsk4.TH_WS_URL, "HSK 4"))
    if 5 not in hsk_levels and (_ROOT / "data" / "th" / "hsk5_th.tsv").exists():
        import hsk5
        if hsk5.th_alternates(_ROOT):
            items.append((hsk5.TH_WS_URL, "HSK 5"))
    items += [(f"{yct.TH_YCT_URL}yct-{n}-character-worksheets/", f"YCT {n}") for n in yct.LEVELS]
    items.append((TH_WS_URL, "ตัวอักษรอะไรก็ได้"))
    out = []
    for url, label in items:
        cur = ' aria-current="page"' if url == current else ""
        out.append(f'<a href="{url}"{cur}>{label}</a>')
    return '<nav class="level-links" aria-label="ชุดตัวอักษร"><span>เริ่มจาก:</span>' + "".join(out) + "</nav>"


def alternates(root, hsk_levels):
    pairs = {"/chinese-character-worksheets/": TH_WS_URL}
    pairs.update({f"/hsk-{n}-character-worksheets/": f"/th/hsk-{n}-character-worksheets/" for n in hsk_levels
                  if (root / "strokes" / f"hsk{n}.json").exists()})
    pairs.update({f"{yct.YCT_URL}yct-{n}-character-worksheets/": f"{yct.TH_YCT_URL}yct-{n}-character-worksheets/"
                  for n in yct.LEVELS})
    return pairs


def build(*, root, tpl, site, css, render, nav, font_link, foot, word_lists, meanings):
    """word_lists: HSK level -> [(word, pinyin, English)]; meanings: HSK level -> [Thai meaning] in the same order."""
    body_tpl = thai_template(tpl)
    hsk_levels = [n for n in sorted(word_lists) if n in meanings and (root / "strokes" / f"hsk{n}.json").exists()]
    urls = []

    def write(url, title, description, body):
        target = root / url.strip("/")
        target.mkdir(parents=True, exist_ok=True)
        (target / "index.html").write_text(render(title, description, site + url, css, body, font_link,
                                                  lang="th", foot=foot), encoding="utf-8")
        urls.append(url)

    # The maker
    body = fill(
        body_tpl, nav=nav(TH_WS_URL), eyebrow="ฟรี · พิมพ์ได้", chips=[],
        h1='<span class="zh">字帖</span>สร้างแบบฝึกคัดตัวอักษรจีน',
        lede="สร้างแบบฝึกเขียนตัวอักษรจีนที่พิมพ์ได้ สำหรับตัวอักษรอะไรก็ได้ มีลำดับขีด ตัวอย่าง ตัวจาง ๆ ให้เขียนตาม "
             "และช่องว่างให้ฝึกเขียนบนตาราง 田 หรือ 米 หรือเริ่มจากตัวอักษรของ HSK หรือ YCT แต่ละระดับ",
        links=links_html(TH_WS_URL, hsk_levels), chars="你好我爱学中文", preset=0, range_html="",
        sheet_title="ฝึกเขียนภาษาจีน", chartable="", about_title="วิธีใช้แบบฝึกเขียน",
        prose=[
            "เริ่มแต่ละตัวจากแถบลำดับขีด ขีดล่าสุดเป็นสีดำ ขีดก่อนหน้าเป็นสีเทา จากนั้นเขียนทับตัวจาง ๆ สีเทา "
            "แล้วเขียนในช่องว่างด้วยตัวเองโดยไม่ต้องดู",
            "ตาราง 田 (เทียน) แบ่งแต่ละช่องเป็นสี่ส่วน ส่วนตาราง 米 (หมี่) เพิ่มเส้นทแยงมุม "
            "ทั้งสองแบบช่วยให้วางแต่ละส่วนของตัวอักษรได้ถูกตำแหน่ง ซึ่งสำคัญกว่าความเร็วสำหรับผู้เริ่มต้น",
            "เขียนตัวอักษรเดิมไม่กี่ครั้งแต่หลายวัน ได้ผลดีกว่าเขียนเต็มหน้าในครั้งเดียว "
            "พิมพ์ตัวละหนึ่งหรือสองแถว แล้วกลับมาฝึกแผ่นเดิมอีกครั้งในสัปดาห์เดียวกัน",
        ],
    )
    write(TH_WS_URL, "สร้างแบบฝึกคัดตัวอักษรจีน พิมพ์ได้ฟรี (ตาราง 田)",
          "สร้างแบบฝึกคัดตัวอักษรจีนที่พิมพ์ได้ฟรี มีลำดับขีด พินอิน ตัวจาง ๆ ให้เขียนตาม และตาราง 田 หรือ 米 "
          "พิมพ์ตัวอักษรเองหรือเริ่มจาก HSK และ YCT", body)

    # HSK presets
    for n in hsk_levels:
        url = f"/th/hsk-{n}-character-worksheets/"
        chars = json.loads((root / "strokes" / f"hsk{n}.json").read_text(encoding="utf-8"))
        order = list(chars)
        entries = list(zip(word_lists[n], meanings[n]))
        rows = []
        for i, c in enumerate(order, 1):
            first = next((e for e in entries if c in e[0][0]), None)
            cellw = word_cell(first[0][0], first[0][1], first[1]) if first else ""
            rows.append(f'<tr><td class="n">{i}</td><td class="hz">{html.escape(c)}</td><td class="w">{cellw}</td></tr>')
        total = len(order)
        new_note = "ตัวอักษรของ HSK 1" if n == 1 else f"ตัวอักษรใหม่ของ HSK {n} (ไม่ซ้ำกับระดับที่ต่ำกว่า)"
        prose = [
            f"หลักสูตร HSK 3.0 กำหนดเป็นคำศัพท์ ไม่ใช่ตัวอักษรเดี่ยว หน้านี้นำตัวอักษรทุกตัวที่อยู่ในคำศัพท์ HSK {n} "
            "มาแสดงตัวละครั้งเดียว ตามลำดับที่ปรากฏครั้งแรกในรายการคำศัพท์",
        ]
        if n > 1:
            prose.append("ตัวอักษรที่เคยใช้ในระดับที่ต่ำกว่าจะไม่ถูกนับซ้ำ ทั้งสามหน้าจึงครอบคลุมตัวอักษรในคำศัพท์ HSK 1–3 "
                         "ครบโดยไม่ซ้ำกัน")
        prose.append("หลักสูตร HSK 3.0 มีรายการตัวอักษรของตัวเองด้วย ซึ่งอาจต่างจากชุดนี้เล็กน้อย ใช้แบบฝึกนี้คู่กับ"
                     f'<a href="/th/hsk-{n}-word-list/">คำศัพท์ HSK {n}</a> ที่คุณกำลังเรียน')
        body = fill(
            body_tpl, nav=nav(TH_WS_URL), eyebrow="HSK ใหม่ · หลักสูตรปี 2025", chips=[f"ระดับ {n}", f"{total} ตัว"],
            h1=f"แบบฝึกเขียนตัวอักษร HSK {n}",
            lede=f"แบบฝึกเขียน{new_note} ทั้ง {total} ตัว มีลำดับขีด พินอิน และช่องให้เขียนตาม "
                 "พิมพ์ได้ทั้งระดับหรือครั้งละ 30 ตัว",
            links=links_html(url, hsk_levels), chars="".join(order), preset=n, range_html=range_select(total),
            sheet_title=f"ตัวอักษร HSK {n}",
            chartable=char_table(f"ตัวอักษรทั้งหมด {total} ตัวในคำศัพท์ HSK {n}", rows),
            about_title="เกี่ยวกับตัวอักษรชุดนี้", prose=prose,
        )
        write(url, f"แบบฝึกเขียนตัวอักษรจีน HSK {n} พิมพ์ได้ฟรี พร้อมลำดับขีด",
              f"แบบฝึกคัดตัวอักษรจีน HSK {n} ({total} ตัว) ตามหลักสูตร HSK 3.0 พิมพ์ได้ฟรี มีลำดับขีด พินอิน "
              "ตัวจาง ๆ ให้เขียนตาม และตาราง 田", body)

    # YCT presets
    levels = {n: yct.read_level(root, n) for n in yct.LEVELS}
    seen = set()
    for n in yct.LEVELS:
        url = f"{yct.TH_YCT_URL}yct-{n}-character-worksheets/"
        thai = yct.read_thai(root, n, levels[n])
        entries = list(zip(levels[n], thai))
        order = []
        for (w, _, _), _ in entries:
            for c in yct.hanzi(w):
                if c not in seen:
                    seen.add(c)
                    order.append(c)
        rows = []
        for i, c in enumerate(order, 1):
            (w, p, _), th = next(e for e in entries if c in e[0][0])
            rows.append(f'<tr><td class="n">{i}</td><td class="hz">{html.escape(c)}</td>'
                        f'<td class="w">{word_cell(w, p, th)}</td></tr>')
        total = len(order)
        new_note = "ตัวอักษรในคำศัพท์ YCT 1" if n == 1 else f"ตัวอักษรใหม่ของ YCT {n} (ไม่ซ้ำกับระดับที่ต่ำกว่า)"
        prose = [
            f"หลักสูตร YCT กำหนดเป็นคำศัพท์ ไม่ใช่ตัวอักษรเดี่ยว หน้านี้นำตัวอักษรทุกตัวในคำศัพท์ YCT {n} "
            "มาแสดงตัวละครั้งเดียว ตามลำดับที่ปรากฏครั้งแรกในรายการคำศัพท์",
        ]
        if n > 1:
            prose.append("ตัวอักษรที่เคยใช้ใน YCT ระดับที่ต่ำกว่าจะไม่ถูกนับซ้ำ ทั้งสี่หน้าจึงครอบคลุมตัวอักษรในคำศัพท์ "
                         "YCT 1–4 ครบโดยไม่ซ้ำกัน")
        prose.append("สำหรับเด็ก ฝึกวันละนิดได้ผลดีที่สุด ตัวละหนึ่งหรือสองแถว แล้วกลับมาฝึกแผ่นเดิมอีกครั้งในสัปดาห์เดียวกัน "
                     f'ใช้คู่กับ<a href="{yct.TH_YCT_URL}yct-{n}-word-list/">คำศัพท์ YCT {n}</a>')
        body = fill(
            body_tpl, nav=nav(yct.TH_YCT_URL), eyebrow="YCT · การสอบภาษาจีนสำหรับนักเรียน",
            chips=[f"ระดับ {n}", f"{total} ตัว"], h1=f"แบบฝึกเขียนตัวอักษร YCT {n}",
            lede=f"แบบฝึกเขียน{new_note} ทั้ง {total} ตัว มีลำดับขีด พินอิน และช่องให้เขียนตาม "
                 "พิมพ์ได้ทั้งระดับหรือครั้งละ 30 ตัว เหมาะสำหรับครูและผู้ปกครอง",
            links=links_html(url, hsk_levels), chars="".join(order), preset=0, range_html=range_select(total),
            sheet_title=f"ตัวอักษร YCT {n}",
            chartable=char_table(f"ตัวอักษรใหม่ทั้งหมด {total} ตัวของ YCT {n}", rows),
            about_title="เกี่ยวกับตัวอักษรชุดนี้", prose=prose,
        )
        write(url, f"แบบฝึกเขียนตัวอักษรจีน YCT {n} พิมพ์ได้ฟรี พร้อมลำดับขีด",
              f"แบบฝึกคัดตัวอักษรจีน YCT ระดับ {n} ({total} ตัว) พิมพ์ได้ฟรี มีลำดับขีด พินอิน ตัวจาง ๆ ให้เขียนตาม "
              "และตาราง 田 สำหรับนักเรียน ครู และผู้ปกครอง", body)
    return urls
