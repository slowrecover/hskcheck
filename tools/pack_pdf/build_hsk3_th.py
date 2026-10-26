"""Build the Thai HSK 3 vocabulary workbook PDF (all 499 HSK 3 words, 25 lessons, A4), and its free lesson 1 sample.

Usage:
  python3 tools/pack_pdf/build_hsk3_th.py            # writes tools/pack_pdf/hsk3_th.html and hsk3_th_lesson1.html
  python3 tools/pack_pdf/topdf.py $PWD/tools/pack_pdf/hsk3_th.html /tmp/hsk3_th.pdf          # full workbook (never commit)
  python3 tools/pack_pdf/topdf.py $PWD/tools/pack_pdf/hsk3_th_lesson1.html \\
      $PWD/th/upgrade-packs/hsk-3-vocabulary-workbook/hsk3-lesson-1-free.pdf             # free sample (committed)
Needs the Noto Sans Thai font (fc-list | grep "Noto Sans Thai").

Same layout and page types as build_pack.py (same pack.css and helpers). Data: lesson plan and sentences in
data/packs/hsk3_th_plan.json and data/packs/hsk3_th_lessons/NN.json (see PACK_HSK3_TH.md), word pinyin from
data/hsk3.tsv, Thai meanings from data/th/hsk3_th.tsv, stroke data from strokes/hsk3.json. New characters are the ones
not in any HSK 1-2 word, taught in the first lesson where they appear. Never commit the full PDF or the HTML files.
"""
import html, json, math, pathlib, random, unicodedata

HERE = pathlib.Path(__file__).resolve().parent
R = HERE.parent.parent
E = html.escape
TITLE = "สมุดแบบฝึกคำศัพท์ HSK 3 · hskcheck.com"
PAGE_URL = "hskcheck.com/th/upgrade-packs/hsk-3-vocabulary-workbook/"
PRICE = "$3.99"


def tsv(path):
    return [l.rstrip("\n").split("\t") for l in (R / path).read_text(encoding="utf-8").splitlines() if "\t" in l]


EN = {r[0]: r for r in tsv("data/hsk3.tsv")}
TH = {r[0]: r[1] for r in tsv("data/th/hsk3_th.tsv")}
STROKES = json.loads((R / "strokes/hsk3.json").read_text(encoding="utf-8"))
OLD_CHARS = {c for n in (1, 2) for r in tsv(f"data/hsk{n}.tsv") for c in r[0]}
PLAN = json.loads((R / "data/packs/hsk3_th_plan.json").read_text(encoding="utf-8"))["lessons"]

# ---- data -------------------------------------------------------------------------------------------------------
# a word is (word, pinyin, Thai meaning, sentence, sentence pinyin, Thai sentence)
days = []
seen = []
for li, plan in enumerate(PLAN, 1):
    data = json.loads((R / f"data/packs/hsk3_th_lessons/{li:02d}.json").read_text(encoding="utf-8"))
    assert [x["w"] for x in data["words"]] == plan["words"], li
    words = [(x["w"], EN[x["w"]][1], TH[x["w"]], x["zh"], x["py"], x["th"]) for x in data["words"]]
    new = []
    for w in words:
        assert w[0] in w[3], w
        for c in w[0]:
            if c not in OLD_CHARS and c not in seen and "一" <= c <= "鿿":
                seen.append(c)
                new.append(c)
    days.append({"title": plan["title_th"], "words": words, "chars": new})
ALL_WORDS = [w for d in days for w in d["words"]]
assert len(days) == 25 and len(ALL_WORDS) == 499 and len(seen) == 284, (len(days), len(ALL_WORDS), len(seen))
assert sorted(w[0] for w in ALL_WORDS) == sorted(EN), "every HSK 3 word exactly once"


def char_reading(c):
    """The reading of c used in the first word that teaches it (stroke data lists all readings)."""
    readings = STROKES[c]["p"]
    w = next(x for x in ALL_WORDS if c in x[0])
    used = [r for r in readings if r in w[1].replace("'", "").lower()]
    return used[0] if len(used) == 1 else " / ".join(readings)


for c in seen:
    assert c in STROKES and STROKES[c]["p"], c
CHAR_PY = {c: char_reading(c) for c in seen}

