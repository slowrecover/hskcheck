"""Grammar practice online: an interactive version of every grammar worksheet, at /learn/<slug>/practice/ (English)
and /th/learn/<slug>/practice/ (Thai, for the pages that have a Thai translation).

The page (templates/grammar_practice_body.html, CSS in templates/grammar_practice.css on top of the practice test's
templates/practice.css) loads one small JSON file and goes through the worksheet's exercises one item at a time,
with instant feedback and a score at the end:
  choose  tap one of the worksheet's options to fill the gap;
  order   tap the words in order; every answer listed in the worksheet is accepted;
  fix     choose the correct sentence: the sentence with the mistake, the first listed correct version and up to two
          other wrong versions made from the same words (data/practice/grammar_fix.tsv).
An item that cannot be asked with exactly one right option is shown with a "Show answer" button and is not scored.
The best score per page stays in the learner's browser (localStorage); nothing is sent anywhere.

Data files read:
  data/learn/<slug>.json, data/th/learn/<slug>.json   the worksheets (Chinese, answers, English and Thai meanings)
  data/practice/grammar_choose.tsv   slug, choose sentence with ＿＿, options left out (comma separated): options that
                                     would also fit the gap and the meaning, so they are not offered for that item
  data/practice/grammar_order.tsv    slug, first listed answer of an order item, another order of the same words that
                                     is also right and means the same; it is accepted too
  data/practice/grammar_fix.tsv      slug, sentence with the mistake, one or two other wrong versions. Every version was
                                     checked by hand to be ungrammatical; it may only use characters of the sentence and
                                     its answers. A fix item without a line is shown with "Show answer".
The build stops if a line no longer matches a worksheet item, if an option or version breaks these rules, or if a
sentence uses a word above the page's level (tools/check_vocab.py).

Outputs:
  learn/<slug>/practice/index.html, learn/<slug>/practice/items.json          English
  th/learn/<slug>/practice/index.html, th/learn/<slug>/practice/items.json    Thai

items.json: {"items": [item, ...]} in worksheet order, each with "t" (c = choose, o = order, f = fix), "x" (exercise
number) and "m" (the meaning in the page's language):
  choose {"b": text before the gap, "a": text after, "r": answer, "o": options (only the answer: show-answer item)}
  order  {"w": words, "r": accepted answers, listed answers first}
  fix    {"s": sentence with the mistake, "r": correct versions, "o": other wrong versions (empty: show-answer item)}

The Thai page is the English template with its text swapped for Thai; the build stops if a string is not found.
"""
import collections
import html
import json
import re
import sys

import learn
import learn_th

BLANK = "＿＿"
PUNCT = re.compile(r"[，。：！？、“”\s]")

