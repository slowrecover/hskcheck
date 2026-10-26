"""Chinese listening practice, built to /chinese-listening-practice/ (English) and /th/chinese-listening-practice/ (Thai).

Per level (HSK 1-5), a round of 10: the page (templates/listening_body.html, CSS in templates/practice.css +
templates/listening.css) says a word, or at HSK 1-4 a short sentence, with the device's Chinese voice, and the learner
chooses what was said from 4 options in characters with pinyin. "Play again" and "Slow" replay it; a "pinyin only"
setting hides the characters. Rounds are words and sentences mixed, words only, or sentences only. Without a Mandarin
voice the page shows a notice and a link to the practice test instead. The best score per level and setting stays in
the learner's browser (localStorage); nothing is sent anywhere.

Data files read:
  data/hskN.tsv, data/th/, tones/words.json, strokes/
                                 through tools/practice.py: the words, their Thai meanings (where a level has no
                                 complete Thai list, its meanings stay in English) and which words a speech voice can say without
                                 context (one reading only; no lone character with several readings or a neutral tone)
  data/learn/<slug>.json, data/th/learn/<slug>.json
                                 the example sentences of the grammar pages (HSK 1-3), with their pinyin, English and
                                 Thai: those of at most MAX_HAN characters, in Chinese characters and ，。！？、 only
  data/practice/listening_stories.tsv
                                 short sentences from the graded stories (HSK 1-4), one per line: story slug, sentence
                                 (exactly as in the story), pinyin, English, Thai. Pinyin and translations were written
                                 for this tool and checked by hand.
The build stops if a sentence is not in its story, uses a word above its level, or if the pinyin of any sentence
does not spell, syllable for syllable, a reading of its words (tones aside), as found in the word lists,
tones/words.json and the stroke data.

Outputs:
  chinese-listening-practice/index.html, chinese-listening-practice/hskN.json        English
  th/chinese-listening-practice/index.html, th/chinese-listening-practice/hskN.json  Thai

hskN.json: {"w": [[word, pinyin, meaning], ...]                       words a voice can say on their own
            "s": [[sentence, pinyin, meaning, "g"|"s", slug, page title], ...]}   g = grammar page, s = story
Wrong options never sound like the answer: a wrong word never shares a reading with it (tones and a final 儿 aside),
and a wrong sentence never has the same syllables. The page checks this when it draws a question.

The Thai page is the English template with its text swapped for Thai; the build stops if a string is not found.
"""
import itertools
import json
import re
import sys
import unicodedata

import practice

URL = "/chinese-listening-practice/"
TH_URL = "/th/chinese-listening-practice/"
LEVELS = (1, 2, 3, 4, 5)
SENTENCE_LEVELS = (1, 2, 3, 4)
MAX_HAN = 14            # grammar examples: short sentences only
MAX_HAN_STORY = 16
SENTENCE_OK = re.compile(r"^[㐀-鿿，。！？、]+$")
HAN = re.compile(r"[㐀-鿿]")
# Names in the stories (not on the word lists), with their toneless pinyin.
NAMES = {"大卫": "dawei", "小雨": "xiaoyu", "王": "wang", "李": "li", "英国": "yingguo"}

