"""Graded reading: short HSK stories at /reading/<slug>/ (English page) and /th/reading/<slug>/ (Thai page).

Each story is data/stories/<slug>.json:
  {
    "slug": "tea-at-the-little-shop",   same as the file name
    "level": 1,                         HSK 3.0 level (1-5): every word must be at or below it
    "episode": 1,                       order within the level
    "published": "2026-10-23",
    "title": "小店里的茶", "title_en": "Tea at the Little Shop", "title_th": "ชาที่ร้านเล็ก ๆ",
    "names": ["大卫", "小雨"],          names and places allowed in the text although not on the word lists
    "paras": ["...", "..."],            the story, one paragraph per item
    "questions": [{"q": "...", "options": ["...", "...", "..."], "answer": 0}]
  }

The build stops if any word in the story, a question or an option is above the story's level (same splitter as the
level checker and tools/check_vocab.py). Every word is tappable for its pinyin and meaning (Thai on the Thai page for
HSK 1-4). Readers can add the story's words of its own level to their flashcards (same browser storage as
/hsk-flashcards/). Also writes reading/index.json, which the flashcards page reads to suggest the latest story.

The fixed cast, so new stories stay consistent: 大卫 (Dàwèi), a British university student learning Chinese;
小雨 (Xiǎoyǔ), who works at the milk tea shop by the school gate; 王老师, his Chinese teacher and 小雨's mother;
李奶奶, the grandmother downstairs who sings every morning.
"""
import datetime
import html
import json
import re
import sys

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))
from check_vocab import allowed_words, split_run  # noqa: E402

URL = "/reading/"
TH_URL = "/th/reading/"
LEVELS = (1, 2, 3, 4, 5)
SLUG = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
HAN = re.compile(r"[㐀-鿿豈-﫿]+")
REQUIRED = ("slug", "level", "episode", "published", "title", "title_en", "title_th", "names", "paras", "questions")

UI = {
    "en": {
        "eyebrow": "Graded reading", "words": "characters", "min": "min read",
        "listen": "Listen", "stop": "Stop", "tapHint": "Tap any word for its pinyin and meaning.",
        "qTitle": "Check your understanding", "right": "Right!", "wrong": "Not quite. Try again.",
        "addTitle": "Learn the words from this story",
        "addText": "Add the {n} HSK {lv} words in this story to your flashcards. They come up first in your next session.",
        "addBtn": "Add to my flashcards", "added": "Added. Open your flashcards to study them.", "open": "Open flashcards",
        "more": "More HSK {lv} stories", "all": "All stories", "next": "Next story",
        "name": "name", "notInList": "not on the HSK lists", "level": "HSK {lv}",
        "indexTitle": "HSK Graded Reading: Short Chinese Stories for HSK 1–5",
        "indexDesc": "Free short Chinese stories written for each HSK 3.0 level. Every word stays within the level; tap any "
                     "word for pinyin and meaning, then add the new words to your flashcards.",
        "indexH1": "Graded Reading", "indexLede": "Short stories written for each HSK level. Every word is checked against "
                                                    "the HSK 3.0 lists, so nothing is above your level. Tap a word to see "
                                                    "what it means.",
        "cast": "The same characters appear in every story: 大卫 (Dàwèi), a student from Britain learning Chinese, and "
                "小雨 (Xiǎoyǔ), who works at the milk tea shop by his school gate.",
        "none": "Stories for this level are coming soon.",
        "flash": "/hsk-flashcards/", "home": "/",
    },
    "th": {
        "eyebrow": "อ่านตามระดับ", "words": "ตัวอักษร", "min": "นาที",
        "listen": "ฟังเสียง", "stop": "หยุด", "tapHint": "แตะคำไหนก็ได้เพื่อดูพินอินและความหมาย",
        "qTitle": "ทดสอบความเข้าใจ", "right": "ถูกต้อง!", "wrong": "ยังไม่ใช่ ลองอีกครั้ง",
        "addTitle": "เรียนคำศัพท์จากเรื่องนี้",
        "addText": "เพิ่มคำศัพท์ HSK {lv} จำนวน {n} คำจากเรื่องนี้ลงในแฟลชการ์ด คำเหล่านี้จะขึ้นมาก่อนในการทบทวนครั้งต่อไป",
        "addBtn": "เพิ่มลงแฟลชการ์ดของฉัน", "added": "เพิ่มแล้ว เปิดแฟลชการ์ดเพื่อเริ่มท่องได้เลย", "open": "เปิดแฟลชการ์ด",
        "more": "เรื่องอื่นระดับ HSK {lv}", "all": "เรื่องทั้งหมด", "next": "เรื่องถัดไป",
        "name": "ชื่อเฉพาะ", "notInList": "ไม่อยู่ในรายการ HSK", "level": "HSK {lv}",
        "indexTitle": "อ่านภาษาจีนตามระดับ HSK เรื่องสั้นสำหรับ HSK 1–5 พร้อมคำแปลไทย",
        "indexDesc": "เรื่องสั้นภาษาจีนฟรีที่เขียนตามระดับ HSK 3.0 ทุกคำไม่เกินระดับ แตะคำเพื่อดูพินอินและความหมายภาษาไทย "
                     "แล้วเพิ่มคำใหม่ลงแฟลชการ์ด",
        "indexH1": "อ่านตามระดับ", "indexLede": "เรื่องสั้นที่เขียนสำหรับแต่ละระดับ HSK ทุกคำตรวจกับรายการคำศัพท์ HSK 3.0 "
                                               "จึงไม่มีคำเกินระดับ แตะคำเพื่อดูความหมาย",
        "cast": "ทุกเรื่องมีตัวละครชุดเดิม: 大卫 (Dàwèi) นักศึกษาชาวอังกฤษที่มาเรียนภาษาจีน และ 小雨 (Xiǎoyǔ) "
                "ที่ทำงานในร้านชานมหน้าประตูโรงเรียน",
        "none": "เรื่องของระดับนี้กำลังจะมา",
        "flash": "/th/hsk-flashcards/", "home": "/th/",
    },
}


