"""Build the Thai YCT workbooks (one per YCT level, A4, for children) and their free lesson 1 samples.

Usage:
  python3 tools/pack_pdf/build_yct_th.py            # writes tools/pack_pdf/yctN_th.html and yctN_th_lesson1.html, N = 1-4
  python3 tools/pack_pdf/build_yct_th.py --pdf      # also makes the PDFs: full workbooks and the bundle in /tmp/yct_th/
                                                    # (never commit), free lesson 1 PDFs into th/upgrade-packs/yct-N-workbook/
Needs the Noto Sans Thai font (fc-list | grep "Noto Sans Thai").

Spec: PACK_YCT_TH.md. Each workbook teaches the words that are new at its level (the YCT lists are cumulative).
Data: data/packs/yct_th/yctN.json (lessons and sentences), word pinyin from data/yct/yctN.tsv, Thai meanings from
data/th/yct/yctN_th.tsv, stroke data from strokes/x/. Same page types and pack.css as build_hsk3_th.py, with bigger
type and bigger writing cells for children. Pattern words such as 一边……一边…… are highlighted and blanked part by part.
"""
import html, json, math, pathlib, random, subprocess, sys, unicodedata

HERE = pathlib.Path(__file__).resolve().parent
R = HERE.parent.parent
E = html.escape
PAGE = "hskcheck.com/th/upgrade-packs/yct-{n}-workbook/"
PRICES = {1: "$1.99", 2: "$1.99", 3: "$2.99", 4: "$3.99"}
EXPECT = {1: (5, 80), 2: (5, 70), 3: (10, 150), 4: (15, 298)}  # lessons, new words
FINAL = {1: 10, 2: 10, 3: 10, 4: 15}  # questions per part of the final check
# The season words 夏, 秋, 冬 can only be shown inside 夏天, 秋天, 冬天 (天 is not a YCT word on its own).
VOCAB_EXCEPTIONS = {"夏天很热。", "秋天来了。", "冬天要多穿衣服。"}


def tsv(path):
    return [l.rstrip("\n").split("\t") for l in (R / path).read_text(encoding="utf-8").splitlines() if "\t" in l]


def strokes(c):
    return json.loads((R / f"strokes/x/{ord(c) % 128:02x}.json").read_text(encoding="utf-8"))[c]


def parts(word):
    return [p for p in word.split("……") if p]


def hl(sentence, word):
    out, rest = "", sentence
    for p in parts(word):
        i = rest.find(p)
        out += E(rest[:i]) + f'<b class="hl">{E(p)}</b>'
        rest = rest[i + len(p):]
    return out + E(rest)


def blank(w):
    out, rest = "", w[3]
    for p in parts(w[0]):
        i = rest.find(p)
        out += rest[:i] + "（　　　）"
        rest = rest[i + len(p):]
    return out + rest


def contains(sentence, word):
    rest = sentence
    for p in parts(word):
        i = rest.find(p)
        if i < 0:
            return False
        rest = rest[i + len(p):]
    return True


def is_han(c):
    return "一" <= c <= "鿿"


