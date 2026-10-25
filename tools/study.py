"""HSK flashcards with spaced review, built to /hsk-flashcards/ (English) and /th/hsk-flashcards/ (Thai).

The page (templates/study_body.html) loads one small JSON file per level, [[word, pinyin, meaning], ...] in syllabus
order, and keeps each learner's progress in their own browser (localStorage); nothing is sent anywhere.

  hsk-flashcards/hskN.json      English meanings, from data/hskN.tsv (N = 1-5)
  th/hsk-flashcards/hskN.json   Thai meanings from data/th/ (HSK 1-4); HSK 5 has no Thai yet and uses English

The Thai page is the English template with its text swapped for Thai; the build stops if a string is not found.
"""
import json

URL = "/hsk-flashcards/"
TH_URL = "/th/hsk-flashcards/"
LEVELS = (1, 2, 3, 4, 5)

UI_EN = {
    "started": "words started", "strong": "well known", "day": "day", "days": "days", "streak": "in a row",
    "newWord": "New", "review": "Review", "show": "Show answer", "know": "I know this word",
    "again": "Again", "got": "Got it", "listen": "Listen",
    "doneHead": "All done for today", "doneSub": "Come back tomorrow for your reviews and new words.",
    "more": "Learn more new words", "allSeen": "You have started every word at this level.",
    "loading": "Loading words…", "loadFail": "The word list could not be loaded. Check your connection and try again.",
    "resetAsk": "Reset your progress for HSK {n}? This cannot be undone.",
    "installHead": "Open it from your home screen tomorrow",
    "installText": "Add the flashcards to your home screen and they open like an app, one tap a day.",
    "installBtn": "Add to home screen",
    "pickHead": "Which HSK level are you studying?",
    "pickSub": "New to Chinese? Start with HSK 1. You can change level any time.",
    "storyHead": "Now read a short HSK story", "readBase": "/reading/", "titleKey": "en",
    "iosTip": "On iPhone: tap the Share button in Safari, then “Add to Home Screen”. The flashcards then open like an app.",
}
UI_TH = {
    "started": "คำที่เริ่มเรียนแล้ว", "strong": "คำที่จำได้ดี", "day": "วัน", "days": "วัน", "streak": "ติดต่อกัน",
    "newWord": "คำใหม่", "review": "ทบทวน", "show": "ดูคำตอบ", "know": "รู้คำนี้แล้ว",
    "again": "อีกครั้ง", "got": "จำได้", "listen": "ฟังเสียง",
    "doneHead": "วันนี้เรียนครบแล้ว", "doneSub": "พรุ่งนี้กลับมาทบทวนและเรียนคำใหม่กัน",
    "more": "เรียนคำใหม่เพิ่ม", "allSeen": "คุณเริ่มเรียนครบทุกคำในระดับนี้แล้ว",
    "loading": "กำลังโหลดคำศัพท์…", "loadFail": "โหลดรายการคำศัพท์ไม่ได้ ตรวจสอบอินเทอร์เน็ตแล้วลองอีกครั้ง",
    "resetAsk": "ล้างความคืบหน้าของ HSK {n} ใช่ไหม ย้อนกลับไม่ได้",
    "installHead": "พรุ่งนี้เปิดจากหน้าจอโฮมได้เลย",
    "installText": "เพิ่มแฟลชการ์ดไว้ที่หน้าจอโฮม แตะครั้งเดียวก็เปิดได้เหมือนแอป",
    "installBtn": "เพิ่มไปยังหน้าจอโฮม",
    "pickHead": "คุณกำลังเรียน HSK ระดับไหน?",
    "pickSub": "เพิ่งเริ่มเรียนภาษาจีน? เริ่มที่ HSK 1 เปลี่ยนระดับได้ทุกเมื่อ",
    "storyHead": "อ่านเรื่องสั้น HSK ต่อเลย", "readBase": "/th/reading/", "titleKey": "th",
    "iosTip": "บน iPhone: แตะปุ่มแชร์ใน Safari แล้วเลือก “เพิ่มไปยังหน้าจอโฮม” แฟลชการ์ดจะเปิดได้เหมือนแอป",
}