# Words that could both be right in the same blank, or are too close in meaning to share a matching exercise.
GROUPS = [
    # spec
    {"常", "常常"}, {"刚", "刚才", "刚刚"}, {"或", "或者"}, {"可", "可是"}, {"总", "总是"}, {"收", "收到"}, {"受", "受到"},
    {"选", "选择"}, {"季", "季节", "四季"}, {"会", "会议", "开会"}, {"变", "变化", "变成"}, {"字典", "词典"}, {"照相", "拍照", "照"},
    {"聊", "聊天儿"}, {"练", "练习"}, {"得到", "得"}, {"认得", "认识"},
    # lessons 1-5
    {"男人", "男生"}, {"女人", "女生"}, {"大人", "老人"}, {"爱人", "夫妻"}, {"阿姨", "叔叔"}, {"别人", "客人"},
    {"像", "一样", "好像"}, {"一样", "不同"}, {"胖", "瘦", "矮"}, {"年轻", "老"}, {"可爱", "聪明", "难看"}, {"长", "像"},
    {"房子", "屋子", "室"}, {"楼梯", "电梯"}, {"灯", "电", "空调"}, {"搬", "搬家"}, {"冰箱", "洗衣机"},
    {"打扫", "扫"}, {"干净", "脏"}, {"刷", "牙刷"}, {"关", "放"}, {"丢", "不见"}, {"平时", "习惯"}, {"盘子", "碗"},
    {"箱子", "瓶子"}, {"酒", "啤酒"}, {"饮料", "矿泉水"}, {"饿", "饱", "渴"}, {"甜", "新鲜"}, {"筷子", "勺子"},
    {"蛋糕", "冰激凌"}, {"西瓜", "香蕉"},
    # lessons 6-10
    {"衬衫", "上衣"}, {"大衣", "雨衣"}, {"短", "短裤"}, {"大小", "合适"}, {"毛", "角"}, {"公斤", "斤"}, {"卡", "银行卡", "信用卡"},
    {"银行", "银行卡"}, {"用", "有用"}, {"外语", "语言"}, {"句", "句子"}, {"请假", "休假"}, {"完成", "结束"}, {"办法", "方法"},
    {"办", "办公室"}, {"需要", "要求"}, {"课本", "课文"}, {"笔记", "笔记本"}, {"初中", "年级", "班级"}, {"放学", "迟到"},
    {"讲", "回答"}, {"留学", "留学生"}, {"水平", "成绩"},
    # lessons 11-15
    {"马路", "街", "路边"}, {"城市", "市"}, {"地点", "地方"}, {"地", "草地"}, {"草", "草地"}, {"花园", "园", "公园"},
    {"北", "南", "东", "西"}, {"东北", "东南", "西北", "西南"}, {"北方", "南方"}, {"东方", "西方"}, {"以上", "以下"},
    {"动物", "动物园"}, {"汽车", "自行车"}, {"牛", "羊", "马", "鸡"}, {"出发", "起飞", "离开"}, {"遇到", "遇见"},
    {"中", "中间"}, {"面前", "身边"}, {"春天", "夏天", "秋天", "冬天"}, {"风", "刮"},
    # lessons 16-20
    {"关心", "担心"}, {"小心", "注意"}, {"出院", "住院"}, {"跳", "爬"}, {"兴趣", "感兴趣"}, {"表演", "节目"}, {"声", "声音"},
    {"开机", "关机"}, {"怕", "害怕"}, {"急", "着急"}, {"行", "不行"}, {"关注", "关心"}, {"感到", "感兴趣"}, {"喜爱", "受到"},
    {"开心", "难过"}, {"邮件", "邮箱"}, {"信", "封"}, {"新闻", "报纸"}, {"发", "发现"}, {"难过", "生气"}, {"网球", "羽毛球"},
    {"运动会", "运动员"}, {"体育馆", "球场"}, {"放心", "相信"},
    # lessons 21-25
    {"认为", "以为"}, {"明白", "清楚", "懂得", "了解"}, {"决定", "打算"}, {"简单", "容易"}, {"有关", "关于"},
    {"后来", "然后", "以后"}, {"终于", "最后"}, {"挺", "比较", "特别"}, {"几乎", "差不多"}, {"一定", "必须", "应该", "该"},
    {"一定", "当然"}, {"别的", "其他"}, {"如果", "只要", "的话"}, {"只要", "只有"}, {"除了", "以外"}, {"为", "为了"},
    {"放假", "假期"}, {"久", "好久", "不久"}, {"节", "节日", "过节"}, {"后天", "前天"}, {"后年", "前年"}, {"以前", "过去"},
    {"一直", "总是"}, {"马上", "突然"}, {"只能", "只是"}, {"不但", "而且"}, {"可是", "其实"}, {"极", "更"},
]


