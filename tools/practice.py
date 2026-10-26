"""HSK practice test, built to /hsk-practice-test/ (English) and /th/hsk-practice-test/ (Thai).

One page with a level picker (HSK 1-5). The page (templates/practice_body.html, CSS in templates/practice.css)
loads one JSON file per level and draws a 20-question test in the browser, mixing five kinds of question:
the meaning of a word, the word for a meaning, the pinyin of a word, a word heard with the device's Chinese voice
(only when it has one), and (HSK 1-3) a sentence with a gap from the grammar pages. The best score per level stays
in the learner's browser (localStorage); nothing is sent anywhere.

Data files read:
  data/hskN.tsv                  words, pinyin, English (N = 1-5); Thai from data/th/ (HSK 5 in English until
                                 data/th/hsk5_th.tsv covers every word, as on the flashcards)
  tones/words.json, strokes/     syllables and dictionary readings, to make wrong pinyin options that are certainly wrong
  data/practice/gaps.tsv         the gap sentences, one per line: slug, worksheet|example, sentence with ＿＿, answer.
                                 Every line was checked by hand to have exactly one right option once the meaning is
                                 shown; the options are the choices of that page's worksheet exercise, the meaning
                                 and pinyin come from data/learn/<slug>.json and data/th/learn/<slug>.json. The build
                                 stops if a line no longer matches the grammar page (edit or remove the line).
                                 New example sentences are not used until a line is added for them.

Outputs:
  hsk-practice-test/index.html, hsk-practice-test/hskN.json        English
  th/hsk-practice-test/index.html, th/hsk-practice-test/hskN.json  Thai

hskN.json: {"w": [[word, pinyin, meaning, [wrong pinyin, ...], audio_ok, [indices of words whose meaning overlaps]],
                  ...],
            "g": [[before gap, after gap, answer, [options], meaning, answer pinyin, sentence pinyin or "", slug], ...]}
Wrong options never share a character, a meaning or the pinyin (ignoring tones) with the answer; the page checks this
again when it draws a question.

The Thai page is the English template with its text swapped for Thai; the build stops if a string is not found.
"""
import glob
import json
import pathlib
import random
import re
import sys
import unicodedata

URL = "/hsk-practice-test/"
TH_URL = "/th/hsk-practice-test/"
LEVELS = (1, 2, 3, 4, 5)
GAP_LEVELS = (1, 2, 3)
BLANK = "＿＿"

# Pinyin of a gap answer when the word list gives another reading, or the option is not a word-list entry.
ANSWER_PINYIN = {
    "不一样": "bù yíyàng", "不太": "bú tài", "不让": "bú ràng", "没有在": "méiyǒu zài", "没有让": "méiyǒu ràng",
    "越来越": "yuè lái yuè", "还没有": "hái méiyǒu", "过": "guo", "还": "hái",
}
ANSWER_PINYIN_BY_PAGE = {("dei-have-to", "得"): "děi"}

