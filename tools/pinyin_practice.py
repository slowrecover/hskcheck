"""Pinyin and tone practice, built to /pinyin-tone-practice/ (English) and /th/pinyin-tone-practice/ (Thai).

Per level (HSK 1-5), rounds of 10 words in one of two modes (templates/pinyin_body.html, CSS in
templates/practice.css + templates/pinyin.css):
  type   see a word (characters and meaning) and type its pinyin. Tone numbers (ni3hao3) and tone marks (nǐhǎo) are
         both accepted, ü as v or u:, spaces and apostrophes optional, the neutral tone with 5, 0 or no number. The
         answer is checked against the readings of the word list; for words with 一 or 不 the original tone (yī, bù)
         is accepted as well as the changed one the word list writes (yìqǐ).
  tones  see a word (characters, pinyin without tones and meaning) or hear it with the device's Chinese voice, and
         choose its tones from 4 patterns (e.g. 3-3, 2-4; 5 is the neutral tone). The tones come from
         tones/words.json and are used only where they agree with the word list. Wrong patterns never sound like the
         right one (3-3 is said 2-3, so 2-3 is never a wrong option for a 3-3 word). Hearing is offered only on a
         device with a Mandarin voice, and only for words a voice can say on their own with their written tones
         (no 一 or 不, no third tone before a third tone).
The best score per level and mode stays in the learner's browser (localStorage); nothing is sent anywhere.

Data files read:
  data/hskN.tsv, data/th/        the words, their pinyin and meanings (Thai on the Thai page), through tools/practice.py
  tones/words.json               dictionary tones and the list of Mandarin syllables; for a word it does not list,
                                 the tones of its characters (used only when they agree with the word list)
  strokes/                       every reading of every character (through tools/practice.py), to split the word
                                 list's pinyin into one syllable per character
The build stops if a level ends up with too few words for either mode, or if a reading cannot be told apart from
the others.

Outputs:
  pinyin-tone-practice/index.html, pinyin-tone-practice/hskN.json        English
  th/pinyin-tone-practice/index.html, th/pinyin-tone-practice/hskN.json  Thai

hskN.json: {"w": [[word, pinyin as in the word list, meaning, [accepted readings, "ni3 hao3" style],
                   dictionary tones for the tone mode ("ni3 hao3") or "", 1 if it can be heard in the tone mode,
                   1 if a speech voice can say it on its own (the Listen button)], ...]}
A lone character read with the same syllable in two tones (好 hǎo / hào) is left out of the tone mode, and the wrong
patterns never change a neutral tone or make one, so no wrong pattern is another reading of the word.

The Thai page is the English template with its text swapped for Thai; the build stops if a string is not found.
"""
import json
import re
import unicodedata

import practice

URL = "/pinyin-tone-practice/"
TH_URL = "/th/pinyin-tone-practice/"
LEVELS = (1, 2, 3, 4, 5)
MIN_WORDS = 60
SEP = " '’-"