def related(a, b):
    return any(a in g and b in g for g in GROUPS)


def clash_free(items):
    names = [w[0] for w in items]
    means = [w[2] for w in items]
    return len(set(means)) == len(means) and not any(related(a, b) for i, a in enumerate(names) for b in names[i + 1:])


def words_with(c):
    return [w[0] for w in ALL_WORDS if c in w[0]]


def blank(w):
    return w[3].replace(w[0], "（　　　）", 1)


# ---- small renderers (as in build_pack.py) ----------------------------------------------------------------------
def hl(sentence, word):
    i = sentence.find(word)
    return E(sentence[:i]) + f'<b class="hl">{E(word)}</b>' + E(sentence[i + len(word):])


def stroke_svg(c, upto=None, size=34, mode="step"):
    """mode step: strokes < upto dark grey, stroke upto-1 red. full: all dark. ghost: all light grey."""
    s = STROKES[c]["s"]
    n = len(s) if upto is None else upto
    paths = []
    for i, d in enumerate(s[:n]):
        if mode == "ghost":
            col = "#d5d9e0"
        elif mode == "full":
            col = "#1e2433"
        else:
            col = "#d6342c" if i == n - 1 else "#4a5160"
        paths.append(f'<path d="{d}" fill="{col}"/>')
    return (f'<svg viewBox="0 0 1024 1024" width="{size}" height="{size}">'
            f'<g transform="scale(1,-1) translate(0,-900)">{"".join(paths)}</g></svg>')


def grid(inner="", cls="cell"):
    return (f'<div class="{cls}"><svg class="g" viewBox="0 0 100 100" preserveAspectRatio="none">'
            '<line x1="0" y1="0" x2="100" y2="100"/><line x1="100" y1="0" x2="0" y2="100"/>'
            '<line x1="50" y1="0" x2="50" y2="100"/><line x1="0" y1="50" x2="100" y2="50"/></svg>'
            f'{inner}</div>')


def first_sense(m):
    return m.split(";")[0].strip()


class Book:
    def __init__(self):
        self.pages = []

    def page(self, body, cls=""):
        self.pages.append((body, cls))

    def html(self, title):
        n = len(self.pages)
        css = (HERE / "pack.css").read_text(encoding="utf-8") + (
            'body { font-family: "Noto Sans Thai", "Inter", "Noto Sans", "Noto Sans CJK SC", sans-serif; line-height: 1.5; } '
            '.wm, .se, .qe, .im, .qm, .fo { font-family: "Noto Sans Thai", sans-serif; } .kicker { letter-spacing: .03em; } '
            '.cover-t { font-size: 36pt; } .wrow { padding: 2.2mm 0; } .free-box { margin-top: 10mm; background: #f1f3f7; '
            'border-radius: 4mm; padding: 6mm 7mm; } .free-box b.big { display: block; font-size: 20pt; color: #2d4a99; } '
            'table.plan.compact td { padding: .75mm 1mm; font-size: 8.8pt; } table.plan.compact th { padding: 1.2mm 1mm; }')
        out = [f"<!doctype html><html lang='th'><head><meta charset='utf-8'><title>{E(title)}</title><style>{css}</style></head><body>"]
        for i, (body, cls) in enumerate(self.pages, 1):
            out.append(f'<section class="page {cls}"><div class="inner">{body}</div>'
                       f'<div class="foot"><span>{E(title)}</span><span>{i} / {n}</span></div></section>')
        out.append("</body></html>")
        return "".join(out), n


# ---- one lesson: word pages, writing pages, quiz ----------------------------------------------------------------
WPP = 8
CPP = 5