# Words that could both be right in the same blank, or are too close in meaning to share a matching exercise.
NUMS = {"一", "二", "三", "四", "五", "六", "七", "八", "九", "十"}
GROUPS = [
    # YCT 1
    NUMS, {"他", "她"}, {"你", "我"}, {"哥哥", "姐姐"}, {"爸爸", "妈妈"}, {"大", "小"}, {"高", "个子", "长"}, {"今天", "明天"},
    {"这", "那", "哪"}, {"吃", "喝"}, {"很", "多"}, {"什么", "哪", "谁", "几"}, {"老师", "谢谢", "再见"}, {"点", "号", "月", "岁"},
    {"星期", "今天", "明天"}, {"猫", "狗", "鸟", "鱼"}, {"米饭", "面条"}, {"牛奶", "水"}, {"鼻子", "耳朵", "眼睛", "手", "头发"},
    {"去", "看"}, {"喜欢", "爱"}, {"是", "在", "有"}, {"学校", "商店", "家"},
    # YCT 2
    {"朋友", "同学", "学生"}, {"弟弟", "妹妹"}, {"红", "黄", "绿"}, {"冷", "热"}, {"早上", "晚上"}, {"可以", "会", "要"},
    {"怎么", "怎么样"}, {"上边", "里面"}, {"没关系", "不客气"}, {"也", "真"}, {"桌子", "椅子"}, {"包子", "香蕉"},
    {"医生", "医院"}, {"起床", "睡觉"}, {"说话", "打电话"}, {"买", "做", "画"}, {"块", "只"}, {"零", "两"},
    # YCT 3
    {"爷爷", "奶奶"}, {"先生", "小姐"}, {"男", "女"}, {"生病", "感冒"}, {"疼", "累"}, {"白", "黑", "蓝"}, {"胖", "瘦"},
    {"新", "坏"}, {"裤子", "裙子", "衣服"}, {"穿", "卖"}, {"饿", "饱"}, {"面包", "鸡蛋", "饺子", "水果", "西瓜", "菜"},
    {"果汁", "杯子"}, {"生日", "快乐"}, {"送", "给"}, {"猴子", "老虎"}, {"太阳", "月亮"}, {"刮风", "下雪"}, {"笑", "哭"},
    {"唱歌", "跳舞"}, {"打篮球", "踢足球", "游泳", "跑步", "运动"}, {"电影", "电脑"}, {"快", "慢"}, {"问", "写", "读"},
    {"懂", "知道"}, {"课", "教室"}, {"左", "右"}, {"前", "后"}, {"进", "出", "回", "走"}, {"飞机", "公共汽车", "自行车"},
    {"百", "千"}, {"远", "近"}, {"时候", "时间"}, {"中午", "去年"}, {"拿", "给"}, {"能", "想"}, {"东西", "事情"},
    {"别", "让"}, {"但是", "所以", "因为"}, {"最", "太"}, {"都", "还", "就"}, {"些", "少"},
    # YCT 4
    {"儿子", "女儿", "孙子"}, {"年轻", "老"}, {"护士", "警察", "服务员", "售票员"}, {"阿姨", "叔叔"}, {"矮", "短"},
    {"戴", "脱"}, {"小心", "注意"}, {"发烧", "渴"}, {"冰箱", "盒子"}, {"楼", "层"}, {"电灯", "空调"}, {"干净", "安静"},
    {"盘子", "筷子"}, {"甜", "辣"}, {"贵", "便宜"}, {"梨", "桃", "葡萄"}, {"饼干", "巧克力", "冰激凌", "糖"}, {"教", "讲"},
    {"明白", "清楚"}, {"复习", "练习"}, {"认真", "马虎"}, {"夏", "秋", "冬", "春季"}, {"东", "西", "南"}, {"暖和", "凉快"},
    {"大象", "兔子"}, {"网球", "排球", "乒乓球"}, {"表演", "节目"}, {"照相", "照片"}, {"坚持", "努力"}, {"火车", "地铁"},
    {"危险", "安全"}, {"附近", "离"}, {"出发", "准时"}, {"带", "接"}, {"上班", "工作", "开会"}, {"超市", "公园"},
    {"旧", "破"}, {"张", "条", "双"}, {"报纸", "杂志", "新闻"}, {"害怕", "担心"}, {"难过", "生气"}, {"敢", "勇敢"},
    {"同意", "决定", "打算", "选择"}, {"暑假", "寒假", "放假"}, {"刚才", "马上", "一会儿"}, {"先", "然后"},
    {"经常", "一直"}, {"以前", "将来"}, {"记得", "忘记"}, {"加", "减"}, {"非常", "特别", "更", "极了"},
    {"一点儿", "一下儿"}, {"可能", "大概", "好像"}, {"一定", "应该", "必须"}, {"着", "正在"}, {"其他", "另外"},
    {"或者", "还是"}, {"只要", "无论"}, {"虽然", "除了"}, {"重要", "容易"}, {"厉害", "聪明"}, {"孩子", "大家", "别人"},
    {"见面", "介绍"}, {"花", "草地"}, {"一样", "好像"},
]


def related(a, b, blank=True):
    """blank=False is for matching meanings, where numbers can't be confused (their Thai names differ)."""
    return any(a in g and b in g for g in GROUPS if blank or g is not NUMS)


def clash_free(items, blank=True):
    names = [w[0] for w in items]
    means = [w[2] for w in items]
    return len(set(means)) == len(means) and not any(related(a, b, blank) for i, a in enumerate(names) for b in names[i + 1:])


