"""Printable YCT vocabulary worksheets at /yct/yct-N-vocabulary-worksheets/, /th/yct/... and /vi/yct/....

Each level's new words (the words first listed at that level) are split into sets of about 20. Every set is one
printable sheet with two matching exercises and an answer key on a separate page:
  A  match each word to its meaning (English, or Thai / Vietnamese on those pages)
  B  match each word to its pinyin
Grammar words (particles and paired patterns) only go into exercise B, since their meaning can't be matched fairly.
Within one exercise no two words share a pinyin, and no two meanings in exercise A share a word (so 一下儿 and 一点儿,
both "a little", never meet), so every item has exactly one right answer.
Sets and letter orders are fixed (seeded), so a printed answer key always matches its sheet.

Called from tools/yct.py; returns the URLs it wrote.
"""
import html
import random
import re
import unicodedata

PER_SET = 20
LETTERS = "ABCDEFGHIJKLMNOPQRST"

T = {
    "en": {
        "eyebrow": "YCT · Youth Chinese Test",
        "h1": "YCT {n} Vocabulary Worksheets",
        "lede": "{sets} printable sheets for the {words} words that are new at YCT {n}: match each word to its meaning and to its "
                "pinyin. Every sheet has an answer key on a separate page. Free to print and copy for your class.",
        "set": "Sheet", "sets_label": "Choose a sheet", "of": "words",
        "show_py": "Pinyin in exercise A", "show_key": "Answer key (prints on page 2)", "print": "Print this sheet",
        "title": "YCT {n} vocabulary · Sheet {k}", "name": "Name", "date": "Date",
        "a": "Match the words to their meanings", "a_inst": "Write the letter of the right meaning in the box.",
        "b": "Match the words to their pinyin", "b_inst": "Write the letter of the right pinyin in the box.",
        "key": "Answer key", "foot": "Free worksheet from {site}",
        "about": "About these worksheets",
        "prose": [
            "The YCT word lists are cumulative, so each level repeats the words of the levels below. These sheets use only the words "
            "that are new at YCT {n}, split into sets of about 20, in the order of the word list.",
            "Exercise A tests meaning and exercise B tests pinyin. Grammar words such as particles only appear in exercise B. "
            "Within each exercise no two words share a meaning or a pinyin, so there is always exactly one right answer.",
            "Turn off “Pinyin in exercise A” to make the meaning exercise a pure reading test. For writing practice, print the "
            '<a href="{ws}">YCT {n} character worksheets</a>.',
        ],
        "doc_title": "YCT {n} Vocabulary Worksheets: Free Printable Sheets with Answers",
        "doc_desc": "{sets} free printable YCT {n} vocabulary worksheets: match the {words} new words to their meanings and pinyin, "
                    "with answer keys. For teachers, parents and students.",
    },
    "th": {
        "eyebrow": "YCT · การสอบภาษาจีนสำหรับนักเรียน",
        "h1": "แบบฝึกหัดคำศัพท์ YCT {n}",
        "lede": "แบบฝึกหัดพิมพ์ได้ {sets} แผ่น สำหรับคำศัพท์ใหม่ {words} คำของ YCT {n} ให้จับคู่คำกับความหมาย และจับคู่คำกับพินอิน "
                "ทุกแผ่นมีเฉลยแยกหน้า พิมพ์และถ่ายเอกสารใช้ในห้องเรียนได้ฟรี",
        "set": "แผ่นที่", "sets_label": "เลือกแผ่น", "of": "คำ",
        "show_py": "แสดงพินอินในข้อ A", "show_key": "เฉลย (พิมพ์ในหน้าที่ 2)", "print": "พิมพ์แผ่นนี้",
        "title": "คำศัพท์ YCT {n} · แผ่นที่ {k}", "name": "ชื่อ", "date": "วันที่",
        "a": "จับคู่คำกับความหมาย", "a_inst": "เขียนตัวอักษรของความหมายที่ถูกต้องลงในช่อง",
        "b": "จับคู่คำกับพินอิน", "b_inst": "เขียนตัวอักษรของพินอินที่ถูกต้องลงในช่อง",
        "key": "เฉลย", "foot": "แบบฝึกหัดฟรีจาก {site}",
        "about": "เกี่ยวกับแบบฝึกหัดชุดนี้",
        "prose": [
            "รายการคำศัพท์ YCT รวมคำของระดับที่ต่ำกว่าไว้ด้วย แบบฝึกหัดชุดนี้จึงใช้เฉพาะคำที่เป็นคำใหม่ของ YCT {n} "
            "แบ่งเป็นชุดละประมาณ 20 คำ ตามลำดับในรายการคำศัพท์",
            "ข้อ A ทดสอบความหมาย ข้อ B ทดสอบพินอิน คำไวยากรณ์อย่างคำช่วยจะอยู่ในข้อ B เท่านั้น "
            "ในแต่ละข้อจะไม่มีสองคำที่ความหมายหรือพินอินซ้ำกัน จึงมีคำตอบที่ถูกเพียงคำตอบเดียวเสมอ",
            "ปิด “แสดงพินอินในข้อ A” ถ้าต้องการให้ข้อความหมายเป็นการทดสอบการอ่านล้วน ๆ ถ้าต้องการฝึกเขียน พิมพ์"
            '<a href="{ws}">แบบฝึกเขียนตัวอักษร YCT {n}</a>',
        ],
        "doc_title": "แบบฝึกหัดคำศัพท์ YCT {n} พิมพ์ได้ฟรี พร้อมเฉลย",
        "doc_desc": "แบบฝึกหัดคำศัพท์ YCT {n} พิมพ์ได้ฟรี {sets} แผ่น จับคู่คำศัพท์ใหม่ {words} คำกับความหมายภาษาไทยและพินอิน "
                    "พร้อมเฉลย สำหรับครู ผู้ปกครอง และนักเรียน",
    },
    "vi": {
        "eyebrow": "YCT · Kỳ thi tiếng Trung cho học sinh",
        "h1": "Phiếu bài tập từ vựng YCT {n}",
        "lede": "{sets} phiếu in được cho {words} từ mới của YCT {n}: nối mỗi từ với nghĩa và với pinyin của nó. "
                "Mỗi phiếu có đáp án ở trang riêng. Miễn phí in và photo cho lớp học.",
        "set": "Phiếu", "sets_label": "Chọn phiếu", "of": "từ",
        "show_py": "Pinyin trong bài A", "show_key": "Đáp án (in ở trang 2)", "print": "In phiếu này",
        "title": "Từ vựng YCT {n} · Phiếu {k}", "name": "Họ tên", "date": "Ngày",
        "a": "Nối từ với nghĩa", "a_inst": "Viết chữ cái của nghĩa đúng vào ô.",
        "b": "Nối từ với pinyin", "b_inst": "Viết chữ cái của pinyin đúng vào ô.",
        "key": "Đáp án", "foot": "Phiếu bài tập miễn phí từ {site}",
        "about": "Về các phiếu bài tập này",
        "prose": [
            "Danh sách từ YCT tính gộp, nên mỗi cấp lặp lại các từ của những cấp thấp hơn. Các phiếu này chỉ dùng những từ "
            "mới ở YCT {n}, chia thành từng bộ khoảng 20 từ, theo thứ tự trong danh sách từ.",
            "Bài A kiểm tra nghĩa, bài B kiểm tra pinyin. Các từ ngữ pháp như trợ từ chỉ có trong bài B. Trong mỗi bài, "
            "không có hai từ trùng nghĩa hay trùng pinyin, nên luôn chỉ có một đáp án đúng.",
            "Tắt “Pinyin trong bài A” để bài nối nghĩa trở thành bài kiểm tra đọc chữ Hán. Để luyện viết, hãy in "
            '<a href="{ws}">phiếu tập viết chữ Hán YCT {n}</a>.',
        ],
        "doc_title": "Phiếu bài tập từ vựng YCT {n} in miễn phí, có đáp án",
        "doc_desc": "{sets} phiếu bài tập từ vựng YCT {n} in miễn phí: nối {words} từ mới với nghĩa tiếng Việt và pinyin, "
                    "có đáp án. Dành cho giáo viên, phụ huynh và học sinh.",
    },
}


