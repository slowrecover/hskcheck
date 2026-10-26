"""Daily HSK quiz, built to /daily-hsk-quiz/ (English) and /th/daily-hsk-quiz/ (Thai).

Ten questions a day per level (HSK 1-5), the same for every learner on the same day: the page
(templates/daily_body.html, CSS in templates/practice.css + templates/daily.css) seeds its random numbers with the
learner's local date and the level, and draws the questions from the same data and with the same checks as the HSK
practice test (tools/practice.py): meaning of a word, word for a meaning, pinyin, a word heard with the device's
Chinese voice and, at HSK 1-3, a sentence with a gap from the grammar pages. A listening question becomes "choose the
word for this meaning" (same word, same options) on a device without a Chinese voice. The streak of days with a
finished quiz and the results of the last 7 days stay in the learner's browser (localStorage); nothing is sent
anywhere.

Data files read:
  hsk-practice-test/hskN.json, th/hsk-practice-test/hskN.json   written by tools/practice.py just before this module
                                                                 runs (format in that file); the daily quiz loads them,
                                                                 so both tools always ask about the same checked data.
Outputs:
  daily-hsk-quiz/index.html      English
  th/daily-hsk-quiz/index.html   Thai

The Thai page is the English template with its text swapped for Thai; the build stops if a string is not found.
"""
import json

import practice

URL = "/daily-hsk-quiz/"
TH_URL = "/th/daily-hsk-quiz/"

UI_EN = {
    "locale": "en-GB", "days": ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"],
    "q": "Question", "of": "of", "start": "Start today's HSK {n} quiz", "resume": "Continue: question {k} of {t}",
    "startSub": "10 questions on the HSK {n} words. About 2 minutes.",
    "askMeaning": "What does this word mean?", "askWord": "Which word means this?",
    "askPinyin": "How do you read this word?", "askListen": "Listen. Which word do you hear?",
    "askGap": "Choose the word that fills the gap.", "play": "Play again", "slow": "Slow",
    "right": "Right!", "wrong": "Not quite.", "next": "Next question", "finish": "See my score",
    "grammar": "Read about this grammar point", "learnBase": "/learn/",
    "scoreHead": "Today's HSK {n} quiz",
    "msg4": "Excellent. You know these HSK {n} words well.", "msg3": "Good work. Review the words below.",
    "msg2": "Keep going. Learn the words below with the flashcards.",
    "msg1": "HSK {n} is still new for you. The flashcards are a good place to start.",
    "missedHead": "Words to review", "noMissed": "You got every question right.",
    "add": "Add these words to my HSK {n} flashcards", "added": "Added. They come first in your next flashcard session.",
    "tomorrow": "Come back tomorrow", "tomorrowSub": "A new quiz is ready at midnight. Until then, keep practising:",
    "testLink": "HSK {n} practice test", "testBase": "/hsk-practice-test/",
    "cardsLink": "HSK {n} flashcards", "cardsBase": "/hsk-flashcards/",
    "streak0": "Finish today's quiz to start a streak.", "streak1": "Streak: 1 day", "streakN": "Streak: {n} days in a row",
    "weekScore": "{s} of {t} at HSK {n}", "weekOther": "done at another level", "weekNone": "no quiz",
    "loading": "Loading today's quiz…", "loadFail": "The quiz could not be loaded. Check your connection and try again.",
}
UI_TH = {
    "locale": "th-TH", "days": ["อา.", "จ.", "อ.", "พ.", "พฤ.", "ศ.", "ส."],
    "q": "ข้อ", "of": "จาก", "start": "เริ่มควิซ HSK {n} ของวันนี้", "resume": "ทำต่อ: ข้อ {k} จาก {t}",
    "startSub": "10 ข้อจากคำศัพท์ HSK {n} ใช้เวลาประมาณ 2 นาที",
    "askMeaning": "คำนี้แปลว่าอะไร?", "askWord": "คำไหนมีความหมายนี้?",
    "askPinyin": "คำนี้อ่านว่าอย่างไร?", "askListen": "ฟังแล้วเลือกคำที่ได้ยิน",
    "askGap": "เลือกคำที่เติมในช่องว่างได้ถูกต้อง", "play": "ฟังอีกครั้ง", "slow": "ช้าลง",
    "right": "ถูกต้อง!", "wrong": "ยังไม่ถูก", "next": "ข้อต่อไป", "finish": "ดูคะแนน",
    "grammar": "อ่านเรื่องไวยากรณ์ข้อนี้", "learnBase": "/th/learn/",
    "scoreHead": "ควิซ HSK {n} ของวันนี้",
    "msg4": "ยอดเยี่ยม คุณรู้คำศัพท์ HSK {n} ชุดนี้ดีมาก", "msg3": "ทำได้ดี ทบทวนคำด้านล่างอีกสักรอบ",
    "msg2": "สู้ต่อไป ท่องคำด้านล่างด้วยแฟลชการ์ด",
    "msg1": "HSK {n} ยังใหม่สำหรับคุณ เริ่มจากแฟลชการ์ดก่อนก็ดี",
    "missedHead": "คำที่ควรทบทวน", "noMissed": "คุณตอบถูกทุกข้อ",
    "add": "เพิ่มคำเหล่านี้ในแฟลชการ์ด HSK {n} ของฉัน", "added": "เพิ่มแล้ว คำเหล่านี้จะขึ้นก่อนในการเรียนแฟลชการ์ดครั้งต่อไป",
    "tomorrow": "พรุ่งนี้มาทำต่อนะ", "tomorrowSub": "ควิซชุดใหม่พร้อมตอนเที่ยงคืน ระหว่างนี้ฝึกต่อได้ที่:",
    "testLink": "แบบทดสอบ HSK {n}", "testBase": "/th/hsk-practice-test/",
    "cardsLink": "แฟลชการ์ด HSK {n}", "cardsBase": "/th/hsk-flashcards/",
    "streak0": "ทำควิซวันนี้ให้ครบเพื่อเริ่มนับวันต่อเนื่อง", "streak1": "ทำต่อเนื่อง 1 วัน", "streakN": "ทำต่อเนื่อง {n} วันติดกัน",
    "weekScore": "ได้ {s} จาก {t} ใน HSK {n}", "weekOther": "ทำในระดับอื่นแล้ว", "weekNone": "ไม่ได้ทำ",
    "loading": "กำลังโหลดควิซของวันนี้…", "loadFail": "โหลดควิซไม่ได้ ตรวจสอบอินเทอร์เน็ตแล้วลองอีกครั้ง",
}

