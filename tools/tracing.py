"""Chinese character tracing, built to /chinese-character-tracing/ (English) and /th/chinese-character-tracing/ (Thai).

The learner traces a character stroke by stroke on a tian grid with a finger or a mouse
(templates/tracing_body.html, CSS in templates/checker.css + templates/practice.css + templates/tracing.css).
A stroke is accepted when it starts near the start of the next stroke, follows its centre line and goes the same
way; otherwise it fades out and can be tried again. The next stroke can be shown as a hint (start dot and arrow),
and "Show me" draws it. Characters come in sets of 10:
  HSK 1-5         the same character sets as the character worksheets: every character used in the words of the
                  level, once, in the order it first appears in the word list, leaving out characters already used
                  at a lower level (HSK 1-3: strokes/hskN.json; HSK 4 and 5: tools/hsk4.py and tools/hsk5.py)
  My characters   any characters typed in, or handed over in the link (#c=<characters>) by the worksheet pages;
                  their strokes are loaded from strokes/x/ and strokes/m/
Which characters have been traced (per level), and the settings, stay in the learner's browser (localStorage);
nothing is sent anywhere.

Data files read:
  data/hskN.tsv, data/th/       the words (and Thai meanings) the characters come from, through tools/practice.py
  strokes/x/, strokes/m/        stroke outlines and stroke medians (centre lines) from Make Me a Hanzi; strokes/m/ is
                                written by  python3 tools/make_stroke_data.py --medians /path/to/makemeahanzi
The build stops if a character of a level has no stroke data, or if its medians do not match its outlines.

Outputs:
  chinese-character-tracing/index.html, chinese-character-tracing/hskN.json        English
  th/chinese-character-tracing/index.html, th/chinese-character-tracing/hskN.json  Thai
  chinese-character-tracing/s/hskN-KK.json   the strokes of set KK (01, 02, ...) of level N, shared by both pages

hskN.json: {"c": [[character, its readings (HSK 1-3: its readings in the HSK words, "hǎo / hào"; HSK 4-5: its
                   reading in the word that follows), the first word of the level that uses it, the word's
                   pinyin, its meaning (Thai on the Thai page, where the Thai list is complete)], ...]}
hskN-KK.json: {"字": {"s": [outline path, ...], "m": [[x0, y0, x1, y1, ...], ...]}, ...} in Make Me a Hanzi
coordinates (draw with transform="scale(1,-1) translate(0,-900)").

The Thai page is the English template with its text swapped for Thai; the build stops if a string is not found.
"""
import json

import practice

URL = "/chinese-character-tracing/"
TH_URL = "/th/chinese-character-tracing/"
STROKE_BASE = URL + "s/"
LEVELS = (1, 2, 3, 4, 5)
SET = 10
SHARDS = 128