# ---- data -------------------------------------------------------------------------------------------------------
def load(n):
    rows = tsv(f"data/yct/yct{n}.tsv")
    py = {r[0]: r[1] for r in rows}
    th = {r[0]: r[1] for r in tsv(f"data/th/yct/yct{n}_th.tsv")}
    lower = {r[0] for r in tsv(f"data/yct/yct{n - 1}.tsv")} if n > 1 else set()
    new_words = [r[0] for r in rows if r[0] not in lower]
    old_chars = {c for w in lower for c in w}
    data = json.loads((R / f"data/packs/yct_th/yct{n}.json").read_text(encoding="utf-8"))["lessons"]
    days, seen = [], []
    for les in data:
        words = [(x["w"], py[x["w"]], th[x["w"]], x["zh"], x["py"], x["th"]) for x in les["words"]]
        new = []
        for w in words:
            assert contains(w[3], w[0]), w
            for c in w[0]:
                if is_han(c) and c not in old_chars and c not in seen:
                    seen.append(c)
                    new.append(c)
        days.append({"title": les["title_th"], "words": words, "chars": new})
    all_words = [w for d in days for w in d["words"]]
    assert (len(days), len(all_words)) == EXPECT[n], (n, len(days), len(all_words))
    assert sorted(w[0] for w in all_words) == sorted(new_words), f"YCT {n}: every new word exactly once"
    stk = {c: strokes(c) for c in seen}
    char_py = {}
    for c in seen:
        readings = stk[c]["p"]
        w = next(x for x in all_words if c in x[0])
        used = [r for r in readings if r in w[1].replace("'", "").lower()]
        char_py[c] = used[0] if len(used) == 1 else " / ".join(readings)
    return days, seen, stk, char_py, all_words


def check_vocab(n, all_words):
    sents = [w[3] for w in all_words if w[3] not in VOCAB_EXCEPTIONS]
    r = subprocess.run([sys.executable, str(R / "tools/check_vocab.py"), "--yct", str(n), *sents], capture_output=True, text=True)
    if r.returncode:
        raise SystemExit(f"YCT {n}: sentences above the level\n" + "\n".join(l for l in r.stdout.splitlines() if l.startswith("OUT")))


# ---- renderers --------------------------------------------------------------------------------------------------
def stroke_svg(stk, c, upto=None, size=34, mode="step"):
    s = stk[c]["s"]
    n = len(s) if upto is None else upto
    paths = []
    for i, d in enumerate(s[:n]):
        col = "#d5d9e0" if mode == "ghost" else "#1e2433" if mode == "full" else ("#d6342c" if i == n - 1 else "#4a5160")
        paths.append(f'<path d="{d}" fill="{col}"/>')
    return (f'<svg viewBox="0 0 1024 1024" width="{size}" height="{size}">'
            f'<g transform="scale(1,-1) translate(0,-900)">{"".join(paths)}</g></svg>')


def grid(inner="", cls="cell"):
    return (f'<div class="{cls}"><svg class="g" viewBox="0 0 100 100" preserveAspectRatio="none">'
            '<line x1="0" y1="0" x2="100" y2="100"/><line x1="100" y1="0" x2="0" y2="100"/>'
            '<line x1="50" y1="0" x2="50" y2="100"/><line x1="0" y1="50" x2="100" y2="50"/></svg>'
            f'{inner}</div>')


KID_CSS = (
    'body { font-family: "Noto Sans Thai", "Inter", "Noto Sans", "Noto Sans CJK SC", sans-serif; line-height: 1.5; } '
    '.wm, .se, .qe, .im, .qm, .fo { font-family: "Noto Sans Thai", sans-serif; } .kicker { letter-spacing: .03em; } '
    '.cover-t { font-size: 38pt; } .cover .topbar { background: #e8833a; } .dayhead { border-left-color: #e8833a; } '
    '.dayhead .dk, .dn { color: #c0611a; } '
    '.wrow { grid-template-columns: 62mm 1fr; padding: 3.2mm 0; } .wz { font-size: 30pt; } .wp { font-size: 11pt; } '
    '.wm { font-size: 10pt; } .sz { font-size: 16pt; } .sp { font-size: 10pt; } .se { font-size: 10pt; } '
    '.cell { width: 18mm; height: 18mm; } .step { width: 9.5mm; height: 9.5mm; } .bigcell { width: 28mm; height: 28mm; } '
    '.crow { grid-template-columns: 30mm 1fr; padding: 3.5mm 0 4mm; } .cin { font-size: 9pt; } '
    '.qa { height: 10.5mm; } .qa .qz { font-size: 16pt; } .qm { height: 10.5mm; font-size: 11pt; } '
    '.bank { font-size: 16pt; } .qb .qz { font-size: 15pt; } .qe { font-size: 9.5pt; } .qc { height: 12mm; } '
    '.qc .qz { font-size: 16pt; } .fq .qz { font-size: 15pt; } .fq { font-size: 10pt; } '
    '.free-box { margin-top: 10mm; background: #fdf1e7; border-radius: 4mm; padding: 6mm 7mm; } '
    '.free-box b.big { display: block; font-size: 20pt; color: #c0611a; } '
    'table.plan.compact td { padding: 1.4mm 1mm; font-size: 9.5pt; }')