UI_EN = {
    "q": "Question", "of": "of", "best": "Best", "start": "Start the HSK {n} test",
    "startSub": "20 questions on {parts}. About 5 minutes.", "pMeaning": "meanings", "pWord": "words",
    "pPinyin": "pinyin", "pListen": "listening", "pGap": "grammar gaps", "sep": ", ", "and": " and ",
    "askMeaning": "What does this word mean?", "askWord": "Which word means this?",
    "askPinyin": "How do you read this word?", "askListen": "Listen. Which word do you hear?",
    "askGap": "Choose the word that fills the gap.", "play": "Play again", "slow": "Slow",
    "right": "Right!", "wrong": "Not quite.", "answer": "Answer", "next": "Next question", "finish": "See my score",
    "grammar": "Read about this grammar point", "learnBase": "/learn/",
    "scoreHead": "Your score", "bestNew": "New best score for HSK {n}!", "bestOld": "Your best for HSK {n}: {b} / 20",
    "msg4": "Excellent. You know HSK {n} well: try the next level.", "msg3": "Good work. Review the words below and try again.",
    "msg2": "Keep going. Learn the words below with the flashcards, then try again.",
    "msg1": "HSK {n} is still new for you. The flashcards are a good place to start.",
    "missedHead": "Words to review", "noMissed": "You got every question right.",
    "add": "Add these words to my HSK {n} flashcards", "added": "Added. They come first in your next flashcard session.",
    "openCards": "Open the HSK {n} flashcards →", "cardsBase": "/hsk-flashcards/",
    "again": "Try again", "nextLevel": "Next level: HSK {m}",
    "loading": "Loading the test…", "loadFail": "The test could not be loaded. Check your connection and try again.",
    "noVoice": "Your device has no Chinese voice, so this test has no listening questions.",
}
UI_TH = {
    "q": "ข้อ", "of": "จาก", "best": "คะแนนสูงสุด", "start": "เริ่มทำแบบทดสอบ HSK {n}",
    "startSub": "20 ข้อ ทั้ง{parts} ใช้เวลาประมาณ 5 นาที", "pMeaning": "ความหมาย", "pWord": "คำศัพท์",
    "pPinyin": "พินอิน", "pListen": "การฟัง", "pGap": "การเติมคำในประโยค", "sep": " ", "and": " และ",
    "askMeaning": "คำนี้แปลว่าอะไร?", "askWord": "คำไหนมีความหมายนี้?",
    "askPinyin": "คำนี้อ่านว่าอย่างไร?", "askListen": "ฟังแล้วเลือกคำที่ได้ยิน",
    "askGap": "เลือกคำที่เติมในช่องว่างได้ถูกต้อง", "play": "ฟังอีกครั้ง", "slow": "ช้าลง",
    "right": "ถูกต้อง!", "wrong": "ยังไม่ถูก", "answer": "คำตอบ", "next": "ข้อต่อไป", "finish": "ดูคะแนน",
    "grammar": "อ่านเรื่องไวยากรณ์ข้อนี้", "learnBase": "/th/learn/",
    "scoreHead": "คะแนนของคุณ", "bestNew": "คะแนนสูงสุดใหม่ของ HSK {n}!", "bestOld": "คะแนนสูงสุดของคุณใน HSK {n}: {b} / 20",
    "msg4": "ยอดเยี่ยม คุณรู้คำศัพท์ HSK {n} ดีมาก ลองระดับถัดไปเลย", "msg3": "ทำได้ดี ทบทวนคำด้านล่างแล้วลองอีกครั้ง",
    "msg2": "สู้ต่อไป ท่องคำด้านล่างด้วยแฟลชการ์ดแล้วลองใหม่อีกครั้ง",
    "msg1": "HSK {n} ยังใหม่สำหรับคุณ เริ่มจากแฟลชการ์ดก่อนก็ดี",
    "missedHead": "คำที่ควรทบทวน", "noMissed": "คุณตอบถูกทุกข้อ",
    "add": "เพิ่มคำเหล่านี้ในแฟลชการ์ด HSK {n} ของฉัน", "added": "เพิ่มแล้ว คำเหล่านี้จะขึ้นก่อนในการเรียนแฟลชการ์ดครั้งต่อไป",
    "openCards": "เปิดแฟลชการ์ด HSK {n} →", "cardsBase": "/th/hsk-flashcards/",
    "again": "ทำอีกครั้ง", "nextLevel": "ระดับถัดไป: HSK {m}",
    "loading": "กำลังโหลดแบบทดสอบ…", "loadFail": "โหลดแบบทดสอบไม่ได้ ตรวจสอบอินเทอร์เน็ตแล้วลองอีกครั้ง",
    "noVoice": "อุปกรณ์ของคุณไม่มีเสียงภาษาจีน แบบทดสอบนี้จึงไม่มีข้อฟังเสียง",
}

