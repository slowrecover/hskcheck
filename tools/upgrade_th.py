"""Thai version of the Old HSK -> New HSK page at /th/old-hsk-to-new-hsk/.

Made from the English template (templates/upgrade_body.html) with its text swapped for Thai, so the two never
drift apart: the build stops if an English string to be replaced is no longer found. Words of new HSK 1-4 show
their Thai meaning (from data/th/hskN_th.tsv and data/th/hsk4_th.tsv), and HSK 5 too once data/th/hsk5_th.tsv is
complete; the other levels have no Thai meanings yet and show the English one.

Called from tools/build_th.py; returns the URLs it wrote.
"""
import json

TH_UP_URL = "/th/old-hsk-to-new-hsk/"
EN_UP_URL = "/old-hsk-to-new-hsk/"

UI = [
    ('<span class="chip">Free</span>', '<span class="chip">ฟรี</span>'),
    ('<h1><span class="zh">新旧</span>Old HSK to New HSK</h1>', '<h1><span class="zh">新旧</span>HSK เก่า สู่ HSK ใหม่</h1>'),
    ("<p class=\"lede\">Studied for the old six-level HSK? Pick the level you reached and the new HSK level you are aiming for. "
     "You get only the words you have not met yet, the new characters inside them, and a file you can import into Anki or Pleco.</p>",
     '<p class="lede">เคยเรียน HSK แบบเก่า 6 ระดับมาแล้วใช่ไหม เลือกระดับที่คุณเรียนถึง และระดับ HSK ใหม่ที่ตั้งเป้าไว้ '
     "แล้วดูเฉพาะคำศัพท์ที่คุณยังไม่เคยเรียน ตัวอักษรใหม่ในคำเหล่านั้น และไฟล์สำหรับนำเข้า Anki หรือ Pleco</p>"),
    ('<h2 id="pick-title" class="visually-hidden">Choose your levels</h2>', '<h2 id="pick-title" class="visually-hidden">เลือกระดับ</h2>'),
    ('<label for="old-level">I studied old HSK</label>', '<label for="old-level">ฉันเรียน HSK เก่าถึง</label>'),
    ('<option value="0">Nothing yet</option>', '<option value="0">ยังไม่เคยเรียน</option>'),
    ("Old HSK 1 (150 words)", "HSK เก่า 1 (150 คำ)"), ("Old HSK 2 (300 words)", "HSK เก่า 2 (300 คำ)"),
    ("Old HSK 3 (600 words)", "HSK เก่า 3 (600 คำ)"), ("Old HSK 4 (1,200 words)", "HSK เก่า 4 (1,200 คำ)"),
    ("Old HSK 5 (2,500 words)", "HSK เก่า 5 (2,500 คำ)"), ("Old HSK 6 (5,000 words)", "HSK เก่า 6 (5,000 คำ)"),
    ("<label for=\"new-level\">I'm aiming for new HSK</label>", '<label for="new-level">เป้าหมาย HSK ใหม่</label>'),
    (">New HSK 1<", ">HSK ใหม่ 1<"), (">New HSK 2<", ">HSK ใหม่ 2<"), (">New HSK 3<", ">HSK ใหม่ 3<"),
    (">New HSK 4<", ">HSK ใหม่ 4<"), (">New HSK 5<", ">HSK ใหม่ 5<"), (">New HSK 6<", ">HSK ใหม่ 6<"),
    (">New HSK 7–9<", ">HSK ใหม่ 7–9<"),
    ('<h2 id="sum-title">What you still need</h2>', '<h2 id="sum-title">สิ่งที่คุณยังต้องเรียน</h2>'),
    # The printable pack has a Thai edition (tools/packs.py TH_PACKS): link it in Thai.
    ('<p class="pack-cta" id="pack-cta" hidden><b>Want this list on paper?</b> The '
     '<a href="/upgrade-packs/old-hsk-1-to-new-hsk-1/">Old HSK 1 → New HSK 1 Upgrade Pack</a> has the same words with '
     'example sentences, writing practice for the new characters, and quizzes, ready to print. $3.99.</p>',
     '<p class="pack-cta" id="pack-cta" hidden><b>อยากได้รายการนี้แบบพิมพ์ได้?</b> '
     '<a href="/th/upgrade-packs/old-hsk-1-to-new-hsk-1/">ชุดอัปเกรด HSK 1 เก่า → HSK 1 ใหม่</a> มีคำศัพท์ชุดเดียวกัน '
     'พร้อมประโยคตัวอย่างแปลไทย แบบฝึกเขียนตัวอักษรใหม่ และแบบทดสอบ พร้อมพิมพ์ $2.99</p>'),
    ('<p class="status" id="load-status">Loading word lists…</p>', '<p class="status" id="load-status">กำลังโหลดรายการคำศัพท์…</p>'),
    ("<span>words to learn</span>", "<span>คำที่ต้องเรียน</span>"),
    ("<span>new characters</span>", "<span>ตัวอักษรใหม่</span>"),
    ("<span>words you already met</span>", "<span>คำที่เคยเรียนแล้ว</span>"),
    ('<th scope="col">New level</th><th scope="col" class="num">Words</th><th scope="col" class="num">Already met</th><th scope="col" class="num">To learn</th>',
     '<th scope="col">ระดับใหม่</th><th scope="col" class="num">คำ</th><th scope="col" class="num">เคยเรียนแล้ว</th><th scope="col" class="num">ต้องเรียน</th>'),
    ('<h2 id="words-title">Words to learn</h2>', '<h2 id="words-title">คำที่ต้องเรียน</h2>'),
    ('aria-label="Which words to show"', 'aria-label="เลือกคำที่จะแสดง"'),
    ('<span id="g-hard">New characters</span>', '<span id="g-hard">ตัวอักษรใหม่</span>'),
    ('<span id="g-easy">Familiar characters</span>', '<span id="g-easy">ตัวอักษรที่รู้แล้ว</span>'),
    ('<span id="g-all">All</span>', '<span id="g-all">ทั้งหมด</span>'),
    ('<p class="hint" id="group-hint">Words with at least one character you have not learned yet. New characters are marked in red.</p>',
     '<p class="hint" id="group-hint"></p>'),
    ('<label class="visually-hidden" for="word-search">Search these words</label>', '<label class="visually-hidden" for="word-search">ค้นหาคำเหล่านี้</label>'),
    ('placeholder="Search: 学, xue or study"', 'placeholder="ค้นหา: 学, xue หรือ เรียน"'),
    ('<th scope="col">Word</th><th scope="col">Pinyin</th><th scope="col">Meaning</th><th scope="col" class="lv">Level</th>',
     '<th scope="col">คำ</th><th scope="col">พินอิน</th><th scope="col">ความหมาย</th><th scope="col" class="lv">ระดับ</th>'),
    ('<p class="empty" id="no-words" hidden>No words here.</p>', '<p class="empty" id="no-words" hidden>ไม่มีคำในกลุ่มนี้</p>'),
    ('id="more-btn" hidden>Show more</button>', 'id="more-btn" hidden>แสดงเพิ่ม</button>'),
    ('id="dl-btn">Download for Anki / Pleco</button>', 'id="dl-btn">ดาวน์โหลดสำหรับ Anki / Pleco</button>'),
    ('id="copy-words">Copy words</button>', 'id="copy-words">คัดลอกคำ</button>'),
    ('<p class="hint">The download is a tab-separated .txt file (word, pinyin, meaning) with the words shown above. '
     'Anki: File → Import. Pleco: Flashcards → Import Cards. "Copy words" gives one word per line, which Skritter and most apps accept.</p>',
     '<p class="hint">ไฟล์ที่ดาวน์โหลดเป็นไฟล์ .txt คั่นด้วยแท็บ (คำ พินอิน ความหมาย) ของคำที่แสดงด้านบน '
     'Anki: File → Import ส่วน Pleco: Flashcards → Import Cards ปุ่ม "คัดลอกคำ" จะได้คำละหนึ่งบรรทัด ซึ่ง Skritter และแอปส่วนใหญ่รองรับ</p>'),
    ('<h2 id="chars-title">New characters</h2>', '<h2 id="chars-title">ตัวอักษรใหม่</h2>'),
    ('<p class="hint">Characters in these words that do not appear in any word of the old HSK level you studied, in the order you meet them.</p>',
     '<p class="hint">ตัวอักษรในคำเหล่านี้ที่ไม่เคยปรากฏในคำศัพท์ HSK เก่าระดับที่คุณเรียน เรียงตามลำดับที่จะได้เจอ</p>'),
    ('<p class="empty" id="no-chars" hidden>No new characters. Every word on your list uses characters you already know.</p>',
     '<p class="empty" id="no-chars" hidden>ไม่มีตัวอักษรใหม่ ทุกคำในรายการใช้ตัวอักษรที่คุณรู้แล้ว</p>'),
    ('<a class="button" id="ws-link" href="/chinese-character-worksheets/">Print writing sheets</a>',
     '<a class="button" id="ws-link" href="/th/chinese-character-worksheets/">พิมพ์แบบฝึกเขียน</a>'),
    ('id="copy-chars">Copy characters</button>', 'id="copy-chars">คัดลอกตัวอักษร</button>'),
    ('The worksheet maker takes up to 400 characters at a time, so the link opens the first 400. Copy the rest and paste them in later.',
     'หน้าสร้างแบบฝึกเขียนรับได้ครั้งละไม่เกิน 400 ตัว ลิงก์จึงเปิด 400 ตัวแรก คัดลอกตัวที่เหลือไปวางทีหลังได้'),
    ('<h2 id="about-title">How the old and new HSK lists compare</h2>', '<h2 id="about-title">คำศัพท์ HSK เก่ากับใหม่ต่างกันอย่างไร</h2>'),
    ("<h3>Why old HSK words don't carry over one to one</h3>", "<h3>ทำไมคำศัพท์ HSK เก่าจึงไม่ตรงกับ HSK ใหม่แบบระดับต่อระดับ</h3>"),
    ("<p>The old HSK had six levels and about 5,000 words. HSK 3.0 has nine levels, and the 2025 syllabus spreads its words differently: "
     "many words move to a lower level, many are new, and some old words are gone. A pass at old HSK 4 does not mean you know the words of new HSK 4.</p>",
     "<p>HSK แบบเก่ามี 6 ระดับ และคำศัพท์ประมาณ 5,000 คำ ส่วน HSK 3.0 มี 9 ระดับ และหลักสูตรปี 2025 กระจายคำศัพท์ต่างออกไป "
     "หลายคำย้ายลงมาอยู่ระดับต่ำกว่า หลายคำเป็นคำใหม่ และคำเก่าบางคำก็ถูกตัดออก สอบผ่าน HSK เก่าระดับ 4 "
     "จึงไม่ได้แปลว่ารู้คำศัพท์ของ HSK ใหม่ระดับ 4</p>"),
    ("<h3>An example</h3>", "<h3>ตัวอย่าง</h3>"),
    ('<h3>"New characters" and "familiar characters"</h3>', '<h3>"ตัวอักษรใหม่" และ "ตัวอักษรที่รู้แล้ว"</h3>'),
    ('<p>Many words that are new on paper are built from characters you already know. The old list has <span class="zh-inline">这</span> and '
     '<span class="zh-inline">个</span>, the new one lists <span class="zh-inline">这个</span> as its own word. These go under "familiar characters" '
     'and are usually quick to pick up. Words with a character you have never studied go under "new characters": start there.</p>',
     '<p>คำจำนวนมากที่ดูเหมือนเป็นคำใหม่ จริง ๆ แล้วประกอบจากตัวอักษรที่คุณรู้อยู่แล้ว เช่น รายการเก่ามี <span class="zh-inline">这</span> และ '
     '<span class="zh-inline">个</span> ส่วนรายการใหม่นับ <span class="zh-inline">这个</span> เป็นอีกคำหนึ่ง คำแบบนี้อยู่ในกลุ่ม "ตัวอักษรที่รู้แล้ว" '
     'และมักเรียนได้เร็ว ส่วนคำที่มีตัวอักษรที่คุณไม่เคยเรียนอยู่ในกลุ่ม "ตัวอักษรใหม่" ให้เริ่มจากกลุ่มนี้</p>'),
    ('<p><b>How it works.</b> Each word of the new HSK levels you pick is looked up in the old HSK lists. If it appears at or below the old level you chose, '
     'it counts as met. Words are compared as written, so a word only counts as met if the old list has that exact word. A word ending in '
     '<span class="zh-inline">儿</span> also matches the same word without it, and a word that is part of an old entry counts as met '
     '(<span class="zh-inline">篮球</span> in <span class="zh-inline">打篮球</span>).</p>',
     '<p><b>วิธีนับ</b> คำศัพท์แต่ละคำของ HSK ใหม่ระดับที่คุณเลือกจะถูกค้นในรายการ HSK เก่า ถ้าอยู่ในระดับเก่าที่คุณเลือกหรือต่ำกว่า '
     'จะนับว่าเคยเรียนแล้ว คำจะถูกเทียบตามที่เขียน คำหนึ่งจะนับว่าเคยเรียนก็ต่อเมื่อรายการเก่ามีคำนั้นตรงทุกตัว คำที่ลงท้ายด้วย '
     '<span class="zh-inline">儿</span> ตรงกับคำเดียวกันที่ไม่มี 儿 ได้ และคำที่เป็นส่วนหนึ่งของคำในรายการเก่าก็นับว่าเคยเรียนแล้ว '
     '(<span class="zh-inline">篮球</span> ใน <span class="zh-inline">打篮球</span>)</p>'),
    ("<p><b>Sources.</b> New HSK 1–4: the site's own lists from the 2025 syllabus, HSK 1–3 cross-checked against two published copies "
     "and HSK 4 against one. "
     "New HSK 5–9 and old HSK 1–6: the open <a href=\"https://github.com/drkameleon/complete-hsk-vocabulary\">complete-hsk-vocabulary</a> "
     "data set (MIT licence), with meanings from CC-CEDICT. Levels 5–9 have not been cross-checked yet.</p>",
     "<p><b>ที่มา</b> HSK ใหม่ 1–4: รายการของเว็บไซต์นี้จากหลักสูตรปี 2025 โดย HSK 1–3 ตรวจทานกับสำเนาที่เผยแพร่สองแหล่ง "
     "และ HSK 4 ตรวจทานกับอีกหนึ่งแหล่ง "
     "HSK ใหม่ 5–9 และ HSK เก่า 1–6: ชุดข้อมูลเปิด <a href=\"https://github.com/drkameleon/complete-hsk-vocabulary\">complete-hsk-vocabulary</a> "
     "(สัญญาอนุญาต MIT) ความหมายมาจาก CC-CEDICT ระดับ 5–9 ยังไม่ได้ตรวจทาน "
     "คำศัพท์ HSK ใหม่ 1–4 แสดงความหมายภาษาไทย ส่วนระดับ 5–9 ยังแสดงความหมายภาษาอังกฤษ</p>"),
    ("<p><b>Privacy.</b> Everything runs in your browser. Nothing you pick is sent anywhere.</p>",
     "<p><b>ความเป็นส่วนตัว</b> ทุกอย่างทำงานในเบราว์เซอร์ของคุณ สิ่งที่คุณเลือกจะไม่ถูกส่งไปที่ไหน</p>"),
    # script
    ('  let result = { hard: [], easy: [], chars: "" }, shown = PAGE;',
     '  let result = { hard: [], easy: [], chars: "" }, shown = PAGE;\n  const TH = __TH_JSON__;\n  const mean = x => TH[x[0]] || x[2];'),
    ('const norm = s => s.toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "").replace(/[\\s\'’-]/g, "");',
     'const norm = s => s.toLowerCase().normalize("NFD").replace(/[\\u0300-\\u036f]/g, "").replace(/[\\s\'’-]/g, "");'),
    ('"|" + norm(x[2]) };', '"|" + norm(x[2]) + "|" + norm(mean(x)) };'),
    ('$("summary-line").textContent = "New HSK " + (T === 1 ? "1" : T === 7 ? "1–9" : "1–" + T) + " has " + fmt(total) + " words. " +\n'
     '      (O ? "You met " + fmt(total - todo) + " of them in old HSK 1" + (O > 1 ? "–" + O : "") + ". " : "") +\n'
     '      fmt(hard.length) + " of the rest use a character you haven\'t learned; " + fmt(easy.length) + " use only characters you know.";',
     '$("summary-line").textContent = "HSK ใหม่ " + (T === 1 ? "1" : T === 7 ? "1–9" : "1–" + T) + " มีคำศัพท์ " + fmt(total) + " คำ " +\n'
     '      (O ? "คุณเคยเรียนมาแล้ว " + fmt(total - todo) + " คำใน HSK เก่า 1" + (O > 1 ? "–" + O : "") + " " : "") +\n'
     '      "ในคำที่เหลือ " + fmt(hard.length) + " คำมีตัวอักษรที่คุณยังไม่เคยเรียน และ " + fmt(easy.length) + " คำใช้แต่ตัวอักษรที่คุณรู้แล้ว";'),
    ('$("g-hard").textContent = "New characters (" + fmt(hard.length) + ")";', '$("g-hard").textContent = "ตัวอักษรใหม่ (" + fmt(hard.length) + ")";'),
    ('$("g-easy").textContent = "Familiar characters (" + fmt(easy.length) + ")";', '$("g-easy").textContent = "ตัวอักษรที่รู้แล้ว (" + fmt(easy.length) + ")";'),
    ('$("g-all").textContent = "All (" + fmt(todo) + ")";', '$("g-all").textContent = "ทั้งหมด (" + fmt(todo) + ")";'),
    ('ws.href = "/chinese-character-worksheets/#c="', 'ws.href = "/th/chinese-character-worksheets/#c="'),
    ('    hard: "Words with at least one character you have not learned yet. New characters are marked in red.",\n'
     '    easy: "Words made only of characters you already know from the old HSK, like 这个 from 这 and 个. Usually quick to learn.",\n'
     '    all: "Every word you still need, both groups together.",',
     '    hard: "คำที่มีตัวอักษรที่คุณยังไม่เคยเรียนอย่างน้อยหนึ่งตัว ตัวอักษรใหม่จะเป็นสีแดง",\n'
     '    easy: "คำที่ประกอบจากตัวอักษรที่คุณรู้แล้วจาก HSK เก่า เช่น 这个 จาก 这 และ 个 มักเรียนได้เร็ว",\n'
     '    all: "คำทั้งหมดที่คุณยังต้องเรียน รวมทั้งสองกลุ่ม",'),
    ('<td class="en">${esc(x[2])}</td>', '<td class="en">${esc(mean(x))}</td>'),
    ('$("word-count").textContent = list.length > shown ? "Showing " + fmt(shown) + " of " + fmt(list.length) : fmt(list.length) + " words";',
     '$("word-count").textContent = list.length > shown ? "แสดง " + fmt(shown) + " จาก " + fmt(list.length) + " คำ" : fmt(list.length) + " คำ";'),
    ('$("load-status").textContent = "Loading HSK 7–9 words…";', '$("load-status").textContent = "กำลังโหลดคำศัพท์ HSK 7–9…";'),
    ('$("load-status").textContent = "Could not load the word lists. Check your connection and reload the page.";',
     '$("load-status").textContent = "โหลดรายการคำศัพท์ไม่สำเร็จ ตรวจสอบอินเทอร์เน็ตแล้วโหลดหน้าใหม่อีกครั้ง";'),
    ('flash(id, "Copied " + what + ".");', 'flash(id, "คัดลอก" + what + "แล้ว");'),
    ('flash(id, "Couldn\'t copy. Select the text and copy it by hand.");', 'flash(id, "คัดลอกไม่สำเร็จ ลองเลือกข้อความแล้วคัดลอกเอง");'),
    ('const lines = list.map(({ x }) => [x[0], x[1], x[2]]', 'const lines = list.map(({ x }) => [x[0], x[1], mean(x)]'),
    ('flash("words-status", "Downloaded " + fmt(list.length) + " words.");', 'flash("words-status", "ดาวน์โหลด " + fmt(list.length) + " คำแล้ว");'),
    ('"words-status", "the words"));', '"words-status", "คำ"));'),
    ('"chars-status", fmt(result.chars.length) + " characters"));', '"chars-status", "ตัวอักษร " + fmt(result.chars.length) + " ตัว"));'),
]


