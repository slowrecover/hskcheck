"""Chinese character tracing, built to /chinese-character-tracing/ (English) and /th/chinese-character-tracing/ (Thai).

The learner writes a character stroke by stroke with a finger or mouse on a tian grid (templates/tracing_body.html,
CSS in templates/checker.css + templates/practice.css + templates/tracing.css). A stroke is accepted when it follows
the stroke's centre line from its start to its end; a stroke drawn the wrong way round, a stroke that belongs later
in the order, or one that misses is shown gently and can be tried again. A hint shows the next stroke being drawn,
and the whole stroke order can be played. Two modes: trace over a faint model character, or write from memory.

Characters come in sets of 10: by HSK level, the same sets as the character worksheets (HSK 1-3: strokes/hskN.json,
the characters first used in that level's words; HSK 4 and 5: the characters of that level's words not used at a
lower level, as on /hsk-4-character-worksheets/ and /hsk-5-character-worksheets/), or any characters the learner
types (also handed over from the worksheet pages as #c=<characters>). The number of characters written without a
mistake or a hint, best per set, stays in the learner's browser (localStorage); nothing is sent anywhere.

Data files read:
  strokes/hskN.json, strokes/x/   stroke outlines and pinyin (Make Me a Hanzi; see tools/make_stroke_data.py)
  strokes/m/                      stroke centre lines (medians), see tools/make_median_data.py
  data/hskN.tsv, data/th/         the words each character is shown with, and their meanings (Thai on the Thai page)
  tones/words.json                Mandarin syllables, to find a HSK 4-5 character's reading in its first word

Outputs:
  chinese-character-tracing/index.html, th/chinese-character-tracing/index.html
  chinese-character-tracing/hskN.json      {"c": [[character, pinyin, first word, its pinyin, meaning], ...]}
  th/chinese-character-tracing/hskN.json   the same with Thai meanings
  chinese-character-tracing/s/N-K.json     outlines and centre lines for set K (from 0) of HSK N, shared by both pages:
                                           {"字": {"s": [outline, ...], "m": [[x0, y0, x1, y1, ...], ...]}}
  chinese-character-tracing/s/index.json   {"字": ["N-K", pinyin]}, so typed characters from the HSK sets load a
                                           small file
Typed characters outside the sets load strokes/x/ and strokes/m/ shards.
The build stops if a character has no stroke data, a stroke has no centre line, or a reading cannot be found.

The Thai page is the English template with its text swapped for Thai; the build stops if a string is not found.
"""
import json
import re
import unicodedata

import hsk4
import hsk5
import pinyin_practice
import practice

URL = "/chinese-character-tracing/"
TH_URL = "/th/chinese-character-tracing/"
LEVELS = (1, 2, 3, 4, 5)
PER_SET = 10
SHARDS = 128
# A character only ever neutral in its first word whose toned readings in the data are not its reading there:
# 匙 is chí (汤匙) or shi (钥匙); the shī of some dictionaries is not standard.
NEUTRAL_READING = {"匙": "shi"}