TH_SWAPS = [
    ('<span>New HSK · 2025 syllabus</span><span class="chip">Levels 1–5</span><span class="chip">Free</span>',
     '<span>HSK ใหม่ · หลักสูตรปี 2025</span><span class="chip">ระดับ 1–5</span><span class="chip">ฟรี</span>'),
    ('<h1><span class="zh">测试</span>HSK Practice Test</h1>', '<h1><span class="zh">测试</span>แบบทดสอบ HSK</h1>'),
    ('<p class="lede">Choose your level and answer 20 questions on the HSK 3.0 words: meanings, pinyin, listening and '
     'grammar. You see the right answer after every question, and the words you missed at the end.</p>',
     '<p class="lede">เลือกระดับแล้วตอบคำถาม 20 ข้อจากคำศัพท์ HSK 3.0 ทั้งความหมาย พินอิน การฟัง และไวยากรณ์ '
     'เห็นเฉลยทันทีหลังตอบแต่ละข้อ และสรุปคำที่ตอบผิดเมื่อทำครบ</p>'),
    ('<h2 id="pick-title" class="visually-hidden">Choose a level</h2>', '<h2 id="pick-title" class="visually-hidden">เลือกระดับ</h2>'),
    ('<div class="levels pt-levels" role="group" aria-label="Level">\n      <span class="lbl">Level</span>',
     '<div class="levels pt-levels" role="group" aria-label="ระดับ">\n      <span class="lbl">ระดับ</span>'),
    ('<h2 id="test-title" class="visually-hidden">Test</h2>', '<h2 id="test-title" class="visually-hidden">แบบทดสอบ</h2>'),
    ('<p class="empty" id="loading">Loading the test…</p>', '<p class="empty" id="loading">กำลังโหลดแบบทดสอบ…</p>'),
    ('This browser is not letting the page save, so your best scores will not be kept.',
     'เบราว์เซอร์นี้ไม่อนุญาตให้บันทึกข้อมูล คะแนนสูงสุดจึงจะไม่ถูกเก็บไว้'),
    ('<a id="quiz-link" href="/daily-hsk-quiz/">Ten new questions every day: the daily HSK quiz →</a>',
     '<a id="quiz-link" href="/th/daily-hsk-quiz/">คำถามใหม่ 10 ข้อทุกวัน: ควิซ HSK ประจำวัน →</a>'),
    ('<a id="listen-link" href="/chinese-listening-practice/">Train your ear: Chinese listening practice →</a>',
     '<a id="listen-link" href="/th/chinese-listening-practice/">ฝึกหูให้คุ้นเสียง: ฝึกฟังภาษาจีน →</a>'),
    ('<a id="pinyin-link" href="/pinyin-tone-practice/">Get the tones right: pinyin and tone practice →</a>',
     '<a id="pinyin-link" href="/th/pinyin-tone-practice/">ออกเสียงวรรณยุกต์ให้แม่น: ฝึกพินอินและวรรณยุกต์ →</a>'),
    ('<h2 id="guide-title">About this practice test</h2>', '<h2 id="guide-title">เกี่ยวกับแบบทดสอบนี้</h2>'),
    ('<h3>What is in the test?</h3>', '<h3>แบบทดสอบมีอะไรบ้าง?</h3>'),
    ('<p>Twenty questions drawn at random from the words of the level you choose, so every test is different. You '
     'choose the meaning of a word, the word for a meaning, and the right pinyin; you hear a word and pick it out; and '
     'at HSK 1–3 you fill the gap in a sentence from the <a href="/learn/">grammar pages</a>.</p>',
     '<p>คำถาม 20 ข้อสุ่มจากคำศัพท์ของระดับที่เลือก ทุกครั้งจึงได้ชุดคำถามไม่ซ้ำกัน มีทั้งเลือกความหมายของคำ เลือกคำจากความหมาย '
     'เลือกพินอินที่ถูกต้อง ฟังเสียงแล้วเลือกคำที่ได้ยิน และในระดับ HSK 1–3 มีข้อเติมคำในประโยคจาก'
     '<a href="/th/learn/">บทเรียนไวยากรณ์</a></p>'),
    ('<h3>Is this the HSK exam?</h3>', '<h3>นี่คือข้อสอบ HSK จริงหรือไม่?</h3>'),
    ('<p>No. It is a practice test for the vocabulary of each level, made from the HSK 3.0 word lists. The exam itself '
     'has its own listening, reading and writing papers. A good score here means you know the words that the exam '
     'expects at your level.</p>',
     '<p>ไม่ใช่ นี่คือแบบทดสอบฝึกคำศัพท์ของแต่ละระดับ ทำจากรายการคำศัพท์ HSK 3.0 ส่วนการสอบจริงมีข้อสอบการฟัง การอ่าน '
     'และการเขียนแยกต่างหาก ถ้าได้คะแนนดีในแบบทดสอบนี้ แสดงว่าคุณรู้คำศัพท์ที่การสอบกำหนดไว้สำหรับระดับของคุณ</p>'),
    ('<h3>Where is my score kept?</h3>', '<h3>คะแนนเก็บไว้ที่ไหน?</h3>'),
    ('<p>Your best score for each level is kept in this browser on this device. Your answers are not sent anywhere. '
     'Words you miss can go straight into the <a href="/hsk-flashcards/">flashcards</a>, which bring them back for '
     'review.</p>',
     '<p>คะแนนสูงสุดของแต่ละระดับเก็บไว้ในเบราว์เซอร์ของอุปกรณ์นี้ คำตอบของคุณไม่ถูกส่งไปที่ไหน '
     'คำที่ตอบผิดเพิ่มลงใน<a href="/th/hsk-flashcards/">แฟลชการ์ด</a>ได้ทันที แล้วแฟลชการ์ดจะนำกลับมาให้ทบทวน</p>'),
    ('<p><b>Words.</b> HSK 3.0 (New HSK) vocabulary, 2025 syllabus, the same lists as the '
     '<a href="/hsk-1-word-list/">word list pages</a>. Listening questions use your device\'s Chinese voice and appear '
     'only when it has one.</p>',
     '<p><b>คำศัพท์</b> คำศัพท์ HSK 3.0 (HSK ใหม่) หลักสูตรปี 2025 ชุดเดียวกับ'
     '<a href="/th/hsk-1-word-list/">หน้ารายการคำศัพท์</a> HSK 1–4 มีความหมายภาษาไทย ส่วน HSK 5 ยังเป็นภาษาอังกฤษ '
     'ข้อฟังเสียงใช้เสียงภาษาจีนของอุปกรณ์ และจะมีเฉพาะเมื่ออุปกรณ์มีเสียงภาษาจีน</p>'),
]