def lesson_pages(book, di, d, rng):
    ws = d["words"]
    n_pages = math.ceil(len(ws) / WPP)
    per = math.ceil(len(ws) / n_pages)
    chunks = [ws[i:i + per] for i in range(0, len(ws), per)]
    for ci, ch in enumerate(chunks):
        items = []
        for w in ch:
            big = "".join(f'<span class="newc">{E(c)}</span>' if c in seen else E(c) for c in w[0])
            items.append(f"""<div class="wrow"><div class="wl"><div class="wz">{big}</div>
<div class="wp">{E(w[1])}</div><div class="wm">{E(w[2])}</div></div>
<div class="wr"><div class="sz">{hl(w[3], w[0])}</div><div class="sp">{E(w[4])}</div><div class="se">{E(w[5])}</div></div></div>""")
        head = (f'<div class="dayhead"><div class="dk">บทที่ {di}</div><h2>{E(d["title"])}</h2>'
                f'<div class="dm">{len(ws)} คำ · ตัวอักษรใหม่ {len(d["chars"])} ตัว · ตัวอักษรสีแดงคือตัวที่ไม่มีใน HSK 1–2</div></div>') if ci == 0 else \
            f'<div class="dayhead small"><div class="dk">บทที่ {di} · ต่อ</div></div>'
        book.page(head + "".join(items))
    # writing
    cs = d["chars"]
    for pi in range(0, len(cs), CPP):
        rows = []
        for c in cs[pi:pi + CPP]:
            n = len(STROKES[c]["s"])
            steps = "".join(grid(stroke_svg(c, k, 30), "step") for k in range(1, n + 1))
            trace = "".join(grid(stroke_svg(c, None, 40, "ghost"), "cell") for _ in range(3)) + \
                "".join(grid("", "cell") for _ in range(7))
            inw = "、".join(words_with(c))
            rows.append(f"""<div class="crow"><div class="cl">{grid(stroke_svg(c, None, 66, 'full'), 'bigcell')}
<div class="cp">{E(CHAR_PY[c])}</div><div class="cn">{n} ขีด</div></div>
<div class="cr"><div class="cin">ใน: {E(inw)}</div><div class="steps">{steps}</div><div class="trace">{trace}</div></div></div>""")
        head = f'<h2 class="ph">บทที่ {di} · ฝึกเขียนตัวอักษรใหม่</h2>'
        if pi == 0:
            head += ('<p class="intro">ทำตามลำดับขีด (ขีดล่าสุดเป็นสีแดง) เขียนทับตัวอักษรสีเทา 3 ตัว '
                     'แล้วเขียนเองในช่องที่ว่าง</p>')
        book.page(head + "".join(rows), "write")
    # quiz
    for _ in range(100000):
        pool = list(ws)
        rng.shuffle(pool)
        if clash_free(pool[:6]) and clash_free(pool[6:11]):
            break
    else:
        raise SystemExit(f"lesson {di}: no clash-free quiz")
    a_items, b_items, c_items = pool[:6], pool[6:11], pool[11:17]
    meanings = [w[2] for w in a_items]
    letters = "abcdef"
    order = list(range(6))
    rng.shuffle(order)
    a_left = "".join(f'<div class="qa"><span class="qn">{i + 1}</span><span class="qz">{E(w[0])}</span><span class="box"></span></div>'
                     for i, w in enumerate(a_items))
    a_right = "".join(f'<div class="qm"><b>{letters[j]}</b>{E(meanings[order[j]])}</div>' for j in range(6))
    a_ans = [letters[order.index(i)] for i in range(6)]
    bank = [w[0] for w in b_items]
    bank_sorted = sorted(bank, key=lambda x: (len(x), x))
    b_list = "".join(f'<div class="qb"><span class="qn">{i + 1}.</span><span class="qz">{E(blank(w))}</span>'
                     f'<div class="qe">{E(w[5])}</div></div>' for i, w in enumerate(b_items))
    half = math.ceil(len(c_items) / 2)

    def crow(i, w):
        return f'<div class="qc"><span class="qn">{i + 1}</span><span class="qz">{E(w[0])}</span><span class="line"></span></div>'
    c_l = "".join(crow(i, w) for i, w in enumerate(c_items[:half]))
    c_r = "".join(crow(i + half, w) for i, w in enumerate(c_items[half:]))
    d["answers"] = {"A": a_ans, "B": bank, "C": [w[1] for w in c_items]}
    book.page(f"""<h2 class="ph">บทที่ {di} · แบบทดสอบ</h2>
<h3 class="qh">A · จับคู่คำศัพท์กับความหมาย</h3>
<div class="two"><div>{a_left}</div><div>{a_right}</div></div>
<h3 class="qh">B · เติมคำในช่องว่าง</h3><p class="intro">ใช้คำในกรอบคำละหนึ่งครั้ง ประโยคภาษาไทยบอกความหมายของประโยค</p>
<div class="bank">{"".join(f"<span>{E(x)}</span>" for x in bank_sorted)}</div>{b_list}
<h3 class="qh">C · เขียนพินอิน พร้อมเครื่องหมายวรรณยุกต์</h3>
<div class="two"><div>{c_l}</div><div>{c_r}</div></div>""", "quiz")