TH_SWAPS = [
    ('<span>New HSK · 2025 syllabus</span><span class="chip">Levels 1–5</span><span class="chip">Free</span>',
     '<span>HSK ใหม่ · หลักสูตรปี 2025</span><span class="chip">ระดับ 1–5</span><span class="chip">ฟรี</span>'),
    ('<h1><span class="zh">每日</span>Daily HSK Quiz</h1>', '<h1><span class="zh">每日</span>ควิซ HSK ประจำวัน</h1>'),
    ('<p class="lede">Ten questions a day for your level, new every day and the same for every learner. Answer them in '
     'two minutes, keep your streak going, and come back tomorrow.</p>',
     '<p class="lede">วันละ 10 ข้อตามระดับของคุณ เปลี่ยนชุดใหม่ทุกวัน และทุกคนได้ข้อเดียวกัน ทำเสร็จใน 2 นาที '
     'รักษาสถิติวันต่อเนื่องไว้ แล้วพรุ่งนี้กลับมาทำใหม่</p>'),
    ('<h2 id="pick-title" class="visually-hidden">Choose a level</h2>', '<h2 id="pick-title" class="visually-hidden">เลือกระดับ</h2>'),
    ('<div class="levels pt-levels" role="group" aria-label="Level">\n      <span class="lbl">Level</span>',
     '<div class="levels pt-levels" role="group" aria-label="ระดับ">\n      <span class="lbl">ระดับ</span>'),
    ('<ol class="dq-week" id="week" aria-label="The last 7 days">', '<ol class="dq-week" id="week" aria-label="7 วันที่ผ่านมา">'),
    ('<h2 id="quiz-title" class="visually-hidden">Today\'s quiz</h2>', '<h2 id="quiz-title" class="visually-hidden">ควิซของวันนี้</h2>'),
    ('<p class="empty" id="loading">Loading today\'s quiz…</p>', '<p class="empty" id="loading">กำลังโหลดควิซของวันนี้…</p>'),
    ('This browser is not letting the page save, so your streak and results will not be kept.',
     'เบราว์เซอร์นี้ไม่อนุญาตให้บันทึกข้อมูล สถิติวันต่อเนื่องและผลคะแนนจึงจะไม่ถูกเก็บไว้'),
    ('<h2 id="guide-title">About the daily quiz</h2>', '<h2 id="guide-title">เกี่ยวกับควิซประจำวัน</h2>'),
    ('<h3>What is in the quiz?</h3>', '<h3>ควิซมีอะไรบ้าง?</h3>'),
    ('<p>Ten questions on the HSK 3.0 words of your level: the meaning of a word, the word for a meaning, the right pinyin, '
     'a word you hear, and at HSK 1–3 a gap to fill in a sentence from the <a href="/learn/">grammar pages</a>. You see '
     'the answer after every question.</p>',
     '<p>คำถาม 10 ข้อจากคำศัพท์ HSK 3.0 ของระดับที่เลือก มีทั้งเลือกความหมายของคำ เลือกคำจากความหมาย เลือกพินอินที่ถูกต้อง '
     'ฟังเสียงแล้วเลือกคำที่ได้ยิน และในระดับ HSK 1–3 มีข้อเติมคำในประโยคจาก<a href="/th/learn/">บทเรียนไวยากรณ์</a> '
     'เห็นเฉลยทันทีหลังตอบแต่ละข้อ</p>'),
    ('<h3>Why is it the same for everyone?</h3>', '<h3>ทำไมทุกคนได้ข้อเดียวกัน?</h3>'),
    ('<p>The questions are picked from the date, so everyone at the same level gets the same quiz on the same day, and a '
     'new one at midnight. Compare your score with a classmate, or do it together with your teacher.</p>',
     '<p>คำถามเลือกตามวันที่ ทุกคนที่เลือกระดับเดียวกันจึงได้ควิซชุดเดียวกันในวันเดียวกัน และได้ชุดใหม่ตอนเที่ยงคืน '
     'เทียบคะแนนกับเพื่อนร่วมชั้น หรือทำไปพร้อมกับครูในห้องเรียนก็ได้</p>'),
    ('<h3>How does the streak work?</h3>', '<h3>นับวันต่อเนื่องอย่างไร?</h3>'),
    ('<p>Finish a quiz at any level and the day counts. Your streak is the number of days in a row you have finished one, '
     'and the week shows your score at the level you have chosen. It is all kept in this browser on this device; nothing '
     'is sent anywhere.</p>',
     '<p>ทำควิซระดับใดก็ได้ให้ครบ วันนั้นก็นับแล้ว จำนวนวันต่อเนื่องคือจำนวนวันติดกันที่คุณทำควิซครบ '
     'ส่วนแถว 7 วันแสดงคะแนนของระดับที่เลือกอยู่ ข้อมูลทั้งหมดเก็บไว้ในเบราว์เซอร์ของอุปกรณ์นี้ ไม่ถูกส่งไปที่ไหน</p>'),
    ('<h3>Want more practice?</h3>', '<h3>อยากฝึกเพิ่ม?</h3>'),
    ('<p>Take a longer <a href="/hsk-practice-test/">HSK practice test</a> of 20 questions as often as you like, or learn '
     'new words every day with the <a href="/hsk-flashcards/">flashcards</a>.</p>',
     '<p>ทำ<a href="/th/hsk-practice-test/">แบบทดสอบ HSK</a> ชุดละ 20 ข้อได้บ่อยเท่าที่ต้องการ '
     'หรือท่องคำใหม่ทุกวันด้วย<a href="/th/hsk-flashcards/">แฟลชการ์ด</a></p>'),
    ('<p><b>Words.</b> HSK 3.0 (New HSK) vocabulary, 2025 syllabus, the same lists as the '
     '<a href="/hsk-1-word-list/">word list pages</a> and the practice test. Listening questions use your device\'s '
     'Chinese voice; without one, you choose the word for its meaning instead.</p>',
     '<p><b>คำศัพท์</b> คำศัพท์ HSK 3.0 (HSK ใหม่) หลักสูตรปี 2025 ชุดเดียวกับ'
     '<a href="/th/hsk-1-word-list/">หน้ารายการคำศัพท์</a>และแบบทดสอบ HSK พร้อมความหมายภาษาไทย '
     'ข้อฟังเสียงใช้เสียงภาษาจีนของอุปกรณ์ ถ้าอุปกรณ์ไม่มีเสียงภาษาจีน จะเปลี่ยนเป็นเลือกคำจากความหมายแทน</p>'),
]