# --- pinyin -------------------------------------------------------------------------------------------------------

TONE_MARK = {"̄": 1, "́": 2, "̌": 3, "̀": 4}
MARK_OF = {v: k for k, v in TONE_MARK.items()}
SEPARATORS = " '’-"
# Syllables that sound close: wrong options that are a real syllable with a different initial or final.
SIMILAR = [("zh", "z"), ("ch", "c"), ("sh", "s"), ("n", "l")]
SIMILAR_FINAL = [("ang", "an"), ("eng", "en"), ("ing", "in")]


def _split_tone(ch):
    """One pinyin letter -> (base letter, tone or 0). ü stays ü."""
    d = unicodedata.normalize("NFD", ch)
    tone = 0
    base = ""
    for c in d:
        if c in TONE_MARK:
            tone = TONE_MARK[c]
        else:
            base += c
    return unicodedata.normalize("NFC", base), tone


def _place(base, tone):
    """Toneless syllable (lowercase, with ü) + tone 1-4 -> syllable with its tone mark."""
    if tone not in MARK_OF:
        return base
    if "a" in base:
        i = base.index("a")
    elif "e" in base:
        i = base.index("e")
    elif "ou" in base:
        i = base.index("o")
    else:
        i = max(base.rfind(v) for v in "iouü")
    return unicodedata.normalize("NFC", base[:i + 1] + MARK_OF[tone] + base[i + 1:])


def plain(p):
    """Pinyin compared as typed: lowercase, no separators."""
    return "".join(c for c in unicodedata.normalize("NFC", p.lower()) if c not in SEPARATORS)


def toneless(p):
    return "".join(_split_tone(c)[0] for c in plain(p)).replace("ü", "u")


def syllables(word, pinyin, tone_data):
    """Split the word list's pinyin into syllables using tones/words.json, or None if they don't line up.
    Returns [(start, end, base, tone)] with positions in the NFC pinyin string; tone 5 = neutral."""
    pinyin = unicodedata.normalize("NFC", pinyin)
    ref = tone_data.get(word)
    if not ref:
        parts = [tone_data.get(c) for c in word]
        if not all(parts):
            return None
        ref = " ".join(parts)
    bases = [re.sub(r"\d", "", s) for s in ref.split()]
    if len(bases) != len(word):
        return None
    letters = [(i, *_split_tone(c)) for i, c in enumerate(pinyin) if c not in SEPARATORS]
    flat = "".join(b.lower() for _, b, _ in letters)
    if flat != "".join(bases):
        return None
    out, k = [], 0
    for b in bases:
        chunk = letters[k:k + len(b)]
        k += len(b)
        tones = [t for _, _, t in chunk if t]
        if len(tones) > 1:
            return None
        out.append((chunk[0][0], chunk[-1][0] + 1, b, tones[0] if tones else 5))
    return out


def _spoken(tones):
    """Third tone before a third tone is said as a second tone."""
    return [2 if t == 3 and k + 1 < len(tones) and tones[k + 1] == 3 else t for k, t in enumerate(tones)]