def load(root):
    folder = root / "data" / "stories"
    stories = []
    for path in sorted(folder.glob("*.json")) if folder.exists() else []:
        d = json.loads(path.read_text(encoding="utf-8"))
        missing = [k for k in REQUIRED if k not in d]
        if missing:
            raise SystemExit(f"{path.name}: missing {missing}")
        if d["slug"] != path.stem or not SLUG.match(d["slug"]):
            raise SystemExit(f"{path.name}: slug must match the file name")
        if d["level"] not in LEVELS:
            raise SystemExit(f"{path.name}: level must be 1-5")
        datetime.date.fromisoformat(d["published"])
        for q in d["questions"]:
            if not (0 <= q["answer"] < len(q["options"])):
                raise SystemExit(f"{path.name}: answer out of range in {q['q']}")
        stories.append(d)
    stories.sort(key=lambda d: (d["level"], d["episode"]))
    seen = set()
    for d in stories:
        if (d["level"], d["episode"]) in seen:
            raise SystemExit(f"{d['slug']}: duplicate episode {d['episode']} at HSK {d['level']}")
        seen.add((d["level"], d["episode"]))
    return stories


def tokenize(text, words, max_len):
    """[(piece, known)] for a paragraph; non-Chinese runs come back as (text, None)."""
    out, pos = [], 0
    for m in HAN.finditer(text):
        if m.start() > pos:
            out.append((text[pos:m.start()], None))
        out += split_run(m.group(0), words, max_len)
        pos = m.end()
    if pos < len(text):
        out.append((text[pos:], None))
    return out


def check(story):
    words = allowed_words(story["level"]) | set(story["names"])
    max_len = max(len(w) for w in words)
    texts = story["paras"] + [q["q"] for q in story["questions"]] + [o for q in story["questions"] for o in q["options"]]
    bad = [p for t in texts for p, k in tokenize(t, words, max_len) if k is False]
    if bad:
        raise SystemExit(f"story {story['slug']} (HSK {story['level']}) uses words above its level: "
                         + " ".join(dict.fromkeys(bad)))
    return words, max_len


def dictionary(root, thai):
    """word -> (pinyin, meaning, level) for HSK 1-5; meanings in Thai where `thai` has them."""
    table = {}
    for n in LEVELS:
        path = root / "data" / f"hsk{n}.tsv"
        if not path.exists():
            continue
        for i, line in enumerate(l for l in path.read_text(encoding="utf-8").splitlines() if l.strip()):
            w, p, en = [x.strip() for x in line.split("\t")]
            m = thai.get(n, [None] * 99999)[i] if n in thai else None
            table.setdefault(w, (p, m or en, n))
    for w, v in list(table.items()):
        if len(w) >= 3 and w.endswith("儿"):
            table.setdefault(w[:-1], v)
    return table


def zh_inline(text):
    return HAN.sub(lambda m: f'<span class="zh-inline">{m.group(0)}</span>', html.escape(text))