UI_EN = {
    "q": "Question", "of": "of",
    "askChoose": "Choose the word that fills the gap.", "askOrder": "Tap the words in the right order.",
    "askFix": "Which sentence is correct?", "askReveal": "Think of the answer, then check it.",
    "check": "Check", "undo": "Undo", "clear": "Start again", "show": "Show answer",
    "right": "Right!", "wrong": "Not quite.", "answer": "Answer", "also": "Also right", "mistake": "With the mistake",
    "notScored": "Two answers could fit here, so this one is not scored.",
    "listen": "Listen", "next": "Next question", "finish": "See my score",
    "scoreHead": "Your score", "bestNew": "New best score!", "bestOld": "Your best: {b} / {n}",
    "msg4": "Excellent. You have this grammar point.", "msg3": "Good work. Look at the answers below and try again.",
    "msg2": "Keep going. Read the explanation again, then try again.",
    "msg1": "This one is still new for you. Read the explanation with examples first.",
    "missedHead": "To review", "noMissed": "You got every question right.",
    "again": "Try again", "read": "Read the explanation again", "sheet": "Print the worksheet", "loading": "Loading the exercises…",
    "loadFail": "The exercises could not be loaded. Check your connection and try again.",
}
UI_TH = {
    "q": "ข้อ", "of": "จาก",
    "askChoose": "เลือกคำที่เติมในช่องว่างได้ถูกต้อง", "askOrder": "แตะคำเรียงตามลำดับให้เป็นประโยคที่ถูกต้อง",
    "askFix": "ประโยคไหนถูกต้อง?", "askReveal": "ลองคิดคำตอบก่อน แล้วกดดูเฉลย",
    "check": "ตรวจคำตอบ", "undo": "ย้อนกลับ", "clear": "เริ่มเรียงใหม่", "show": "ดูเฉลย",
    "right": "ถูกต้อง!", "wrong": "ยังไม่ถูก", "answer": "คำตอบ", "also": "ตอบแบบนี้ก็ถูก", "mistake": "ประโยคที่ผิด",
    "notScored": "ข้อนี้เติมได้มากกว่าหนึ่งคำ จึงไม่นับคะแนน",
    "listen": "ฟังเสียง", "next": "ข้อต่อไป", "finish": "ดูคะแนน",
    "scoreHead": "คะแนนของคุณ", "bestNew": "คะแนนสูงสุดใหม่!", "bestOld": "คะแนนสูงสุดของคุณ: {b} / {n}",
    "msg4": "ยอดเยี่ยม คุณเข้าใจไวยากรณ์ข้อนี้แล้ว", "msg3": "ทำได้ดี ดูคำตอบด้านล่างแล้วลองอีกครั้ง",
    "msg2": "สู้ต่อไป อ่านคำอธิบายอีกรอบแล้วลองใหม่",
    "msg1": "ไวยากรณ์ข้อนี้ยังใหม่สำหรับคุณ อ่านคำอธิบายพร้อมตัวอย่างก่อนก็ดี",
    "missedHead": "ข้อที่ควรทบทวน", "noMissed": "คุณตอบถูกทุกข้อ",
    "again": "ทำอีกครั้ง", "read": "อ่านคำอธิบายอีกครั้ง", "sheet": "พิมพ์แบบฝึกหัด", "loading": "กำลังโหลดแบบฝึกหัด…",
    "loadFail": "โหลดแบบฝึกหัดไม่ได้ ตรวจสอบอินเทอร์เน็ตแล้วลองอีกครั้ง",
}
KINDS_EN = {"choose": "fill the gap", "order": "put the words in order", "fix": "pick the correct sentence"}
KINDS_SHORT_EN = {"choose": "gap fill", "order": "word order", "fix": "spot the mistake"}
KINDS_TH = {"choose": "เติมคำในช่องว่าง", "order": "เรียงคำเป็นประโยค", "fix": "เลือกประโยคที่ถูกต้อง"}

