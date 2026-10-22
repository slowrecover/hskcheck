"""Thai-language pages at /th/, built from data/th/ and templates/th/.

Outputs:
  th/index.html                    the level checker in Thai, with Thai meanings for words above the level
  th/hsk-N-word-list/index.html    one page per level that has data/th/hskN_th.tsv
  th/learn/...                     Thai grammar explainers and worksheets (see tools/learn_th.py)
  th/yct/...                       Thai YCT word lists (see tools/yct.py)
  th/...-character-worksheets/     Thai worksheet maker and presets (see tools/worksheets_th.py)
  th/chinese-measure-words/        Thai measure word finder (see tools/measure_th.py)
  th/old-hsk-to-new-hsk/           Thai old HSK -> new HSK page (see tools/upgrade_th.py)

data/th/hskN_th.tsv has two columns, word and Thai meaning, in the same order as data/hskN.tsv.
The build stops if the words do not match exactly.

Called from tools/build.py; returns the URLs it wrote so they go into sitemap.xml.
"""
import html
import json

import learn_th
import measure_th
import upgrade_th
import worksheets_th
import yct

TH_URL = "/th/"

LEVEL_COPY = {
    1: {
        "lede": "คำศัพท์ HSK 1 ทั้ง 300 คำ ตามหลักสูตร HSK 3.0 (HSK ใหม่) พร้อมพินอินและความหมายภาษาไทย "
                "ค้นหาได้ด้วยตัวอักษรจีน พินอิน หรือภาษาไทย",
        "prose": [
            "HSK 1 เป็นระดับแรกจากทั้งหมด 9 ระดับของ HSK 3.0 คำศัพท์ 300 คำครอบคลุมตัวเลข ครอบครัว เวลา อาหาร สถานที่ "
            "และคำกริยาที่ใช้บ่อยที่สุด เพียงพอสำหรับบทสนทนาสั้น ๆ ในชีวิตประจำวัน",
            "ระดับถัดไปต่อยอดจากรายการนี้: HSK 2 เพิ่มอีก 200 คำ รวมเป็น 500 คำ และ HSK 3 เพิ่มอีก 500 คำ รวมเป็น 1,000 คำ",
            "บางคำมักถูกมองข้าม เพราะหลักสูตรกำหนดเป็นคำ ไม่ใช่ตัวอักษร <span class=\"zh-inline\">杯子</span> (แก้ว) อยู่ในรายการ "
            "แต่ลักษณนาม <span class=\"zh-inline\">杯</span> ไม่อยู่ ดังนั้น <span class=\"zh-inline\">一杯茶</span> จึงเกินระดับ HSK 1",
        ],
    },
    2: {
        "lede": "คำศัพท์ใหม่ของ HSK 2 ทั้ง 200 คำ ตามหลักสูตร HSK 3.0 (HSK ใหม่) พร้อมพินอินและความหมายภาษาไทย "
                "รวมกับ HSK 1 เป็น 500 คำ ค้นหาได้ด้วยตัวอักษรจีน พินอิน หรือภาษาไทย",
        "prose": [
            "HSK 2 เพิ่มคำศัพท์ 200 คำต่อจาก 300 คำของ HSK 1 ครอบคลุมทิศทาง การเดินทาง การซื้อของ สภาพอากาศ สุขภาพ "
            "และความรู้สึกง่าย ๆ รวมถึงคำเชื่อมอย่าง <span class=\"zh-inline\">因为</span> <span class=\"zh-inline\">所以</span> "
            "และ <span class=\"zh-inline\">虽然</span>",
            "หลักสูตรระบุ <span class=\"zh-inline\">过</span> และ <span class=\"zh-inline\">花</span> ไว้สองครั้งตามการใช้งานหลัก "
            "หน้านี้แสดงแต่ละคำเพียงครั้งเดียวพร้อมทั้งสองความหมาย ตารางจึงมี 198 แถว",
            "ตัวอักษรบางตัวจาก HSK 1 กลับมาในคำใหม่หรือการใช้แบบใหม่ เช่น <span class=\"zh-inline\">点</span> ในความหมาย "
            "สั่งอาหาร และคำช่วย <span class=\"zh-inline\">得</span> กับ <span class=\"zh-inline\">地</span>",
        ],
    },
    3: {
        "lede": "คำศัพท์ใหม่ของ HSK 3 ทั้ง 500 คำ ตามหลักสูตร HSK 3.0 (HSK ใหม่) พร้อมพินอินและความหมายภาษาไทย "
                "รวมกับ HSK 1 และ 2 เป็น 1,000 คำ ค้นหาได้ด้วยตัวอักษรจีน พินอิน หรือภาษาไทย",
        "prose": [
            "HSK 3 เพิ่มคำศัพท์เป็นสองเท่า คือเพิ่มอีก 500 คำ รวมเป็น 1,000 คำ ระดับนี้ผู้เรียนเริ่มพูดเรื่องในชีวิตประจำวันได้ลึกขึ้น "
            "เช่น การเรียนและการทำงาน การเดินทาง สุขภาพ สภาพอากาศและฤดูกาล รวมถึงความคิดเห็นของตัวเอง",
            "ตัวอักษรที่คุ้นเคยหลายตัวกลับมาพร้อมเสียงอ่านหรือความหมายใหม่ <span class=\"zh-inline\">还</span> อ่านว่า huán (คืน) "
            "<span class=\"zh-inline\">长</span> อ่านว่า zhǎng (เติบโต) และ <span class=\"zh-inline\">只</span> อ่านว่า zhī "
            "เป็นลักษณนามของสัตว์",
            "หลักสูตรระบุ <span class=\"zh-inline\">得</span> ไว้สองครั้ง คือ dé (ได้รับ) และ děi (ต้อง) "
            "หน้านี้แสดงเพียงครั้งเดียวพร้อมทั้งสองเสียงอ่าน ตารางจึงมี 499 แถว",
        ],
    },
}