UI_EN = {
    "q": "Question", "of": "of", "best": "Best", "start": "Start listening: HSK {n}",
    "startSub": "10 questions: {what}. Turn your sound on.", "wMix": "words and short sentences", "wWords": "words",
    "wSent": "short sentences", "ask": "Listen. What did you hear?", "play": "Play again", "slow": "Slow",
    "playFirst": "Play", "right": "Right!", "wrong": "Not quite.", "next": "Next question", "finish": "See my score",
    "fromG": "From the grammar page", "fromS": "From the story", "learnBase": "/learn/", "readBase": "/reading/",
    "scoreHead": "Your score", "bestNew": "New best score for HSK {n}!", "bestOld": "Your best for HSK {n} ({what}): {b} / {t}",
    "msg4": "Excellent. Your ear for HSK {n} is sharp: try the next level.",
    "msg3": "Good work. Listen to the ones below again, then try another round.",
    "msg2": "Keep going. Try the slow button, and learn the words below with the flashcards.",
    "msg1": "HSK {n} is still new for your ear. Try a round with characters and pinyin, and use the slow button.",
    "missedHead": "Listen again", "noMissed": "You got every question right.",
    "add": "Add the missed words to my HSK {n} flashcards", "added": "Added. They come first in your next flashcard session.",
    "cardsBase": "/hsk-flashcards/", "again": "Another round", "nextLevel": "Next level: HSK {m}",
    "testLink": "Take the HSK {n} practice test", "testBase": "/hsk-practice-test/",
    "loading": "Loading…", "loadFail": "The questions could not be loaded. Check your connection and try again.",
    "noSent": "There are no sentences at HSK 5 yet, so this round is words only.",
}
UI_TH = {
    "q": "ข้อ", "of": "จาก", "best": "คะแนนสูงสุด", "start": "เริ่มฝึกฟัง HSK {n}",
    "startSub": "10 ข้อ: {what} เปิดเสียงก่อนเริ่มนะ", "wMix": "คำศัพท์และประโยคสั้น", "wWords": "คำศัพท์",
    "wSent": "ประโยคสั้น", "ask": "ฟังแล้วเลือกสิ่งที่ได้ยิน", "play": "ฟังอีกครั้ง", "slow": "ช้าลง",
    "playFirst": "ฟังเสียง", "right": "ถูกต้อง!", "wrong": "ยังไม่ถูก", "next": "ข้อต่อไป", "finish": "ดูคะแนน",
    "fromG": "จากบทเรียนไวยากรณ์", "fromS": "จากเรื่อง", "learnBase": "/th/learn/", "readBase": "/th/reading/",
    "scoreHead": "คะแนนของคุณ", "bestNew": "คะแนนสูงสุดใหม่ของ HSK {n}!", "bestOld": "คะแนนสูงสุดของคุณใน HSK {n} ({what}): {b} / {t}",
    "msg4": "ยอดเยี่ยม หูของคุณฟัง HSK {n} ได้แม่นมาก ลองระดับถัดไปเลย",
    "msg3": "ทำได้ดี ฟังข้อด้านล่างอีกครั้ง แล้วลองอีกรอบ",
    "msg2": "สู้ต่อไป ลองกดปุ่มช้าลง และท่องคำด้านล่างด้วยแฟลชการ์ด",
    "msg1": "หูของคุณยังไม่คุ้นกับ HSK {n} ลองฝึกแบบแสดงตัวอักษรจีนและพินอิน แล้วใช้ปุ่มช้าลงช่วย",
    "missedHead": "ฟังอีกครั้ง", "noMissed": "คุณตอบถูกทุกข้อ",
    "add": "เพิ่มคำที่ตอบผิดในแฟลชการ์ด HSK {n} ของฉัน", "added": "เพิ่มแล้ว คำเหล่านี้จะขึ้นก่อนในการเรียนแฟลชการ์ดครั้งต่อไป",
    "cardsBase": "/th/hsk-flashcards/", "again": "ฝึกอีกรอบ", "nextLevel": "ระดับถัดไป: HSK {m}",
    "testLink": "ทำแบบทดสอบ HSK {n}", "testBase": "/th/hsk-practice-test/",
    "loading": "กำลังโหลด…", "loadFail": "โหลดคำถามไม่ได้ ตรวจสอบอินเทอร์เน็ตแล้วลองอีกครั้ง",
    "noSent": "HSK 5 ยังไม่มีประโยค รอบนี้จึงมีแต่คำศัพท์",
}