def answer_block(di, a):
    return f"""<div class="ans"><h3>บทที่ {di}</h3>
<p><b>A</b> {'　'.join(f'{i + 1} {x}' for i, x in enumerate(a['A']))}</p>
<p><b>B</b> {'　'.join(f'{i + 1} {E(x)}' for i, x in enumerate(a['B']))}</p>
<p><b>C</b> {'　'.join(f'{i + 1} {E(x)}' for i, x in enumerate(a['C']))}</p></div>"""


HOW_TO = """<ol class="steps">
  <li><b>เรียนคำศัพท์</b> อ่านแต่ละคำ พินอิน และความหมาย แล้วอ่านประโยคตัวอย่างออกเสียงดัง ๆ
  ทุกประโยคใช้เฉพาะคำศัพท์ HSK 1–3 คุณจึงเข้าใจได้ทั้งประโยค</li>
  <li><b>ฝึกเขียนตัวอักษรใหม่</b> ทำตามลำดับขีด เขียนทับตัวอักษรสีเทา แล้วเขียนเอง
  ในส่วนนี้มีเฉพาะตัวอักษรที่ไม่มีในคำศัพท์ HSK 1–2 และยังไม่ได้เรียนในบทก่อนหน้า</li>
  <li><b>ทำแบบทดสอบ</b> ทำโดยไม่ย้อนกลับไปดู แล้วตรวจคำตอบที่ท้ายเล่ม
  ทำเครื่องหมายคำที่ตอบผิด แล้วอ่านทวนอีกครั้งในวันรุ่งขึ้น</li>
</ol>"""
PINYIN_NOTE = """<p class="note"><b>หมายเหตุเรื่องพินอิน</b> พินอินในประโยคแสดงเสียงวรรณยุกต์ตามที่ออกเสียงจริง: 不 เปลี่ยนเป็น bú
และ 一 เปลี่ยนเป็น yí หรือ yì เมื่ออยู่หน้าเสียงบางเสียง ส่วนเสียงเบาไม่มีเครื่องหมาย</p>"""
FOOT_NOTE = """<p class="small">พบข้อผิดพลาด? อีเมลมาที่ willowbewater@gmail.com แล้วเราจะส่งไฟล์ที่แก้ไขแล้วให้
สมุดเล่มนี้สำหรับผู้เรียนหนึ่งคนใช้เรียนด้วยตนเอง hskcheck.com เป็นเว็บไซต์อิสระ ไม่มีส่วนเกี่ยวข้องกับผู้จัดสอบ HSK</p>"""