def wrong_pinyin(word, pinyin, tone_data, valid, char_readings, rng):
    """Up to 6 pinyin strings that are certainly not a reading of the word: one or two syllables with another tone,
    or a close-sounding real syllable. Never touches 一 and 不 (their tone changes), neutral tones or 儿, and never
    gives a tone pattern that sounds the same as the right one (3-3 is said 2-3)."""
    if ";" in pinyin or "/" in pinyin:
        return []
    pinyin = unicodedata.normalize("NFC", pinyin)
    sy = syllables(word, pinyin, tone_data)
    if not sy:
        return []
    bad = {plain(pinyin)}
    ref = tone_data.get(word, "").split()
    if ref and all(re.fullmatch(r"[a-zü]+[1-5]", x) for x in ref):  # the dictionary reading, if written differently
        bad.add(plain("".join(_place(x[:-1], int(x[-1])) for x in ref)))
    if len(word) == 1:
        bad |= {plain(r) for r in char_readings.get(word, ())}
    bases = [x[2] for x in sy]
    tones = [x[3] for x in sy]

    def render(changes):
        s, shift = pinyin, 0
        for k, (base, tone) in sorted(changes.items()):
            a, b, _, _ = sy[k]
            text = _place(base, tone)
            if pinyin[a].isupper():
                text = text[0].upper() + text[1:]
            s = s[:a + shift] + text + s[b + shift:]
            shift += len(text) - (b - a)
        return s

    def sounds_right(changes):
        nb = [changes.get(k, (bases[k], tones[k]))[0] for k in range(len(sy))]
        nt = [changes.get(k, (bases[k], tones[k]))[1] for k in range(len(sy))]
        return nb == bases and _spoken(nt) == _spoken(tones)

    changeable = [k for k in range(len(sy)) if tones[k] in (1, 2, 3, 4) and word[k] not in "一不" and bases[k] != "r"]
    tone_opts, similar, two = [], [], []
    for k in changeable:
        base, tone = bases[k], tones[k]
        tone_opts += [{k: (base, t)} for t in (1, 2, 3, 4) if t != tone]
        alts = set()
        for x, y in SIMILAR:
            for a, b in ((x, y), (y, x)):
                if base.startswith(a) and not (len(a) == 1 and base[1:2] == "h" and a in "zcs"):
                    alts.add(b + base[len(a):])
        for x, y in SIMILAR_FINAL:
            for a, b in ((x, y), (y, x)):
                if base.endswith(a):
                    alts.add(base[:-len(a)] + b)
        similar += [{k: (nb, tone)} for nb in sorted(alts) if nb in valid and nb != base]
    for i, a in enumerate(changeable):
        for b in changeable[i + 1:]:
            two += [{a: (bases[a], ta), b: (bases[b], tb)} for ta in (1, 2, 3, 4) for tb in (1, 2, 3, 4)
                    if ta != tones[a] and tb != tones[b]]
    rng.shuffle(tone_opts)
    rng.shuffle(similar)
    rng.shuffle(two)
    order = []  # two tone changes for every close-sounding syllable, then changes to two syllables
    for k in range(max(len(tone_opts), 2 * len(similar))):
        order += tone_opts[2 * k:2 * k + 2] + similar[k:k + 1]
    order += two
    out = []
    for ch in order:
        if sounds_right(ch):
            continue
        s = render(ch)
        if plain(s) not in bad and s not in out:
            out.append(s)
        if len(out) == 6:
            break
    return out if len(out) >= 3 else []


# --- meanings ------------------------------------------------------------------------------------------------------

EN_STOP = {"to", "a", "an", "the", "of", "for", "be", "and", "or", "in", "on", "at", "by", "with", "as", "sb", "sth",
           "someone", "something", "one's", "etc", "e", "g", "is", "it", "its", "s"}


def _en_tokens(m):
    out = set()
    for w in re.findall(r"[a-z']+", m.lower()):
        w = w.strip("'")
        if not w or w in EN_STOP:
            continue
        if len(w) > 4 and w.endswith("ies"):
            w = w[:-3] + "y"
        elif len(w) > 3 and w.endswith("s") and not w.endswith("ss"):
            w = w[:-1]
        out.add(w)
    return out


def _th_tokens(m):
    return {t for t in re.split(r"[\s,;()/、:“”\"'.!?…]+", m) if len(t) >= 2}


def _th_overlap(a, b):
    for x in a:
        for y in b:
            if x == y or (len(x) >= 3 and x in y) or (len(y) >= 3 and y in x):
                return True
    return False


