"""Build the Old HSK 1 -> New HSK 1 Upgrade Pack PDF (60 pages, A4).

Usage:  python3 tools/pack_pdf/build_pack.py && python3 tools/pack_pdf/topdf.py $PWD/tools/pack_pdf/pack.html /tmp/pack.pdf
Content (10 lessons, 155 words with example sentences) is in content.py; check sentences with tools/check_vocab.py --level 1.
To make another level, copy content.py with that level's new words and change the level filter and text. Never commit the PDF or pack.html.
"""
import html, json, math, pathlib, random, sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from content import DAYS, CHAR_PY  # noqa: E402

R = HERE.parent.parent
UP = json.loads((R / "old-hsk-to-new-hsk/words.json").read_text(encoding="utf-8"))
OLD1_CHARS = set(UP["oc"][1])
STROKES = json.loads((R / "strokes/hsk1.json").read_text(encoding="utf-8"))
E = html.escape
TITLE = "Old HSK 1 → New HSK 1 Upgrade Pack · hskcheck.com"
rng = random.Random(20261025)

# ---- data -------------------------------------------------------------------------------------------------------
days = []
seen = []
for title, words in DAYS:
    new = []
    for w in words:
        for c in w[0]:
            if c not in OLD1_CHARS and c not in seen and "一" <= c <= "鿿":
                seen.append(c)
                new.append(c)
    days.append({"title": title, "words": words, "chars": new})
ALL_WORDS = [w for d in days for w in d["words"]]
assert len(ALL_WORDS) == 155 and len(seen) == 74, (len(ALL_WORDS), len(seen))
for c in seen:
    assert c in STROKES and c in CHAR_PY, c


GROUPS = [{"这里", "这儿"}, {"那里", "那儿"}, {"哪里", "哪儿"}, {"星期日", "星期天"}, {"一些", "有的", "有些"},
          {"半", "一半"}, {"早", "早上"}, {"晚", "晚上"}, {"他们", "她们", "它们", "你们"}, {"女", "女士"},
          {"学", "读书"}, {"这边", "这里", "这儿"}, {"那边", "那里", "那儿"}, {"外", "外边"}, {"饭", "饭店"},
          {"上学", "上课"}, {"有点儿", "一点儿"}, {"病", "生病"}, {"见", "听见"}, {"事", "没事"}, {"要", "可以"},
          {"非常", "真"}, {"晚饭", "午饭", "早饭"}, {"小学", "中学", "大学"}, {"小学生", "中学生", "大学生"},
          {"今年", "明年", "去年"}, {"哥哥", "弟弟"}, {"姐姐", "妹妹"}, {"男朋友", "女朋友"}, {"百", "千"},
          {"包子", "饺子", "面包", "面条儿"}, {"店", "书店", "超市"}, {"贵", "便宜"}, {"好看", "好听", "好玩儿", "好吃"},
          {"上班", "下班"}, {"上课", "下课"}, {"前", "后"}, {"这个", "那个"}, {"这些", "那些"}, {"雨", "雪"}]


def related(a, b):
    return any(a in g and b in g for g in GROUPS)


def clash_free(items):
    names = [w[0] for w in items]
    means = [w[2] for w in items]
    return len(set(means)) == len(means) and not any(related(a, b) for i, a in enumerate(names) for b in names[i + 1:])


def alts(word):
    """Other words that would also be right in a fill-in sentence written for `word`."""
    return []


def words_with(c):
    return [w[0] for w in ALL_WORDS if c in w[0]]


# ---- small renderers --------------------------------------------------------------------------------------------
def zh_word_html(word, chars_new):
    return "".join(f'<span class="newc">{E(c)}</span>' if c in chars_new else E(c) for c in word)


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


pages = []


def page(body, cls=""):
    pages.append((body, cls))