UI_EN = {
    "q": "Question", "of": "of", "best": "Best", "start": "Start: HSK {n}",
    "subType": "10 words: type the pinyin with its tones.", "subSee": "10 words: choose the tones of each word.",
    "subHear": "10 words: listen and choose the tones. Turn your sound on.",
    "askType": "Type the pinyin of this word, with tones.", "askSee": "Which tones does this word have?",
    "askHear": "Listen. Which tones do you hear?",
    "hint": "Tone numbers (ni3hao3) or tone marks (nǐhǎo). Type ü as v. Neutral tone: 5 or no number.",
    "inputLabel": "Pinyin", "check": "Check", "dunno": "Show the answer", "play": "Play again", "slow": "Slow",
    "listen": "Listen", "right": "Right!", "wrong": "Not quite.",
    "noTones": "Add the tones: a number after each syllable (ni3hao3) or tone marks (nǐhǎo).",
    "badChars": "Type the pinyin in Latin letters, with tone numbers or tone marks.",
    "tonesWrong": "The syllables are right, but not all the tones.",
    "spoken": "That is how it is said, but pinyin writes the original tones. See tone changes.",
    "toneLink": "/mandarin-tone-changes/", "yourAnswer": "You typed", "neutral": "5 = neutral tone",
    "next": "Next question", "finish": "See my score",
    "scoreHead": "Your score", "bestNew": "New best score for HSK {n}!", "bestOld": "Your best for HSK {n} ({what}): {b} / {t}",
    "wType": "typing pinyin", "wSee": "choosing tones", "wHear": "hearing tones",
    "msg4": "Excellent. Your pinyin for HSK {n} is solid: try the next level.",
    "msg3": "Good work. Look at the words below again, then try another round.",
    "msg2": "Keep going. Say the words below out loud with their tones, and learn them with the flashcards.",
    "msg1": "Tones take time. Say each word below out loud with its tones, then try again.",
    "missedHead": "Words to review", "noMissed": "You got every question right.",
    "add": "Add the missed words to my HSK {n} flashcards", "added": "Added. They come first in your next flashcard session.",
    "cardsBase": "/hsk-flashcards/", "again": "Another round", "nextLevel": "Next level: HSK {m}",
    "testLink": "Take the HSK {n} practice test", "testBase": "/hsk-practice-test/",
    "loading": "Loading…", "loadFail": "The words could not be loaded. Check your connection and try again.",
}
UI_TH = {
    "q": "ข้อ", "of": "จาก", "best": "คะแนนสูงสุด", "start": "เริ่ม: HSK {n}",
    "subType": "10 คำ: พิมพ์พินอินพร้อมวรรณยุกต์", "subSee": "10 คำ: เลือกวรรณยุกต์ของแต่ละคำ",
    "subHear": "10 คำ: ฟังแล้วเลือกวรรณยุกต์ เปิดเสียงก่อนเริ่มนะ",
    "askType": "พิมพ์พินอินของคำนี้พร้อมวรรณยุกต์", "askSee": "คำนี้มีวรรณยุกต์อะไรบ้าง?",
    "askHear": "ฟังแล้วเลือกวรรณยุกต์ที่ได้ยิน",
    "hint": "ใช้ตัวเลขวรรณยุกต์ (ni3hao3) หรือเครื่องหมายวรรณยุกต์ (nǐhǎo) ก็ได้ พิมพ์ ü เป็น v เสียงเบาใช้ 5 หรือไม่ใส่ตัวเลข",
    "inputLabel": "พินอิน", "check": "ตรวจคำตอบ", "dunno": "ดูเฉลย", "play": "ฟังอีกครั้ง", "slow": "ช้าลง",
    "listen": "ฟังเสียง", "right": "ถูกต้อง!", "wrong": "ยังไม่ถูก",
    "noTones": "ใส่วรรณยุกต์ด้วย: ตัวเลขหลังแต่ละพยางค์ (ni3hao3) หรือเครื่องหมายวรรณยุกต์ (nǐhǎo)",
    "badChars": "พิมพ์พินอินเป็นตัวอักษรโรมัน พร้อมตัวเลขหรือเครื่องหมายวรรณยุกต์",
    "tonesWrong": "พยางค์ถูกแล้ว แต่วรรณยุกต์ยังไม่ถูกทั้งหมด",
    "spoken": "นี่คือเสียงที่พูดจริง แต่พินอินเขียนวรรณยุกต์เดิม ดูเรื่องการเปลี่ยนเสียงวรรณยุกต์",
    "toneLink": "/mandarin-tone-changes/", "yourAnswer": "คุณพิมพ์", "neutral": "5 = เสียงเบา",
    "next": "ข้อต่อไป", "finish": "ดูคะแนน",
    "scoreHead": "คะแนนของคุณ", "bestNew": "คะแนนสูงสุดใหม่ของ HSK {n}!", "bestOld": "คะแนนสูงสุดของคุณใน HSK {n} ({what}): {b} / {t}",
    "wType": "พิมพ์พินอิน", "wSee": "เลือกวรรณยุกต์", "wHear": "ฟังวรรณยุกต์",
    "msg4": "ยอดเยี่ยม พินอินระดับ HSK {n} ของคุณแม่นมาก ลองระดับถัดไปเลย",
    "msg3": "ทำได้ดี ทบทวนคำด้านล่างอีกครั้ง แล้วลองอีกรอบ",
    "msg2": "สู้ต่อไป ลองออกเสียงคำด้านล่างพร้อมวรรณยุกต์ดัง ๆ และท่องด้วยแฟลชการ์ด",
    "msg1": "วรรณยุกต์ต้องใช้เวลาฝึก ลองออกเสียงคำด้านล่างดัง ๆ ทีละคำพร้อมวรรณยุกต์ แล้วลองใหม่อีกครั้ง",
    "missedHead": "คำที่ควรทบทวน", "noMissed": "คุณตอบถูกทุกข้อ",
    "add": "เพิ่มคำที่ตอบผิดในแฟลชการ์ด HSK {n} ของฉัน", "added": "เพิ่มแล้ว คำเหล่านี้จะขึ้นก่อนในการเรียนแฟลชการ์ดครั้งต่อไป",
    "cardsBase": "/th/hsk-flashcards/", "again": "ฝึกอีกรอบ", "nextLevel": "ระดับถัดไป: HSK {m}",
    "testLink": "ทำแบบทดสอบ HSK {n}", "testBase": "/th/hsk-practice-test/",
    "loading": "กำลังโหลด…", "loadFail": "โหลดคำศัพท์ไม่ได้ ตรวจสอบอินเทอร์เน็ตแล้วลองอีกครั้ง",
}