def conflicts(en, th):
    """For each word, the indices of the words in the same level whose meaning overlaps (in English or in Thai)."""
    ent = [_en_tokens(m) for m in en]
    tht = [_th_tokens(m) for m in th] if th else None
    out = [[] for _ in en]
    for i in range(len(en)):
        for j in range(i + 1, len(en)):
            if ent[i] & ent[j] or en[i] == en[j] or (tht and (_th_overlap(tht[i], tht[j]) or th[i] == th[j])):
                out[i].append(j)
                out[j].append(i)
    return out


# --- data ----------------------------------------------------------------------------------------------------------

def _rows(root, n):
    rows = []
    for line in (root / "data" / f"hsk{n}.tsv").read_text(encoding="utf-8").splitlines():
        if line.strip():
            p = [x.strip() for x in line.split("\t")]
            rows.append((p[0], unicodedata.normalize("NFC", p[1]), p[2]))
    return rows


def _thai(root):
    """{level: [Thai meaning, ...]} for every level whose Thai list is complete."""
    import hsk4
    import hsk5
    out = {}
    for n in (1, 2, 3):
        path = root / "data" / "th" / f"hsk{n}_th.tsv"
        if path.exists():
            rows = [l.split("\t") for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]
            words = [r[0] for r in _rows(root, n)]
            if [r[0].strip() for r in rows] == words:
                out[n] = [r[1].strip() for r in rows]
    if (root / "data" / "hsk4.tsv").exists():
        _, rows4 = hsk4.read(root)
        th4 = hsk4.read_thai(root, rows4)
        if th4 and [r[0] for r in rows4] == [r[0] for r in _rows(root, 4)]:
            out[4] = th4
    th5, rows5 = hsk5.thai_meanings(root)
    if th5 and [r[0] for r in rows5] == [r[0] for r in _rows(root, 5)]:
        out[5] = th5
    return out


def _readings(root):
    """Every reading of every character, from the stroke data (Make Me a Hanzi + HSK words) and the word lists."""
    out = {}
    for f in sorted(glob.glob(str(root / "strokes" / "**" / "*.json"), recursive=True)):
        if pathlib.Path(f).parent.name == "m":
            continue  # strokes/m/ holds stroke centre lines, no readings
        for c, v in json.loads(open(f, encoding="utf-8").read()).items():
            out.setdefault(c, set()).update(unicodedata.normalize("NFC", p) for p in v.get("p", []))
    for n in LEVELS:
        for w, p, _ in _rows(root, n):
            if len(w) == 1:
                out.setdefault(w, set()).update(x.strip() for x in p.split(";"))
    # and the reading each character has inside the 12,000 words of tones/words.json (分 is fèn in 过分)
    tone_data = json.loads((root / "tones" / "words.json").read_text(encoding="utf-8"))["w"]
    for w, numbered in tone_data.items():
        syl = numbered.split()
        if len(syl) == len(w):
            for c, x in zip(w, syl):
                m = re.fullmatch(r"([a-zü]+)([1-5])", x)
                if m and m.group(1) != "r":
                    out.setdefault(c, set()).add(_place(m.group(1), int(m.group(2))))
    return out