TH_SWAPS = [
    ('<span>HSK grammar practice</span>', '<span>ฝึกไวยากรณ์ HSK</span>'),
    ('</span>Practise Online</h1>', '</span>ฝึกทำออนไลน์</h1>'),
    ('<p class="lede">Practise __NAME__ with __COUNT__ exercises that use only HSK __LEVEL__ words: __KINDS__. You see '
     'the answer straight away and your score at the end. Need the rules first? Read the '
     '<a href="__URL__">explanation with examples</a>.</p>',
     '<p class="lede">ฝึก__NAME__ ด้วยแบบฝึกหัด __COUNT__ ข้อ ใช้เฉพาะคำศัพท์ HSK __LEVEL__ ทั้ง__KINDS__ '
     'รู้คำตอบทันทีหลังตอบแต่ละข้อ และเห็นคะแนนเมื่อทำครบ อยากทบทวนกฎก่อน? อ่าน'
     '<a href="__URL__">คำอธิบายพร้อมตัวอย่าง</a></p>'),
    ('<h2 id="ex-title" class="visually-hidden">Exercises</h2>', '<h2 id="ex-title" class="visually-hidden">แบบฝึกหัด</h2>'),
    ('<p class="empty" id="loading">Loading the exercises…</p>', '<p class="empty" id="loading">กำลังโหลดแบบฝึกหัด…</p>'),
    ('This browser is not letting the page save, so your best score will not be kept.',
     'เบราว์เซอร์นี้ไม่อนุญาตให้บันทึกข้อมูล คะแนนสูงสุดจึงจะไม่ถูกเก็บไว้'),
    ('<h2 id="guide-title">How this practice works</h2>', '<h2 id="guide-title">วิธีใช้แบบฝึกหัดนี้</h2>'),
    ('<h3>Where do the exercises come from?</h3>', '<h3>แบบฝึกหัดมาจากไหน?</h3>'),
    ('<p>They are the exercises of the <a href="__URL__worksheet/">printable worksheet</a> for this grammar point, '
     'in a different order each time. Every sentence uses only HSK __LEVEL__ words, and the English under each '
     'sentence tells you what it should mean.</p>',
     '<p>เป็นแบบฝึกหัดชุดเดียวกับ<a href="__URL__worksheet/">แบบฝึกหัดพิมพ์ได้</a>ของไวยากรณ์ข้อนี้ '
     'แต่สลับลำดับใหม่ทุกครั้ง ทุกประโยคใช้เฉพาะคำศัพท์ HSK __LEVEL__ และคำแปลภาษาไทยใต้ประโยคบอกว่าประโยคนั้นควรมีความหมายว่าอะไร</p>'),
    ('<h3>How do I answer?</h3>', '<h3>ตอบอย่างไร?</h3>'),
    ('<p>Tap an answer, or press 1–4 on a keyboard. To put words in order, tap them one by one (or press their '
     'numbers), then check. Where more than one order is right, every one of them counts.</p>',
     '<p>แตะคำตอบ หรือกดปุ่ม 1–4 บนแป้นพิมพ์ ข้อเรียงคำให้แตะคำทีละคำ (หรือกดตัวเลขของคำนั้น) แล้วกดตรวจคำตอบ '
     'ถ้าเรียงได้ถูกมากกว่าหนึ่งแบบ ทุกแบบนับว่าถูก</p>'),
    ('<h3>Where is my score kept?</h3>', '<h3>คะแนนเก็บไว้ที่ไหน?</h3>'),
    ('<p>Your best score for this page is kept in this browser on this device. Your answers are not sent anywhere.</p>',
     '<p>คะแนนสูงสุดของหน้านี้เก็บไว้ในเบราว์เซอร์ของอุปกรณ์นี้ คำตอบของคุณไม่ถูกส่งไปที่ไหน</p>'),
    ('<h2>More grammar practice</h2>', '<h2>ฝึกไวยากรณ์ข้ออื่น</h2>'),
    ('<a href="/learn/">All grammar points</a> · <a href="/hsk-practice-test/">HSK practice test</a>',
     '<a href="/th/learn/">ไวยากรณ์ทั้งหมด</a> · <a href="/th/hsk-practice-test/">แบบทดสอบ HSK</a>'),
]


def _strip(s):
    return PUNCT.sub("", s)


def _tsv(root, name, cols):
    path = root / "data" / "practice" / name
    rows = []
    if not path.exists():
        return rows
    for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        parts = line.split("\t")
        if len(parts) not in cols:
            raise SystemExit(f"data/practice/{name} line {i}: expected {max(cols)} tab-separated columns")
        rows.append((f"data/practice/{name} line {i}", parts))
    return rows


def _checks(root):
    """The hand-checked extras, keyed by (slug, sentence)."""
    leave_out = {}
    for where, (slug, zh, opts) in _tsv(root, "grammar_choose.tsv", (3,)):
        if (slug, zh) in leave_out:
            raise SystemExit(f"{where}: listed twice")
        leave_out[(slug, zh)] = (where, [o.strip() for o in opts.split(",") if o.strip()])
    also = collections.defaultdict(list)
    for where, (slug, first, extra) in _tsv(root, "grammar_order.tsv", (3,)):
        also[(slug, first)].append((where, extra))
    wrong = {}
    for where, parts in _tsv(root, "grammar_fix.tsv", (3, 4)):
        slug, zh = parts[0], parts[1]
        if (slug, zh) in wrong:
            raise SystemExit(f"{where}: listed twice")
        wrong[(slug, zh)] = (where, [p for p in parts[2:] if p])
    return leave_out, also, wrong