UI_EN = {
    "set": "Characters {a}–{b}", "best": "best {b}/{t}", "of": "of", "char": "Character", "stroke": "Stroke",
    "strokes": "strokes", "start": "Start writing", "loading": "Loading…",
    "loadFail": "The stroke data could not be loaded. Check your connection and try again.",
    "noData": "No stroke data for: {c}", "typeSome": "Type some Chinese characters above.",
    "customCount": "{n} characters, in sets of 10.",
    "askTrace": "Write over the grey character, one stroke at a time, in stroke order.",
    "askMemory": "Write the character from memory, one stroke at a time, in stroke order.",
    "first": "Start with the first stroke.", "good": "Good. Next stroke.",
    "dir": "Right place, but start from the other end of the stroke.",
    "order": "That stroke comes later. Look for an earlier one.",
    "already": "That stroke is already written. Look for the next one.",
    "miss": "Not quite. Follow the shape of the stroke from start to end.",
    "short": "Draw the whole stroke, from where it starts to where it ends.",
    "hinted": "Here is the next stroke. Now draw it.",
    "doneClean": "Well written: no mistakes.", "doneWith": "Done, with {x}.", "and": " and ",
    "mist1": "1 mistake", "mistN": "{n} mistakes", "hint1": "1 hint", "hintN": "{n} hints",
    "hint": "Hint", "play": "Stroke order", "restart": "Start again", "next": "Next character", "finish": "See my score",
    "scoreHead": "Your score", "scoreSub": "characters written without a mistake or a hint",
    "bestNew": "New best for this set!", "bestOld": "Your best for this set: {b} / {t}",
    "msg4": "Excellent. Your stroke order is solid: go on to the next set.",
    "msg3": "Good work. Write the characters below once more, then go on.",
    "msg2": "Keep going. Play the stroke order of the characters below, then write them again.",
    "msg1": "Stroke order takes practice. Use the hints, then try this set again.",
    "missedHead": "Characters to practise again", "noMissed": "Every character was written without help.",
    "redo": "Practise these again", "again": "Try this set again", "nextSet": "Next set: {s}",
    "nextLevel": "Next level: HSK {m}", "print": "Print a worksheet for these characters",
    "wsBase": "/chinese-character-worksheets/", "box": "Writing box for {c}",
    "levelSet": "HSK {n} · {s}", "anySet": "Your characters · {s}",
}
UI_TH = {
    "set": "ตัวที่ {a}–{b}", "best": "สูงสุด {b}/{t}", "of": "จาก", "char": "ตัวที่", "stroke": "ขีดที่",
    "strokes": "ขีด", "start": "เริ่มเขียน", "loading": "กำลังโหลด…",
    "loadFail": "โหลดข้อมูลลำดับขีดไม่สำเร็จ ตรวจสอบอินเทอร์เน็ตแล้วลองใหม่อีกครั้ง",
    "noData": "ไม่มีข้อมูลลำดับขีดของ: {c}", "typeSome": "พิมพ์ตัวอักษรจีนในช่องด้านบน",
    "customCount": "{n} ตัว แบ่งเป็นชุดละ 10 ตัว",
    "askTrace": "เขียนทับตัวอักษรสีเทาทีละขีด ตามลำดับขีด",
    "askMemory": "เขียนตัวอักษรเองโดยไม่ดูตัวอย่าง ทีละขีด ตามลำดับขีด",
    "first": "เริ่มจากขีดแรก", "good": "ดีมาก ขีดต่อไป",
    "dir": "ตำแหน่งถูกแล้ว แต่ต้องเริ่มจากอีกปลายหนึ่งของขีด",
    "order": "ขีดนี้ต้องเขียนทีหลัง ลองหาขีดที่มาก่อน",
    "already": "ขีดนี้เขียนไปแล้ว ลองหาขีดถัดไป",
    "miss": "ยังไม่ถูก ลากตามรูปของขีดตั้งแต่ต้นจนจบ",
    "short": "ลากให้ครบทั้งขีด ตั้งแต่จุดเริ่มจนถึงจุดจบ",
    "hinted": "นี่คือขีดถัดไป ลองเขียนตามเลย",
    "doneClean": "เขียนได้สวย ไม่ผิดเลย", "doneWith": "เสร็จแล้ว {x}", "and": " ",
    "mist1": "ผิด 1 ครั้ง", "mistN": "ผิด {n} ครั้ง", "hint1": "ใช้ตัวช่วย 1 ครั้ง", "hintN": "ใช้ตัวช่วย {n} ครั้ง",
    "hint": "ตัวช่วย", "play": "ดูลำดับขีด", "restart": "เริ่มใหม่", "next": "ตัวต่อไป", "finish": "ดูคะแนน",
    "scoreHead": "คะแนนของคุณ", "scoreSub": "ตัวที่เขียนได้โดยไม่ผิดและไม่ใช้ตัวช่วย",
    "bestNew": "คะแนนสูงสุดใหม่ของชุดนี้!", "bestOld": "คะแนนสูงสุดของคุณในชุดนี้: {b} / {t}",
    "msg4": "ยอดเยี่ยม ลำดับขีดของคุณแม่นมาก ไปชุดถัดไปได้เลย",
    "msg3": "ทำได้ดี เขียนตัวอักษรด้านล่างอีกครั้ง แล้วไปต่อ",
    "msg2": "สู้ต่อไป ดูลำดับขีดของตัวอักษรด้านล่าง แล้วลองเขียนอีกครั้ง",
    "msg1": "ลำดับขีดต้องอาศัยการฝึก ใช้ตัวช่วยได้เลย แล้วลองชุดนี้อีกครั้ง",
    "missedHead": "ตัวอักษรที่ควรฝึกอีก", "noMissed": "คุณเขียนได้ทุกตัวโดยไม่ต้องใช้ตัวช่วย",
    "redo": "ฝึกตัวเหล่านี้อีกครั้ง", "again": "ฝึกชุดนี้อีกครั้ง", "nextSet": "ชุดถัดไป: {s}",
    "nextLevel": "ระดับถัดไป: HSK {m}", "print": "พิมพ์แบบฝึกเขียนของตัวอักษรเหล่านี้",
    "wsBase": "/th/chinese-character-worksheets/", "box": "ช่องเขียนตัวอักษร {c}",
    "levelSet": "HSK {n} · {s}", "anySet": "ตัวอักษรของคุณ · {s}",
}