# ---- cover ------------------------------------------------------------------------------------------------------
page(f"""
<div class="topbar"></div>
<div class="brand">hskcheck.com</div>
<div class="kicker">HSK 2.0 → HSK 3.0 · PRINTABLE PACK</div>
<h1 class="cover-t">Old HSK 1<br><span class="arrow">→</span><br><span class="green">New HSK 1</span></h1>
<div class="cover-sub">Upgrade Pack</div>
<p class="cover-lede">You studied the old six-level HSK 1. The new HSK 1 (2025 syllabus) has 300 words. 145 of them were
already in old HSK 1. This pack teaches you the other 155, in ten short lessons.</p>
<div class="stats">
  <div><b>155</b><span>words to learn</span></div>
  <div><b>74</b><span>new characters to write</span></div>
  <div><b>10</b><span>lessons, one a day</span></div>
</div>
<ul class="bul">
  <li>Every word with pinyin, meaning and an example sentence that uses only new HSK 1 words</li>
  <li>Stroke order and tracing practice for every character you haven't met in old HSK 1</li>
  <li>A quiz after each lesson, a final check, and answers at the back</li>
</ul>
<div class="cover-foot">Word lists follow the 2025 HSK 3.0 syllabus. Made by hskcheck.com, where the HSK level checker,
word lists and the old → new HSK word gap tool are free.</div>
""", "cover")

# ---- how to use / plan ------------------------------------------------------------------------------------------
plan_rows = []
pg_guess = {}
rows = "".join(
    f'<tr><td class="dn">Day {i}</td><td>{E(d["title"])}</td><td class="num">{len(d["words"])}</td>'
    f'<td class="num">{len(d["chars"])}</td><td class="tick"><span class="box"></span></td></tr>'
    for i, d in enumerate(days, 1))
page(f"""
<h2 class="ph">How to use this pack</h2>
<p>Each day has three parts. Together they take about 30 minutes.</p>
<ol class="steps">
  <li><b>Learn the words.</b> Read each word, its pinyin and meaning, then read the example sentence aloud.
  Every sentence uses only words from the new HSK 1 list, so you can understand all of it.</li>
  <li><b>Write the new characters.</b> Follow the stroke order, trace the grey characters, then write your own.
  Only characters you didn't meet in old HSK 1 are here.</li>
  <li><b>Take the quiz.</b> Do it without looking back, then check your answers at the back of the pack.
  Mark the words you missed and read them again the next day.</li>
</ol>
<h2 class="ph2">Your 10-day plan</h2>
<table class="plan"><thead><tr><th></th><th>Topic</th><th class="num">Words</th><th class="num">New characters</th><th>Done</th></tr></thead>
<tbody>{rows}</tbody></table>
<p class="note">After Day 10, take the final check. Then use the free tools at hskcheck.com: the HSK level checker shows
which words in any Chinese text are above HSK 1, and the HSK flashcards help you review all 300 words.</p>
<p class="note"><b>Pinyin note.</b> Pinyin in the sentences shows tone changes as you say them: 不 becomes bú and 一
becomes yí or yì before some tones. Neutral tones have no mark.</p>
""")