_CACHE = {}


def _items(root):
    """{slug: [item dict with both meanings]} for every English page with a worksheet."""
    if "items" in _CACHE:
        return _CACHE["items"]
    sys.path.insert(0, str(root / "tools"))
    from check_vocab import allowed_words, check
    leave_out, also, wrong = _checks(root)
    used = set()
    vocab = {n: allowed_words(n) for n in (1, 2, 3)}
    th_pages = {p["slug"]: p for p in learn_th.load_pages(root)}
    out = {}
    for p in learn.load_pages():
        w = p.get("worksheet")
        if not w:
            continue
        slug = p["slug"]
        words = vocab[p["level"]]
        max_len = max(len(x) for x in words)
        th = th_pages.get(slug)

        def level_ok(sentence, where):
            tokens, bad = check(sentence, words, max_len)
            if bad:
                raise SystemExit(f"{where}: above HSK {p['level']}: {sentence} ({' / '.join(tokens)})")

        items = []
        for k, ex in enumerate(w["exercises"]):
            for j, it in enumerate(ex["items"]):
                m = {"en": it["en"], "th": th["worksheet"]["exercises"][k]["items"][j]["en"] if th else None}
                if ex["type"] == "choose":
                    opts = list(ex["options"])
                    hit = leave_out.get((slug, it["zh"]))
                    if hit:
                        used.add(("c", slug, it["zh"]))
                        where, drop = hit
                        if it["answer"] in drop or any(d not in opts for d in drop):
                            raise SystemExit(f"{where}: options to leave out must be other options of the item")
                        opts = [o for o in opts if o not in drop]
                    before, after = it["zh"].split(BLANK)
                    items.append({"t": "c", "x": k, "b": before, "a": after, "r": it["answer"],
                                  "o": opts if len(opts) > 1 else [it["answer"]], "m": m})
                elif ex["type"] == "order":
                    accepted = list(it["answers"])
                    for where, extra in also.get((slug, it["answers"][0]), []):
                        used.add(("o", slug, it["answers"][0], extra))
                        if sorted(_strip(extra)) != sorted("".join(it["words"])):
                            raise SystemExit(f"{where}: {extra} is not made of the item's words")
                        if _strip(extra) in {_strip(a) for a in accepted}:
                            raise SystemExit(f"{where}: {extra} is already accepted")
                        level_ok(extra, where)
                        accepted.append(extra)
                    if len(it["words"]) < 2:
                        raise SystemExit(f"data/learn/{slug}.json: order item needs at least two words: {it['words']}")
                    items.append({"t": "o", "x": k, "w": it["words"], "r": accepted, "m": m})
                else:
                    others = []
                    hit = wrong.get((slug, it["zh"]))
                    if hit:
                        used.add(("f", slug, it["zh"]))
                        where, others = hit
                        allowed_chars = set(_strip(it["zh"] + "".join(it["answers"])))
                        right = {_strip(a) for a in it["answers"]}
                        seen = {_strip(it["zh"])}
                        for o in others:
                            s = _strip(o)
                            if s in right:
                                raise SystemExit(f"{where}: {o} is one of the correct versions")
                            if s in seen:
                                raise SystemExit(f"{where}: {o} repeats another option")
                            if not set(s) <= allowed_chars:
                                raise SystemExit(f"{where}: {o} uses characters that are not in the item")
                            level_ok(o, where)
                            seen.add(s)
                    items.append({"t": "f", "x": k, "s": it["zh"], "r": it["answers"], "o": others, "m": m})
        out[slug] = items
    known = ({("c", s, z) for (s, z) in leave_out} | {("f", s, z) for (s, z) in wrong}
             | {("o", s, f, e) for (s, f), lst in also.items() for _, e in lst})
    for k in sorted(known - used):
        raise SystemExit(f"data/practice: no worksheet item for {k[1]}: {k[2]} (edit or remove the line)")
    _CACHE["items"] = out
    return out