def _gaps(root):
    """The checked gap sentences, by level: dicts with the parts, options, en/th meanings and pinyin."""
    sys.path.insert(0, str(root / "tools"))
    from check_vocab import allowed_words, check
    pages = {}
    for path in sorted((root / "data" / "learn").glob("*.json")):
        p = json.loads(path.read_text(encoding="utf-8"))
        t = root / "data" / "th" / "learn" / path.name
        pages[p["slug"]] = (p, json.loads(t.read_text(encoding="utf-8")) if t.exists() else None)
    vocab = {n: allowed_words(n) for n in GAP_LEVELS}
    py_of = {}
    for n in LEVELS:
        for w, p, _ in _rows(root, n):
            py_of.setdefault(w, p)
    out = {n: [] for n in GAP_LEVELS}
    seen = set()
    path = root / "data" / "practice" / "gaps.tsv"
    for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        where = f"data/practice/gaps.tsv line {i}"
        parts = line.split("\t")
        if len(parts) != 4:
            raise SystemExit(f"{where}: expected slug, worksheet|example, sentence, answer")
        slug, kind, gapped, answer = parts
        if slug not in pages or gapped.count(BLANK) != 1 or kind not in ("worksheet", "example"):
            raise SystemExit(f"{where}: unknown page, kind, or not exactly one {BLANK}")
        if (slug, gapped, answer) in seen:
            raise SystemExit(f"{where}: listed twice")
        seen.add((slug, gapped, answer))
        p, th = pages[slug]
        if th is None:
            raise SystemExit(f"{where}: {slug} has no Thai page in data/th/learn/")
        exs = [(k, e) for k, e in enumerate((p.get("worksheet") or {}).get("exercises", [])) if e["type"] == "choose"]
        if not exs:
            raise SystemExit(f"{where}: {slug} has no choose exercise to take the options from")
        k_ex, ex = exs[0]
        options = ex["options"]
        if answer not in options:
            raise SystemExit(f"{where}: answer {answer} is not one of the worksheet options {options}")
        full = gapped.replace(BLANK, answer)
        th_ex = th["worksheet"]["exercises"][k_ex]
        if kind == "worksheet":
            hit = [(it, th_ex["items"][j]) for j, it in enumerate(ex["items"]) if it["zh"] == gapped]
            if len(hit) != 1 or hit[0][0]["answer"] != answer:
                raise SystemExit(f"{where}: no worksheet item {gapped} with answer {answer} on {slug}")
            en, th_text, spy = hit[0][0]["en"], hit[0][1], ""
        else:
            hit = []
            for si, s in enumerate(p["sections"]):
                for ei, e in enumerate(s.get("examples", [])):
                    if e["zh"] == full:
                        hit.append((e, th["sections"][si]["examples"][ei]))
            if len(hit) != 1:
                raise SystemExit(f"{where}: no example sentence {full} on {slug}")
            words = vocab[p["level"]]
            max_len = max(len(w) for w in words)
            start = gapped.index(BLANK)
            # the gap must be whole words of the sentence, and the only place any option appears as words
            pos, spans = 0, []
            for run in re.finditer(r"[㐀-鿿豈-﫿]+", full):
                q = run.start()
                for tok in check(run.group(0), words, max_len)[0]:
                    spans.append((q, q + len(tok), tok))
                    q += len(tok)
            occ = []
            for a in range(len(spans)):
                for b in range(a, min(len(spans), a + 4)):
                    text = "".join(x[2] for x in spans[a:b + 1])
                    if text in options:
                        occ.append((spans[a][0], spans[b][1]))
            occ = [o for o in occ if not any(q != o and q[0] <= o[0] and o[1] <= q[1] for q in occ)]
            if occ != [(start, start + len(answer))]:
                raise SystemExit(f"{where}: the gap is not the one place the options appear as whole words")
            en, th_text, spy = hit[0][0]["en"], hit[0][1], hit[0][0]["py"]
        tokens, bad = check(full, vocab[p["level"]], max(len(w) for w in vocab[p["level"]]))
        if bad:
            raise SystemExit(f"{where}: above HSK {p['level']}: {full}")
        apy = ANSWER_PINYIN_BY_PAGE.get((slug, answer)) or ANSWER_PINYIN.get(answer) or py_of.get(answer)
        if not apy:
            raise SystemExit(f"{where}: no pinyin for {answer}; add it to ANSWER_PINYIN in tools/practice.py")
        before, after = gapped.split(BLANK)
        out[p["level"]].append({"before": before, "after": after, "answer": answer, "options": options,
                                "en": en, "th": th_text, "apy": apy, "spy": spy, "slug": slug})
    return out


_CACHE = {}


def _level_data(root):
    """Everything both pages need, computed once: rows, Thai, wrong pinyin, audio flags, conflicts, gaps."""
    if "d" in _CACHE:
        return _CACHE["d"]
    tone_data = json.loads((root / "tones" / "words.json").read_text(encoding="utf-8"))["w"]
    valid = {re.sub(r"\d", "", s) for v in tone_data.values() for s in v.split()}
    readings = _readings(root)
    thai = _thai(root)
    gaps = _gaps(root)
    levels = {}
    for n in LEVELS:
        rows = _rows(root, n)
        th = thai.get(n)
        conf = conflicts([r[2] for r in rows], th)
        words = []
        for (w, p, m), c in zip(rows, conf):
            rng = random.Random(f"{n}:{w}")
            wp = wrong_pinyin(w, p, tone_data, valid, readings, rng)
            # Heard words: one reading only, and no lone character with several readings or a neutral tone,
            # since a speech voice reads those out of context.
            sy = syllables(w, p, tone_data)
            audio = int(";" not in p and "/" not in p and not (len(w) == 1 and (
                len(readings.get(w, ())) > 1 or (sy and sy[0][3] == 5))))
            words.append([w, p, m, wp, audio, c])
        levels[n] = {"words": words, "th": th}
    _CACHE["d"] = (levels, gaps)
    return _CACHE["d"]