FONT_LINK = ('<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+Thai:wght@400;500;600'
             '&display=swap">')
FOOT = '\n<footer class="site-foot">hskcheck.com · <a href="/privacy/" hreflang="en">นโยบายความเป็นส่วนตัว</a></footer>'


def read_meanings(root, n, entries):
    """Thai meanings for level n, checked against the word order in data/hskN.tsv."""
    path = root / "data" / "th" / f"hsk{n}_th.tsv"
    if not path.exists():
        return None
    rows = []
    for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        parts = line.split("\t")
        if len(parts) != 2 or not parts[1].strip():
            raise SystemExit(f"th/hsk{n}_th.tsv line {i}: expected word<TAB>Thai meaning")
        rows.append((parts[0].strip(), parts[1].strip()))
    got = [w for w, _ in rows]
    expected = [e[0] for e in entries]
    if got != expected:
        missing = [w for w in expected if w not in got]
        extra = [w for w in got if w not in expected]
        raise SystemExit(f"th/hsk{n}_th.tsv does not match hsk{n}.tsv; missing={missing} extra={extra}")
    return [m for _, m in rows]


def thai_key(text):
    """Thai is matched as typed: lowercased, spaces removed (mirrors the page's search normaliser for Thai)."""
    return "".join(text.lower().split())


def available_levels(root, levels):
    return [n for n in levels if (root / "data" / "th" / f"hsk{n}_th.tsv").exists()]