TITLE = "Chinese Character Tracing: Stroke Order Practice Online"
DESC = ("Trace Chinese characters stroke by stroke with your finger or mouse. Free stroke order practice for HSK 1–5 "
        "or any characters, with hints.")
TH_TITLE = "ฝึกเขียนตัวอักษรจีนตามลำดับขีดออนไลน์ฟรี HSK 1–5"
TH_DESC = ("ฝึกเขียนตัวอักษรจีนทีละขีดด้วยนิ้วหรือเมาส์ ตามลำดับขีดที่ถูกต้อง มีตัวช่วยบอกขีดถัดไป "
           "เลือกตัวอักษร HSK 1–5 หรือพิมพ์ตัวอักษรเองก็ได้ ฟรี")

TH_SWAPS = [
    ('<span>Free · stroke order</span><span class="chip">HSK 1–5</span><span class="chip">Any characters</span>',
     '<span>ฟรี · ลำดับขีด</span><span class="chip">HSK 1–5</span><span class="chip">ตัวอักษรอะไรก็ได้</span>'),
    ('<h1><span class="zh">描红</span>Chinese Character Tracing</h1>',
     '<h1><span class="zh">描红</span>ฝึกเขียนตัวอักษรจีนตามลำดับขีด</h1>'),
    ('<p class="lede">Write Chinese characters stroke by stroke with your finger or mouse. Each stroke is checked for '
     'its place, its shape and its direction, and a hint shows the next stroke whenever you need it.</p>',
     '<p class="lede">เขียนตัวอักษรจีนทีละขีดด้วยนิ้วหรือเมาส์ ทุกขีดจะถูกตรวจทั้งตำแหน่ง รูปร่าง และทิศทาง '
     'และกดตัวช่วยเพื่อดูขีดถัดไปได้ทุกเมื่อ</p>'),
    ('<h2 id="pick-title" class="visually-hidden">Choose the characters</h2>',
     '<h2 id="pick-title" class="visually-hidden">เลือกตัวอักษร</h2>'),
    ('<div class="levels pt-levels" role="group" aria-label="Characters">\n      <span class="lbl">Characters</span>',
     '<div class="levels pt-levels" role="group" aria-label="ตัวอักษร">\n      <span class="lbl">ตัวอักษร</span>'),
    ('data-level="0" aria-pressed="false">Any characters</button>',
     'data-level="0" aria-pressed="false">ตัวอักษรอะไรก็ได้</button>'),
    ('<label for="set-pick">Set</label>', '<label for="set-pick">ชุด</label>'),
    ('<label for="custom">Characters to write</label>', '<label for="custom">ตัวอักษรที่จะเขียน</label>'),
    ('<div class="levels lp-set" role="group" aria-label="Model">\n        <span class="lbl">Model</span>',
     '<div class="levels lp-set" role="group" aria-label="ตัวอย่าง">\n        <span class="lbl">ตัวอย่าง</span>'),
    ('data-mode="trace" aria-pressed="false">Trace it</button>', 'data-mode="trace" aria-pressed="false">เขียนทับตัวจาง</button>'),
    ('data-mode="memory" aria-pressed="false">From memory</button>', 'data-mode="memory" aria-pressed="false">เขียนเอง</button>'),
    ('<h2 id="test-title" class="visually-hidden">Writing practice</h2>',
     '<h2 id="test-title" class="visually-hidden">ฝึกเขียน</h2>'),
    ('<p class="empty" id="loading">Loading…</p>', '<p class="empty" id="loading">กำลังโหลด…</p>'),
    ('This browser is not letting the page save, so your best scores and settings will not be kept.',
     'เบราว์เซอร์นี้ไม่อนุญาตให้บันทึกข้อมูล คะแนนสูงสุดและการตั้งค่าจึงจะไม่ถูกเก็บไว้'),
    ('<h2 id="guide-title">About character tracing</h2>', '<h2 id="guide-title">เกี่ยวกับการฝึกเขียนตามลำดับขีด</h2>'),
    ('<h3>How is a stroke checked?</h3>', '<h3>ระบบตรวจแต่ละขีดอย่างไร?</h3>'),
    ('<p>Each stroke has a centre line from where the brush starts to where it lifts. Your stroke is accepted when it '
     'starts near the start, ends near the end and follows the shape in between, so neat handwriting is not needed, '
     'but the direction is: horizontal strokes go left to right and vertical strokes top to bottom. A stroke drawn the '
     'wrong way round, or one that belongs later in the order, is not accepted, and the page tells you why.</p>',
     '<p>ทุกขีดมีเส้นกลางตั้งแต่จุดที่เริ่มลงพู่กันจนถึงจุดที่ยกพู่กันขึ้น ขีดที่คุณเขียนจะผ่านเมื่อเริ่มใกล้จุดเริ่ม '
     'จบใกล้จุดจบ และลากตามรูปของขีดตรงกลาง จึงไม่ต้องเขียนสวยมาก แต่ทิศทางต้องถูก ขีดแนวนอนลากจากซ้ายไปขวา '
     'ขีดแนวตั้งลากจากบนลงล่าง ขีดที่ลากกลับทิศ หรือขีดที่ต้องเขียนทีหลังจะไม่ผ่าน และหน้านี้จะบอกเหตุผลให้</p>'),
    ('<h3>What do Hint and Stroke order do?</h3>', '<h3>ปุ่มตัวช่วยและดูลำดับขีดใช้ทำอะไร?</h3>'),
    ('<p>Hint draws the next stroke for you slowly, from its start, so you can see where it goes and which way; then '
     'you write it yourself. After two misses on the same stroke the hint appears by itself. Stroke order plays the '
     'whole character. On a keyboard, press H for a hint, P to play the stroke order, R to start the character again '
     'and Enter for the next character.</p>',
     '<p>ตัวช่วยจะค่อย ๆ วาดขีดถัดไปให้ดูตั้งแต่จุดเริ่ม ให้เห็นว่าขีดอยู่ตรงไหนและลากไปทางไหน แล้วคุณเขียนตามเอง '
     'ถ้าเขียนขีดเดียวกันผิดสองครั้ง ตัวช่วยจะขึ้นมาเอง ส่วนปุ่มดูลำดับขีดจะแสดงการเขียนทั้งตัว บนแป้นพิมพ์ กด H '
     'เพื่อใช้ตัวช่วย กด P เพื่อดูลำดับขีด กด R เพื่อเริ่มตัวนี้ใหม่ และกด Enter เพื่อไปตัวต่อไป</p>'),
    ('<h3>Which characters are in each set?</h3>', '<h3>แต่ละชุดมีตัวอักษรอะไรบ้าง?</h3>'),
    ('<p>The same characters as the <a href="/hsk-1-character-worksheets/">character worksheets</a>: every character '
     'used in the words of a level, in the order it first appears in the word list, without the characters of lower '
     'levels, in sets of 10. Each one is shown with the first word it appears in. Choose "Any characters" to write '
     'your own, such as your name or the new words of a lesson.</p>',
     '<p>ชุดเดียวกับ<a href="/th/hsk-1-character-worksheets/">แบบฝึกเขียนตัวอักษร</a> คือตัวอักษรทุกตัวในคำศัพท์ของระดับนั้น '
     'เรียงตามลำดับที่ปรากฏครั้งแรกในรายการคำศัพท์ ไม่รวมตัวอักษรของระดับที่ต่ำกว่า แบ่งเป็นชุดละ 10 ตัว '
     'แต่ละตัวแสดงพร้อมคำแรกที่มีตัวนั้น เลือก "ตัวอักษรอะไรก็ได้" เพื่อเขียนตัวอักษรที่ต้องการเอง '
     'เช่น ชื่อของคุณ หรือคำศัพท์ใหม่ของบทเรียน</p>'),
    ('<h3>Where is my score kept?</h3>', '<h3>คะแนนเก็บไว้ที่ไหน?</h3>'),
    ('<p>A character counts when you write it without a mistake and without a hint (playing the stroke order counts as a hint). Your best for each set is kept in '
     'this browser on this device, and nothing is sent anywhere. To write on paper as well, print the same characters '
     'from the <a href="/chinese-character-worksheets/">worksheet maker</a>.</p>',
     '<p>ตัวอักษรที่นับคะแนนคือตัวที่เขียนได้โดยไม่ผิดและไม่ใช้ตัวช่วย (การกดดูลำดับขีดก็นับเป็นตัวช่วย) คะแนนสูงสุดของแต่ละชุดเก็บไว้ในเบราว์เซอร์ของอุปกรณ์นี้ '
     'และไม่มีข้อมูลใดถูกส่งไปที่ไหน ถ้าอยากฝึกเขียนบนกระดาษด้วย พิมพ์ตัวอักษรชุดเดียวกันได้จาก'
     '<a href="/th/chinese-character-worksheets/">หน้าสร้างแบบฝึกเขียน</a></p>'),
    ('<p><b>Stroke data.</b> Stroke outlines, centre lines and pinyin come from '
     '<a href="https://github.com/skishore/makemeahanzi">Make Me a Hanzi</a> (Arphic Public License and GNU LGPL, see '
     '<a href="/strokes/LICENSE.md">licence</a>). Stroke order follows mainland China standards for simplified '
     'characters. Words and meanings: HSK 3.0 (New HSK) vocabulary, 2025 syllabus, the same lists as the '
     '<a href="/hsk-1-word-list/">word list pages</a>.</p>',
     '<p><b>ข้อมูลลำดับขีด</b> รูปขีด เส้นกลางของขีด และพินอินมาจาก '
     '<a href="https://github.com/skishore/makemeahanzi">Make Me a Hanzi</a> (Arphic Public License และ GNU LGPL ดู'
     '<a href="/strokes/LICENSE.md" hreflang="en">สัญญาอนุญาต</a>) ลำดับขีดเป็นไปตามมาตรฐานตัวอักษรจีนตัวย่อของจีนแผ่นดินใหญ่ '
     'คำศัพท์และความหมาย: คำศัพท์ HSK 3.0 (HSK ใหม่) หลักสูตรปี 2025 ชุดเดียวกับ'
     '<a href="/th/hsk-1-word-list/">หน้ารายการคำศัพท์</a> พร้อมความหมายภาษาไทย</p>'),
]