TH_SWAPS = [
    ('<span>New HSK · 2025 syllabus</span><span class="chip">Levels 1–5</span><span class="chip">Free</span>',
     '<span>HSK ใหม่ · หลักสูตรปี 2025</span><span class="chip">ระดับ 1–5</span><span class="chip">ฟรี</span>'),
    ('<h1><span class="zh">听力</span>Chinese Listening Practice</h1>', '<h1><span class="zh">听力</span>ฝึกฟังภาษาจีน</h1>'),
    ('<p class="lede">Hear a word or a short sentence from your HSK level and choose what was said. Replay it as often as '
     'you like, slow it down, or hide the characters and listen with pinyin only.</p>',
     '<p class="lede">ฟังคำศัพท์หรือประโยคสั้นตามระดับ HSK ของคุณ แล้วเลือกสิ่งที่ได้ยิน ฟังซ้ำได้ไม่จำกัด กดให้ช้าลงได้ '
     'หรือซ่อนตัวอักษรจีนแล้วฝึกฟังกับพินอินอย่างเดียว</p>'),
    ('<h2 id="pick-title" class="visually-hidden">Choose a level</h2>', '<h2 id="pick-title" class="visually-hidden">เลือกระดับ</h2>'),
    ('<div class="levels pt-levels" role="group" aria-label="Level">\n      <span class="lbl">Level</span>',
     '<div class="levels pt-levels" role="group" aria-label="ระดับ">\n      <span class="lbl">ระดับ</span>'),
    ('<div class="levels lp-set" role="group" aria-label="What to hear" id="kind-set">\n      <span class="lbl">Hear</span>',
     '<div class="levels lp-set" role="group" aria-label="ฟังอะไร" id="kind-set">\n      <span class="lbl">ฟัง</span>'),
    ('data-kind="mix" aria-pressed="false">Words and sentences</button>', 'data-kind="mix" aria-pressed="false">คำและประโยค</button>'),
    ('data-kind="words" aria-pressed="false">Words</button>', 'data-kind="words" aria-pressed="false">คำศัพท์</button>'),
    ('data-kind="sent" aria-pressed="false">Sentences</button>', 'data-kind="sent" aria-pressed="false">ประโยค</button>'),
    ('<div class="levels lp-set" role="group" aria-label="Answers in">\n      <span class="lbl">Answers</span>',
     '<div class="levels lp-set" role="group" aria-label="แสดงตัวเลือกเป็น">\n      <span class="lbl">ตัวเลือก</span>'),
    ('data-py="0" aria-pressed="false">Characters and pinyin</button>', 'data-py="0" aria-pressed="false">อักษรจีนและพินอิน</button>'),
    ('data-py="1" aria-pressed="false">Pinyin only</button>', 'data-py="1" aria-pressed="false">พินอินอย่างเดียว</button>'),
    ('<h2 id="test-title" class="visually-hidden">Listening</h2>', '<h2 id="test-title" class="visually-hidden">ฝึกฟัง</h2>'),
    ('<p class="empty" id="loading">Loading…</p>', '<p class="empty" id="loading">กำลังโหลด…</p>'),
    ('<p class="v">Your device has no Chinese voice</p>', '<p class="v">อุปกรณ์ของคุณไม่มีเสียงภาษาจีน</p>'),
    ('<p>This page uses the Mandarin Chinese voice of your phone or computer to read the words, and none was found. Most '
     'phones and computers can add one for free in their text-to-speech or language settings; then reload this page. '
     'Until then, you can practise the same words without sound:</p>',
     '<p>หน้านี้ใช้เสียงภาษาจีนกลางของโทรศัพท์หรือคอมพิวเตอร์ในการอ่านคำ แต่ไม่พบเสียงนี้ในอุปกรณ์ของคุณ '
     'โทรศัพท์และคอมพิวเตอร์ส่วนใหญ่เพิ่มเสียงภาษาจีนได้ฟรีในการตั้งค่าการอ่านออกเสียงหรือการตั้งค่าภาษา เพิ่มแล้วโหลดหน้านี้ใหม่ '
     'ระหว่างนี้ฝึกคำศัพท์ชุดเดียวกันแบบไม่ใช้เสียงได้ที่</p>'),
    ('<a class="button" href="/hsk-practice-test/" id="novoice-link">HSK practice test</a>',
     '<a class="button" href="/th/hsk-practice-test/" id="novoice-link">แบบทดสอบ HSK</a>'),
    ('This browser is not letting the page save, so your best scores and settings will not be kept.',
     'เบราว์เซอร์นี้ไม่อนุญาตให้บันทึกข้อมูล คะแนนสูงสุดและการตั้งค่าจึงจะไม่ถูกเก็บไว้'),
    ('<h2 id="guide-title">About listening practice</h2>', '<h2 id="guide-title">เกี่ยวกับการฝึกฟัง</h2>'),
    ('<h3>What will I hear?</h3>', '<h3>จะได้ฟังอะไรบ้าง?</h3>'),
    ('<p>Words from the HSK 3.0 list of your level and, at HSK 1–4, short sentences from the example sentences of the '
     '<a href="/learn/">grammar pages</a> and from the <a href="/reading/">graded stories</a>. Every sentence uses only '
     'words of its level. The four answers never sound alike, so there is always one right answer.</p>',
     '<p>คำศัพท์จากรายการ HSK 3.0 ของระดับที่เลือก และในระดับ HSK 1–4 มีประโยคสั้นจากตัวอย่างใน'
     '<a href="/th/learn/">บทเรียนไวยากรณ์</a>และจาก<a href="/th/reading/">เรื่องสั้นตามระดับ</a> '
     'ทุกประโยคใช้เฉพาะคำศัพท์ในระดับนั้น ตัวเลือกทั้งสี่ไม่มีคู่ไหนออกเสียงเหมือนกัน จึงมีคำตอบที่ถูกเพียงข้อเดียวเสมอ</p>'),
    ('<h3>How should I practise?</h3>', '<h3>ควรฝึกอย่างไร?</h3>'),
    ('<p>Listen first, before you read the answers. If you are not sure, press Slow and listen again. When the characters '
     'start to feel easy, switch to pinyin only: then you have to recognise the sounds, not the characters, which is '
     'closer to what the listening paper of the exam asks.</p>',
     '<p>ฟังก่อนแล้วค่อยอ่านตัวเลือก ถ้าไม่แน่ใจให้กดช้าลงแล้วฟังอีกครั้ง เมื่อดูตัวอักษรจีนแล้วรู้สึกง่าย '
     'ให้เปลี่ยนเป็นพินอินอย่างเดียว คุณจะต้องจำเสียงได้จริง ๆ ไม่ใช่แค่จำตัวอักษร ซึ่งใกล้เคียงกับข้อสอบการฟังมากกว่า</p>'),
    ('<h3>Why does the voice sound different on my phone?</h3>', '<h3>ทำไมเสียงในโทรศัพท์ของฉันฟังไม่เหมือนกัน?</h3>'),
    ('<p>The words are read by the Chinese voice built into your device, so the voice depends on your phone or computer. '
     'Words that a voice can easily misread on their own, such as single characters with two readings, are left out. '
     'For written and spoken tones, see <a href="/mandarin-tone-changes/">tone changes</a>.</p>',
     '<p>คำต่าง ๆ อ่านด้วยเสียงภาษาจีนที่มีอยู่ในอุปกรณ์ เสียงจึงต่างกันไปตามโทรศัพท์หรือคอมพิวเตอร์ '
     'คำที่เสียงอ่านอาจอ่านผิดได้ง่ายเมื่ออยู่ลำพัง เช่น อักษรตัวเดียวที่อ่านได้สองแบบ จะไม่นำมาใช้ '
     'ส่วนวรรณยุกต์ที่เขียนกับที่ออกเสียงจริง ดูได้ที่<a href="/mandarin-tone-changes/">การเปลี่ยนเสียงวรรณยุกต์</a></p>'),
    ('<h3>Where is my score kept?</h3>', '<h3>คะแนนเก็บไว้ที่ไหน?</h3>'),
    ('<p>Your best score for each level is kept in this browser on this device, and nothing is sent anywhere. Words you '
     'miss can go straight into the <a href="/hsk-flashcards/">flashcards</a>. For a mixed test of meanings, pinyin and '
     'grammar, try the <a href="/hsk-practice-test/">HSK practice test</a>.</p>',
     '<p>คะแนนสูงสุดของแต่ละระดับเก็บไว้ในเบราว์เซอร์ของอุปกรณ์นี้ และไม่มีข้อมูลใดถูกส่งไปที่ไหน คำที่ตอบผิดเพิ่มลงใน'
     '<a href="/th/hsk-flashcards/">แฟลชการ์ด</a>ได้ทันที ถ้าอยากทดสอบทั้งความหมาย พินอิน และไวยากรณ์ ลองทำ'
     '<a href="/th/hsk-practice-test/">แบบทดสอบ HSK</a></p>'),
    ('<p><b>Words and sentences.</b> HSK 3.0 (New HSK) vocabulary, 2025 syllabus, the same lists as the '
     '<a href="/hsk-1-word-list/">word list pages</a>. Sentences come from this site\'s grammar pages and stories, with '
     'pinyin checked against the word lists. Audio uses your device\'s Chinese voice.</p>',
     '<p><b>คำศัพท์และประโยค</b> คำศัพท์ HSK 3.0 (HSK ใหม่) หลักสูตรปี 2025 ชุดเดียวกับ'
     '<a href="/th/hsk-1-word-list/">หน้ารายการคำศัพท์</a> พร้อมความหมายภาษาไทย '
     'ประโยคมาจากบทเรียนไวยากรณ์และเรื่องสั้นของเว็บไซต์นี้ พินอินตรวจกับรายการคำศัพท์แล้ว เสียงใช้เสียงภาษาจีนของอุปกรณ์</p>'),
]