def story_page(story, lang, dic, nav_html, prev_next):
    ui = UI[lang]
    base = TH_URL if lang == "th" else URL
    words, max_len = check(story)
    used = {}
    paras = []
    level_words = []
    for para in story["paras"]:
        bits = []
        for piece, known in tokenize(para, words, max_len):
            if known is None:
                bits.append(html.escape(piece))
                continue
            bits.append(f'<span class="w" tabindex="0">{html.escape(piece)}</span>')
            if piece in dic:
                used[piece] = list(dic[piece])
                if dic[piece][2] == story["level"] and piece not in level_words:
                    level_words.append(piece)
            elif piece in story["names"]:
                used[piece] = ["", ui["name"], 0]
        paras.append('<p class="st-p" lang="zh-Hans">' + "".join(bits) + "</p>")
    chars = sum(len(m) for p in story["paras"] for m in HAN.findall(p))
    minutes = max(1, round(chars / 120))
    title_local = story["title_th"] if lang == "th" else story["title_en"]
    qs = []
    for i, q in enumerate(story["questions"]):
        opts = "".join(f'<button type="button" class="st-opt" data-q="{i}" data-ok="{1 if j == q["answer"] else 0}">'
                       f'<span lang="zh-Hans">{html.escape(o)}</span></button>' for j, o in enumerate(q["options"]))
        qs.append(f'<li><p class="st-q" lang="zh-Hans">{html.escape(q["q"])}</p><div class="st-opts">{opts}</div>'
                  f'<p class="st-fb" id="fb{i}" aria-live="polite"></p></li>')
    more = []
    for s in prev_next:
        t = s["title_th"] if lang == "th" else s["title_en"]
        more.append(f'<li><a href="{base}{s["slug"]}/"><span class="zh-inline">{html.escape(s["title"])}</span> '
                    f'<span class="st-more-en">{html.escape(t)}</span></a></li>')
    more_html = (f'<section class="sheet" aria-labelledby="more-title"><h2 id="more-title">'
                 f'{ui["more"].format(lv=story["level"])}</h2><ul class="st-more">{"".join(more)}</ul>'
                 f'<p class="st-all"><a href="{base}">{ui["all"]} →</a></p></section>') if more else (
                 f'<p class="st-all"><a href="{base}">{ui["all"]} →</a></p>')
    add_html = ""
    if level_words:
        add_html = (f'<section class="sheet st-add" aria-labelledby="add-title"><h2 id="add-title">{ui["addTitle"]}</h2>'
                    f'<p>{ui["addText"].format(n=len(level_words), lv=story["level"])}</p>'
                    f'<p class="st-add-words" lang="zh-Hans">{"、".join(html.escape(w) for w in level_words)}</p>'
                    f'<div class="st-add-row"><button type="button" class="button" id="add-btn">{ui["addBtn"]}</button>'
                    f'<a class="st-open" href="{ui["flash"]}#hsk{story["level"]}" id="open-link" hidden>{ui["open"]} →</a></div>'
                    f'<p class="st-added" id="added" hidden>{ui["added"]}</p></section>')
    data = json.dumps({"level": story["level"], "words": level_words, "dict": used, "text": "".join(story["paras"])},
                      ensure_ascii=False, separators=(",", ":"))
    js_ui = json.dumps({k: ui[k] for k in ("listen", "stop", "right", "wrong", "notInList", "level")}, ensure_ascii=False)
    body = f'''<div class="wrap">
  <header>
    {nav_html}
    <div class="eyebrow"><span>{ui["eyebrow"]}</span><span class="chip">HSK {story["level"]}</span><span class="chip">{chars} {ui["words"]} · {minutes} {ui["min"]}</span></div>
    <h1><span class="zh">{html.escape(story["title"])}</span>{html.escape(title_local)}</h1>
  </header>

  <section class="sheet st-sheet" aria-label="{html.escape(title_local)}">
    <div class="st-tools"><p class="st-hint">{ui["tapHint"]}</p><button type="button" class="ghost" id="listen-btn" hidden>{ui["listen"]}</button></div>
    <div class="st-text">
{chr(10).join("      " + p for p in paras)}
    </div>
  </section>

  <section class="sheet" aria-labelledby="q-title">
    <h2 id="q-title">{ui["qTitle"]}</h2>
    <ol class="st-qs">{"".join(qs)}</ol>
  </section>

  {add_html}

  {more_html}
</div>

<div class="st-pop" id="pop" role="dialog" aria-live="polite" hidden>
  <button type="button" class="st-pop-x" id="pop-x" aria-label="Close">×</button>
  <div class="st-pop-w" lang="zh-Hans" id="pop-w"></div><div class="st-pop-p" id="pop-p"></div>
  <div class="st-pop-m" id="pop-m"></div><div class="st-pop-l" id="pop-l"></div>
</div>

<script>
const STORY = {data};
const T = {js_ui};
const KEY = "hskcheck-flashcards-v1";
const pop = document.getElementById("pop");
function esc(s) {{ return String(s).replace(/[&<>"]/g, c => ({{ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }}[c])); }}
function voice() {{ return ("speechSynthesis" in window) ? speechSynthesis.getVoices().find(v => /^zh(-|_)?(CN|Hans)?/i.test(v.lang)) || null : null; }}
function speak(text, rate) {{ const v = voice(); if (!v) return; const u = new SpeechSynthesisUtterance(text); u.voice = v; u.lang = v.lang; u.rate = rate || 0.85; speechSynthesis.cancel(); speechSynthesis.speak(u); return u; }}
let openEl = null;
function showWord(el) {{
  const w = el.textContent, d = STORY.dict[w];
  if (openEl) openEl.classList.remove("on");
  openEl = el; el.classList.add("on");
  document.getElementById("pop-w").textContent = w;
  document.getElementById("pop-p").textContent = d ? d[0] : "";
  document.getElementById("pop-m").textContent = d ? d[1] : T.notInList;
  document.getElementById("pop-l").textContent = d && d[2] ? T.level.replace("{{lv}}", d[2]) : "";
  pop.hidden = false;
  speak(w);
}}
document.querySelectorAll(".st-text .w").forEach(el => {{
  el.addEventListener("click", () => showWord(el));
  el.addEventListener("keydown", e => {{ if (e.key === "Enter" || e.key === " ") {{ e.preventDefault(); showWord(el); }} }});
}});
document.getElementById("pop-x").addEventListener("click", () => {{ pop.hidden = true; if (openEl) openEl.classList.remove("on"); }});
document.addEventListener("keydown", e => {{ if (e.key === "Escape") {{ pop.hidden = true; }} }});

const lb = document.getElementById("listen-btn");
let speaking = false;
function setupListen() {{ if (voice()) lb.hidden = false; }}
setupListen();
if ("speechSynthesis" in window) speechSynthesis.onvoiceschanged = setupListen;
lb.addEventListener("click", () => {{
  if (speaking) {{ speechSynthesis.cancel(); speaking = false; lb.textContent = T.listen; return; }}
  const u = speak(STORY.text, 0.8); if (!u) return;
  speaking = true; lb.textContent = T.stop;
  u.onend = () => {{ speaking = false; lb.textContent = T.listen; }};
}});

document.querySelectorAll(".st-opt").forEach(b => b.addEventListener("click", () => {{
  const fb = document.getElementById("fb" + b.dataset.q), ok = b.dataset.ok === "1";
  b.classList.add(ok ? "ok" : "no");
  fb.textContent = ok ? T.right : T.wrong;
  fb.className = "st-fb " + (ok ? "ok" : "no");
  if (ok) b.parentNode.querySelectorAll(".st-opt").forEach(x => x.disabled = true);
}}));

const addBtn = document.getElementById("add-btn");
if (addBtn) addBtn.addEventListener("click", () => {{
  let s = null;
  try {{ s = JSON.parse(localStorage.getItem(KEY) || "null"); }} catch (e) {{}}
  if (!s || !s.lv) s = {{ lv: {{}}, intro: {{}}, streak: {{ last: -1, n: 0 }}, set: {{ newPerDay: 10, pinyin: false, level: STORY.level }} }};
  s.boost = s.boost || {{}};
  const list = s.boost[STORY.level] || [];
  STORY.words.forEach(w => {{ if (!list.includes(w)) list.push(w); }});
  s.boost[STORY.level] = list;
  s.set.level = STORY.level; s.set.chosen = true;
  try {{ localStorage.setItem(KEY, JSON.stringify(s)); }} catch (e) {{}}
  addBtn.hidden = true;
  document.getElementById("added").hidden = false;
  document.getElementById("open-link").hidden = false;
}});
</script>'''
    return body, level_words