TITLE = "Pinyin and Tone Practice: Free HSK 1–5 Pinyin Quiz"
DESC = ("Free pinyin and tone practice for HSK 1–5 (HSK 3.0): type a word's pinyin with tone numbers or marks, "
        "or see or hear a word and choose its tones. No sign-up.")
TH_TITLE = "ฝึกพินอินและวรรณยุกต์ภาษาจีน HSK 1–5 ออนไลน์ฟรี"
TH_DESC = ("ฝึกพินอินและวรรณยุกต์ภาษาจีนฟรี ระดับ HSK 1–5 (HSK 3.0) พิมพ์พินอินของคำ หรือดูและฟังคำแล้วเลือกวรรณยุกต์ "
           "พร้อมความหมายภาษาไทย ไม่ต้องสมัคร")

TH_SWAPS = [
    ('<span>New HSK · 2025 syllabus</span><span class="chip">Levels 1–5</span><span class="chip">Free</span>',
     '<span>HSK ใหม่ · หลักสูตรปี 2025</span><span class="chip">ระดับ 1–5</span><span class="chip">ฟรี</span>'),
    ('<h1><span class="zh">拼音</span>Pinyin and Tone Practice</h1>', '<h1><span class="zh">拼音</span>ฝึกพินอินและวรรณยุกต์</h1>'),
    ('<p class="lede">Type the pinyin of the words of your HSK level, or see or hear a word and choose its tones. '
     'Every answer shows the right pinyin, so you learn the tones as you go.</p>',
     '<p class="lede">พิมพ์พินอินของคำศัพท์ตามระดับ HSK ของคุณ หรือดูและฟังคำแล้วเลือกวรรณยุกต์ '
     'ทุกข้อมีเฉลยพินอินที่ถูกต้อง จึงจำวรรณยุกต์ได้ไปพร้อมกับการฝึก</p>'),
    ('<h2 id="pick-title" class="visually-hidden">Choose a level</h2>', '<h2 id="pick-title" class="visually-hidden">เลือกระดับ</h2>'),
    ('<div class="levels pt-levels" role="group" aria-label="Level">\n      <span class="lbl">Level</span>',
     '<div class="levels pt-levels" role="group" aria-label="ระดับ">\n      <span class="lbl">ระดับ</span>'),
    ('<div class="levels lp-set" role="group" aria-label="Practice">\n        <span class="lbl">Practice</span>',
     '<div class="levels lp-set" role="group" aria-label="แบบฝึก">\n        <span class="lbl">ฝึก</span>'),
    ('data-mode="type" aria-pressed="false">Type the pinyin</button>', 'data-mode="type" aria-pressed="false">พิมพ์พินอิน</button>'),
    ('data-mode="tones" aria-pressed="false">Choose the tones</button>', 'data-mode="tones" aria-pressed="false">เลือกวรรณยุกต์</button>'),
    ('<div class="levels lp-set" role="group" aria-label="Tones from" id="how-set">\n        <span class="lbl">Word</span>',
     '<div class="levels lp-set" role="group" aria-label="แสดงคำแบบ" id="how-set">\n        <span class="lbl">คำ</span>'),
    ('data-hear="0" aria-pressed="false">See it</button>', 'data-hear="0" aria-pressed="false">ดูคำ</button>'),
    ('data-hear="1" aria-pressed="false">Hear it</button>', 'data-hear="1" aria-pressed="false">ฟังเสียง</button>'),
    ('<p class="pt-note" id="novoice-note" hidden>Your device has no Chinese voice, so the words can only be seen, '
     'not heard. Most phones and computers can add one for free in their text-to-speech or language settings.</p>',
     '<p class="pt-note" id="novoice-note" hidden>อุปกรณ์ของคุณไม่มีเสียงภาษาจีน จึงดูคำได้อย่างเดียว ฟังเสียงไม่ได้ '
     'โทรศัพท์และคอมพิวเตอร์ส่วนใหญ่เพิ่มเสียงภาษาจีนได้ฟรีในการตั้งค่าการอ่านออกเสียงหรือการตั้งค่าภาษา</p>'),
    ('<h2 id="test-title" class="visually-hidden">Practice</h2>', '<h2 id="test-title" class="visually-hidden">แบบฝึก</h2>'),
    ('<p class="empty" id="loading">Loading…</p>', '<p class="empty" id="loading">กำลังโหลด…</p>'),
    ('This browser is not letting the page save, so your best scores and settings will not be kept.',
     'เบราว์เซอร์นี้ไม่อนุญาตให้บันทึกข้อมูล คะแนนสูงสุดและการตั้งค่าจึงจะไม่ถูกเก็บไว้'),
    ('<h2 id="guide-title">About pinyin and tone practice</h2>', '<h2 id="guide-title">เกี่ยวกับการฝึกพินอินและวรรณยุกต์</h2>'),
    ('<h3>How do I type the tones?</h3>', '<h3>พิมพ์วรรณยุกต์อย่างไร?</h3>'),
    ('<p>Put a number after each syllable: 1 for the first tone (mā), 2 for the second (má), 3 for the third (mǎ), '
     '4 for the fourth (mà), and 5 or nothing for the neutral tone, so 你好 is ni3hao3 and 朋友 is peng2you5 or '
     'peng2you. Tone marks work too, if your keyboard has them. Type ü as v (女 is nv3) or u:. Spaces, apostrophes '
     'and capital letters do not matter. On a phone, the buttons under the box add the numbers and ü.</p>',
     '<p>ใส่ตัวเลขหลังแต่ละพยางค์: 1 คือเสียงที่หนึ่ง (mā) 2 คือเสียงที่สอง (má) 3 คือเสียงที่สาม (mǎ) '
     '4 คือเสียงที่สี่ (mà) และ 5 หรือไม่ใส่อะไรเลยสำหรับเสียงเบา เช่น 你好 พิมพ์ว่า ni3hao3 และ 朋友 พิมพ์ว่า '
     'peng2you5 หรือ peng2you ถ้าแป้นพิมพ์มีเครื่องหมายวรรณยุกต์ก็ใช้ได้เหมือนกัน พิมพ์ ü เป็น v (女 คือ nv3) หรือ u: '
     'เว้นวรรค อะพอสทรอฟี และตัวพิมพ์ใหญ่ไม่มีผล บนโทรศัพท์ใช้ปุ่มใต้ช่องพิมพ์เพื่อใส่ตัวเลขและ ü ได้</p>'),
    ('<h3>Which pinyin counts as right?</h3>', '<h3>พินอินแบบไหนนับว่าถูก?</h3>'),
    ('<p>The readings of the HSK 3.0 word list, the same as on the <a href="/hsk-1-word-list/">word list pages</a>. '
     'Pinyin writes each syllable with its own tone, so 你好 is nǐ hǎo even though it is said ní hǎo. The one '
     'exception is 一 and 不: the word lists write their changed tones (一起 yìqǐ, 不客气 bú kèqi), and the original '
     'tones (yīqǐ, bù kèqi) are accepted too.</p>',
     '<p>ใช้คำอ่านตามรายการคำศัพท์ HSK 3.0 ชุดเดียวกับ<a href="/th/hsk-1-word-list/">หน้ารายการคำศัพท์</a> '
     'พินอินเขียนวรรณยุกต์เดิมของแต่ละพยางค์ เช่น 你好 เขียนว่า nǐ hǎo แม้จะออกเสียงว่า ní hǎo ยกเว้น 一 และ 不 '
     'ที่รายการคำศัพท์เขียนวรรณยุกต์ที่เปลี่ยนแล้ว (一起 yìqǐ, 不客气 bú kèqi) ซึ่งพิมพ์วรรณยุกต์เดิม '
     '(yīqǐ, bù kèqi) ก็นับว่าถูกเช่นกัน</p>'),
    ('<h3>What do the tone numbers mean?</h3>', '<h3>ตัวเลขวรรณยุกต์หมายถึงอะไร?</h3>'),
    ('<p>In "Choose the tones", 3-3 means two third tones, like 你好 nǐ hǎo, and 5 is the neutral tone, like the '
     'second syllable of 朋友 péngyou. The answer is the tones as written. When you hear a word, words whose tones '
     'change in speech (a third tone before a third tone, 一 and 不) are left out, so what you hear is what is '
     'written. Read more about <a href="/mandarin-tone-changes/">tone changes</a>.</p>',
     '<p>ในแบบฝึก "เลือกวรรณยุกต์" 3-3 หมายถึงเสียงที่สามสองพยางค์ เช่น 你好 nǐ hǎo และ 5 คือเสียงเบา เช่น '
     'พยางค์ที่สองของ 朋友 péngyou คำตอบคือวรรณยุกต์ตามที่เขียน เมื่อฝึกแบบฟังเสียง จะไม่มีคำที่วรรณยุกต์เปลี่ยนเวลาพูด '
     '(เสียงที่สามก่อนเสียงที่สาม 一 และ 不) สิ่งที่ได้ยินจึงตรงกับที่เขียนเสมอ อ่านเพิ่มเติมเรื่อง'
     '<a href="/mandarin-tone-changes/">การเปลี่ยนเสียงวรรณยุกต์</a> (ภาษาอังกฤษ)</p>'),
    ('<h3>Where is my score kept?</h3>', '<h3>คะแนนเก็บไว้ที่ไหน?</h3>'),
    ('<p>Your best score for each level and mode is kept in this browser on this device, and nothing is sent '
     'anywhere. Words you miss can go straight into the <a href="/hsk-flashcards/">flashcards</a>. To train your '
     'ear with whole sentences, try the <a href="/chinese-listening-practice/">listening practice</a>.</p>',
     '<p>คะแนนสูงสุดของแต่ละระดับและแต่ละแบบฝึกเก็บไว้ในเบราว์เซอร์ของอุปกรณ์นี้ และไม่มีข้อมูลใดถูกส่งไปที่ไหน '
     'คำที่ตอบผิดเพิ่มลงใน<a href="/th/hsk-flashcards/">แฟลชการ์ด</a>ได้ทันที ถ้าอยากฝึกหูกับประโยคเต็ม ลองไปที่'
     '<a href="/th/chinese-listening-practice/">ฝึกฟังภาษาจีน</a></p>'),
    ('<p><b>Words and tones.</b> HSK 3.0 (New HSK) vocabulary, 2025 syllabus, the same lists as the '
     '<a href="/hsk-1-word-list/">word list pages</a>. Tones checked against '
     '<a href="https://github.com/drkameleon/complete-hsk-vocabulary">complete-hsk-vocabulary</a> (MIT). Audio uses '
     'your device\'s Chinese voice.</p>',
     '<p><b>คำศัพท์และวรรณยุกต์</b> คำศัพท์ HSK 3.0 (HSK ใหม่) หลักสูตรปี 2025 ชุดเดียวกับ'
     '<a href="/th/hsk-1-word-list/">หน้ารายการคำศัพท์</a> พร้อมความหมายภาษาไทย วรรณยุกต์ตรวจกับ '
     '<a href="https://github.com/drkameleon/complete-hsk-vocabulary">complete-hsk-vocabulary</a> (MIT) '
     'เสียงใช้เสียงภาษาจีนของอุปกรณ์</p>'),
]