def _json(items, lang):
    rows = []
    for it in items:
        r = {k: v for k, v in it.items() if k != "m"}
        r["m"] = it["m"][lang]
        rows.append(r)
    return json.dumps({"items": rows}, ensure_ascii=False, separators=(",", ":"))


def _join(parts, sep, last):
    return parts[0] if len(parts) == 1 else sep.join(parts[:-1]) + last + parts[-1]


def _name_en(p):
    t = p["worksheet"]["title"]
    if " Worksheet:" not in t:
        raise SystemExit(f"grammar practice: worksheet title of {p['slug']} has no ' Worksheet:': {t}")
    return t.split(" Worksheet:")[0]


def _name_th(p):
    t = p["worksheet"]["title"]
    suffix = f" HSK {p['level']} พิมพ์ได้ พร้อมเฉลย"
    if not t.startswith("แบบฝึกหัด") or not t.endswith(suffix):
        raise SystemExit(f"grammar practice: Thai worksheet title of {p['slug']} is not 'แบบฝึกหัด… HSK N พิมพ์ได้ พร้อมเฉลย'")
    return t[len("แบบฝึกหัด"):-len(suffix)]


def _more(pages, p, base, label):
    lv = p["level"]
    others = [q for q in pages if q is not p]
    others.sort(key=lambda q: (q["level"] != lv, abs(q["level"] - lv), q["slug"]))
    return '<ul class="more">' + "".join(
        f'<li><a href="{base}{q["slug"]}/practice/"><span class="zh-inline">{html.escape(q["zh"])}</span> '
        f'{label(q)}</a> <span class="lv">HSK {q["level"]}</span></li>' for q in others[:6]) + "</ul>"


def _ld(name, url, desc, lang, level, part_of):
    return json.dumps({
        "@context": "https://schema.org", "@type": "LearningResource", "name": name, "description": desc,
        "learningResourceType": "Quiz", "educationalLevel": f"HSK {level}", "inLanguage": [lang, "zh-Hans"],
        "isAccessibleForFree": True, "url": url, "isPartOf": part_of,
        "publisher": {"@type": "Organization", "name": "hskcheck.com", "url": "https://hskcheck.com/"},
    }, ensure_ascii=False)


def _page(tpl_text, *, nav_html, p, name, kinds, url, ui, more, count):
    return (tpl_text.replace("__NAV__", nav_html)
            .replace("__UI_JSON__", json.dumps(ui, ensure_ascii=False))
            .replace("__DATA__", f"{url}practice/items.json")
            .replace("__SLUG__", p["slug"])
            .replace("__NAME__", learn.zh_spans(name))
            .replace("__KINDS__", html.escape(kinds))
            .replace("__COUNT__", str(count))
            .replace("__LEVEL__", str(p["level"]))
            .replace("__ZH__", html.escape(p["zh"]))
            .replace("__URL__", url)
            .replace("__MORE__", more))


def _check_meta(title, desc, where):
    if len(title) >= 65 or len(desc) >= 160:
        raise SystemExit(f"grammar practice: title or description too long for {where}: {title} | {desc}")


