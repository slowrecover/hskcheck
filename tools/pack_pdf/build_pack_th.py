"""Build the Thai edition of the Old HSK 1 -> New HSK 1 Upgrade Pack (same layout and quizzes as build_pack.py).

Usage:  python3 tools/pack_pdf/build_pack_th.py && python3 tools/pack_pdf/topdf.py $PWD/tools/pack_pdf/pack_th.html /tmp/pack_th.pdf
Needs the Noto Sans Thai font installed (fc-list | grep "Noto Sans Thai") so the PDF renders Thai properly.

How it works: it reads build_pack.py, swaps every English string for Thai (each swap must be found exactly once,
so a change to build_pack.py that breaks a swap stops this build), and runs it. Word meanings come from
data/th/hsk1_th.tsv; day titles and the Thai translation of each example sentence are in content_th.py.
Never commit the PDF or pack_th.html.
"""
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
SRC = (HERE / "build_pack.py").read_text(encoding="utf-8")

DATA = '''from content import DAYS as _EN_DAYS, CHAR_PY  # noqa: E402
from content_th import DAY_TITLES as _TH_TITLES, SENT as _TH_SENT  # noqa: E402
_TH_MEAN = dict(l.rstrip("\\n").split("\\t")[:2] for l in (HERE.parent.parent / "data/th/hsk1_th.tsv").read_text(encoding="utf-8").splitlines() if "\\t" in l)
DAYS = [(_TH_TITLES[i], [(w[0], w[1], _TH_MEAN[w[0]], w[3], w[4], _TH_SENT[w[0]]) for w in ws]) for i, (_t, ws) in enumerate(_EN_DAYS)]
assert len(_TH_TITLES) == len(_EN_DAYS) and len(_TH_SENT) == sum(len(ws) for _t, ws in _EN_DAYS)'''