# --- splitting pinyin into syllables -------------------------------------------------------------------------------

def _letters(p):
    """Pinyin -> [(letter, tone or 0, boundary before it)]; ü kept; separators become boundaries."""
    out, boundary = [], False
    for ch in unicodedata.normalize("NFC", p.lower()):
        if ch in SEP:
            boundary = True
            continue
        base, tone = practice._split_tone(ch)
        if not re.fullmatch(r"[a-zü]", base):
            return None
        out.append((base, tone, boundary))
        boundary = False
    return out


def split(word, pinyin, valid, char_readings):
    """One reading of the word list -> [(syllable, tone 1-5)], one syllable per character, or None.
    Each syllable must be a Mandarin syllable and a known reading of its character (儿 after another character may
    be the -r of erhua). Returns None if the split is not unique."""
    lt = _letters(pinyin)
    if not lt:
        return None
    s = "".join(x[0] for x in lt)
    n = len(word)
    found = []

    def ok_for(k, syl):
        c = word[k]
        if c == "儿" and k > 0 and syl == "r":
            return True
        return syl in valid and syl in char_readings.get(c, ())

    def go(i, k, acc):
        if len(found) > 1:
            return
        if k == n:
            if i == len(s):
                found.append(list(acc))
            return
        for j in range(i + 1, min(len(s), i + 6) + 1):
            # a separator inside a syllable is not allowed
            if any(lt[x][2] for x in range(i + 1, j)):
                break
            syl = s[i:j]
            if ok_for(k, syl):
                tones = [lt[x][1] for x in range(i, j) if lt[x][1]]
                if len(tones) > 1:
                    continue
                acc.append((syl, tones[0] if tones else 5))
                go(j, k + 1, acc)
                acc.pop()

    go(0, 0, [])
    return found[0] if len(found) == 1 else None