def index_page(stories, lang, nav_html):
    ui = UI[lang]
    base = TH_URL if lang == "th" else URL
    secs = []
    for n in LEVELS:
        items = [s for s in stories if s["level"] == n]
        if items:
            lis = "".join(
                f'<li><a href="{base}{s["slug"]}/"><span class="st-ep">{s["episode"]}</span>'
                f'<span class="zh-inline st-t">{html.escape(s["title"])}</span>'
                f'<span class="st-more-en">{html.escape(s["title_th"] if lang == "th" else s["title_en"])}</span></a></li>'
                for s in sorted(items, key=lambda s: -s["episode"]))
            inner = f'<ul class="st-list">{lis}</ul>'
        else:
            inner = f'<p class="empty">{ui["none"]}</p>'
        secs.append(f'<section class="sheet" id="hsk{n}" aria-labelledby="h{n}"><h2 id="h{n}">HSK {n}</h2>{inner}</section>')
    return f'''<div class="wrap">
  <header>
    {nav_html}
    <div class="eyebrow"><span>{ui["eyebrow"]}</span><span class="chip">HSK 1–5</span></div>
    <h1><span class="zh">阅读</span>{ui["indexH1"]}</h1>
    <p class="lede">{ui["indexLede"]}</p>
    <p class="lede">{zh_inline(ui["cast"])}</p>
  </header>
  {"".join(secs)}
</div>'''