# --- data ----------------------------------------------------------------------------------------------------------

def _shard(root, kind, c):
    return json.loads((root / "strokes" / kind / f"{ord(c) % SHARDS:02x}.json").read_text(encoding="utf-8"))


_CACHE = {}


def _data(root):
    """{level: [(character, pinyin, row index of the first word)]}, the rows and Thai meanings, and the stroke data."""
    if "d" in _CACHE:
        return _CACHE["d"]
    rows = {n: practice._rows(root, n) for n in LEVELS}
    thai = practice._thai(root)
    tone_data = json.loads((root / "tones" / "words.json").read_text(encoding="utf-8"))["w"]
    valid = {re.sub(r"\d", "", s) for v in tone_data.values() for s in v.split()} - {"r"}
    marked = practice._readings(root)
    bare = {c: {pinyin_practice._bare(r) for r in rs} for c, rs in marked.items()}

    shards = {}

    def stroke_entry(c):
        key = ord(c) % SHARDS
        if key not in shards:
            shards[key] = (_shard(root, "x", c), _shard(root, "m", c))
        x, m = shards[key]
        if c not in x or c not in m:
            raise SystemExit(f"character tracing: no stroke data for {c}")
        if len(x[c]["s"]) != len(m[c]) or not all(len(p) >= 4 and len(p) % 2 == 0 for p in m[c]):
            raise SystemExit(f"character tracing: the centre lines of {c} do not match its strokes")
        return x[c], m[c]

    def reading_in(c, word, pinyin):
        """The reading of c inside the first variant of the word list's pinyin; a neutral tone gets the toned reading."""
        first = unicodedata.normalize("NFC", re.split(r"[;/]", pinyin)[0].strip())
        if len(word) == 1:
            return first
        sy = pinyin_practice.split(word, first, valid, bare)
        if sy is None:
            return None
        base, tone = sy[word.index(c)]
        if tone == 5:
            if c in NEUTRAL_READING:
                return NEUTRAL_READING[c]
            toned = sorted(r for r in marked.get(c, ()) if pinyin_practice._bare(r) == base and r != base)
            return toned[0] if len(toned) == 1 else None
        return practice._place(base, tone)

    sets = {}
    lower = set()
    for n in LEVELS:
        if n <= 3:
            level = json.loads((root / "strokes" / f"hsk{n}.json").read_text(encoding="utf-8"))
            chars = [(c, " / ".join(v["p"])) for c, v in level.items()]
        else:
            mod = hsk4 if n == 4 else hsk5
            _, mrows = mod.read(root)
            if [r[0] for r in mrows] != [r[0] for r in rows[n]]:
                raise SystemExit(f"character tracing: data/hsk{n}.tsv rows differ")
            chars, failed = [], []
            for c in mod.new_chars(mrows, [w for k in range(1, n) for w, _, _ in rows[k]]):
                w, p, _ = next(r for r in rows[n] if c in r[0])
                r = reading_in(c, w, p)
                if not r:
                    failed.append(f"{c} in {w} {p}")
                chars.append((c, r))
            if failed:
                raise SystemExit(f"character tracing: no reading for " + ", ".join(failed))
        out = []
        for c, py in chars:
            if c in lower:
                raise SystemExit(f"character tracing: {c} is in two levels")
            i = next(k for k, r in enumerate(rows[n]) if c in r[0])
            out.append((c, py, i))
            stroke_entry(c)
        lower.update(c for c, _, _ in out)
        sets[n] = out
    _CACHE["d"] = (sets, rows, thai, stroke_entry)
    return _CACHE["d"]