def numbered(sy):
    return " ".join(f"{b}{t}" for b, t in sy)


def _bare(p):
    return "".join(practice._split_tone(ch)[0] for ch in unicodedata.normalize("NFC", p.lower()) if ch not in SEP)


def _spoken(tones):
    """Third tone before a third tone is said as a second tone (every one but the last in a run)."""
    return [2 if t == 3 and k + 1 < len(tones) and tones[k + 1] == 3 else t for k, t in enumerate(tones)]


# --- data ----------------------------------------------------------------------------------------------------------

_CACHE = {}


def _data(root):
    if "d" in _CACHE:
        return _CACHE["d"]
    tone_data = json.loads((root / "tones" / "words.json").read_text(encoding="utf-8"))["w"]
    valid = {re.sub(r"\d", "", s) for v in tone_data.values() for s in v.split()} - {"r"}
    marked = practice._readings(root)
    chars = {c: {_bare(r) for r in rs} for c, rs in marked.items()}
    # characters read with the same syllable in more than one tone (好 hǎo / hào): left out of the tone mode alone
    two_tones = {c for c, rs in marked.items()
                 if len({_bare(r) for r in rs}) < len({unicodedata.normalize("NFC", r.lower()) for r in rs})}
    # tone data readings count as character readings too
    for w, v in tone_data.items():
        syl = v.split()
        if len(syl) == len(w):
            for c, x in zip(w, syl):
                chars.setdefault(c, set()).add(re.sub(r"\d", "", x))
    levels, _gaps = practice._level_data(root)
    out = {}
    for n in LEVELS:
        words = []
        dropped = []
        for i, (w, p, m, _wp, audio, _c) in enumerate(levels[n]["words"]):
            readings = []
            for r in re.split(r"[;/]", p):
                sy = split(w, r.strip(), valid, chars)
                if sy is None:
                    readings = None
                    break
                readings.append(sy)
            if not readings:
                dropped.append(f"{w} {p}")
                continue
            accepted = []
            for sy in readings:
                accepted.append(sy)
                # the original tones of 一 and 不, where the word list writes the changed ones
                alt = [(b, 1) if c == "一" and b == "yi" else (b, 4) if c == "不" and b == "bu" else (b, t)
                       for c, (b, t) in zip(w, sy)]
                if alt != sy:
                    accepted.append(alt)
            acc_str = []
            for sy in accepted:
                if numbered(sy) not in acc_str:
                    acc_str.append(numbered(sy))
            # tone mode: one reading, agreeing with the dictionary tones, no 一 / 不 / erhua, no leading neutral tone
            tone = ""
            hear = 0
            sy = readings[0]
            # the dictionary tones of the word, or else of each of its characters
            ref = tone_data.get(w) or " ".join(tone_data.get(c, "?") for c in w)
            if (len(readings) == 1 and 1 <= len(w) <= 4 and not set(w) & set("一不") and w not in two_tones
                    and ref and numbered(sy) == ref and all(b != "r" for b, _ in sy) and sy[0][1] != 5):
                tone = numbered(sy)
                tones = [t for _, t in sy]
                hear = int(bool(audio) and _spoken(tones) == tones)
            words.append([w, p, m, acc_str, tone, hear, int(bool(audio)), i])
        out[n] = (words, dropped)
    _CACHE["d"] = (out, levels)
    return _CACHE["d"]