TITLE = "Daily HSK Quiz: 10 Free Questions a Day for HSK 1–5"
DESC = ("A new 10-question HSK quiz every day for HSK 1–5 (HSK 3.0): meanings, pinyin, listening and grammar, "
        "with answers. Keep a daily streak. Free, no sign-up.")
TH_TITLE = "ควิซ HSK ประจำวัน วันละ 10 ข้อ ฟรี ระดับ 1–5"
TH_DESC = ("ควิซ HSK ชุดใหม่ทุกวัน วันละ 10 ข้อ ระดับ 1–5 (HSK 3.0) ทั้งความหมาย พินอิน การฟัง และไวยากรณ์ "
           "พร้อมเฉลยภาษาไทย เก็บสถิติวันต่อเนื่อง ฟรี ไม่ต้องสมัคร")


def _check_data(root, base):
    """The quiz loads the practice test's word files: stop if one is missing or has no words."""
    for n in practice.LEVELS:
        path = root / base.strip("/") / f"hsk{n}.json"
        if not path.exists():
            raise SystemExit(f"daily: {path} not found; tools/practice.py must be built first")
        d = json.loads(path.read_text(encoding="utf-8"))
        if len(d.get("w", [])) < 50:
            raise SystemExit(f"daily: {path} has too few words for a daily quiz")
        if n in practice.GAP_LEVELS and len({g[7] for g in d.get("g", [])}) < 2:
            raise SystemExit(f"daily: {path} needs gap sentences from at least two grammar pages")