# ---- full workbook ----------------------------------------------------------------------------------------------
def build_full():
    rng = random.Random(20261026)
    book = Book()
    book.page(f"""
<div class="topbar"></div>
<div class="brand">hskcheck.com</div>
<div class="kicker">HSK 3.0 · สมุดแบบฝึกพิมพ์ได้ · ฉบับภาษาไทย</div>
<h1 class="cover-t">HSK 3<br><span class="green">คำศัพท์ครบ 499 คำ</span></h1>
<div class="cover-sub">สมุดแบบฝึกคำศัพท์ HSK 3</div>
<p class="cover-lede">คำศัพท์ HSK 3 ใหม่ (หลักสูตรปี 2025) ครบทั้ง 499 คำ จัดเป็น 25 บทเรียนตามหัวข้อในชีวิตประจำวัน
ทุกคำมีพินอิน ความหมายภาษาไทย และประโยคตัวอย่างที่ใช้เฉพาะคำศัพท์ HSK 1–3 พร้อมคำแปลภาษาไทย</p>
<div class="stats">
  <div><b>499</b><span>คำศัพท์ HSK 3</span></div>
  <div><b>284</b><span>ตัวอักษรใหม่ที่ต้องฝึกเขียน</span></div>
  <div><b>25</b><span>บทเรียน วันละบท</span></div>
</div>
<ul class="bul">
  <li>ทุกคำมีพินอิน ความหมายภาษาไทย และประโยคตัวอย่างพร้อมพินอินและคำแปลภาษาไทย</li>
  <li>ลำดับขีดและช่องฝึกเขียนตามรอย สำหรับตัวอักษร 284 ตัวที่ไม่มีในคำศัพท์ HSK 1–2</li>
  <li>แบบทดสอบท้ายทุกบท แบบทดสอบรวม 30 ข้อ เฉลย และดัชนีคำศัพท์</li>
</ul>
<div class="cover-foot">รายการคำศัพท์อ้างอิงหลักสูตร HSK 3.0 ปี 2025 จัดทำโดย hskcheck.com ซึ่งมีรายการคำศัพท์
เครื่องมือตรวจระดับ HSK แฟลชการ์ด และแบบฝึกเขียนตัวอักษรภาษาไทยให้ใช้ฟรี</div>
""", "cover")

    rows = "".join(
        f'<tr><td class="dn">บทที่ {i}</td><td>{E(d["title"])}</td><td class="num">{len(d["words"])}</td>'
        f'<td class="num">{len(d["chars"])}</td><td class="tick"><span class="box"></span></td></tr>'
        for i, d in enumerate(days, 1))
    book.page(f"""
<h2 class="ph">วิธีใช้สมุดเล่มนี้</h2>
<p>แต่ละบทมี 3 ส่วน ใช้เวลารวมประมาณ 40 นาที</p>
{HOW_TO}
{PINYIN_NOTE}
<p class="note">หลังบทที่ 25 ให้ทำแบบทดสอบรวม จากนั้นทบทวนคำศัพท์ต่อด้วยเครื่องมือฟรีที่ hskcheck.com/th
(ดูหน้าสุดท้าย)</p>""")
    book.page(f"""<h2 class="ph">แผนเรียน 25 บท</h2>
<table class="plan compact"><thead><tr><th></th><th>หัวข้อ</th><th class="num">คำศัพท์</th><th class="num">ตัวอักษรใหม่</th><th>เสร็จ</th></tr></thead>
<tbody>{rows}</tbody></table>""")

    for di, d in enumerate(days, 1):
        lesson_pages(book, di, d, rng)

    # final check: 15 choose the meaning + 15 write the missing word
    syn = set().union(*GROUPS)
    for _ in range(100000):
        pool = list(ALL_WORDS)
        rng.shuffle(pool)
        fa = pool[:15]
        fb = [w for w in pool[15:] if w[0] not in syn and len(w[0]) > 1][:15]
        if clash_free(fa) and clash_free(fb):
            break
    else:
        raise SystemExit("final check: no clash-free set")
    fa_html, fa_ans = [], []
    for i, w in enumerate(fa):
        others = sorted({x[2] for x in ALL_WORDS if x[2] != w[2] and not related(x[0], w[0])})
        opts = [w[2]] + rng.sample(others, 2)
        rng.shuffle(opts)
        fa_ans.append("abc"[opts.index(w[2])])
        fa_html.append(f'<div class="fq"><span class="qn">{i + 1}</span><span class="qz">{E(w[0])}</span>'
                       + "".join(f'<span class="fo"><b>{"abc"[k]}</b> {E(o)}</span>' for k, o in enumerate(opts)) + "</div>")
    fb_html = "".join(f'<div class="qb"><span class="qn">{i + 16}.</span><span class="qz">{E(blank(w))}</span>'
                      f'<div class="qe">{E(w[5])}</div></div>' for i, w in enumerate(fb))
    book.page(f"""<h2 class="ph">แบบทดสอบรวม</h2>
<p class="intro">30 ข้อ จากคำศัพท์ทั้ง 25 บท ลองทำโดยไม่ย้อนกลับไปดู ถ้าถูก 24 ข้อขึ้นไป
แปลว่าคุณรู้คำศัพท์ HSK 3 ดีแล้ว</p>
<h3 class="qh">A · เลือกความหมายที่ถูกต้อง</h3>{''.join(fa_html)}""", "quiz")
    book.page(f"""<h2 class="ph">แบบทดสอบรวม · ต่อ</h2>
<h3 class="qh">B · เขียนคำที่หายไปเป็นตัวอักษรจีน</h3>
<p class="intro">ประโยคภาษาไทยบอกความหมายของประโยค คำที่หายไปทุกคำเป็นคำศัพท์ HSK 3 จากสมุดเล่มนี้</p>
{fb_html}
<div class="score">คะแนนของคุณ: <span class="line short"></span> / 30</div>""", "quiz")

    blocks = [answer_block(di, d["answers"]) for di, d in enumerate(days, 1)]
    blocks.append(f"""<div class="ans"><h3>แบบทดสอบรวม</h3>
<p><b>A</b> {'　'.join(f'{i + 1} {x}' for i, x in enumerate(fa_ans))}</p>
<p><b>B</b> {'　'.join(f'{i + 16} {E(w[0])}' for i, w in enumerate(fb))}</p></div>""")
    APP = 7
    for k in range(0, len(blocks), APP):
        book.page(f'<h2 class="ph">เฉลย{" · ต่อ" if k else ""}</h2>' + "".join(blocks[k:k + APP]), "answers")

    # index in pinyin order
    def pykey(w):
        s = unicodedata.normalize("NFD", w[1].lower())
        return "".join(ch for ch in s if unicodedata.category(ch) != "Mn").replace(" ", "").replace("'", "")
    idx = sorted(((w, di) for di, d in enumerate(days, 1) for w in d["words"]), key=lambda x: (pykey(x[0]), x[0][1], x[0][0]))
    per = 28
    for k in range(0, len(idx), per * 2):
        cols = []
        for cstart in (k, k + per):
            part = idx[cstart:cstart + per]
            cols.append("".join(f'<div class="ix"><span class="iz">{E(w[0])}</span><span class="ip">{E(w[1])}</span>'
                                f'<span class="im">{E(first_sense(w[2]))}</span><span class="id">{di}</span></div>' for w, di in part))
        book.page(f'<h2 class="ph">ดัชนีคำศัพท์{" · ต่อ" if k else ""}</h2>' +
                  ('<p class="intro">คำศัพท์ทั้ง 499 คำ เรียงตามพินอิน ตัวเลขด้านขวาคือบทที่ได้เรียนคำนั้น</p>' if k == 0 else "") +
                  f'<div class="two ixc"><div>{cols[0]}</div><div>{cols[1]}</div></div>', "index")

    book.page("""<h2 class="ph">เรียนต่ออย่างไรดี</h2>
<p>ตอนนี้คุณรู้คำศัพท์ HSK 3 ครบทั้ง 499 คำแล้ว นี่คือวิธีจำให้แม่นและเรียนต่อ ด้วยเครื่องมือฟรีที่ hskcheck.com:</p>
<ul class="bul big">
  <li><b>แฟลชการ์ด HSK</b> (hskcheck.com/th/hsk-flashcards): ทบทวนคำศัพท์ HSK 3 วันละไม่กี่นาที
  คำใหม่และคำที่ถึงเวลาทบทวนจะขึ้นมาให้เอง และความคืบหน้าจะเก็บไว้ในโทรศัพท์ของคุณ</li>
  <li><b>แบบทดสอบ HSK</b> (hskcheck.com/th/hsk-practice-test): 20 ข้อสั้น ๆ เรื่องความหมาย พินอิน การฟัง และไวยากรณ์</li>
  <li><b>ควิซ HSK ประจำวัน</b> (hskcheck.com/th/daily-hsk-quiz): วันละ 10 ข้อ ช่วยให้ทบทวนทุกวันอย่างต่อเนื่อง</li>
  <li><b>เครื่องมือตรวจระดับ HSK</b> (hskcheck.com/th): วางข้อความภาษาจีนใดก็ได้ แล้วดูว่าคำไหนสูงกว่า HSK 3</li>
  <li><b>แบบฝึกเขียนตัวอักษร HSK 3</b> (hskcheck.com/th/hsk-3-character-worksheets): พิมพ์แบบฝึกเขียนเพิ่มได้ฟรี</li>
  <li><b>ไวยากรณ์และเรื่องอ่าน</b> (hskcheck.com/th/learn และ hskcheck.com/th/reading): คำอธิบายไวยากรณ์สั้น ๆ
  และเรื่องสั้นตามระดับ HSK</li>
  <li><b>คำศัพท์ HSK 4</b> (hskcheck.com/th/hsk-4-word-list): เมื่อพร้อมแล้ว เริ่มเรียนระดับถัดไป</li>
</ul>
<div class="notes"><h3>บันทึก</h3>""" + "".join('<div class="nl"></div>' for _ in range(8)) + "</div>" + FOOT_NOTE)

    text, n = book.html(TITLE)
    (HERE / "hsk3_th.html").write_text(text, encoding="utf-8")
    return days, n