def _check(n, words):
    """Stop the build if a mode lacks words or a reading is not one syllable per character."""
    if len(words) < MIN_WORDS:
        raise SystemExit(f"pinyin practice: HSK {n} has only {len(words)} words with readings")
    tone_words = [x for x in words if x[4]]
    hear_words = [x for x in tone_words if x[5]]
    if len(tone_words) < MIN_WORDS or len(hear_words) < MIN_WORDS:
        raise SystemExit(f"pinyin practice: HSK {n} has too few words for the tone mode "
                         f"({len(tone_words)} to see, {len(hear_words)} to hear)")
    for w, p, m, acc, tone, hear, audio in words:
        for r in acc:
            if len(r.split()) != len(w) or not all(re.fullmatch(r"([a-zü]+|r)[1-5]", s) for s in r.split()):
                raise SystemExit(f"pinyin practice: bad reading for {w}: {r}")
        if tone and tone not in acc:
            raise SystemExit(f"pinyin practice: the tones of {w} are not one of its readings")


def _write(root, base, lang, data, levels):
    folder = root / base.strip("/")
    folder.mkdir(parents=True, exist_ok=True)
    for n in LEVELS:
        words, _ = data[n]
        th = levels[n]["th"] if lang == "th" else None  # Thai meanings, in word list order (i = row)
        words = [[w, p, th[i] if th else m, acc, tone, hear, audio] for w, p, m, acc, tone, hear, audio, i in words]
        _check(n, words)
        (folder / f"hsk{n}.json").write_text(json.dumps({"w": words}, ensure_ascii=False, separators=(",", ":")),
                                             encoding="utf-8")