def grammar_word(word, meaning_en):
    return "……" in word or "particle" in meaning_en


def norm_py(p):
    return unicodedata.normalize("NFC", re.sub(r"[\s'’\-…]", "", p.lower()))


def norm_meaning(m):
    return re.sub(r"\s+", " ", m.lower()).strip()


STOP = {"to", "a", "an", "the", "of", "in", "on", "for", "and", "or", "be", "one", "with", "thing", "things", "measure",
        "word", "words", "someone", "do", "make", "after", "verb", "up", "out", "is", "it", "at", "s"}


VI_STOP = {"của", "và", "hoặc", "là", "một", "cái", "con", "sự", "được", "trong", "với", "khi", "các", "những", "lượng",
           "từ", "trợ", "dùng"}


def meaning_tokens(m, lang="en"):
    """Words in a meaning, for spotting two meanings that could be confused (ผม is both "hair" and "I").
    Vietnamese is compared by syllable, leaving out a few function syllables (của, và, cái, con...)."""
    m = m.lower()
    if re.search(r"[\u0e00-\u0e7f]", m):
        return {t for t in re.split(r"[\s;,()]+", m) if t}
    if lang == "vi":
        return {t for t in re.split(r"[\s;,()….]+", m) if t and t not in VI_STOP}
    return {t for t in re.findall(r"[a-z']+", m) if t not in STOP}