# ---- free sample: lesson 1 --------------------------------------------------------------------------------------
def build_sample():
    rng = random.Random(20261026)  # same seed and order as the full book, so lesson 1 is identical
    d = dict(days[0])
    book = Book()
    book.page(f"""
<div class="topbar"></div>
<div class="brand">hskcheck.com</div>
<div class="kicker">HSK 3.0 · สมุดแบบฝึกคำศัพท์ HSK 3 · ฉบับภาษาไทย</div>
<h1 class="cover-t">บทที่ 1<br><span class="green">ทดลองเรียนฟรี</span></h1>
<div class="cover-sub">{E(d["title"])} · {len(d["words"])} คำ · ตัวอักษรใหม่ {len(d["chars"])} ตัว</div>
<p class="cover-lede">นี่คือบทที่ 1 จากสมุดแบบฝึกคำศัพท์ HSK 3 ฉบับเต็ม 25 บท (499 คำ) ทุกคำมีพินอิน ความหมายภาษาไทย
และประโยคตัวอย่างพร้อมคำแปล ตามด้วยแบบฝึกเขียนตัวอักษรใหม่ แบบทดสอบ และเฉลย</p>
<h2 class="ph2">วิธีใช้</h2>
{HOW_TO}
{PINYIN_NOTE}
<div class="cover-foot">รายการคำศัพท์อ้างอิงหลักสูตร HSK 3.0 ปี 2025 จัดทำโดย hskcheck.com · แจกฟรี พิมพ์และแบ่งปันได้</div>
""", "cover")
    lesson_pages(book, 1, d, rng)
    book.page('<h2 class="ph">เฉลย</h2>' + answer_block(1, d["answers"]), "answers")
    book.page(f"""<h2 class="ph">เรียนต่อให้ครบ 499 คำ</h2>
<p>ชอบบทที่ 1 ไหม? สมุดแบบฝึกคำศัพท์ HSK 3 ฉบับเต็มมีครบทั้ง 25 บท ในรูปแบบเดียวกันนี้</p>
<ul class="bul big">
  <li>คำศัพท์ HSK 3 ครบ 499 คำ ใน 25 บทเรียนตามหัวข้อ พร้อมประโยคตัวอย่างแปลไทยทุกคำ</li>
  <li>แบบฝึกเขียนตัวอักษรใหม่ทั้ง 284 ตัว พร้อมลำดับขีด</li>
  <li>แบบทดสอบท้ายทุกบท แบบทดสอบรวม 30 ข้อ เฉลย และดัชนีคำศัพท์เรียงตามพินอิน</li>
</ul>
<div class="free-box"><b class="big">{PRICE} · ฉบับเต็ม 25 บท</b>
<p>ดาวน์โหลด PDF พิมพ์ได้ที่ <b>{PAGE_URL}</b></p></div>
<p class="note">เครื่องมือฟรีสำหรับเรียน HSK 3: รายการคำศัพท์ HSK 3 พร้อมคำแปลไทย (hskcheck.com/th/hsk-3-word-list)
แฟลชการ์ด (hskcheck.com/th/hsk-flashcards) และแบบทดสอบ (hskcheck.com/th/hsk-practice-test)</p>
{FOOT_NOTE}""")
    text, n = book.html("บทที่ 1 ทดลองเรียนฟรี · สมุดแบบฝึกคำศัพท์ HSK 3 · hskcheck.com")
    (HERE / "hsk3_th_lesson1.html").write_text(text, encoding="utf-8")
    return n


if __name__ == "__main__":
    _, n_full = build_full()
    lesson1_answers = dict(days[0]["answers"])
    n_free = build_sample()
    assert days[0]["answers"] == lesson1_answers, "free lesson 1 must match the full workbook"
    print("pages", n_full, "free sample pages", n_free, "words", len(ALL_WORDS), "new characters", len(seen), "lessons", len(days))