# ---- day pages --------------------------------------------------------------------------------------------------
WPP = 9
CPP = 5
day_first_page = {}
for di, d in enumerate(days, 1):
    ws = d["words"]
    chunks = [ws[i:i + WPP] for i in range(0, len(ws), WPP)]
    if len(chunks) == 2 and len(chunks[1]) < 5:
        half = math.ceil(len(ws) / 2)
        chunks = [ws[:half], ws[half:]]
    day_first_page[di] = len(pages) + 1
    for ci, ch in enumerate(chunks):
        items = []
        for w in ch:
            big = "".join(f'<span class="newc">{E(c)}</span>' if c in d["chars"] or (c in seen and c not in OLD1_CHARS and c in d["chars"]) else E(c) for c in w[0])
            big = "".join(f'<span class="newc">{E(c)}</span>' if c in seen else E(c) for c in w[0])
            items.append(f"""<div class="wrow"><div class="wl"><div class="wz">{big}</div>
<div class="wp">{E(w[1])}</div><div class="wm">{E(w[2])}</div></div>
<div class="wr"><div class="sz">{hl(w[3], w[0])}</div><div class="sp">{E(w[4])}</div><div class="se">{E(w[5])}</div></div></div>""")
        head = (f'<div class="dayhead"><div class="dk">DAY {di}</div><h2>{E(d["title"])}</h2>'
                f'<div class="dm">{len(ws)} words · {len(d["chars"])} new characters</div></div>') if ci == 0 else \
            f'<div class="dayhead small"><div class="dk">DAY {di} · CONTINUED</div></div>'
        page(head + "".join(items))
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
<div class="cp">{E(CHAR_PY[c])}</div><div class="cn">{n} stroke{'s' if n > 1 else ''}</div></div>
<div class="cr"><div class="cin">in: {E(inw)}</div><div class="steps">{steps}</div><div class="trace">{trace}</div></div></div>""")
        head = f'<h2 class="ph">Day {di} · Write the new characters</h2>'
        if pi == 0:
            head += ('<p class="intro">Follow the stroke order (the newest stroke is red), trace the three grey '
                     'characters, then fill the empty boxes.</p>')
        page(head + "".join(rows), "write")
    # quiz
    while True:
        pool = list(ws)
        rng.shuffle(pool)
        if clash_free(pool[:6]) and clash_free(pool[6:11]):
            break
    a_items = pool[:6]
    b_items = pool[6:11]
    c_items = pool[11:17] if len(pool) >= 17 else (pool[11:] + pool[:6 - len(pool[11:])])
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
    b_list = "".join(
        f'<div class="qb"><span class="qn">{i + 1}.</span><span class="qz">{E(w[3].replace(w[0], "（　　　）", 1))}</span>'
        f'<div class="qe">{E(w[5])}</div></div>' for i, w in enumerate(b_items))
    half = math.ceil(len(c_items) / 2)
    def crow(i, w):
        return f'<div class="qc"><span class="qn">{i + 1}</span><span class="qz">{E(w[0])}</span><span class="line"></span></div>'
    c_l = "".join(crow(i, w) for i, w in enumerate(c_items[:half]))
    c_r = "".join(crow(i + half, w) for i, w in enumerate(c_items[half:]))
    d["answers"] = {"A": a_ans, "B": bank, "C": [w[1] for w in c_items]}
    page(f"""<h2 class="ph">Day {di} · Quiz</h2>
<h3 class="qh">A · Match each word to its meaning</h3>
<div class="two"><div>{a_left}</div><div>{a_right}</div></div>
<h3 class="qh">B · Fill in the blanks</h3><p class="intro">Use each word in the box once. The English tells you what the sentence means.</p>
<div class="bank">{"".join(f"<span>{E(x)}</span>" for x in bank_sorted)}</div>{b_list}
<h3 class="qh">C · Write the pinyin, with tone marks</h3>
<div class="two"><div>{c_l}</div><div>{c_r}</div></div>""", "quiz")

# ---- final check ------------------------------------------------------------------------------------------------
SYN = set().union(*GROUPS[:12])
while True:
    pool = list(ALL_WORDS)
    rng.shuffle(pool)
    fa = pool[:10]
    fb = [w for w in pool[10:] if w[0] not in SYN and len(w[0]) > 1][:10]
    if clash_free(fa) and clash_free(fb):
        break
fa_html, fa_ans = [], []
for i, w in enumerate(fa):
    others = sorted({x[2] for x in ALL_WORDS if x[2] != w[2] and not related(x[0], w[0])})
    opts = [w[2]] + rng.sample(others, 2)
    rng.shuffle(opts)
    fa_ans.append("abc"[opts.index(w[2])])
    fa_html.append(f'<div class="fq"><span class="qn">{i + 1}</span><span class="qz">{E(w[0])}</span>'
                   + "".join(f'<span class="fo"><b>{"abc"[k]}</b> {E(o)}</span>' for k, o in enumerate(opts)) + "</div>")
fb_html = "".join(f'<div class="qb"><span class="qn">{i + 11}.</span><span class="qz">{E(w[3].replace(w[0], "（　　　）", 1))}</span>'
                  f'<div class="qe">{E(w[5])}</div></div>' for i, w in enumerate(fb))
page(f"""<h2 class="ph">Final check</h2>
<p class="intro">20 questions on words from all ten days. Try it without looking back. 16 or more right means you
know the new HSK 1 words well.</p>
<h3 class="qh">A · Choose the meaning</h3>{''.join(fa_html)}""", "quiz")
page(f"""<h2 class="ph">Final check · continued</h2>
<h3 class="qh">B · Write the missing word in Chinese characters</h3>
<p class="intro">The English tells you what the sentence means. Each missing word is a new HSK 1 word from this pack.</p>
{fb_html}
<div class="score">Your score: <span class="line short"></span> / 20</div>""", "quiz")

# ---- answers ----------------------------------------------------------------------------------------------------
blocks = []
for di, d in enumerate(days, 1):
    a = d["answers"]
    blocks.append(f"""<div class="ans"><h3>Day {di}</h3>