UI_EN = {
    "of": "of", "charN": "Character {i} of {n}", "strokeN": "Stroke {i} of {n}", "set": "Characters {a}–{b}",
    "traced": "{d} of {n} characters traced", "loading": "Loading…",
    "loadFail": "The stroke data could not be loaded. Check your connection and try again.",
    "start": "Start at the dot and follow the arrow.", "startNoHint": "Write the first stroke.",
    "goOn": "Good. Now the next stroke.", "goOnNoHint": "Good. Now the next stroke.",
    "wrong": "Not quite. Start at the dot and follow the arrow.",
    "wrongAgain": "Watch how this stroke is written, then try it again.",
    "tooShort": "Draw the whole stroke in one line, without lifting your finger.",
    "done": "Well done!", "doneMistakes": "Done, with {m} {mw}.", "mistake": "mistake", "mistakes": "mistakes",
    "showMe": "Show me", "restart": "Start again", "next": "Next character", "skip": "Skip", "finish": "See my set",
    "boardLabel": "Tracing board for {c}. Draw each stroke with a finger or mouse.",
    "sumHead": "Set done", "sumLine": "You traced {t} of {n} characters, {c} of them without a mistake.",
    "skipped": "skipped", "noMistake": "no mistakes",
    "again": "Trace these again", "nextSet": "Next 10 characters", "nextLevel": "Next level: HSK {m}",
    "print": "Print these characters as a worksheet", "printBase": "/chinese-character-worksheets/",
    "mineEmpty": "Type some Chinese characters first.", "mineNone": "There is no stroke data for: {c}",
    "mineCount": "{n} characters, in sets of 10.", "mineSet": "My characters",
}
UI_TH = {
    "of": "จาก", "charN": "ตัวที่ {i} จาก {n}", "strokeN": "ขีดที่ {i} จาก {n}", "set": "ตัวที่ {a}–{b}",
    "traced": "เขียนแล้ว {d} จาก {n} ตัว", "loading": "กำลังโหลด…",
    "loadFail": "โหลดข้อมูลลำดับขีดไม่สำเร็จ ตรวจสอบอินเทอร์เน็ตแล้วลองใหม่อีกครั้ง",
    "start": "เริ่มที่จุด แล้วลากตามลูกศร", "startNoHint": "เขียนขีดแรก",
    "goOn": "ดีมาก ต่อด้วยขีดถัดไป", "goOnNoHint": "ดีมาก ต่อด้วยขีดถัดไป",
    "wrong": "ยังไม่ถูก เริ่มที่จุดแล้วลากตามลูกศร",
    "wrongAgain": "ดูวิธีเขียนขีดนี้ก่อน แล้วลองใหม่อีกครั้ง",
    "tooShort": "ลากให้ครบทั้งขีดในครั้งเดียว โดยไม่ยกนิ้ว",
    "done": "เก่งมาก!", "doneMistakes": "เขียนครบแล้ว ผิด {m} ครั้ง", "mistake": "", "mistakes": "",
    "showMe": "ดูวิธีเขียน", "restart": "เริ่มใหม่", "next": "ตัวถัดไป", "skip": "ข้าม", "finish": "ดูผลชุดนี้",
    "boardLabel": "ช่องฝึกเขียน {c} ใช้นิ้วหรือเมาส์ลากทีละขีด",
    "sumHead": "จบชุดแล้ว", "sumLine": "คุณเขียน {t} จาก {n} ตัว ไม่ผิดเลย {c} ตัว",
    "skipped": "ข้าม", "noMistake": "ไม่ผิดเลย",
    "again": "เขียนชุดนี้อีกครั้ง", "nextSet": "10 ตัวถัดไป", "nextLevel": "ระดับถัดไป: HSK {m}",
    "print": "พิมพ์ตัวอักษรชุดนี้เป็นแบบฝึกเขียน", "printBase": "/th/chinese-character-worksheets/",
    "mineEmpty": "พิมพ์ตัวอักษรจีนก่อน", "mineNone": "ไม่มีข้อมูลลำดับขีดของ: {c}",
    "mineCount": "{n} ตัว แบ่งเป็นชุดละ 10 ตัว", "mineSet": "ตัวอักษรของฉัน",
}

TITLE = "Chinese Character Tracing Online: Stroke Order Practice"
DESC = ("Trace Chinese characters stroke by stroke on a tian grid with your finger or mouse, with hints. "
        "HSK 1–5 character sets or any characters. Free.")
TH_TITLE = "ฝึกเขียนตัวอักษรจีนตามลำดับขีดออนไลน์ HSK 1–5 ฟรี"
TH_DESC = ("ฝึกเขียนตัวอักษรจีนทีละขีดบนตาราง 田 ด้วยนิ้วหรือเมาส์ มีคำใบ้ขีดถัดไป เลือกตัวอักษรตามระดับ HSK 1–5 "
           "หรือพิมพ์ตัวอักษรเอง ฟรี ไม่ต้องสมัคร")