def build(root, pages, nav, render, base_css, tpl, site):
    """English pages. Returns URLs."""
    stories = load(root)
    if not stories:
        return []
    dic = dictionary(root, {})
    css = base_css + (tpl / "reading.css").read_text(encoding="utf-8")
    urls = []
    for s in stories:
        same = [x for x in stories if x["level"] == s["level"] and x["slug"] != s["slug"]]
        url = f"{URL}{s['slug']}/"
        body, _ = story_page(s, "en", dic, nav(pages, URL), same[-6:])
        desc = (f"A short HSK {s['level']} Chinese story, {s['title']} ({s['title_en']}). Every word is HSK {s['level']} or "
                f"below; tap any word for pinyin and meaning, then check your understanding.")
        out = render(f"HSK {s['level']} Reading: {s['title']} ({s['title_en']}) | Graded Chinese Story", desc,
                     site + url, css, body)
        (root / url.strip("/")).mkdir(parents=True, exist_ok=True)
        (root / url.strip("/") / "index.html").write_text(out, encoding="utf-8")
        urls.append(url)
    ui = UI["en"]
    (root / URL.strip("/") / "index.html").write_text(
        render(ui["indexTitle"], ui["indexDesc"], site + URL, css, index_page(stories, "en", nav(pages, URL))),
        encoding="utf-8")
    latest = {n: [{"slug": s["slug"], "title": s["title"], "en": s["title_en"], "th": s["title_th"]}
                  for s in sorted([x for x in stories if x["level"] == n], key=lambda x: -x["episode"])]
              for n in LEVELS}
    (root / URL.strip("/") / "index.json").write_text(json.dumps(latest, ensure_ascii=False, separators=(",", ":")),
                                                      encoding="utf-8")
    return [URL] + urls


def build_th(*, root, tpl, site, render, nav, font_link, foot, base_css, th_css, thai):
    stories = load(root)
    if not stories:
        return []
    dic = dictionary(root, thai)
    css = base_css + (tpl / "reading.css").read_text(encoding="utf-8") + th_css
    urls = []
    for s in stories:
        same = [x for x in stories if x["level"] == s["level"] and x["slug"] != s["slug"]]
        url = f"{TH_URL}{s['slug']}/"
        body, _ = story_page(s, "th", dic, nav(TH_URL), same[-6:])
        desc = (f"เรื่องสั้นภาษาจีนระดับ HSK {s['level']}: {s['title']} ({s['title_th']}) ทุกคำไม่เกินระดับ HSK {s['level']} "
                f"แตะคำเพื่อดูพินอินและความหมายภาษาไทย")
        out = render(f"อ่านภาษาจีน HSK {s['level']}: {s['title']} ({s['title_th']})", desc, site + url, css, body,
                     font_link, lang="th", foot=foot)
        (root / url.strip("/")).mkdir(parents=True, exist_ok=True)
        (root / url.strip("/") / "index.html").write_text(out, encoding="utf-8")
        urls.append(url)
    ui = UI["th"]
    (root / TH_URL.strip("/")).mkdir(parents=True, exist_ok=True)
    (root / TH_URL.strip("/") / "index.html").write_text(
        render(ui["indexTitle"], ui["indexDesc"], site + TH_URL, css, index_page(stories, "th", nav(TH_URL)),
               font_link, lang="th", foot=foot), encoding="utf-8")
    return [TH_URL] + urls


def alternates(root):
    stories = load(root)
    if not stories:
        return {}
    pairs = {URL: TH_URL}
    pairs.update({f"{URL}{s['slug']}/": f"{TH_URL}{s['slug']}/" for s in stories})
    return pairs