TH_SWAPS = [
    ('<span>New HSK · 2025 syllabus</span><span class="chip">Levels 1–5</span><span class="chip">Free</span>',
     '<span>HSK ใหม่ · หลักสูตรปี 2025</span><span class="chip">ระดับ 1–5</span><span class="chip">ฟรี</span>'),
    ('<h1><span class="zh">背词</span>HSK Flashcards</h1>', '<h1><span class="zh">背词</span>แฟลชการ์ด HSK</h1>'),
    ('<p class="lede">A few minutes a day. You get new words and the ones you are due to review, and your progress is saved '
     'on this device, with no account.</p>',
     '<p class="lede">วันละไม่กี่นาที ได้ทั้งคำใหม่และคำที่ถึงเวลาทบทวน ความคืบหน้าบันทึกไว้ในอุปกรณ์นี้ ไม่ต้องสมัครสมาชิก</p>'),
    ('<h2 id="pick-title" class="visually-hidden">Choose a level</h2>', '<h2 id="pick-title" class="visually-hidden">เลือกระดับ</h2>'),
    ('<div class="levels" role="group" aria-label="Level">\n      <span class="lbl">Level</span>',
     '<div class="levels" role="group" aria-label="ระดับ">\n      <span class="lbl">ระดับ</span>'),
    ('<h2 id="card-title">Today</h2>', '<h2 id="card-title">วันนี้</h2>'),
    ('<p class="empty" id="loading">Loading words…</p>', '<p class="empty" id="loading">กำลังโหลดคำศัพท์…</p>'),
    ('<a id="test-link" href="/hsk-practice-test/">Test yourself: take the HSK practice test →</a>',
     '<a id="test-link" href="/th/hsk-practice-test/">ทดสอบตัวเอง: ทำแบบทดสอบ HSK →</a>'),
    ('<h2 id="set-title">Settings</h2>', '<h2 id="set-title">ตั้งค่า</h2>'),
    ('<label class="fc-set">New words a day', '<label class="fc-set">คำใหม่ต่อวัน'),
    ('<input type="checkbox" id="show-pinyin"> Show pinyin on the front</label>',
     '<input type="checkbox" id="show-pinyin"> แสดงพินอินด้านหน้าการ์ด</label>'),
    ('<button type="button" class="ghost" id="reset-btn">Reset this level</button>',
     '<button type="button" class="ghost" id="reset-btn">ล้างความคืบหน้าระดับนี้</button>'),
    ('This browser is not letting the page save, so your progress will be lost when you close it.',
     'เบราว์เซอร์นี้ไม่อนุญาตให้บันทึกข้อมูล ความคืบหน้าจะหายไปเมื่อปิดหน้านี้'),
    ('<h2 id="guide-title">How it works</h2>', '<h2 id="guide-title">วิธีใช้งาน</h2>'),
    ('<h3>New words and reviews</h3>', '<h3>คำใหม่และคำทบทวน</h3>'),
    ('<p>Each day you get a few new words from your level, in syllabus order, plus the words you are due to review. '
     'Say the meaning to yourself, then tap <b>Show answer</b>.</p>',
     '<p>ทุกวันจะได้คำใหม่จากระดับที่เลือกจำนวนหนึ่งตามลำดับในหลักสูตร พร้อมคำที่ถึงเวลาทบทวน '
     'นึกความหมายในใจก่อน แล้วแตะ <b>ดูคำตอบ</b></p>'),
    ('<h3>Got it, or again</h3>', '<h3>จำได้ หรือ อีกครั้ง</h3>'),
    ("<p>If you knew it, the word comes back later: after 1 day, then 3, 7, 14 and 30 days. If not, it comes back at the "
     "end of today's session and again tomorrow. Words you already know can be skipped with <b>I know this word</b>.</p>",
     "<p>ถ้าจำได้ คำนั้นจะกลับมาให้ทบทวนในภายหลัง คือหลัง 1 วัน แล้ว 3, 7, 14 และ 30 วัน ถ้าจำไม่ได้ "
     "จะกลับมาอีกครั้งตอนท้ายของวันนี้และพรุ่งนี้ คำที่รู้อยู่แล้วกด <b>รู้คำนี้แล้ว</b> เพื่อข้ามได้</p>"),
    ('<h3>Where is my progress kept?</h3>', '<h3>ความคืบหน้าเก็บไว้ที่ไหน?</h3>'),
    ('<p>In this browser on this device. Nothing is sent to us. Clearing your browser data, or using another phone or '
     'computer, starts you from the beginning.</p>',
     '<p>เก็บไว้ในเบราว์เซอร์ของอุปกรณ์นี้ ไม่มีการส่งข้อมูลมาที่เรา ถ้าล้างข้อมูลเบราว์เซอร์ หรือใช้โทรศัพท์หรือคอมพิวเตอร์เครื่องอื่น '
     'จะเริ่มต้นใหม่ตั้งแต่แรก</p>'),
    ('<p><b>Word lists.</b> HSK 3.0 (New HSK) vocabulary, 2025 syllabus, the same lists as the '
     '<a href="/hsk-1-word-list/">word list pages</a>. Pronunciation uses your device\'s Chinese voice when it has one.</p>',
     '<p><b>รายการคำศัพท์</b> คำศัพท์ HSK 3.0 (HSK ใหม่) หลักสูตรปี 2025 ชุดเดียวกับ'
     '<a href="/th/hsk-1-word-list/">หน้ารายการคำศัพท์</a> HSK 1–4 มีความหมายภาษาไทย ส่วน HSK 5 ยังเป็นภาษาอังกฤษ '
     'เสียงอ่านใช้เสียงภาษาจีนของอุปกรณ์ (ถ้ามี)</p>'),
]