class Book:
    def __init__(self):
        self.pages = []

    def page(self, body, cls=""):
        self.pages.append((body, cls))

    def html(self, title):
        n = len(self.pages)
        css = (HERE / "pack.css").read_text(encoding="utf-8") + KID_CSS
        out = [f"<!doctype html><html lang='th'><head><meta charset='utf-8'><title>{E(title)}</title><style>{css}</style></head><body>"]
        for i, (body, cls) in enumerate(self.pages, 1):
            out.append(f'<section class="page {cls}"><div class="inner">{body}</div>'
                       f'<div class="foot"><span>{E(title)}</span><span>{i} / {n}</span></div></section>')
        out.append("</body></html>")
        return "".join(out), n


WPP = 6
CPP = 4


def lesson_pages(book, n, di, d, rng, seen, stk, char_py, all_words):
    ws = d["words"]
    n_pages = math.ceil(len(ws) / WPP)
    per = math.ceil(len(ws) / n_pages)
    for ci in range(0, len(ws), per):
        items = []
        for w in ws[ci:ci + per]:
            big = "".join(f'<span class="newc">{E(c)}</span>' if c in seen else E(c) for c in w[0])
            size = ' style="font-size:19pt"' if len(w[0]) >= 5 else ""
            items.append(f"""<div class="wrow"><div class="wl"><div class="wz"{size}>{big}</div>
<div class="wp">{E(w[1])}</div><div class="wm">{E(w[2])}</div></div>
<div class="wr"><div class="sz">{hl(w[3], w[0])}</div><div class="sp">{E(w[4])}</div><div class="se">{E(w[5])}</div></div></div>""")
        head = (f'<div class="dayhead"><div class="dk">YCT {n} · บทที่ {di}</div><h2>{E(d["title"])}</h2>'
                f'<div class="dm">{len(ws)} คำ · ตัวอักษรใหม่ {len(d["chars"])} ตัว (สีแดง)</div></div>') if ci == 0 else \
            f'<div class="dayhead small"><div class="dk">YCT {n} · บทที่ {di} · ต่อ</div></div>'
        book.page(head + "".join(items))
    cs = d["chars"]
    for pi in range(0, len(cs), CPP):
        rows = []
        for c in cs[pi:pi + CPP]:
            k = len(stk[c]["s"])
            steps = "".join(grid(stroke_svg(stk, c, j, 32), "step") for j in range(1, k + 1))
            trace = "".join(grid(stroke_svg(stk, c, None, 48, "ghost"), "cell") for _ in range(3)) + \
                "".join(grid("", "cell") for _ in range(5))
            inw = "、".join(w[0] for w in all_words if c in w[0])
            rows.append(f"""<div class="crow"><div class="cl">{grid(stroke_svg(stk, c, None, 74, 'full'), 'bigcell')}
<div class="cp">{E(char_py[c])}</div><div class="cn">{k} ขีด</div></div>
<div class="cr"><div class="cin">ใน: {E(inw)}</div><div class="steps">{steps}</div><div class="trace">{trace}</div></div></div>""")
        head = f'<h2 class="ph">บทที่ {di} · ฝึกเขียนตัวอักษรใหม่</h2>'
        if pi == 0:
            head += '<p class="intro">ดูลำดับขีด (ขีดล่าสุดเป็นสีแดง) เขียนทับตัวสีเทา 3 ตัว แล้วเขียนเองในช่องว่าง</p>'
        book.page(head + "".join(rows), "write")
    for _ in range(100000):
        pool = list(ws)
        rng.shuffle(pool)
        if clash_free(pool[:6], blank=False) and clash_free(pool[6:11]):
            break
    else:
        raise SystemExit(f"YCT {n} lesson {di}: no clash-free quiz")
    a_items, b_items, c_items = pool[:6], pool[6:11], pool[11:17]
    letters = "abcdef"
    order = list(range(6))
    rng.shuffle(order)
    a_left = "".join(f'<div class="qa"><span class="qn">{i + 1}</span><span class="qz">{E(w[0])}</span><span class="box"></span></div>'
                     for i, w in enumerate(a_items))
    a_right = "".join(f'<div class="qm"><b>{letters[j]}</b>{E(a_items[order[j]][2])}</div>' for j in range(6))
    a_ans = [letters[order.index(i)] for i in range(6)]
    bank = [w[0] for w in b_items]
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
<div class="bank">{"".join(f"<span>{E(x)}</span>" for x in sorted(bank, key=lambda x: (len(x), x)))}</div>{b_list}""", "quiz")
    book.page(f"""<h2 class="ph">บทที่ {di} · แบบทดสอบ · ต่อ</h2>