TH_SWAPS = [
    ('<span>New HSK · 2025 syllabus</span><span class="chip">Levels 1–5</span><span class="chip">Free</span>',
     '<span>HSK ใหม่ · หลักสูตรปี 2025</span><span class="chip">ระดับ 1–5</span><span class="chip">ฟรี</span>'),
    ('<h1><span class="zh">描红</span>Chinese Character Tracing</h1>',
     '<h1><span class="zh">描红</span>ฝึกเขียนตัวอักษรจีนตามรอย</h1>'),
    ('<p class="lede">Write Chinese characters stroke by stroke with your finger or a mouse. Each stroke is checked as '
     'you write it: where it starts, the way it goes and the path it follows. Pick an HSK level or type your own '
     'characters.</p>',
     '<p class="lede">เขียนตัวอักษรจีนทีละขีดด้วยนิ้วหรือเมาส์ ทุกขีดจะถูกตรวจทันทีที่เขียน ทั้งจุดเริ่ม ทิศทาง '
     'และแนวของขีด เลือกระดับ HSK หรือพิมพ์ตัวอักษรที่อยากฝึกเอง</p>'),
    ('<h2 id="pick-title" class="visually-hidden">Choose the characters</h2>',
     '<h2 id="pick-title" class="visually-hidden">เลือกตัวอักษร</h2>'),
    ('<div class="levels tr-levels" role="group" aria-label="Characters">\n      <span class="lbl">Characters</span>',
     '<div class="levels tr-levels" role="group" aria-label="ตัวอักษร">\n      <span class="lbl">ตัวอักษร</span>'),
    ('data-level="0" aria-pressed="false">My characters</button>',
     'data-level="0" aria-pressed="false">ตัวอักษรของฉัน</button>'),
    ('<label for="tr-set">Set</label>', '<label for="tr-set">ชุด</label>'),
    ('<label for="tr-mine">Characters to trace</label>', '<label for="tr-mine">ตัวอักษรที่จะฝึก</label>'),
    ('id="tr-mine-go">Start tracing</button>', 'id="tr-mine-go">เริ่มฝึก</button>'),
    ('<div class="tr-switches" role="group" aria-label="Show">',
     '<div class="tr-switches" role="group" aria-label="แสดง">'),
    ('aria-pressed="true">Show the character</button>', 'aria-pressed="true">แสดงตัวอักษรจาง ๆ</button>'),
    ('aria-pressed="true">Show the next stroke</button>', 'aria-pressed="true">แสดงขีดถัดไป</button>'),
    ('<h2 id="board-title" class="visually-hidden">Tracing</h2>', '<h2 id="board-title" class="visually-hidden">ฝึกเขียน</h2>'),
    ('<p class="empty" id="loading">Loading…</p>', '<p class="empty" id="loading">กำลังโหลด…</p>'),
    ('<p class="tr-keys">Keys: H shows the next stroke, R starts the character again, Enter goes to the next one.</p>',
     '<p class="tr-keys">แป้นลัด: H ดูวิธีเขียนขีดถัดไป, R เริ่มตัวนี้ใหม่, Enter ไปตัวถัดไป</p>'),
    ('This browser is not letting the page save, so the characters you trace and your settings will not be kept.',
     'เบราว์เซอร์นี้ไม่อนุญาตให้บันทึกข้อมูล ตัวอักษรที่เขียนแล้วและการตั้งค่าจึงจะไม่ถูกเก็บไว้'),
    ('<h2 id="guide-title">About character tracing</h2>', '<h2 id="guide-title">เกี่ยวกับการฝึกเขียนตามรอย</h2>'),
    ('<h3>How do I trace a character?</h3>', '<h3>ฝึกเขียนตามรอยอย่างไร?</h3>'),
    ('<p>Draw each stroke in one go, from where it starts to where it ends, without lifting your finger. The dot shows '
     'where the next stroke starts and the arrow shows which way it goes. A stroke that follows the right path in the '
     'right direction turns dark. If it does not, it fades away and you try it again; after three tries the page '
     'shows you how the stroke is written. Turn the hints off when you know the character, and turn the grey '
     'character off to write it from memory.</p>',
     '<p>ลากแต่ละขีดให้จบในครั้งเดียว ตั้งแต่จุดเริ่มถึงจุดสิ้นสุด โดยไม่ยกนิ้ว จุดบอกว่าขีดถัดไปเริ่มตรงไหน '
     'และลูกศรบอกทิศทางที่ต้องลาก ถ้าลากถูกแนวและถูกทิศ ขีดนั้นจะกลายเป็นสีเข้ม ถ้าไม่ถูก รอยที่ลากจะค่อย ๆ หายไป '
     'ให้ลองใหม่ได้ และเมื่อลองครบสามครั้ง หน้าเว็บจะแสดงวิธีเขียนขีดนั้นให้ดู เมื่อจำตัวอักษรได้แล้ว ลองปิดคำใบ้ '
     'และปิดตัวอักษรจาง ๆ เพื่อเขียนจากความจำ</p>'),
    ('<h3>Why does stroke order matter?</h3>', '<h3>ทำไมลำดับขีดจึงสำคัญ?</h3>'),
    ('<p>Stroke order is the way characters are written by hand. It makes them quicker to write, neater, and easier to '
     'remember. A few rules cover most characters: top before bottom (<span class="zh-inline">三</span>), left before '
     'right (<span class="zh-inline">川</span>), horizontal before vertical (<span class="zh-inline">十</span>), the '
     'stroke to the left before the stroke to the right (<span class="zh-inline">人</span>), the middle before the '
     'sides (<span class="zh-inline">小</span>), and the outside before the inside, closing the box last '
     '(<span class="zh-inline">日</span>).</p>',
     '<p>ลำดับขีดคือวิธีเขียนตัวอักษรด้วยมือ ช่วยให้เขียนได้เร็วขึ้น สวยขึ้น และจำได้ง่ายขึ้น กฎไม่กี่ข้อใช้ได้กับตัวอักษรส่วนใหญ่ '
     'บนก่อนล่าง (<span class="zh-inline">三</span>) ซ้ายก่อนขวา (<span class="zh-inline">川</span>) '
     'ขีดนอนก่อนขีดตั้ง (<span class="zh-inline">十</span>) ขีดเฉียงซ้ายก่อนขีดเฉียงขวา '
     '(<span class="zh-inline">人</span>) ตรงกลางก่อนสองข้าง (<span class="zh-inline">小</span>) '
     'และนอกก่อนใน แล้วปิดกรอบเป็นขีดสุดท้าย (<span class="zh-inline">日</span>)</p>'),
    ('<h3>Which characters are in each level?</h3>', '<h3>แต่ละระดับมีตัวอักษรอะไรบ้าง?</h3>'),
    ('<p>The same sets as the <a href="/hsk-1-character-worksheets/">character worksheets</a>: every character used in '
     'the words of that HSK 3.0 level, once, in the order it first appears in the word list. Characters already used '
     'at a lower level are not repeated. Each character comes with the first word of the level that uses it. To '
     'trace anything else, choose My characters and type or paste any Chinese text.</p>',
     '<p>ชุดเดียวกับ<a href="/th/hsk-1-character-worksheets/">แบบฝึกเขียนตัวอักษร</a> คือตัวอักษรทุกตัวที่อยู่ในคำศัพท์ '
     'HSK 3.0 ของระดับนั้น ตัวละครั้งเดียว ตามลำดับที่ปรากฏครั้งแรกในรายการคำศัพท์ ตัวอักษรที่เคยมีในระดับที่ต่ำกว่าจะไม่ซ้ำ '
     'ทุกตัวแสดงคู่กับคำแรกในระดับที่ใช้ตัวอักษรนั้น ถ้าอยากฝึกตัวอื่น เลือก "ตัวอักษรของฉัน" แล้วพิมพ์หรือวางข้อความภาษาจีนอะไรก็ได้</p>'),
    ('<h3>Is my progress kept?</h3>', '<h3>ความคืบหน้าถูกเก็บไว้ไหม?</h3>'),
    ('<p>The characters you have traced, and your settings, are kept in this browser on this device, and nothing is '
     'sent anywhere. Writing on paper helps too: print the same characters as a '
     '<a href="/chinese-character-worksheets/">writing worksheet</a>, and learn the words they come from with the '
     '<a href="/hsk-flashcards/">flashcards</a>.</p>',
     '<p>ตัวอักษรที่เขียนแล้วและการตั้งค่าเก็บไว้ในเบราว์เซอร์ของอุปกรณ์นี้ และไม่มีข้อมูลใดถูกส่งไปที่ไหน '
     'การเขียนบนกระดาษก็ช่วยได้มาก พิมพ์ตัวอักษรชุดเดียวกันเป็น<a href="/th/chinese-character-worksheets/">แบบฝึกเขียน</a> '
     'และท่องคำศัพท์ที่ใช้ตัวอักษรเหล่านั้นด้วย<a href="/th/hsk-flashcards/">แฟลชการ์ด</a></p>'),
    ('<p><b>Stroke data.</b> Stroke outlines, stroke centre lines and character readings come from '
     '<a href="https://github.com/skishore/makemeahanzi">Make Me a Hanzi</a> (Arphic Public License and GNU LGPL, see '
     '<a href="/strokes/LICENSE.md">licence</a>). Stroke order follows mainland China standards for simplified '
     'characters. Words: HSK 3.0 (New HSK) vocabulary, 2025 syllabus, the same lists as the '
     '<a href="/hsk-1-word-list/">word list pages</a>.</p>',
     '<p><b>ข้อมูลลำดับขีด</b> รูปขีด เส้นกลางของขีด และเสียงอ่านของตัวอักษรมาจาก '
     '<a href="https://github.com/skishore/makemeahanzi">Make Me a Hanzi</a> (Arphic Public License และ GNU LGPL ดู'
     '<a href="/strokes/LICENSE.md" hreflang="en">สัญญาอนุญาต</a>) ลำดับขีดเป็นไปตามมาตรฐานตัวอักษรจีนตัวย่อของจีนแผ่นดินใหญ่ '
     'คำศัพท์: HSK 3.0 (HSK ใหม่) หลักสูตรปี 2025 ชุดเดียวกับ<a href="/th/hsk-1-word-list/">หน้ารายการคำศัพท์</a> '
     'พร้อมความหมายภาษาไทย</p>'),
]