TITLE = "Chinese Listening Practice: Free HSK 1–5 Audio Quiz"
DESC = ("Free Chinese listening practice for HSK 1–5 (HSK 3.0): hear a word or short sentence and choose what was said. "
        "Slow replay and a pinyin-only mode. No sign-up.")
TH_TITLE = "ฝึกฟังภาษาจีน HSK 1–5 ฟรี ฟังคำและประโยคแล้วเลือกคำตอบ"
TH_DESC = ("ฝึกฟังภาษาจีนฟรี ระดับ HSK 1–5 (HSK 3.0) ฟังคำหรือประโยคสั้นแล้วเลือกสิ่งที่ได้ยิน "
           "ฟังซ้ำแบบช้าได้ มีโหมดพินอินอย่างเดียว พร้อมความหมายภาษาไทย ไม่ต้องสมัคร")


# --- pinyin check --------------------------------------------------------------------------------------------------

def _toneless(p):
    return "".join(c for c in unicodedata.normalize("NFD", p.lower()) if "a" <= c <= "z")


def _reading_index(root):
    """Every toneless reading of every word and character the site knows."""
    out = {}
    for n in LEVELS:
        for w, p, _ in practice._rows(root, n):
            for r in re.split(r"[;/]", p):
                out.setdefault(w, set()).add(_toneless(r))
    tone_data = json.loads((root / "tones" / "words.json").read_text(encoding="utf-8"))["w"]
    for w, v in tone_data.items():
        out.setdefault(w, set()).add(re.sub(r"[^a-z]", "", v.replace("ü", "u")))
    for c, rs in practice._readings(root).items():
        out.setdefault(c, set()).update(_toneless(r) for r in rs)
    for w, r in NAMES.items():
        out.setdefault(w, set()).add(r)
    return out