def _body(tpl, nav_html, ui, data_base):
    return ((tpl / "daily_body.html").read_text(encoding="utf-8").replace("__NAV__", nav_html)
            .replace("__UI_JSON__", json.dumps(ui, ensure_ascii=False)).replace("__DATA_BASE__", data_base))


def _ld(name, url, desc, lang):
    return json.dumps({
        "@context": "https://schema.org", "@type": "WebApplication", "name": name, "url": url, "inLanguage": lang,
        "applicationCategory": "EducationalApplication", "operatingSystem": "Any",
        "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"}, "description": desc,
    }, ensure_ascii=False)


def _css(tpl):
    return ((tpl / "checker.css").read_text(encoding="utf-8") + (tpl / "practice.css").read_text(encoding="utf-8")
            + (tpl / "daily.css").read_text(encoding="utf-8"))


def build(root, pages, nav, render, base_css, tpl, site):
    _check_data(root, practice.URL)
    body = _body(tpl, nav(pages, URL), UI_EN, practice.URL)
    out = render(TITLE, DESC, site + URL, base_css + _css(tpl), body,
                 f'<script type="application/ld+json">{_ld("Daily HSK Quiz", site + URL, DESC, "en")}</script>')
    (root / URL.strip("/")).mkdir(parents=True, exist_ok=True)
    (root / URL.strip("/") / "index.html").write_text(out, encoding="utf-8")
    return [URL]


def build_th(*, root, tpl, site, render, nav, font_link, foot, base_css, th_css):
    _check_data(root, practice.TH_URL)
    body = _body(tpl, nav(TH_URL), UI_TH, practice.TH_URL)
    for a, b in TH_SWAPS:
        if body.count(a) != 1:
            raise SystemExit(f"daily: English text not found for the Thai page: {a[:60]}")
        body = body.replace(a, b)
    out = render(TH_TITLE, TH_DESC, site + TH_URL, base_css + _css(tpl) + th_css, body,
                 font_link + f'\n<script type="application/ld+json">{_ld("ควิซ HSK ประจำวัน", site + TH_URL, TH_DESC, "th")}</script>',
                 lang="th", foot=foot)
    (root / TH_URL.strip("/")).mkdir(parents=True, exist_ok=True)
    (root / TH_URL.strip("/") / "index.html").write_text(out, encoding="utf-8")
    return [TH_URL]


def alternates(root):
    return {URL: TH_URL}