# --- data ----------------------------------------------------------------------------------------------------------

def _new_chars(rows, known):
    out = []
    for w, _, _ in rows:
        for c in w:
            if "一" <= c <= "鿿" and c not in known and c not in out:
                out.append(c)
    return out


def level_sets(root):
    """{level: [(character, row index of the first word that uses it)]}: the character worksheet sets."""
    rows = {n: practice._rows(root, n) for n in LEVELS}
    sets = {}
    for n in (1, 2, 3):
        chars = list(json.loads((root / "strokes" / f"hsk{n}.json").read_text(encoding="utf-8")))
        sets[n] = chars
    # HSK 4 and 5: the characters not used in the words of the lower levels (tools/hsk4.py, tools/hsk5.py)
    sets[4] = _new_chars(rows[4], {c for n in (1, 2, 3) for w, _, _ in rows[n] for c in w})
    sets[5] = _new_chars(rows[5], {c for n in (1, 2, 3, 4) for w, _, _ in rows[n] for c in w})
    out = {}
    for n in LEVELS:
        items = []
        for c in sets[n]:
            i = next((k for k, r in enumerate(rows[n]) if c in r[0]), None)
            if i is None:
                raise SystemExit(f"tracing: HSK {n} character {c} is in no word of the level")
            items.append((c, i))
        out[n] = items
    return out, rows