def _token_readings(tok, idx):
    if tok in idx:
        return idx[tok]
    if tok.endswith("儿") and tok[:-1] in idx:
        return {x + "r" for x in idx[tok[:-1]]}
    if tok + "儿" in idx:
        return {x[:-1] for x in idx[tok + "儿"] if x.endswith("r")}
    if len(tok) <= 4 and all(c in idx for c in tok):
        return {"".join(t) for t in itertools.product(*[sorted(idx[c]) for c in tok])}
    return set()


def pinyin_matches(sentence, pinyin, words, max_len, idx):
    """True if the pinyin spells, in order, one reading of each word of the sentence (tones aside)."""
    from check_vocab import check
    toks = [t.strip("[]") for t in check(sentence, words, max_len)[0]]
    target = _toneless(pinyin)
    ends = {0}
    for t in toks:
        ends = {i + len(o) for i in ends for o in _token_readings(t, idx) if o and target.startswith(o, i)}
        if not ends:
            return False
    return len(target) in ends


# --- data ----------------------------------------------------------------------------------------------------------

def _sentences(root):
    """{level: [dict(zh, py, en, th, kind, slug, title_en, title_th)]} from the grammar pages and the stories."""
    sys.path.insert(0, str(root / "tools"))
    from check_vocab import allowed_words, check
    idx = _reading_index(root)
    vocab = {n: allowed_words(n) for n in SENTENCE_LEVELS}
    out = {n: [] for n in SENTENCE_LEVELS}
    seen = set()

    def add(n, item, where):
        words = vocab[n]
        max_len = max(len(w) for w in words)
        bare = item["zh"]
        if item["kind"] == "s":  # names in a story are allowed although not on the word lists
            for name in NAMES:
                bare = bare.replace(name, "，")
        if check(bare, words, max_len)[1]:
            raise SystemExit(f"listening: {where}: above HSK {n}: {item['zh']}")
        if not pinyin_matches(item["zh"], item["py"], words | set(NAMES), max(max_len, 2), idx):
            raise SystemExit(f"listening: {where}: the pinyin does not match the characters: {item['zh']} {item['py']}")
        if _key(item["py"]) in seen:  # the same sentence, or one that sounds the same (他 / 她): keep the first
            return
        seen.add(_key(item["py"]))
        out[n].append(item)

    for path in sorted((root / "data" / "learn").glob("*.json")):
        p = json.loads(path.read_text(encoding="utf-8"))
        n = p["level"]
        if n not in SENTENCE_LEVELS:
            continue
        tpath = root / "data" / "th" / "learn" / path.name
        th = json.loads(tpath.read_text(encoding="utf-8")) if tpath.exists() else None
        for si, s in enumerate(p["sections"]):
            for ei, e in enumerate(s.get("examples", [])):
                if not SENTENCE_OK.match(e["zh"]) or len(HAN.findall(e["zh"])) > MAX_HAN:
                    continue
                try:
                    th_text = th["sections"][si]["examples"][ei] if th else e["en"]
                except (IndexError, KeyError):
                    raise SystemExit(f"listening: data/th/learn/{path.name} does not line up with the English page")
                add(n, {"zh": e["zh"], "py": e["py"], "en": e["en"], "th": th_text, "kind": "g", "slug": p["slug"],
                        "title_en": p["h1"], "title_th": th["h1"] if th else p["h1"]}, f"data/learn/{path.name}")

    stories = {}
    for path in (root / "data" / "stories").glob("*.json"):
        s = json.loads(path.read_text(encoding="utf-8"))
        stories[s["slug"]] = s
    tsv = root / "data" / "practice" / "listening_stories.tsv"
    for i, line in enumerate(tsv.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        where = f"data/practice/listening_stories.tsv line {i}"
        parts = line.split("\t")
        if len(parts) != 5:
            raise SystemExit(f"{where}: expected slug, sentence, pinyin, English, Thai")
        slug, zh, py, en, th_text = parts
        s = stories.get(slug)
        if not s:
            raise SystemExit(f"{where}: no story {slug}")
        if s["level"] not in SENTENCE_LEVELS or zh not in "".join(s["paras"]):
            raise SystemExit(f"{where}: {zh} is not in the story {slug}")
        if not SENTENCE_OK.match(zh) or len(HAN.findall(zh)) > MAX_HAN_STORY:
            raise SystemExit(f"{where}: not a short sentence in characters and ，。！？、 only")
        add(s["level"], {"zh": zh, "py": unicodedata.normalize("NFC", py), "en": en, "th": th_text, "kind": "s",
                         "slug": slug, "title_en": s["title_en"], "title_th": s["title_th"]}, where)
    return out


def _key(py):
    """What a sentence sounds like, tones aside."""
    return _toneless(py)


def _write(root, base, lang, levels, sentences):
    folder = root / base.strip("/")
    folder.mkdir(parents=True, exist_ok=True)
    for n in LEVELS:
        d = levels[n]
        th = d["th"] if lang == "th" else None
        words = [[w, p, th[i] if th else m] for i, (w, p, m, _wp, audio, _c) in enumerate(d["words"]) if audio]
        if len(words) < 50:
            raise SystemExit(f"listening: HSK {n} has only {len(words)} words a voice can say")
        sent = sentences.get(n, [])
        keys = [_key(x["py"]) for x in sent]
        if len(set(keys)) != len(keys):
            dup = [x["zh"] for x, k in zip(sent, keys) if keys.count(k) > 1]
            raise SystemExit(f"listening: HSK {n} sentences that sound the same: {dup}")
        if sent and len(sent) < 6:
            raise SystemExit(f"listening: HSK {n} needs at least 6 sentences for wrong options")
        s = [[x["zh"], x["py"], x[lang], x["kind"], x["slug"], x["title_" + lang]] for x in sent]
        (folder / f"hsk{n}.json").write_text(json.dumps({"w": words, "s": s}, ensure_ascii=False, separators=(",", ":")),
                                             encoding="utf-8")


_CACHE = {}


def _data(root):
    if "d" not in _CACHE:
        levels, _gaps = practice._level_data(root)
        _CACHE["d"] = (levels, _sentences(root))
    return _CACHE["d"]


def _body(tpl, nav_html, ui, data_base):
    return ((tpl / "listening_body.html").read_text(encoding="utf-8").replace("__NAV__", nav_html)
            .replace("__UI_JSON__", json.dumps(ui, ensure_ascii=False)).replace("__DATA_BASE__", data_base))


def _ld(name, url, desc, lang):
    return json.dumps({
        "@context": "https://schema.org", "@type": "WebApplication", "name": name, "url": url, "inLanguage": lang,
        "applicationCategory": "EducationalApplication", "operatingSystem": "Any",
        "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"}, "description": desc,
    }, ensure_ascii=False)