<h3 class="qh">C · เขียนพินอิน พร้อมเครื่องหมายวรรณยุกต์</h3>
<div class="two"><div>{c_l}</div><div>{c_r}</div></div>
<div class="notes"><h3>ฝึกเขียนคำที่ยังจำไม่ได้</h3>""" + "".join('<div class="nl"></div>' for _ in range(10)) + "</div>", "quiz")


def answer_block(di, a):
    return f"""<div class="ans"><h3>บทที่ {di}</h3>
<p><b>A</b> {'　'.join(f'{i + 1} {x}' for i, x in enumerate(a['A']))}</p>
<p><b>B</b> {'　'.join(f'{i + 1} {E(x)}' for i, x in enumerate(a['B']))}</p>
<p><b>C</b> {'　'.join(f'{i + 1} {E(x)}' for i, x in enumerate(a['C']))}</p></div>"""


def how_to(n):
    lower = "" if n == 1 else f" (ตัวอักษรที่เรียนแล้วใน {"YCT 1" if n == 2 else f"YCT 1–{n - 1}"} ไม่ต้องเขียนซ้ำ)"
    return f"""<ol class="steps">
  <li><b>เรียนคำศัพท์</b> อ่านคำ พินอิน และความหมาย แล้วอ่านประโยคตัวอย่างออกเสียงดัง ๆ
  ทุกประโยคใช้เฉพาะคำศัพท์ {"YCT 1" if n == 1 else f"YCT 1–{n}"} จึงอ่านเข้าใจได้ทั้งประโยค</li>
  <li><b>ฝึกเขียนตัวอักษรใหม่</b> ดูลำดับขีด เขียนทับตัวสีเทา แล้วเขียนเอง{lower}</li>
  <li><b>ทำแบบทดสอบ</b> ทำเองโดยไม่ดูหน้าก่อน แล้วตรวจคำตอบที่ท้ายเล่ม คำที่ตอบผิดให้อ่านทวนในวันถัดไป</li>
</ol>
<p class="note"><b>สำหรับผู้ปกครองและคุณครู</b> เรียนวันละหนึ่งบท ประมาณ 20–30 นาที อ่านประโยคให้เด็กฟังก่อน แล้วให้เด็กอ่านตาม
พินอินแสดงเสียงวรรณยุกต์ตามที่ออกเสียงจริง (不 เป็น bú และ 一 เป็น yí หรือ yì หน้าเสียงบางเสียง) เสียงเบาไม่มีเครื่องหมาย</p>"""


FOOT_NOTE = """<p class="small">พบข้อผิดพลาด? อีเมลมาที่ willowbewater@gmail.com แล้วเราจะส่งไฟล์ที่แก้ไขแล้วให้
สมุดเล่มนี้สำหรับผู้เรียนหนึ่งคน (หรือหนึ่งครอบครัว) ใช้เรียนเอง คุณครูที่อยากถ่ายเอกสารให้นักเรียนทั้งห้อง ดูใบอนุญาตสำหรับห้องเรียนที่หน้าชุดรวม YCT 1–4
hskcheck.com เป็นเว็บไซต์อิสระ ไม่มีส่วนเกี่ยวข้องกับผู้จัดสอบ YCT</p>"""


def cover(n, days, all_words, seen, sample=False):
    words = len(all_words)
    total = {1: 80, 2: 150, 3: 300, 4: 600}[n]
    lede = (f"YCT {n} มีคำศัพท์ {total} คำ" + ("" if n == 1 else f" ในนั้น {words} คำเป็นคำใหม่ของระดับนี้ (คำของ {"YCT 1" if n == 2 else f"YCT 1–{n - 1}"} อยู่ในเล่มก่อนหน้า)") +
            f" สมุดเล่มนี้สอนคำ{'ทั้งหมด' if n == 1 else 'ใหม่ทั้ง ' + str(words) + ' คำ'} ใน {len(days)} บทเรียนสั้น ๆ ตามหัวข้อที่เด็กคุ้นเคย "
            "ทุกคำมีพินอิน ความหมายภาษาไทย และประโยคตัวอย่างง่าย ๆ พร้อมคำแปล")
    if sample:
        return f"""