def _rows(path, cols):
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            parts = [p.strip() for p in line.split("\t")]
            out.append([parts[c] for c in cols])
    return out


def _english(root, n):
    return _rows(root / "data" / f"hsk{n}.tsv", (0, 1, 2))


def _write_json(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(rows, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")


def _ld(name, url, desc, lang):
    return json.dumps({
        "@context": "https://schema.org", "@type": "WebApplication", "name": name, "url": url, "inLanguage": lang,
        "applicationCategory": "EducationalApplication", "operatingSystem": "Any",
        "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"}, "description": desc,
    }, ensure_ascii=False)


def _body(tpl, nav_html, ui, data_base):
    return ((tpl / "study_body.html").read_text(encoding="utf-8").replace("__NAV__", nav_html)
            .replace("__UI_JSON__", json.dumps(ui, ensure_ascii=False)).replace("__DATA_BASE__", data_base))


def build(root, pages, nav, render, base_css, tpl, site):
    for n in LEVELS:
        _write_json(root / URL.strip("/") / f"hsk{n}.json", _english(root, n))
    body = _body(tpl, nav(pages, URL), UI_EN, URL)
    desc = ("Free HSK flashcards for the HSK 3.0 word lists, levels 1–5, with daily spaced review. "
            "No sign-up: your progress stays on your device.")
    out = render("HSK Flashcards: Learn HSK 1–5 Words with Daily Review (HSK 3.0)", desc, site + URL,
                 base_css + (tpl / "checker.css").read_text(encoding="utf-8") + (tpl / "study.css").read_text(encoding="utf-8"),
                 body, f'<script type="application/ld+json">{_ld("HSK Flashcards", site + URL, desc, "en")}</script>')
    (root / URL.strip("/") / "index.html").write_text(out, encoding="utf-8")
    return [URL]


def build_th(*, root, tpl, site, render, nav, font_link, foot, css, thai):
    """thai: {level: [Thai meaning, ...]} in data/hskN.tsv order, for the levels that have Thai."""
    for n in LEVELS:
        rows = _english(root, n)
        if n in thai:
            if len(thai[n]) != len(rows):
                raise SystemExit(f"study: Thai meanings for HSK {n} do not match the word list")
            rows = [[w, p, m] for (w, p, _), m in zip(rows, thai[n])]
        _write_json(root / TH_URL.strip("/") / f"hsk{n}.json", rows)
    body = _body(tpl, nav(TH_URL), UI_TH, TH_URL)
    for a, b in TH_SWAPS:
        if body.count(a) != 1:
            raise SystemExit(f"study: English text not found for the Thai page: {a[:60]}")
        body = body.replace(a, b)
    desc = "แฟลชการ์ดคำศัพท์ HSK 3.0 ระดับ 1–5 ฟรี พร้อมความหมายภาษาไทยและการทบทวนรายวัน ไม่ต้องสมัคร ความคืบหน้าเก็บในอุปกรณ์ของคุณ"
    out = render("แฟลชการ์ด HSK ท่องคำศัพท์ HSK 1–5 พร้อมคำแปลไทย ทบทวนทุกวัน ฟรี", desc, site + TH_URL, css, body,
                 font_link + f'\n<script type="application/ld+json">{_ld("แฟลชการ์ด HSK", site + TH_URL, desc, "th")}</script>',
                 lang="th", foot=foot)
    (root / TH_URL.strip("/") / "index.html").write_text(out, encoding="utf-8")
    return [TH_URL]


def alternates(root):
    return {URL: TH_URL}