def build(*, root, tpl, site, base_css, render, word_lists, level_table, search_key, read_words, measure=None):
    """Write the Thai pages. Returns the URLs written."""
    levels = [n for n in available_levels(root, sorted(word_lists)) if n in word_lists]
    if not levels:
        return []
    meanings = {n: read_meanings(root, n, word_lists[n]) for n in levels}

    pages = [(TH_URL, "ตรวจระดับคำศัพท์")]
    pages += [(f"{TH_URL}hsk-{n}-word-list/", f"คำศัพท์ HSK {n}") for n in levels]
    pages.append((worksheets_th.TH_WS_URL, "แบบฝึกเขียน"))
    if measure and measure_th.available(root):
        pages.append((measure_th.TH_MW_URL, "ลักษณนาม"))
    if (root / "old-hsk-to-new-hsk" / "words.json").exists():
        pages.append((upgrade_th.TH_UP_URL, "HSK เก่า → ใหม่"))
    if learn_th.slugs(root):
        pages.append((learn_th.TH_LEARN_URL, "ไวยากรณ์"))
    if yct.has_thai(root):
        pages.append((yct.TH_YCT_URL, "YCT"))
    pages.append(("/", "English"))

    def nav(current):
        links = []
        for url, label in pages:
            cur = ' aria-current="page"' if url == current else ""
            lang = ' hreflang="en" lang="en"' if url == "/" else ""
            links.append(f'<a href="{url}"{cur}{lang}>{label}</a>')
        return '<nav class="site-nav" aria-label="เมนูเว็บไซต์">' + "".join(links) + "</nav>"

    th_css = (tpl / "th" / "th.css").read_text(encoding="utf-8")
    urls = []

    # Level checker
    word_th = {}
    for n in levels:
        for (word, _, _), m in zip(word_lists[n], meanings[n]):
            word_th.setdefault(word, m)
    for w, m in list(word_th.items()):
        if len(w) >= 3 and w.endswith("儿"):
            word_th.setdefault(w[:-1], m)
    ld = json.dumps({
        "@context": "https://schema.org", "@type": "WebApplication", "name": "ตรวจคำศัพท์เกินระดับ HSK 3.0",
        "url": site + TH_URL, "inLanguage": "th", "applicationCategory": "EducationalApplication", "operatingSystem": "Any",
        "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"},
        "description": "วางข้อความภาษาจีนแล้วดูว่าคำไหนเกินระดับ HSK 3.0 ของคุณ พร้อมคำแปลภาษาไทย",
    }, ensure_ascii=False)
    body = (tpl / "th" / "checker_body.html").read_text(encoding="utf-8")
    body = (body.replace("__NAV__", nav(TH_URL))
            .replace("__LEVELS_JSON__", json.dumps(level_table(), ensure_ascii=False, separators=(",", ":")))
            .replace("__MEANINGS_JSON__", json.dumps(word_th, ensure_ascii=False, separators=(",", ":"))))
    out = render(
        "ตรวจคำศัพท์เกินระดับ HSK 3.0 (超纲词) พร้อมคำแปลไทย ฟรี",
        "วางข้อความภาษาจีนแล้วรู้ทันทีว่าคำไหนเกินระดับ HSK 3.0 ของคุณ พร้อมคำแปลภาษาไทย ฟรี ใช้งานในเบราว์เซอร์ ไม่ต้องสมัคร",
        site + TH_URL,
        base_css + (tpl / "checker.css").read_text(encoding="utf-8") + th_css,
        body,
        FONT_LINK + f'\n<script type="application/ld+json">{ld}</script>',
        lang="th", foot=FOOT,
    )
    (root / "th").mkdir(exist_ok=True)
    (root / "th" / "index.html").write_text(out, encoding="utf-8")
    urls.append(TH_URL)

    # Word list pages
    wl_body = (tpl / "th" / "wordlist_body.html").read_text(encoding="utf-8")
    wl_css = base_css + (tpl / "wordlist.css").read_text(encoding="utf-8") + th_css
    for n in levels:
        rows = []
        for i, ((word, pinyin, en), th) in enumerate(zip(word_lists[n], meanings[n]), 1):
            key = html.escape(search_key(word, pinyin, en) + "|" + thai_key(th), quote=True)
            rows.append(
                f'          <tr data-k="{key}"><td class="n">{i}</td><td class="hz">{html.escape(word)}</td>'
                f'<td class="py">{html.escape(pinyin)}</td><td class="en">{html.escape(th)}</td></tr>'
            )
        copy = LEVEL_COPY.get(n, {})
        official = len(read_words(n))
        url = f"{TH_URL}hsk-{n}-word-list/"
        body = (wl_body.replace("__NAV__", nav(url))
                .replace("__ROWS__", "\n".join(rows))
                .replace("__PROSE__", "\n".join(f"    <p>{p}</p>" for p in copy.get("prose", [])))
                .replace("__LEDE__", copy.get("lede", ""))
                .replace("__ROWCOUNT__", str(len(word_lists[n])))
                .replace("__COUNT__", str(official))
                .replace("__LEVEL__", str(n)))
        out = render(
            f"คำศัพท์ HSK {n} (HSK 3.0) {official} คำ พร้อมคำแปลภาษาไทย",
            f"คำศัพท์ HSK {n} ทั้ง {official} คำ ตามหลักสูตร HSK 3.0 (HSK ใหม่) พร้อมพินอินและความหมายภาษาไทย ค้นหาได้ ฟรี",
            site + url, wl_css, body, FONT_LINK, lang="th", foot=FOOT,
        )
        target = root / url.strip("/")
        target.mkdir(parents=True, exist_ok=True)
        (target / "index.html").write_text(out, encoding="utf-8")
        urls.append(url)

    # Character worksheets
    urls += worksheets_th.build(root=root, tpl=tpl, site=site, render=render, nav=nav, font_link=FONT_LINK, foot=FOOT,
                                css=base_css + (tpl / "worksheet.css").read_text(encoding="utf-8") + th_css,
                                word_lists=word_lists, meanings=meanings)

    # Measure words
    if measure:
        urls += measure_th.build(root=root, tpl=tpl, site=site, render=render, nav=nav, font_link=FONT_LINK, foot=FOOT,
                                 css=base_css + (tpl / "measure.css").read_text(encoding="utf-8") + th_css,
                                 level_table=level_table, search_key=search_key, thai_key=thai_key, **measure)

    # Old HSK -> new HSK
    urls += upgrade_th.build(root=root, tpl=tpl, site=site, render=render, nav=nav, font_link=FONT_LINK, foot=FOOT,
                             css=base_css + (tpl / "upgrade.css").read_text(encoding="utf-8") + th_css, thai_meanings=word_th)

    # YCT word lists
    urls += yct.build_th(root=root, tpl=tpl, site=site, render=render, nav=nav, font_link=FONT_LINK, foot=FOOT,
                         css=wl_css + (tpl / "yct.css").read_text(encoding="utf-8"),
                         search_key=search_key, thai_key=thai_key)

    # Grammar explainers
    urls += learn_th.build(
        root=root, tpl=tpl, site=site, render=render, nav=nav, font_link=FONT_LINK, foot=FOOT,
        css=base_css + (tpl / "learn.css").read_text(encoding="utf-8") + th_css,
        ws_css=base_css + (tpl / "learn_worksheet.css").read_text(encoding="utf-8") + th_css,
    )
    return urls


def alternates(root, levels):
    """English path -> Thai path, for pages that exist in both languages."""
    have = available_levels(root, levels)
    if not have:
        return {}
    pairs = {"/": TH_URL}
    pairs.update({f"/hsk-{n}-word-list/": f"{TH_URL}hsk-{n}-word-list/" for n in have})
    pairs.update(learn_th.alternates(root))
    pairs.update(yct.alternates(root))
    pairs.update(worksheets_th.alternates(root, have))
    pairs.update(measure_th.alternates(root))
    pairs.update(upgrade_th.alternates(root))
    return pairs