def _strokes(root, chars):
    """{character: {"p": readings, "s": outlines, "m": medians}} from strokes/x/ and strokes/m/."""
    need = {}
    for c in chars:
        need.setdefault(ord(c) % SHARDS, []).append(c)
    out = {}
    for i, cs in need.items():
        x = json.loads((root / "strokes" / "x" / f"{i:02x}.json").read_text(encoding="utf-8"))
        m = json.loads((root / "strokes" / "m" / f"{i:02x}.json").read_text(encoding="utf-8"))
        for c in cs:
            if c not in x or c not in m:
                raise SystemExit(f"tracing: no stroke data for {c}")
            if len(x[c]["s"]) != len(m[c]) or any(len(v) < 4 or len(v) % 2 for v in m[c]):
                raise SystemExit(f"tracing: the medians of {c} do not match its strokes")
            out[c] = {"p": x[c]["p"], "s": x[c]["s"], "m": m[c]}
    return out


NEUTRAL_ONLY = {"匙"}  # read only in the neutral tone in its HSK word (钥匙 yàoshi); the stroke data's shī is wrong here


def _in_word_readings(root, sets, rows, strokes):
    """HSK 4 and 5: the reading of each character in its first word, from the word list (the Make Me a Hanzi
    reading in strokes/x/ can be another one: 茄 jiā, not qié as in 番茄). A neutral tone is shown with the
    character's own tone (户 hù in 窗户 chuānghu) when the stroke data or tones/words.json gives one."""
    import re
    import unicodedata
    import pinyin_practice
    tone_data = json.loads((root / "tones" / "words.json").read_text(encoding="utf-8"))["w"]
    valid = {re.sub(r"\d", "", x) for v in tone_data.values() for x in v.split()} - {"r"}
    marked = practice._readings(root)
    chars = {c: {pinyin_practice._bare(r) for r in rs} for c, rs in marked.items()}
    for w, v in tone_data.items():
        syl = v.split()
        if len(syl) == len(w):
            for c, x in zip(w, syl):
                chars.setdefault(c, set()).add(re.sub(r"\d", "", x))
    out = {}
    for n in (4, 5):
        for c, i in sets[n]:
            w, p, _ = rows[n][i]
            first = re.split(r"[;/]", p)[0].strip()
            if len(w) == 1:
                out[c] = unicodedata.normalize("NFC", first)
                continue
            sy = pinyin_practice.split(w, first, valid, chars)
            if sy is None:
                raise SystemExit(f"tracing: cannot split the pinyin of {w} {p}")
            base, tone = sy[w.index(c)]
            if tone == 5 and c not in NEUTRAL_ONLY:
                own = [r for r in strokes[c]["p"] if pinyin_practice._bare(r) == base and pinyin_practice._bare(r) != unicodedata.normalize("NFC", r)]
                td = tone_data.get(c, "")
                if own:
                    out[c] = own[0]
                    continue
                if re.fullmatch(base + r"[1-4]", td):
                    tone = int(td[-1])
            out[c] = practice._place(base, tone)
    return out