<div class="topbar"></div>
<div class="brand">hskcheck.com</div>
<div class="kicker">YCT {n} · สมุดแบบฝึกคำศัพท์สำหรับเด็ก · ฉบับภาษาไทย</div>
<h1 class="cover-t">YCT {n} · บทที่ 1<br><span class="green">ทดลองเรียนฟรี</span></h1>
<div class="cover-sub">{E(days[0]["title"])} · {len(days[0]["words"])} คำ · ตัวอักษรใหม่ {len(days[0]["chars"])} ตัว</div>
<p class="cover-lede">นี่คือบทที่ 1 จากสมุดแบบฝึกคำศัพท์ YCT {n} ฉบับเต็ม {len(days)} บท ({words} คำ) มีหน้าคำศัพท์ แบบฝึกเขียน แบบทดสอบ และเฉลย
พิมพ์ให้ลูกหรือนักเรียนลองทำได้เลย</p>
<h2 class="ph2">วิธีใช้</h2>
{how_to(n)}
<div class="cover-foot">คำศัพท์อ้างอิงรายการคำศัพท์ YCT (中小学生汉语考试) จัดทำโดย hskcheck.com · แจกฟรี พิมพ์และแบ่งปันได้</div>"""
    return f"""
<div class="topbar"></div>
<div class="brand">hskcheck.com</div>
<div class="kicker">YCT · สมุดแบบฝึกพิมพ์ได้สำหรับเด็ก · ฉบับภาษาไทย</div>
<h1 class="cover-t">YCT {n}<br><span class="green">คำศัพท์ {'ครบ ' + str(words) if n == 1 else 'ใหม่ ' + str(words)} คำ</span></h1>
<div class="cover-sub">สมุดแบบฝึกคำศัพท์ YCT ระดับ {n}</div>
<p class="cover-lede">{lede}</p>
<div class="stats">
  <div><b>{words}</b><span>คำศัพท์ที่ต้องเรียน</span></div>
  <div><b>{len(seen)}</b><span>ตัวอักษรใหม่ที่ต้องฝึกเขียน</span></div>
  <div><b>{len(days)}</b><span>บทเรียน วันละบท</span></div>
</div>
<ul class="bul">
  <li>ตัวอักษรใหญ่ อ่านง่าย ประโยคสั้นเกี่ยวกับบ้าน โรงเรียน เพื่อน สัตว์ และอาหาร</li>
  <li>ลำดับขีดและช่องฝึกเขียนตามรอยขนาดใหญ่ สำหรับตัวอักษรใหม่ทุกตัว</li>
  <li>แบบทดสอบท้ายทุกบท แบบทดสอบรวม เฉลย และดัชนีคำศัพท์</li>