SWAPS = [
    ("from content import DAYS, CHAR_PY  # noqa: E402", DATA),
    ('TITLE = "Old HSK 1 → New HSK 1 Upgrade Pack · hskcheck.com"',
     'TITLE = "ชุดอัปเกรด HSK 1 เก่า → HSK 1 ใหม่ · hskcheck.com"'),
    # cover
    ('<div class="kicker">HSK 2.0 → HSK 3.0 · PRINTABLE PACK</div>',
     '<div class="kicker">HSK 2.0 → HSK 3.0 · ชุดแบบฝึกพิมพ์ได้</div>'),
    ('<h1 class="cover-t">Old HSK 1<br><span class="arrow">→</span><br><span class="green">New HSK 1</span></h1>',
     '<h1 class="cover-t">HSK 1 เก่า<br><span class="arrow">→</span><br><span class="green">HSK 1 ใหม่</span></h1>'),
    ('<div class="cover-sub">Upgrade Pack</div>', '<div class="cover-sub">ชุดอัปเกรด (ฉบับภาษาไทย)</div>'),
    ('''<p class="cover-lede">You studied the old six-level HSK 1. The new HSK 1 (2025 syllabus) has 300 words. 145 of them were
already in old HSK 1. This pack teaches you the other 155, in ten short lessons.</p>''',
     '''<p class="cover-lede">คุณเคยเรียน HSK 1 แบบเก่า (ระบบ 6 ระดับ) มาแล้ว HSK 1 แบบใหม่ (หลักสูตรปี 2025) มีคำศัพท์ 300 คำ
ในนั้น 145 คำมีอยู่ใน HSK 1 เก่าแล้ว ชุดนี้จะสอนอีก 155 คำที่เหลือ ใน 10 บทเรียนสั้น ๆ</p>'''),
    ("<div><b>155</b><span>words to learn</span></div>", "<div><b>155</b><span>คำศัพท์ที่ต้องเรียน</span></div>"),
    ("<div><b>74</b><span>new characters to write</span></div>", "<div><b>74</b><span>ตัวอักษรใหม่ที่ต้องฝึกเขียน</span></div>"),
    ("<div><b>10</b><span>lessons, one a day</span></div>", "<div><b>10</b><span>บทเรียน วันละบท</span></div>"),
    ("<li>Every word with pinyin, meaning and an example sentence that uses only new HSK 1 words</li>",
     "<li>ทุกคำมีพินอิน ความหมายภาษาไทย และประโยคตัวอย่างที่ใช้เฉพาะคำศัพท์ HSK 1 ใหม่</li>"),
    ("<li>Stroke order and tracing practice for every character you haven't met in old HSK 1</li>",
     "<li>ลำดับขีดและช่องฝึกเขียนตามรอย สำหรับทุกตัวอักษรที่ไม่มีใน HSK 1 เก่า</li>"),
    ("<li>A quiz after each lesson, a final check, and answers at the back</li>",
     "<li>แบบทดสอบท้ายทุกบท แบบทดสอบรวม และเฉลยท้ายเล่ม</li>"),
    ('''<div class="cover-foot">Word lists follow the 2025 HSK 3.0 syllabus. Made by hskcheck.com, where the HSK level checker,
word lists and the old → new HSK word gap tool are free.</div>''',
     '''<div class="cover-foot">รายการคำศัพท์อ้างอิงหลักสูตร HSK 3.0 ปี 2025 จัดทำโดย hskcheck.com ซึ่งมีเครื่องมือตรวจระดับ HSK
รายการคำศัพท์ และเครื่องมือเทียบคำศัพท์ HSK เก่า → ใหม่ ให้ใช้ฟรี</div>'''),
    # how to use
    ("""f'<tr><td class="dn">Day {i}</td>""", """f'<tr><td class="dn">วันที่ {i}</td>"""),
    ('<h2 class="ph">How to use this pack</h2>', '<h2 class="ph">วิธีใช้ชุดนี้</h2>'),
    ("<p>Each day has three parts. Together they take about 30 minutes.</p>",
     "<p>แต่ละวันมี 3 ส่วน ใช้เวลารวมประมาณ 30 นาที</p>"),
    ('''<li><b>Learn the words.</b> Read each word, its pinyin and meaning, then read the example sentence aloud.
  Every sentence uses only words from the new HSK 1 list, so you can understand all of it.</li>''',
     '''<li><b>เรียนคำศัพท์</b> อ่านแต่ละคำ พินอิน และความหมาย แล้วอ่านประโยคตัวอย่างออกเสียงดัง ๆ
  ทุกประโยคใช้เฉพาะคำในรายการ HSK 1 ใหม่ คุณจึงเข้าใจได้ทั้งประโยค</li>'''),
    ('''<li><b>Write the new characters.</b> Follow the stroke order, trace the grey characters, then write your own.
  Only characters you didn't meet in old HSK 1 are here.</li>''',
     '''<li><b>ฝึกเขียนตัวอักษรใหม่</b> ทำตามลำดับขีด เขียนทับตัวอักษรสีเทา แล้วเขียนเอง
  ในส่วนนี้มีเฉพาะตัวอักษรที่ไม่มีใน HSK 1 เก่า</li>'''),
    ('''<li><b>Take the quiz.</b> Do it without looking back, then check your answers at the back of the pack.
  Mark the words you missed and read them again the next day.</li>''',
     '''<li><b>ทำแบบทดสอบ</b> ทำโดยไม่ย้อนกลับไปดู แล้วตรวจคำตอบที่ท้ายเล่ม
  ทำเครื่องหมายคำที่ตอบผิด แล้วอ่านทวนอีกครั้งในวันรุ่งขึ้น</li>'''),
    ('<h2 class="ph2">Your 10-day plan</h2>', '<h2 class="ph2">แผนเรียน 10 วันของคุณ</h2>'),
    ('<th>Topic</th><th class="num">Words</th><th class="num">New characters</th><th>Done</th>',
     '<th>หัวข้อ</th><th class="num">คำศัพท์</th><th class="num">ตัวอักษรใหม่</th><th>เสร็จ</th>'),
    ('''<p class="note">After Day 10, take the final check. Then use the free tools at hskcheck.com: the HSK level checker shows
which words in any Chinese text are above HSK 1, and the HSK flashcards help you review all 300 words.</p>''',
     '''<p class="note">หลังวันที่ 10 ให้ทำแบบทดสอบรวม จากนั้นใช้เครื่องมือฟรีที่ hskcheck.com/th: เครื่องมือตรวจระดับ HSK
บอกได้ว่าคำไหนในข้อความภาษาจีนสูงกว่า HSK 1 และแฟลชการ์ด HSK ช่วยทบทวนคำศัพท์ครบทั้ง 300 คำ</p>'''),
    ('''<p class="note"><b>Pinyin note.</b> Pinyin in the sentences shows tone changes as you say them: 不 becomes bú and 一
becomes yí or yì before some tones. Neutral tones have no mark.</p>''',
     '''<p class="note"><b>หมายเหตุเรื่องพินอิน</b> พินอินในประโยคแสดงเสียงวรรณยุกต์ตามที่ออกเสียงจริง: 不 เปลี่ยนเป็น bú
และ 一 เปลี่ยนเป็น yí หรือ yì เมื่ออยู่หน้าเสียงบางเสียง ส่วนเสียงเบาไม่มีเครื่องหมาย</p>'''),
    # day pages
    ("""head = (f'<div class="dayhead"><div class="dk">DAY {di}</div><h2>{E(d["title"])}</h2>'
                f'<div class="dm">{len(ws)} words · {len(d["chars"])} new characters</div></div>') if ci == 0 else \\
            f'<div class="dayhead small"><div class="dk">DAY {di} · CONTINUED</div></div>'""",
     """head = (f'<div class="dayhead"><div class="dk">วันที่ {di}</div><h2>{E(d["title"])}</h2>'
                f'<div class="dm">{len(ws)} คำ · ตัวอักษรใหม่ {len(d["chars"])} ตัว</div></div>') if ci == 0 else \\
            f'<div class="dayhead small"><div class="dk">วันที่ {di} · ต่อ</div></div>'"""),
    ("""<div class="cn">{n} stroke{'s' if n > 1 else ''}</div>""", """<div class="cn">{n} ขีด</div>"""),
    ('<div class="cin">in: {E(inw)}</div>', '<div class="cin">ใน: {E(inw)}</div>'),
    ("""head = f'<h2 class="ph">Day {di} · Write the new characters</h2>'""",
     """head = f'<h2 class="ph">วันที่ {di} · ฝึกเขียนตัวอักษรใหม่</h2>'"""),
    ("""head += ('<p class="intro">Follow the stroke order (the newest stroke is red), trace the three grey '
                     'characters, then fill the empty boxes.</p>')""",
     """head += ('<p class="intro">ทำตามลำดับขีด (ขีดล่าสุดเป็นสีแดง) เขียนทับตัวอักษรสีเทา 3 ตัว '
                     'แล้วเขียนเองในช่องที่ว่าง</p>')"""),
    # quizzes
    ('page(f"""<h2 class="ph">Day {di} · Quiz</h2>', 'page(f"""<h2 class="ph">วันที่ {di} · แบบทดสอบ</h2>'),
    ('<h3 class="qh">A · Match each word to its meaning</h3>', '<h3 class="qh">A · จับคู่คำศัพท์กับความหมาย</h3>'),
    ('<h3 class="qh">B · Fill in the blanks</h3><p class="intro">Use each word in the box once. The English tells you what the sentence means.</p>',
     '<h3 class="qh">B · เติมคำในช่องว่าง</h3><p class="intro">ใช้คำในกรอบคำละหนึ่งครั้ง ประโยคภาษาไทยบอกความหมายของประโยค</p>'),
    ('<h3 class="qh">C · Write the pinyin, with tone marks</h3>', '<h3 class="qh">C · เขียนพินอิน พร้อมเครื่องหมายวรรณยุกต์</h3>'),
    ('page(f"""<h2 class="ph">Final check</h2>', 'page(f"""<h2 class="ph">แบบทดสอบรวม</h2>'),
    ('''<p class="intro">20 questions on words from all ten days. Try it without looking back. 16 or more right means you
know the new HSK 1 words well.</p>''',
     '''<p class="intro">20 ข้อ จากคำศัพท์ทั้ง 10 วัน ลองทำโดยไม่ย้อนกลับไปดู ถ้าถูก 16 ข้อขึ้นไป
แปลว่าคุณรู้คำศัพท์ HSK 1 ใหม่ดีแล้ว</p>'''),
    ('<h3 class="qh">A · Choose the meaning</h3>', '<h3 class="qh">A · เลือกความหมายที่ถูกต้อง</h3>'),
    ('page(f"""<h2 class="ph">Final check · continued</h2>', 'page(f"""<h2 class="ph">แบบทดสอบรวม · ต่อ</h2>'),
    ('<h3 class="qh">B · Write the missing word in Chinese characters</h3>', '<h3 class="qh">B · เขียนคำที่หายไปเป็นตัวอักษรจีน</h3>'),
    ('<p class="intro">The English tells you what the sentence means. Each missing word is a new HSK 1 word from this pack.</p>',
     '<p class="intro">ประโยคภาษาไทยบอกความหมายของประโยค คำที่หายไปทุกคำเป็นคำศัพท์ HSK 1 ใหม่จากชุดนี้</p>'),
    ('<div class="score">Your score: <span class="line short"></span> / 20</div>',
     '<div class="score">คะแนนของคุณ: <span class="line short"></span> / 20</div>'),
    # answers
    ('blocks.append(f"""<div class="ans"><h3>Day {di}</h3>', 'blocks.append(f"""<div class="ans"><h3>วันที่ {di}</h3>'),
    ('blocks.append(f"""<div class="ans"><h3>Final check</h3>', 'blocks.append(f"""<div class="ans"><h3>แบบทดสอบรวม</h3>'),
    ("""page('<h2 class="ph">Answers</h2>'""", """page('<h2 class="ph">เฉลย</h2>'"""),
    ("""page('<h2 class="ph">Answers · continued</h2>'""", """page('<h2 class="ph">เฉลย · ต่อ</h2>'"""),
    # index
    ("""page(f'<h2 class="ph">Word index{" · continued" if k else ""}</h2>' +""",
     """page(f'<h2 class="ph">ดัชนีคำศัพท์{" · ต่อ" if k else ""}</h2>' +"""),
    ("""('<p class="intro">All 155 words in pinyin order, with the day where you learn them.</p>' if k == 0 else "")""",
     """('<p class="intro">คำศัพท์ทั้ง 155 คำ เรียงตามพินอิน ตัวเลขด้านขวาคือวันที่ได้เรียนคำนั้น</p>' if k == 0 else "")"""),
    ("""page('<h2 class="ph">The 145 words you already know</h2><p class="intro">These new HSK 1 words were already in old HSK 1. '
     'Read through them once: if one looks unfamiliar, look it up in the HSK 1 word list at hskcheck.com.</p>'""",
     """page('<h2 class="ph">145 คำที่คุณรู้แล้ว</h2><p class="intro">คำศัพท์ HSK 1 ใหม่เหล่านี้มีอยู่ใน HSK 1 เก่าแล้ว '
     'อ่านผ่าน ๆ หนึ่งรอบ ถ้าคำไหนดูไม่คุ้น ให้เปิดดูในรายการคำศัพท์ HSK 1 ที่ hskcheck.com/th/hsk-1-word-list</p>'"""),
    # last page
    ('''page("""<h2 class="ph">What next?</h2>
<p>You now know all 300 words of the new HSK 1. Here is how to keep them and move on, using the free tools at hskcheck.com:</p>
<ul class="bul big">
  <li><b>HSK flashcards</b> (hskcheck.com/hsk-flashcards): review all 300 HSK 1 words a few minutes a day. New words and
  words due for review come up on their own, and your progress stays on your phone.</li>
  <li><b>HSK practice test</b> (hskcheck.com/hsk-practice-test): 20 quick questions on meanings, pinyin and listening.</li>
  <li><b>HSK level checker</b> (hskcheck.com): paste any Chinese text and see which words are above HSK 1.</li>
  <li><b>Grammar pages</b> (hskcheck.com/learn): short explanations of HSK 1 grammar such as 了, 吗, 呢 and 不 vs 没有,
  each with a free worksheet.</li>
  <li><b>Old → new HSK</b> (hskcheck.com/old-hsk-to-new-hsk): when you are ready for HSK 2, see which words you still need.</li>
</ul>
<div class="notes"><h3>Notes</h3>""''',
     '''page("""<h2 class="ph">เรียนต่ออย่างไรดี</h2>
<p>ตอนนี้คุณรู้คำศัพท์ HSK 1 ใหม่ครบทั้ง 300 คำแล้ว นี่คือวิธีจำให้แม่นและเรียนต่อ ด้วยเครื่องมือฟรีที่ hskcheck.com:</p>
<ul class="bul big">
  <li><b>แฟลชการ์ด HSK</b> (hskcheck.com/th/hsk-flashcards): ทบทวนคำศัพท์ HSK 1 ทั้ง 300 คำวันละไม่กี่นาที
  คำใหม่และคำที่ถึงเวลาทบทวนจะขึ้นมาให้เอง และความคืบหน้าจะเก็บไว้ในโทรศัพท์ของคุณ</li>
  <li><b>แบบทดสอบ HSK</b> (hskcheck.com/th/hsk-practice-test): 20 ข้อสั้น ๆ เรื่องความหมาย พินอิน และการฟัง</li>
  <li><b>เครื่องมือตรวจระดับ HSK</b> (hskcheck.com/th): วางข้อความภาษาจีนใดก็ได้ แล้วดูว่าคำไหนสูงกว่า HSK 1</li>
  <li><b>ไวยากรณ์</b> (hskcheck.com/th/learn): คำอธิบายสั้น ๆ ของไวยากรณ์ HSK 1 เช่น 了 吗 呢 และ 不 กับ 没有
  พร้อมใบงานฟรีทุกหัวข้อ</li>
  <li><b>HSK เก่า → ใหม่</b> (hskcheck.com/th/old-hsk-to-new-hsk): เมื่อพร้อมเรียน HSK 2 ดูได้ว่ายังต้องเรียนคำไหนอีก</li>
</ul>
<div class="notes"><h3>บันทึก</h3>""'''),
    ('''<p class="small">Found a mistake? Email willowbewater@gmail.com and we will send you a corrected file.
This pack is for one learner's own study. hskcheck.com is independent and not affiliated with the organisers of the HSK exam.</p>''',
     '''<p class="small">พบข้อผิดพลาด? อีเมลมาที่ willowbewater@gmail.com แล้วเราจะส่งไฟล์ที่แก้ไขแล้วให้
ชุดนี้สำหรับผู้เรียนหนึ่งคนใช้เรียนด้วยตนเอง hskcheck.com เป็นเว็บไซต์อิสระ ไม่มีส่วนเกี่ยวข้องกับผู้จัดสอบ HSK</p>'''),
    # assemble: Thai font, Thai lang, own output file
    ('CSS = (HERE / "pack.css").read_text(encoding="utf-8")',
     'CSS = (HERE / "pack.css").read_text(encoding="utf-8") + (\'body { font-family: "Noto Sans Thai", "Inter", "Noto Sans", '
     '"Noto Sans CJK SC", sans-serif; line-height: 1.5; } .wm, .se, .qe, .im, .qm, .fo { font-family: "Noto Sans Thai", sans-serif; } .kicker { letter-spacing: .03em; }\')'),
    ("<html lang='en'>", "<html lang='th'>"),
    ('(HERE / "pack.html").write_text', '(HERE / "pack_th.html").write_text'),
]

code = SRC
for old, new in SWAPS:
    n = code.count(old)
    if n != 1:
        raise SystemExit(f"build_pack_th: expected 1 match, found {n}: {old[:80]!r}")
    code = code.replace(old, new)
exec(compile(code, str(HERE / "build_pack.py"), "exec"), {"__name__": "__main__", "__file__": str(HERE / "build_pack.py")})