def _write_strokes(root):
    sets, _, _, stroke_entry = _data(root)
    folder = root / URL.strip("/") / "s"
    folder.mkdir(parents=True, exist_ok=True)
    index = {}
    for n in LEVELS:
        chars = sets[n]
        for k in range(0, len(chars), PER_SET):
            chunk = {}
            for c, py, _ in chars[k:k + PER_SET]:
                x, m = stroke_entry(c)
                chunk[c] = {"s": x["s"], "m": m}
                index[c] = [f"{n}-{k // PER_SET}", py]
            (folder / f"{n}-{k // PER_SET}.json").write_text(
                json.dumps(chunk, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    (folder / "index.json").write_text(json.dumps(index, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")


def _write_levels(root, base, lang):
    sets, rows, thai, _ = _data(root)
    folder = root / base.strip("/")
    folder.mkdir(parents=True, exist_ok=True)
    for n in LEVELS:
        if lang == "th" and n not in thai:
            raise SystemExit(f"character tracing: no complete Thai meanings for HSK {n}")
        out = []
        for c, py, i in sets[n]:
            w, p, en = rows[n][i]
            out.append([c, py, w, p, thai[n][i] if lang == "th" else en])
        (folder / f"hsk{n}.json").write_text(json.dumps({"c": out}, ensure_ascii=False, separators=(",", ":")),
                                             encoding="utf-8")


def _body(tpl, nav_html, ui, data_base):
    return ((tpl / "tracing_body.html").read_text(encoding="utf-8").replace("__NAV__", nav_html)
            .replace("__UI_JSON__", json.dumps(ui, ensure_ascii=False)).replace("__DATA_BASE__", data_base)
            .replace("__STROKE_BASE__", URL + "s/"))


def _ld(name, url, desc, lang):
    return json.dumps({
        "@context": "https://schema.org", "@type": "WebApplication", "name": name, "url": url, "inLanguage": lang,
        "applicationCategory": "EducationalApplication", "operatingSystem": "Any",
        "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"}, "description": desc,
    }, ensure_ascii=False)


def _css(tpl):
    return "".join((tpl / f).read_text(encoding="utf-8") for f in ("checker.css", "practice.css", "tracing.css"))


def build(root, pages, nav, render, base_css, tpl, site):
    _write_strokes(root)
    _write_levels(root, URL, "en")
    body = _body(tpl, nav(pages, URL), UI_EN, URL)
    out = render(TITLE, DESC, site + URL, base_css + _css(tpl), body,
                 f'<script type="application/ld+json">{_ld("Chinese Character Tracing", site + URL, DESC, "en")}</script>')
    (root / URL.strip("/") / "index.html").write_text(out, encoding="utf-8")
    return [URL]


def build_th(*, root, tpl, site, render, nav, font_link, foot, base_css, th_css):
    _write_levels(root, TH_URL, "th")
    body = _body(tpl, nav(TH_URL), UI_TH, TH_URL)
    for a, b in TH_SWAPS:
        if body.count(a) != 1:
            raise SystemExit(f"character tracing: English text not found for the Thai page: {a[:60]}")
        body = body.replace(a, b)
    out = render(TH_TITLE, TH_DESC, site + TH_URL, base_css + _css(tpl) + th_css, body,
                 font_link + f'\n<script type="application/ld+json">{_ld("ฝึกเขียนตัวอักษรจีนตามลำดับขีด", site + TH_URL, TH_DESC, "th")}</script>',
                 lang="th", foot=foot)
    (root / TH_URL.strip("/") / "index.html").write_text(out, encoding="utf-8")
    return [TH_URL]


def alternates(root):
    return {URL: TH_URL}