def thai_template(tpl):
    body = (tpl / "upgrade_body.html").read_text(encoding="utf-8")
    for en, th in UI:
        if body.count(en) != 1:
            raise SystemExit(f"upgrade_th: expected the English text once in templates/upgrade_body.html: {en[:70]}")
        body = body.replace(en, th)
    return body


def example(words):
    oc = words["oc"]
    old4 = set("".join(oc[1:5]))
    gap = [x for x in words["w"] if x[3] <= 4 and not (x[4] and x[4] <= 4)]
    hard = sum(1 for x in gap if any(c not in old4 for c in x[0] if "一" <= c <= "鿿"))
    total4 = sum(1 for x in words["w"] if x[3] <= 4)
    return (f"HSK ใหม่ 1–4 มีคำศัพท์ {total4:,} คำ คนที่เรียน HSK เก่า 1–4 มาครบ เคยเรียนไปแล้ว {total4 - len(gap):,} คำ "
            f"จึงยังเหลือ {len(gap):,} คำที่ต้องเรียน ในจำนวนนี้ {hard:,} คำมีตัวอักษรอย่างน้อยหนึ่งตัว "
            "ที่ไม่เคยปรากฏในคำศัพท์ HSK เก่า 1–4 เลย")


def build(*, root, tpl, site, css, render, nav, font_link, foot, thai_meanings):
    data = root / "old-hsk-to-new-hsk" / "words.json"
    if not data.exists():
        return []
    words = json.loads(data.read_text(encoding="utf-8"))
    body = (thai_template(tpl).replace("__NAV__", nav(TH_UP_URL)).replace("__EXAMPLE__", example(words))
            .replace("__TH_JSON__", json.dumps(thai_meanings, ensure_ascii=False, separators=(",", ":"))))
    ld = json.dumps({
        "@context": "https://schema.org", "@type": "WebApplication", "name": "HSK เก่า สู่ HSK ใหม่",
        "url": site + TH_UP_URL, "inLanguage": "th", "applicationCategory": "EducationalApplication",
        "operatingSystem": "Any", "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"},
        "description": "ดูว่าต้องเรียนคำศัพท์และตัวอักษร HSK 3.0 อะไรเพิ่ม หลังจากเรียน HSK 2.0 แบบเก่ามาแล้ว",
    }, ensure_ascii=False)
    target = root / TH_UP_URL.strip("/")
    target.mkdir(parents=True, exist_ok=True)
    (target / "index.html").write_text(render(
        "HSK เก่า สู่ HSK ใหม่ (HSK 3.0): ต้องเรียนคำศัพท์อะไรเพิ่ม",
        "เคยเรียน HSK 2.0 แบบเก่ามาแล้ว เลือกระดับเก่าและระดับ HSK 3.0 ที่ตั้งเป้า แล้วดูเฉพาะคำศัพท์และตัวอักษรที่ยังไม่เคยเรียน "
        "ฟรี ส่งออกไป Anki และ Pleco ได้",
        site + TH_UP_URL, css, body, font_link + f'\n<script type="application/ld+json">{ld}</script>',
        lang="th", foot=foot), encoding="utf-8")
    return [TH_UP_URL]


def alternates(root):
    return {EN_UP_URL: TH_UP_URL} if (root / "old-hsk-to-new-hsk" / "words.json").exists() else {}