def build(root, pages_nav, nav, render, base_css, tpl, site):
    """Write /learn/<slug>/practice/ for every English grammar page with a worksheet. Returns the URLs written."""
    items = _items(root)
    pages = [p for p in learn.load_pages() if p["slug"] in items]
    css = (base_css + (tpl / "checker.css").read_text(encoding="utf-8") + (tpl / "practice.css").read_text(encoding="utf-8")
           + (tpl / "grammar_practice.css").read_text(encoding="utf-8"))
    tpl_text = (tpl / "grammar_practice_body.html").read_text(encoding="utf-8")
    urls = []
    for p in pages:
        url = f"{learn.LEARN_URL}{p['slug']}/"
        its = items[p["slug"]]
        name = _name_en(p)
        kinds = _join([KINDS_EN[e["type"]] for e in p["worksheet"]["exercises"]], ", ", " and ")
        title = f"{name} Practice Online: HSK {p['level']} Grammar Quiz"
        short = _join([KINDS_SHORT_EN[e["type"]] for e in p["worksheet"]["exercises"]], ", ", " and ")
        desc = (f"Practise {name} online: {len(its)} HSK {p['level']} exercises ({short}) with instant answers and "
                "a score. Free, no sign-up.")
        _check_meta(title, desc, p["slug"])
        more = _more(pages, p, learn.LEARN_URL, lambda q: html.escape(q["h1"]))
        body = _page(tpl_text, nav_html=nav(pages_nav, learn.LEARN_URL), p=p, name=name, kinds=kinds, url=url,
                     ui=UI_EN, more=more, count=len(its))
        folder = root / url.strip("/") / "practice"
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "items.json").write_text(_json(its, "en"), encoding="utf-8")
        (folder / "index.html").write_text(render(
            title, desc, f"{site}{url}practice/", css, body,
            f'<script type="application/ld+json">{_ld(title, f"{site}{url}practice/", desc, "en", p["level"], site + url)}</script>'),
            encoding="utf-8")
        urls.append(f"{url}practice/")
    return urls


def build_th(*, root, tpl, site, render, nav, font_link, foot, css):
    """Write /th/learn/<slug>/practice/ for every Thai grammar page with a worksheet. Returns the URLs written."""
    items = _items(root)
    pages = [p for p in learn_th.load_pages(root) if p["slug"] in items and p.get("worksheet")]
    css = css + (tpl / "grammar_practice.css").read_text(encoding="utf-8")
    tpl_text = (tpl / "grammar_practice_body.html").read_text(encoding="utf-8")
    for a, b in TH_SWAPS:
        if tpl_text.count(a) != 1:
            raise SystemExit(f"grammar practice: English text not found for the Thai page: {a[:60]}")
        tpl_text = tpl_text.replace(a, b)
    urls = []
    for p in pages:
        url = f"{learn_th.TH_LEARN_URL}{p['slug']}/"
        its = items[p["slug"]]
        if any(it["m"]["th"] is None for it in its):
            raise SystemExit(f"grammar practice: missing Thai meaning on {p['slug']}")
        name = _name_th(p)
        kinds_list = [KINDS_TH[e["type"]] for e in p["worksheet"]["exercises"]]
        kinds = _join(kinds_list, " ", " และ")
        title = f"แบบฝึกหัด{name} ออนไลน์ HSK {p['level']} เฉลยทันที"
        desc = (f"ฝึก{name} ออนไลน์ฟรี {len(its)} ข้อ ระดับ HSK {p['level']} ทั้ง{kinds} "
                "รู้คำตอบทันทีพร้อมคะแนน ไม่ต้องสมัคร")
        _check_meta(title, desc, "th/" + p["slug"])
        more = _more(pages, p, learn_th.TH_LEARN_URL, lambda q: learn.zh_spans(q["h1"]))
        body = _page(tpl_text, nav_html=nav(learn_th.TH_LEARN_URL), p=p, name=name, kinds=kinds, url=url,
                     ui=UI_TH, more=more, count=len(its))
        folder = root / url.strip("/") / "practice"
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "items.json").write_text(_json(its, "th"), encoding="utf-8")
        (folder / "index.html").write_text(render(
            title, desc, f"{site}{url}practice/", css, body,
            font_link + f'\n<script type="application/ld+json">{_ld(title, f"{site}{url}practice/", desc, "th", p["level"], site + url)}</script>',
            lang="th", foot=foot), encoding="utf-8")
        urls.append(f"{url}practice/")
    return urls


def alternates(root):
    """English path -> Thai path for the practice pages that exist in both languages."""
    pairs = {}
    for en_path, th_path in learn_th.alternates(root).items():
        if en_path.endswith("/worksheet/"):
            base_en, base_th = en_path[:-len("worksheet/")], th_path[:-len("worksheet/")]
            pairs[f"{base_en}practice/"] = f"{base_th}practice/"
    return pairs