<p><b>A</b> {'　'.join(f'{i + 1} {x}' for i, x in enumerate(a['A']))}</p>
<p><b>B</b> {'　'.join(f'{i + 1} {E(x)}' for i, x in enumerate(a['B']))}</p>
<p><b>C</b> {'　'.join(f'{i + 1} {E(x)}' for i, x in enumerate(a['C']))}</p></div>""")
blocks.append(f"""<div class="ans"><h3>Final check</h3>
<p><b>A</b> {'　'.join(f'{i + 1} {x}' for i, x in enumerate(fa_ans))}</p>
<p><b>B</b> {'　'.join(f'{i + 11} {E(w[0])}' for i, w in enumerate(fb))}</p></div>""")
page('<h2 class="ph">Answers</h2>' + "".join(blocks[:6]), "answers")
page('<h2 class="ph">Answers · continued</h2>' + "".join(blocks[6:]), "answers")

# ---- index ------------------------------------------------------------------------------------------------------
def pykey(w):
    import unicodedata
    s = unicodedata.normalize("NFD", w[1].lower())
    return "".join(ch for ch in s if unicodedata.category(ch) != "Mn").replace(" ", "")
idx = sorted(((w, di) for di, d in enumerate(days, 1) for w in d["words"]), key=lambda x: (pykey(x[0]), x[0][0]))
per = 27
for k in range(0, len(idx), per * 2):
    cols = []
    for cstart in (k, k + per):
        part = idx[cstart:cstart + per]
        cols.append("".join(f'<div class="ix"><span class="iz">{E(w[0])}</span><span class="ip">{E(w[1])}</span>'
                            f'<span class="im">{E(w[2])}</span><span class="id">{di}</span></div>' for w, di in part))
    page(f'<h2 class="ph">Word index{" · continued" if k else ""}</h2>' +
         ('<p class="intro">All 155 words in pinyin order, with the day where you learn them.</p>' if k == 0 else "") +
         f'<div class="two ixc"><div>{cols[0]}</div><div>{cols[1]}</div></div>', "index")

# ---- words you already know ---------------------------------------------------------------------------------
known = [x for x in UP["w"] if x[3] == 1 and x[4] == 1]
assert len(known) == 145, len(known)
page('<h2 class="ph">The 145 words you already know</h2><p class="intro">These new HSK 1 words were already in old HSK 1. '
     'Read through them once: if one looks unfamiliar, look it up in the HSK 1 word list at hskcheck.com.</p>'
     '<div class="known">' + "".join(f'<div><span class="iz">{E(x[0])}</span> <span class="ip">{E(x[1])}</span></div>' for x in known) + '</div>', "index")

# ---- last page ---------------------------------------------------------------------------------------------------
page("""<h2 class="ph">What next?</h2>
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
<div class="notes"><h3>Notes</h3>""" + "".join('<div class="nl"></div>' for _ in range(12)) + """</div>
<p class="small">Found a mistake? Email willowbewater@gmail.com and we will send you a corrected file.
This pack is for one learner's own study. hskcheck.com is independent and not affiliated with the organisers of the HSK exam.</p>""")

# ---- assemble ---------------------------------------------------------------------------------------------------
N = len(pages)
CSS = (HERE / "pack.css").read_text(encoding="utf-8")
out = [f"<!doctype html><html lang='en'><head><meta charset='utf-8'><title>{E(TITLE)}</title><style>{CSS}</style></head><body>"]
for i, (body, cls) in enumerate(pages, 1):
    out.append(f'<section class="page {cls}"><div class="inner">{body}</div>'
               f'<div class="foot"><span>{E(TITLE)}</span><span>{i} / {N}</span></div></section>')
out.append("</body></html>")
(HERE / "pack.html").write_text("".join(out), encoding="utf-8")
print("pages", N)