</ul>
<div class="cover-foot">คำศัพท์อ้างอิงรายการคำศัพท์ YCT (中小学生汉语考试) จัดทำโดย hskcheck.com ซึ่งมีรายการคำศัพท์ YCT
แบบฝึกเขียน และใบงานคำศัพท์ภาษาไทยให้ใช้ฟรี</div>"""


def build_level(n):
    days, seen, stk, char_py, all_words = load(n)
    check_vocab(n, all_words)
    title = f"สมุดแบบฝึกคำศัพท์ YCT {n} · hskcheck.com"
    rng = random.Random(20261026 + n)
    book = Book()
    book.page(cover(n, days, all_words, seen), "cover")
    rows = "".join(
        f'<tr><td class="dn">บทที่ {i}</td><td>{E(d["title"])}</td><td class="num">{len(d["words"])}</td>'
        f'<td class="num">{len(d["chars"])}</td><td class="tick"><span class="box"></span></td></tr>'
        for i, d in enumerate(days, 1))
    plan_head = f'<h2 class="{"ph2" if len(days) <= 10 else "ph"}">แผนเรียน {len(days)} บท</h2>'
    if len(days) > 10:
        book.page(f'''<h2 class="ph">วิธีใช้สมุดเล่มนี้</h2>
<p>แต่ละบทมี 3 ส่วน</p>
{how_to(n)}''')
    book.page((f'''<h2 class="ph">วิธีใช้สมุดเล่มนี้</h2>
<p>แต่ละบทมี 3 ส่วน</p>
{how_to(n)}''' if len(days) <= 10 else "") + f"""{plan_head}
<table class="plan compact"><thead><tr><th></th><th>หัวข้อ</th><th class="num">คำศัพท์</th><th class="num">ตัวอักษรใหม่</th><th>เสร็จ</th></tr></thead>
<tbody>{rows}</tbody></table>""")
    for di, d in enumerate(days, 1):
        lesson_pages(book, n, di, d, rng, seen, stk, char_py, all_words)

    k = FINAL[n]
    # final check B: the learner writes the word, so leave out words with a true synonym in the list
    syn = {"非常", "特别", "可能", "大概", "一定", "必须", "应该", "或者", "还是", "一点儿", "一下儿", "刚才", "马上",
           "极了", "更", "经常", "一直", "怎么", "怎么样", "也", "真", "很", "多", "可以", "会", "要", "能", "想"}
    for _ in range(100000):
        pool = list(all_words)
        rng.shuffle(pool)
        fa = pool[:k]
        fb = [w for w in pool[k:] if w[0] not in syn and len(w[0]) > 1 and "……" not in w[0]][:k]
        if len(fb) == k and clash_free(fa, blank=False) and clash_free(fb):
            break
    else:
        raise SystemExit(f"YCT {n}: no clash-free final check")
    fa_html, fa_ans = [], []
    for i, w in enumerate(fa):
        others = sorted({x[2] for x in all_words if x[2] != w[2] and not related(x[0], w[0], blank=False)})
        opts = [w[2]] + rng.sample(others, 2)
        rng.shuffle(opts)
        fa_ans.append("abc"[opts.index(w[2])])
        fa_html.append(f'<div class="fq"><span class="qn">{i + 1}</span><span class="qz">{E(w[0])}</span>'
                       + "".join(f'<span class="fo"><b>{"abc"[j]}</b> {E(o)}</span>' for j, o in enumerate(opts)) + "</div>")
    fb_html = [f'<div class="qb"><span class="qn">{i + k + 1}.</span><span class="qz">{E(blank(w))}</span>'
               f'<div class="qe">{E(w[5])}</div></div>' for i, w in enumerate(fb)]
    per = 8
    for j in range(0, k, per):
        book.page((f'<h2 class="ph">แบบทดสอบรวม</h2><p class="intro">{2 * k} ข้อ จากคำศัพท์ทั้งเล่ม ลองทำโดยไม่ย้อนกลับไปดู</p>'
                   if j == 0 else '<h2 class="ph">แบบทดสอบรวม · ต่อ</h2>') +
                  (f'<h3 class="qh">A · เลือกความหมายที่ถูกต้อง</h3>' if j == 0 else "") + "".join(fa_html[j:j + per]), "quiz")
    for j in range(0, k, per):
        last = j + per >= k
        book.page('<h2 class="ph">แบบทดสอบรวม · ต่อ</h2>' +
                  ('<h3 class="qh">B · เขียนคำที่หายไปเป็นตัวอักษรจีน</h3><p class="intro">ประโยคภาษาไทยบอกความหมายของประโยค</p>' if j == 0 else "") +
                  "".join(fb_html[j:j + per]) +
                  (f'<div class="score">คะแนน: <span class="line short"></span> / {2 * k}</div>' if last else ""), "quiz")

    blocks = [answer_block(di, d["answers"]) for di, d in enumerate(days, 1)]
    blocks.append(f"""<div class="ans"><h3>แบบทดสอบรวม</h3>
<p><b>A</b> {'　'.join(f'{i + 1} {x}' for i, x in enumerate(fa_ans))}</p>
<p><b>B</b> {'　'.join(f'{i + k + 1} {E(w[0])}' for i, w in enumerate(fb))}</p></div>""")
    for j in range(0, len(blocks), 7):
        book.page(f'<h2 class="ph">เฉลย{" · ต่อ" if j else ""}</h2>' + "".join(blocks[j:j + 7]), "answers")

    def pykey(w):
        s = unicodedata.normalize("NFD", w[1].lower())
        return "".join(ch for ch in s if unicodedata.category(ch) != "Mn").replace(" ", "").replace("'", "")
    idx = sorted(((w, di) for di, d in enumerate(days, 1) for w in d["words"]), key=lambda x: (pykey(x[0]), x[0][1], x[0][0]))
    per = 26
    for j in range(0, len(idx), per * 2):
        cols = ["".join(f'<div class="ix"><span class="iz">{E(w[0])}</span><span class="ip">{E(w[1])}</span>'
                        f'<span class="im">{E(w[2].split(";")[0])}</span><span class="id">{di}</span></div>'
                        for w, di in idx[s:s + per]) for s in (j, j + per)]
        book.page(f'<h2 class="ph">ดัชนีคำศัพท์{" · ต่อ" if j else ""}</h2>' +
                  (f'<p class="intro">คำศัพท์ทั้ง {len(idx)} คำ เรียงตามพินอิน ตัวเลขด้านขวาคือบทที่ได้เรียน</p>' if j == 0 else "") +
                  f'<div class="two ixc"><div>{cols[0]}</div><div>{cols[1]}</div></div>', "index")

    nxt = (f'<li><b>YCT {n + 1}</b>: สมุดแบบฝึก YCT {n + 1} สอนคำใหม่ของระดับถัดไปในรูปแบบเดียวกัน '
           f'(hskcheck.com/th/upgrade-packs/yct-{n + 1}-workbook)</li>') if n < 4 else \
        '<li><b>HSK</b>: เมื่อเรียน YCT 4 จบแล้ว ต่อด้วยคำศัพท์ HSK 3 (hskcheck.com/th/hsk-3-word-list)</li>'
    book.page(f"""<h2 class="ph">เรียนต่ออย่างไรดี</h2>