_CACHE = {}


def _data(root):
    if "d" not in _CACHE:
        sets, rows = level_sets(root)
        strokes = _strokes(root, {c for n in LEVELS for c, _ in sets[n]})
        for n in LEVELS:
            if len(sets[n]) < SET:
                raise SystemExit(f"tracing: HSK {n} has only {len(sets[n])} characters")
        for c, r in _in_word_readings(root, sets, rows, strokes).items():
            strokes[c]["p"] = [r]
        _CACHE["d"] = (sets, rows, strokes, practice._thai(root))
    return _CACHE["d"]


def _write_strokes(root, sets, strokes):
    folder = root / STROKE_BASE.strip("/")
    folder.mkdir(parents=True, exist_ok=True)
    written = set()
    for n in LEVELS:
        chars = [c for c, _ in sets[n]]
        for k in range(0, len(chars), SET):
            name = f"hsk{n}-{k // SET + 1:02d}.json"
            part = {c: {"s": strokes[c]["s"], "m": strokes[c]["m"]} for c in chars[k:k + SET]}
            (folder / name).write_text(json.dumps(part, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
            written.add(name)
    for f in folder.glob("hsk*.json"):
        if f.name not in written:
            f.unlink()


def _write_levels(root, base, lang, sets, rows, strokes, thai):
    folder = root / base.strip("/")
    folder.mkdir(parents=True, exist_ok=True)
    for n in LEVELS:
        th = thai.get(n) if lang == "th" else None
        out = []
        for c, i in sets[n]:
            w, p, m = rows[n][i]
            out.append([c, " / ".join(strokes[c]["p"]), w, p, th[i] if th else m])
            if not out[-1][1]:
                raise SystemExit(f"tracing: no reading for {c}")
        (folder / f"hsk{n}.json").write_text(json.dumps({"c": out}, ensure_ascii=False, separators=(",", ":")),
                                             encoding="utf-8")


def _body(tpl, nav_html, ui, data_base, counts):
    body = ((tpl / "tracing_body.html").read_text(encoding="utf-8").replace("__NAV__", nav_html)
            .replace("__UI_JSON__", json.dumps(ui, ensure_ascii=False)).replace("__DATA_BASE__", data_base)
            .replace("__STROKE_BASE__", STROKE_BASE)
            .replace("__COUNTS_JSON__", json.dumps(counts, separators=(",", ":"))))
    if "__" in body.replace("__proto__", ""):
        raise SystemExit("tracing: a placeholder was left in the page")
    return body


def _ld(name, url, desc, lang):
    return json.dumps({
        "@context": "https://schema.org", "@type": "WebApplication", "name": name, "url": url, "inLanguage": lang,
        "applicationCategory": "EducationalApplication", "operatingSystem": "Any",
        "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"}, "description": desc,
    }, ensure_ascii=False)


def _css(tpl):
    return ((tpl / "checker.css").read_text(encoding="utf-8") + (tpl / "practice.css").read_text(encoding="utf-8")
            + (tpl / "tracing.css").read_text(encoding="utf-8"))


def _counts(sets):
    return {str(n): len(sets[n]) for n in LEVELS}


def build(root, pages, nav, render, base_css, tpl, site):
    sets, rows, strokes, thai = _data(root)
    _write_strokes(root, sets, strokes)
    _write_levels(root, URL, "en", sets, rows, strokes, thai)
    body = _body(tpl, nav(pages, URL), UI_EN, URL, _counts(sets))
    out = render(TITLE, DESC, site + URL, base_css + _css(tpl), body,
                 f'<script type="application/ld+json">{_ld("Chinese Character Tracing", site + URL, DESC, "en")}</script>')
    (root / URL.strip("/") / "index.html").write_text(out, encoding="utf-8")
    return [URL]


def build_th(*, root, tpl, site, render, nav, font_link, foot, base_css, th_css):
    sets, rows, strokes, thai = _data(root)
    _write_levels(root, TH_URL, "th", sets, rows, strokes, thai)
    body = _body(tpl, nav(TH_URL), UI_TH, TH_URL, _counts(sets))
    for a, b in TH_SWAPS:
        if body.count(a) != 1:
            raise SystemExit(f"tracing: English text not found for the Thai page: {a[:60]}")
        body = body.replace(a, b)
    out = render(TH_TITLE, TH_DESC, site + TH_URL, base_css + _css(tpl) + th_css, body,
                 font_link + f'\n<script type="application/ld+json">{_ld("ฝึกเขียนตัวอักษรจีนตามรอย", site + TH_URL, TH_DESC, "th")}</script>',
                 lang="th", foot=foot)
    (root / TH_URL.strip("/") / "index.html").write_text(out, encoding="utf-8")
    return [TH_URL]


def alternates(root):
    return {URL: TH_URL}