def _check_level(n, words):
    """Stop the build if a level could not give every question three wrong options."""
    for i, (w, p, m, wp, audio, conf) in enumerate(words):
        bad = set(conf)
        ok = [j for j, x in enumerate(words) if j != i and j not in bad and not set(x[0]) & set(w)
              and toneless(x[1]) != toneless(p)]
        if len(ok) < 8:
            raise SystemExit(f"practice: HSK {n} {w} has only {len(ok)} possible wrong options")
        if wp and (len(set(wp)) != len(wp) or plain(p) in {plain(x) for x in wp}):
            raise SystemExit(f"practice: bad wrong pinyin for {w}: {wp}")


def _write(root, base, lang, levels, gaps):
    folder = root / base.strip("/")
    folder.mkdir(parents=True, exist_ok=True)
    for n in LEVELS:
        d = levels[n]
        th = d["th"] if lang == "th" else None
        words = [[w, p, (th[i] if th else m), wp, audio, conf]
                 for i, (w, p, m, wp, audio, conf) in enumerate(d["words"])]
        _check_level(n, words)
        g = [[x["before"], x["after"], x["answer"], x["options"], x[lang], x["apy"], x["spy"], x["slug"]]
             for x in gaps.get(n, [])]
        (folder / f"hsk{n}.json").write_text(json.dumps({"w": words, "g": g}, ensure_ascii=False, separators=(",", ":")),
                                             encoding="utf-8")


def _ld(name, url, desc, lang):
    return json.dumps({
        "@context": "https://schema.org", "@type": "WebApplication", "name": name, "url": url, "inLanguage": lang,
        "applicationCategory": "EducationalApplication", "operatingSystem": "Any",
        "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"}, "description": desc,
    }, ensure_ascii=False)


def _body(tpl, nav_html, ui, data_base):
    return ((tpl / "practice_body.html").read_text(encoding="utf-8").replace("__NAV__", nav_html)
            .replace("__UI_JSON__", json.dumps(ui, ensure_ascii=False)).replace("__DATA_BASE__", data_base))


TITLE = "HSK Practice Test Online: Free HSK 1–5 Quiz with Answers"
DESC = ("Free HSK practice test for HSK 1–5 (HSK 3.0): 20 questions on meanings, pinyin, listening and grammar, "
        "with the answer after each one. No sign-up.")
TH_TITLE = "แบบทดสอบ HSK ออนไลน์ ฟรี ระดับ 1–5 พร้อมเฉลยทุกข้อ"
TH_DESC = ("แบบทดสอบ HSK ฟรี ระดับ 1–5 (HSK 3.0) ชุดละ 20 ข้อ ทั้งความหมาย พินอิน การฟัง และไวยากรณ์ "
           "พร้อมความหมายภาษาไทยและเฉลยทันที ไม่ต้องสมัคร")


def build(root, pages, nav, render, base_css, tpl, site):
    levels, gaps = _level_data(root)
    _write(root, URL, "en", levels, gaps)
    body = _body(tpl, nav(pages, URL), UI_EN, URL)
    css = base_css + (tpl / "checker.css").read_text(encoding="utf-8") + (tpl / "practice.css").read_text(encoding="utf-8")
    out = render(TITLE, DESC, site + URL, css, body,
                 f'<script type="application/ld+json">{_ld("HSK Practice Test", site + URL, DESC, "en")}</script>')
    (root / URL.strip("/") / "index.html").write_text(out, encoding="utf-8")
    return [URL]


def build_th(*, root, tpl, site, render, nav, font_link, foot, css):
    levels, gaps = _level_data(root)
    _write(root, TH_URL, "th", levels, gaps)
    body = _body(tpl, nav(TH_URL), UI_TH, TH_URL)
    for a, b in TH_SWAPS:
        if body.count(a) != 1:
            raise SystemExit(f"practice: English text not found for the Thai page: {a[:60]}")
        body = body.replace(a, b)
    out = render(TH_TITLE, TH_DESC, site + TH_URL, css, body,
                 font_link + f'\n<script type="application/ld+json">{_ld("แบบทดสอบ HSK", site + TH_URL, TH_DESC, "th")}</script>',
                 lang="th", foot=foot)
    (root / TH_URL.strip("/") / "index.html").write_text(out, encoding="utf-8")
    return [TH_URL]


def alternates(root):
    return {URL: TH_URL}