<p>เก่งมาก! ตอนนี้รู้คำศัพท์ YCT {n} ครบแล้ว ทบทวนต่อได้ฟรีที่ hskcheck.com:</p>
<ul class="bul big">
  <li><b>รายการคำศัพท์ YCT {n}</b> (hskcheck.com/th/yct/yct-{n}-word-list): คำทั้งหมดของระดับนี้ พร้อมพินอินและความหมายภาษาไทย</li>
  <li><b>ใบงานคำศัพท์ YCT {n}</b> (hskcheck.com/th/yct/yct-{n}-vocabulary-worksheets): ใบงานจับคู่ พร้อมเฉลย พิมพ์ได้ฟรี</li>
  <li><b>แบบฝึกเขียนตัวอักษร YCT {n}</b> (hskcheck.com/th/yct/yct-{n}-character-worksheets): พิมพ์แบบฝึกเขียนเพิ่มได้</li>
  {nxt}
</ul>
<div class="notes"><h3>บันทึก</h3>""" + "".join('<div class="nl"></div>' for _ in range(8)) + "</div>" + FOOT_NOTE)
    text, pages = book.html(title)
    (HERE / f"yct{n}_th.html").write_text(text, encoding="utf-8")

    # free sample: lesson 1, same seed so it matches the full book
    rng = random.Random(20261026 + n)
    d1 = dict(days[0])
    s = Book()
    s.page(cover(n, days, all_words, seen, sample=True), "cover")
    lesson_pages(s, n, 1, d1, rng, seen, stk, char_py, all_words)
    assert d1["answers"] == days[0]["answers"]
    s.page('<h2 class="ph">เฉลย</h2>' + answer_block(1, d1["answers"]), "answers")
    s.page(f"""<h2 class="ph">เรียนต่อให้ครบ {len(all_words)} คำ</h2>
<p>สมุดแบบฝึกคำศัพท์ YCT {n} ฉบับเต็มมีครบทั้ง {len(days)} บท ในรูปแบบเดียวกันนี้</p>
<ul class="bul big">
  <li>คำศัพท์ {len(all_words)} คำ ใน {len(days)} บทเรียน พร้อมประโยคตัวอย่างแปลไทยทุกคำ</li>
  <li>แบบฝึกเขียนตัวอักษรใหม่ทั้ง {len(seen)} ตัว พร้อมลำดับขีด</li>
  <li>แบบทดสอบท้ายทุกบท แบบทดสอบรวม เฉลย และดัชนีคำศัพท์</li>
</ul>
<div class="free-box"><b class="big">{PRICES[n]} · ฉบับเต็ม {len(days)} บท</b>
<p>ดาวน์โหลด PDF พิมพ์ได้ที่ <b>{PAGE.format(n=n)}</b></p>
<p>หรือซื้อชุดรวม YCT 1–4 ทั้งสี่เล่มในราคา $6.99</p></div>
{FOOT_NOTE}""")
    stext, spages = s.html(f"บทที่ 1 ทดลองเรียนฟรี · สมุดแบบฝึกคำศัพท์ YCT {n} · hskcheck.com")
    (HERE / f"yct{n}_th_lesson1.html").write_text(stext, encoding="utf-8")
    print(f"YCT {n}: {len(days)} lessons, {len(all_words)} words, {len(seen)} new characters, {pages} pages, free sample {spages} pages")
    return pages


if __name__ == "__main__":
    pages = {n: build_level(n) for n in (1, 2, 3, 4)}
    if "--pdf" in sys.argv:
        out = pathlib.Path("/tmp/yct_th")
        out.mkdir(exist_ok=True)
        for n in (1, 2, 3, 4):
            subprocess.run([sys.executable, str(HERE / "topdf.py"), str(HERE / f"yct{n}_th.html"), str(out / f"yct-{n}-workbook-th.pdf")], check=True)
            free = R / f"th/upgrade-packs/yct-{n}-workbook"
            free.mkdir(parents=True, exist_ok=True)
            subprocess.run([sys.executable, str(HERE / "topdf.py"), str(HERE / f"yct{n}_th_lesson1.html"), str(free / f"yct-{n}-lesson-1-free.pdf")], check=True)
        subprocess.run(["pdfunite", *[str(out / f"yct-{n}-workbook-th.pdf") for n in (1, 2, 3, 4)], str(out / "yct-1-4-workbooks-th.pdf")], check=True)
        print("pages", pages, "PDFs in", out)