def _css(tpl):
    return ((tpl / "checker.css").read_text(encoding="utf-8") + (tpl / "practice.css").read_text(encoding="utf-8")
            + (tpl / "listening.css").read_text(encoding="utf-8"))


def build(root, pages, nav, render, base_css, tpl, site):
    levels, sentences = _data(root)
    _write(root, URL, "en", levels, sentences)
    body = _body(tpl, nav(pages, URL), UI_EN, URL)
    out = render(TITLE, DESC, site + URL, base_css + _css(tpl), body,
                 f'<script type="application/ld+json">{_ld("Chinese Listening Practice", site + URL, DESC, "en")}</script>')
    (root / URL.strip("/") / "index.html").write_text(out, encoding="utf-8")
    return [URL]


def build_th(*, root, tpl, site, render, nav, font_link, foot, base_css, th_css):
    levels, sentences = _data(root)
    _write(root, TH_URL, "th", levels, sentences)
    body = _body(tpl, nav(TH_URL), UI_TH, TH_URL)
    for a, b in TH_SWAPS:
        if body.count(a) != 1:
            raise SystemExit(f"listening: English text not found for the Thai page: {a[:60]}")
        body = body.replace(a, b)
    out = render(TH_TITLE, TH_DESC, site + TH_URL, base_css + _css(tpl) + th_css, body,
                 font_link + f'\n<script type="application/ld+json">{_ld("ฝึกฟังภาษาจีน", site + TH_URL, TH_DESC, "th")}</script>',
                 lang="th", foot=foot)
    (root / TH_URL.strip("/") / "index.html").write_text(out, encoding="utf-8")
    return [TH_URL]


def alternates(root):
    return {URL: TH_URL}