def _body(tpl, nav_html, ui, data_base):
    return ((tpl / "pinyin_body.html").read_text(encoding="utf-8").replace("__NAV__", nav_html)
            .replace("__UI_JSON__", json.dumps(ui, ensure_ascii=False)).replace("__DATA_BASE__", data_base))


def _ld(name, url, desc, lang):
    return json.dumps({
        "@context": "https://schema.org", "@type": "WebApplication", "name": name, "url": url, "inLanguage": lang,
        "applicationCategory": "EducationalApplication", "operatingSystem": "Any",
        "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"}, "description": desc,
    }, ensure_ascii=False)


def _css(tpl):
    return ((tpl / "checker.css").read_text(encoding="utf-8") + (tpl / "practice.css").read_text(encoding="utf-8")
            + (tpl / "pinyin.css").read_text(encoding="utf-8"))


def build(root, pages, nav, render, base_css, tpl, site):
    data, levels = _data(root)
    _write(root, URL, "en", data, levels)
    body = _body(tpl, nav(pages, URL), UI_EN, URL)
    out = render(TITLE, DESC, site + URL, base_css + _css(tpl), body,
                 f'<script type="application/ld+json">{_ld("Pinyin and Tone Practice", site + URL, DESC, "en")}</script>')
    (root / URL.strip("/") / "index.html").write_text(out, encoding="utf-8")
    return [URL]


def build_th(*, root, tpl, site, render, nav, font_link, foot, base_css, th_css):
    data, levels = _data(root)
    _write(root, TH_URL, "th", data, levels)
    body = _body(tpl, nav(TH_URL), UI_TH, TH_URL)
    for a, b in TH_SWAPS:
        if body.count(a) != 1:
            raise SystemExit(f"pinyin practice: English text not found for the Thai page: {a[:60]}")
        body = body.replace(a, b)
    out = render(TH_TITLE, TH_DESC, site + TH_URL, base_css + _css(tpl) + th_css, body,
                 font_link + f'\n<script type="application/ld+json">{_ld("ฝึกพินอินและวรรณยุกต์", site + TH_URL, TH_DESC, "th")}</script>',
                 lang="th", foot=foot)
    (root / TH_URL.strip("/") / "index.html").write_text(out, encoding="utf-8")
    return [TH_URL]


def alternates(root):
    return {URL: TH_URL}