def make_sets(words, lang="en"):
    """words: [(word, pinyin, meaning_en, meaning_shown)]. Returns [(A items, B items)] with no clashes inside an exercise.

    Words keep their list order as far as possible: each goes into the first set, from its own one onwards, where it fits
    without a clash, preferring exercise A until A holds half the set."""
    k = max(1, round(len(words) / PER_SET))
    size = -(-len(words) // k)
    sets = [{"a": [], "b": [], "tok": set(), "mean": set(), "py": set()} for _ in range(k)]

    def fits_a(st, w):
        return (not grammar_word(w[0], w[2]) and norm_meaning(w[3]) not in st["mean"]
                and not (meaning_tokens(w[3], lang) & st["tok"]))

    def put_a(st, w):
        st["a"].append(w)
        st["mean"].add(norm_meaning(w[3]))
        st["tok"] |= meaning_tokens(w[3], lang)

    for i, w in enumerate(words):
        home = min(i // size, k - 1)
        for st in sets[home:] + sets[:home]:
            full = len(st["a"]) + len(st["b"]) >= size + 1
            if full:
                continue
            if len(st["a"]) < size // 2 and fits_a(st, w):
                put_a(st, w)
                break
            if norm_py(w[1]) not in st["py"]:
                st["b"].append(w)
                st["py"].add(norm_py(w[1]))
                break
            if fits_a(st, w):
                put_a(st, w)
                break
        else:
            raise SystemExit(f"yct_ws: cannot place {w[0]} without a clash")
    return [(st["a"], st["b"]) for st in sets]


def exercise(letter, title, inst, items, answers_of, seed, zh_py=False):
    """items: list of words; answers_of: function word -> answer text. Returns (html, key list)."""
    order = list(items)
    choices = [answers_of(w) for w in order]
    shuffled = list(range(len(order)))
    random.Random(seed).shuffle(shuffled)
    letters = {}
    for pos, idx in enumerate(shuffled):
        letters[idx] = LETTERS[pos]
    left = "".join(
        f'<li><span class="m-box"></span><span class="ws-zh">{html.escape(w[0])}</span>'
        + (f'<span class="m-py">{html.escape(w[1])}</span>' if zh_py else "") + "</li>"
        for w in order)
    right = "".join(f'<li><b>{LETTERS[pos]}</b> {html.escape(choices[idx])}</li>' for pos, idx in enumerate(shuffled))
    body = (f'<div class="ws-ex"><h3><span class="ws-letter">{letter}</span>{html.escape(title)}</h3>'
            f'<p class="ws-inst">{html.escape(inst)}</p>'
            f'<div class="match"><ol class="m-left">{left}</ol><ul class="m-right">{right}</ul></div></div>')
    key = [f'{html.escape(w[0])} {letters[i]}' for i, w in enumerate(order)]
    return body, key


def page(n, lang, rows, first, thai, site, nav_html, ws_url, url):
    t = T[lang]
    shown = thai if lang in ("th", "vi") else [r[2] for r in rows]
    new = [(r[0], r[1], r[2], m) for r, m in zip(rows, shown) if first[r[0]] == n]
    sets = make_sets(new, lang)
    papers, options = [], []
    for k, (a, b) in enumerate(sets, 1):
        ex_a, key_a = exercise("A", t["a"], t["a_inst"], a, lambda w: w[3], f"yct{n}-{k}-a", zh_py=True)
        ex_b, key_b = exercise("B", t["b"], t["b_inst"], b, lambda w: w[1], f"yct{n}-{k}-b")
        title = t["title"].format(n=n, k=k)
        keys = "".join(f'<div class="ws-key-ex"><h4>{x}</h4><ol>{"".join(f"<li>{i}</li>" for i in key)}</ol></div>'
                       for x, key in (("A", key_a), ("B", key_b)))
        papers.append(
            f'<article class="ws-paper yv-paper" data-set="{k}"{"" if k == 1 else " hidden"}>'
            f'<div class="ws-head"><div class="ws-title">{html.escape(title)}</div>'
            f'<div class="ws-name">{t["name"]} <span class="ws-fill"></span> {t["date"]} <span class="ws-fill short"></span></div></div>'
            f'{ex_a}{ex_b}<div class="ws-foot">{html.escape(t["foot"].format(site=(site + url).replace("https://", "")))}</div>'
            f'<div class="ws-key"><div class="ws-head"><div class="ws-title">{html.escape(title)} · {t["key"]}</div></div>{keys}</div>'
            "</article>")
        options.append(f'<option value="{k}">{t["set"]} {k} ({len(a) + len(b)} {t["of"]})</option>')
    prose = "\n".join(f"    <p>{p.format(n=n, ws=ws_url)}</p>" for p in t["prose"])
    body = f"""<div class="wrap">
  <header class="no-print">
    {nav_html}
    <div class="eyebrow"><span>{t["eyebrow"]}</span><span class="chip">YCT {n}</span><span class="chip">{len(sets)} × A4</span></div>
    <h1>{html.escape(t["h1"].format(n=n))}</h1>
    <p class="lede">{html.escape(t["lede"].format(n=n, sets=len(sets), words=len(new)))}</p>
  </header>

  <section class="sheet ws-controls no-print" aria-label="{t["sets_label"]}">
    <div class="field"><label for="set-pick">{t["sets_label"]}</label> <select id="set-pick">{"".join(options)}</select></div>
    <div class="ws-checks">
      <label><input type="checkbox" id="opt-py" checked> {t["show_py"]}</label>
      <label><input type="checkbox" id="opt-key" checked> {t["show_key"]}</label>
    </div>
    <div><button type="button" class="button" id="print">{t["print"]}</button></div>
  </section>

  <div class="ws-preview" id="papers">
{chr(10).join(papers)}
  </div>

  <section class="prose no-print" aria-labelledby="about-title">
    <h2 id="about-title">{t["about"]}</h2>
{prose}
  </section>
</div>
<script>
(function () {{
  var wrap = document.getElementById("papers"), pick = document.getElementById("set-pick");
  var papers = Array.prototype.slice.call(wrap.querySelectorAll(".yv-paper"));
  function show() {{ papers.forEach(function (p) {{ p.hidden = p.dataset.set !== pick.value; }}); }}
  function sync(id, cls) {{
    var box = document.getElementById(id);
    var apply = function () {{ wrap.classList.toggle(cls, !box.checked); }};
    box.addEventListener("change", apply); apply();
  }}
  sync("opt-py", "no-py"); sync("opt-key", "no-key");
  var m = location.hash.match(/^#(\\d+)$/);
  if (m && papers.some(function (p) {{ return p.dataset.set === m[1]; }})) pick.value = m[1];
  pick.addEventListener("change", function () {{ history.replaceState(null, "", "#" + pick.value); show(); }});
  document.getElementById("print").addEventListener("click", function () {{ window.print(); }});
  show();
}})();
</script>"""
    return body, len(sets), len(new)


CSS = """
.yv-paper[hidden] { display: none !important; }
.match { display: grid; grid-template-columns: 1fr 1.3fr; gap: 3mm 8mm; align-items: start; }
.m-left { margin: 0; padding-left: 7mm; display: grid; gap: 2.6mm; }
.m-left li { display: flex; align-items: center; gap: 3mm; break-inside: avoid; }
.m-left li::marker { font: 500 9pt var(--f-num); color: #555; }
.m-box { display: inline-block; width: 7mm; height: 7mm; border: 0.3mm solid #111; border-radius: 1mm; flex: none; }
.m-py { font-size: 9pt; color: #555; }
.no-py .m-py { display: none; }
.m-right { margin: 0; padding: 0; list-style: none; display: grid; gap: 2.6mm; font-size: 10.5pt; }
.m-right li { min-height: 7mm; display: flex; align-items: center; gap: 2.5mm; break-inside: avoid; }
.m-right b { display: inline-grid; place-items: center; width: 5.5mm; height: 5.5mm; border: 0.25mm solid #555; border-radius: 50%; font-size: 8.5pt; flex: none; }
.ws-key-ex ol { columns: 3; }
.no-key .ws-key { display: none; }
@media (max-width: 520px) { .match { grid-template-columns: 1fr; } .ws-key-ex ol { columns: 2; } }
"""
