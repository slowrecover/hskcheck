"""Grammar and usage explainers at /learn/<slug>/, built from data/learn/<slug>.json.

Each JSON file:
  {
    "slug": "ba-sentences",            same as the file name
    "level": 3,                        HSK 3.0 level the page is written for (1-3)
    "published": "2026-10-10",
    "title": "...",                    <title>, under ~65 characters
    "description": "...",              meta description, under ~160 characters
    "zh": "把",                        the word or pattern, shown large in the heading
    "h1": "...",                       English heading
    "lede": "...",                     one or two sentences under the heading
    "sections": [
      {"h2": "...", "paras": ["..."], "examples": [{"zh": "...", "py": "...", "en": "..."}]}
    ],
    "worksheet": {                     optional: a printable worksheet at /learn/<slug>/worksheet/
      "title": "...", "description": "...",
      "exercises": [
        {"type": "choose", "h2": "...", "instructions": "...", "options": ["不", "没有"],
         "items": [{"zh": "我昨天＿＿去学校。", "en": "...", "answer": "没有"}]},
        {"type": "order", "h2": "...", "instructions": "...",
         "items": [{"words": ["钱", "没有", "我"], "en": "...", "answers": ["我没有钱。"]}]},
        {"type": "fix", "h2": "...", "instructions": "...",
         "items": [{"zh": "我不有哥哥。", "en": "...", "answers": ["我没有哥哥。"]}]}
      ]
    }
  }

Text fields are plain text: Chinese in them is wrapped for the Chinese font, nothing else
is treated as HTML. The build stops if any example sentence uses a word above the page's
level, judged with the same splitter as tools/check_vocab.py and the level checker.
Worksheet sentences (filled-in gaps, answers and the sentences to fix) are checked the same
way; ＿＿ marks the gap in a "choose" item, and an "order" item's words must make up each answer.
"""
import datetime
import html
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from check_vocab import allowed_words, check  # noqa: E402

LEARN_URL = "/learn/"
SLUG = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
HAN_RUN = re.compile(r"[㐀-鿿，。：！？、“”]+")
REQUIRED = ("slug", "level", "published", "title", "description", "zh", "h1", "lede", "sections")


def zh_spans(text):
    return HAN_RUN.sub(lambda m: f'<span class="zh-inline">{m.group(0)}</span>', html.escape(text))


def load_pages():
    folder = ROOT / "data" / "learn"
    if not folder.exists():
        return []
    vocab = {n: allowed_words(n) for n in (1, 2, 3)}
    pages = []
    for path in sorted(folder.glob("*.json")):
        p = json.loads(path.read_text(encoding="utf-8"))
        name = path.name
        missing = [k for k in REQUIRED if not p.get(k)]
        if missing:
            raise SystemExit(f"data/learn/{name}: missing {missing}")
        if p["slug"] != path.stem or not SLUG.match(p["slug"]):
            raise SystemExit(f"data/learn/{name}: slug must be lowercase-with-dashes and match the file name")
        if p["level"] not in (1, 2, 3):
            raise SystemExit(f"data/learn/{name}: level must be 1, 2 or 3")
        datetime.date.fromisoformat(p["published"])
        words = vocab[p["level"]]
        max_len = max(len(w) for w in words)
        n_examples = 0
        for s in p["sections"]:
            if not s.get("h2") or not (s.get("paras") or s.get("examples")):
                raise SystemExit(f"data/learn/{name}: every section needs h2 and paras or examples")
            for ex in s.get("examples", []):
                if not all(ex.get(k) for k in ("zh", "py", "en")):
                    raise SystemExit(f"data/learn/{name}: every example needs zh, py and en")
                tokens, bad = check(ex["zh"], words, max_len)
                if bad:
                    raise SystemExit(f"data/learn/{name}: example above HSK {p['level']}: {ex['zh']}  "
                                     f"({' / '.join(tokens)})")
                n_examples += 1
        if n_examples < 6:
            raise SystemExit(f"data/learn/{name}: needs at least 6 example sentences, has {n_examples}")
        if p.get("worksheet"):
            check_worksheet(p["worksheet"], words, max_len, name, p["level"])
        pages.append(p)
    pages.sort(key=lambda p: (p["level"], p["published"], p["slug"]))
    return pages


BLANK = "＿＿"
PUNCT = re.compile(r"[，。：！？、“”\s]")


def check_worksheet(w, words, max_len, name, level):
    def vocab(sentence):
        tokens, bad = check(sentence, words, max_len)
        if bad:
            raise SystemExit(f"data/learn/{name}: worksheet sentence above HSK {level}: {sentence}  "
                             f"({' / '.join(tokens)})")

    for k in ("title", "description", "exercises"):
        if not w.get(k):
            raise SystemExit(f"data/learn/{name}: worksheet needs {k}")
    for ex in w["exercises"]:
        kind = ex.get("type")
        if kind not in ("choose", "order", "fix") or not ex.get("h2") or not ex.get("items"):
            raise SystemExit(f"data/learn/{name}: worksheet exercises need type (choose/order/fix), h2 and items")
        for it in ex["items"]:
            if not it.get("en"):
                raise SystemExit(f"data/learn/{name}: every worksheet item needs en")
            if kind == "choose":
                if it.get("zh", "").count(BLANK) != 1 or it.get("answer") not in ex.get("options", []):
                    raise SystemExit(f"data/learn/{name}: choose item needs one {BLANK} and an answer from options: {it}")
                vocab(it["zh"].replace(BLANK, it["answer"]))
            else:
                if not it.get("answers"):
                    raise SystemExit(f"data/learn/{name}: {kind} item needs answers: {it}")
                for a in it["answers"]:
                    vocab(a)
                    if kind == "order" and sorted(PUNCT.sub("", a)) != sorted("".join(it.get("words", []))):
                        raise SystemExit(f"data/learn/{name}: order item words don't make up the answer {a}")
                if kind == "fix":
                    vocab(it.get("zh", ""))


def worksheet_html(p):
    """The paper: exercises, then the answer key on its own page."""
    w = p["worksheet"]
    letters = "ABCDEFGH"
    parts, keys = [], []
    for i, ex in enumerate(w["exercises"]):
        head = (f'<div class="ws-ex"><h3><span class="ws-letter">{letters[i]}</span>{zh_spans(ex["h2"])}</h3>'
                f'<p class="ws-inst">{zh_spans(ex.get("instructions", ""))}</p><ol class="ws-items">')
        items, ans = [], []
        for it in ex["items"]:
            en = f'<span class="ws-en">{html.escape(it["en"])}</span>'
            if ex["type"] == "choose":
                before, after = (html.escape(x) for x in it["zh"].split(BLANK))
                opts = " / ".join(html.escape(o) for o in ex["options"])
                items.append(f'<li><span class="ws-zh" lang="zh-Hans">{before}<span class="ws-gap"></span>{after}</span>'
                             f'<span class="ws-opts" lang="zh-Hans">（{opts}）</span>{en}</li>')
                ans.append(f'<li lang="zh-Hans">{html.escape(it["answer"])}</li>')
            else:
                if ex["type"] == "order":
                    shown = "".join(f'<span class="ws-word">{html.escape(x)}</span>' for x in it["words"])
                    shown = f'<span class="ws-words" lang="zh-Hans">{shown}</span>'
                else:
                    shown = f'<span class="ws-zh" lang="zh-Hans">{html.escape(it["zh"])}</span>'
                items.append(f'<li>{shown}{en}<span class="ws-line"></span></li>')
                ans.append(f'<li lang="zh-Hans">{" / ".join(html.escape(a) for a in it["answers"])}</li>')
        parts.append(head + "".join(items) + "</ol></div>")
        keys.append(f'<div class="ws-key-ex"><h4>{letters[i]}</h4><ol>{"".join(ans)}</ol></div>')
    return "\n".join(parts), "\n".join(keys)


def section_html(s):
    out = [f'  <section class="sheet learn">', f"    <h2>{html.escape(s['h2'])}</h2>"]
    for para in s.get("paras", []):
        out.append(f"    <p>{zh_spans(para)}</p>")
    if s.get("examples"):
        out.append('    <ol class="examples">')
        for ex in s["examples"]:
            out.append(
                f'      <li><span class="ex-zh" lang="zh-Hans">{html.escape(ex["zh"])}</span>'
                f'<span class="ex-py">{html.escape(ex["py"])}</span>'
                f'<span class="ex-en">{html.escape(ex["en"])}</span></li>'
            )
        out.append("    </ol>")
    out.append("  </section>")
    return "\n".join(out)


def worksheet_cta(p, url):
    if not p.get("worksheet"):
        return ""
    n = sum(len(ex["items"]) for ex in p["worksheet"]["exercises"])
    return ('<section class="sheet learn">\n    <h2>Printable worksheet</h2>\n'
            f'    <p>Practise this grammar point on paper: {n} exercises using only HSK {p["level"]} words, '
            'with an answer key on a separate page. Free to print and copy for your class.</p>\n'
            f'    <div class="cta"><a class="button" href="{url}worksheet/">Open the worksheet</a>'
            f'<a class="button ghost" href="{url}practice/">Practise online</a></div>\n  </section>\n')


def write_worksheet(p, url, tpl, css, nav, pages_nav, render, site):
    w = p["worksheet"]
    ws_url = f"{url}worksheet/"
    exercises, key = worksheet_html(p)
    n = sum(len(ex["items"]) for ex in w["exercises"])
    body = (tpl.replace("__NAV__", nav(pages_nav, LEARN_URL))
            .replace("__LEVEL__", str(p["level"]))
            .replace("__ZH__", html.escape(p["zh"]))
            .replace("__COUNT__", str(n))
            .replace("__URL__", url)
            .replace("__SITE_URL__", (site + url).replace("https://", ""))
            .replace("__EXERCISES__", exercises)
            .replace("__KEY__", key))
    ld = json.dumps({
        "@context": "https://schema.org", "@type": "LearningResource", "name": w["title"],
        "description": w["description"], "learningResourceType": "Worksheet",
        "educationalLevel": f"HSK {p['level']}", "inLanguage": ["en", "zh-Hans"], "isAccessibleForFree": True,
        "url": site + ws_url, "isPartOf": site + url,
        "publisher": {"@type": "Organization", "name": "hskcheck.com", "url": site + "/"},
    }, ensure_ascii=False)
    target = ROOT / ws_url.strip("/")
    target.mkdir(parents=True, exist_ok=True)
    (target / "index.html").write_text(
        render(w["title"], w["description"], site + ws_url, css, body,
               f'<script type="application/ld+json">{ld}</script>'),
        encoding="utf-8")
    return ws_url


def build(pages_nav, nav, render, base_css, tpl_dir, site):
    """Write /learn/ and one page per JSON file. Returns the URLs written."""
    pages = load_pages()
    if not pages:
        return []
    css = base_css + (tpl_dir / "learn.css").read_text(encoding="utf-8")
    body_tpl = (tpl_dir / "learn_body.html").read_text(encoding="utf-8")
    ws_css = base_css + (tpl_dir / "learn_worksheet.css").read_text(encoding="utf-8")
    ws_tpl = (tpl_dir / "learn_worksheet_body.html").read_text(encoding="utf-8")
    urls = []
    for p in pages:
        url = f"{LEARN_URL}{p['slug']}/"
        lv = p["level"]
        others = [q for q in pages if q is not p]
        others.sort(key=lambda q: (q["level"] != lv, abs(q["level"] - lv), q["slug"]))
        more = "".join(
            f'<li><a href="{LEARN_URL}{q["slug"]}/"><span class="zh-inline">{html.escape(q["zh"])}</span> '
            f'{html.escape(q["h1"])}</a> <span class="lv">HSK {q["level"]}</span></li>'
            for q in others[:6]
        )
        body = (body_tpl.replace("__NAV__", nav(pages_nav, LEARN_URL))
                .replace("__LEVEL__", str(lv))
                .replace("__ZH__", html.escape(p["zh"]))
                .replace("__H1__", html.escape(p["h1"]))
                .replace("__LEDE__", zh_spans(p["lede"]))
                .replace("__SECTIONS__", "\n".join(section_html(s) for s in p["sections"]))
                .replace("__MORE__", f'<ul class="more">{more}</ul>' if more else "")
                .replace("__WORKSHEET__", worksheet_cta(p, url)))
        ld = json.dumps({
            "@context": "https://schema.org", "@type": "Article", "headline": p["title"],
            "description": p["description"], "datePublished": p["published"],
            "inLanguage": "en", "about": "Chinese grammar (HSK 3.0)", "url": site + url,
            "publisher": {"@type": "Organization", "name": "hskcheck.com", "url": site + "/"},
        }, ensure_ascii=False)
        target = ROOT / url.strip("/")
        target.mkdir(parents=True, exist_ok=True)
        (target / "index.html").write_text(
            render(p["title"], p["description"], site + url, css, body,
                   f'<script type="application/ld+json">{ld}</script>'),
            encoding="utf-8")
        urls.append(url)
        if p.get("worksheet"):
            urls.append(write_worksheet(p, url, ws_tpl, ws_css, nav, pages_nav, render, site))

    # Index
    groups = []
    for lv in (1, 2, 3):
        items = [p for p in pages if p["level"] == lv]
        if not items:
            continue
        lis = "".join(
            f'<li><a href="{LEARN_URL}{p["slug"]}/"><span class="zh-inline">{html.escape(p["zh"])}</span> '
            f'{html.escape(p["h1"])}</a></li>' for p in items
        )
        groups.append(f'  <section class="sheet learn"><h2>HSK {lv}</h2><ul class="more">{lis}</ul></section>')
    body = (tpl_dir / "learn_index_body.html").read_text(encoding="utf-8")
    body = (body.replace("__NAV__", nav(pages_nav, LEARN_URL))
            .replace("__COUNT__", str(len(pages)))
            .replace("__GROUPS__", "\n".join(groups)))
    target = ROOT / LEARN_URL.strip("/")
    target.mkdir(exist_ok=True)
    (target / "index.html").write_text(render(
        "HSK Grammar Explained: HSK 1-3 Grammar Points with Examples",
        "Short, clear explanations of HSK 1-3 grammar points in the HSK 3.0 syllabus. "
        "Every example sentence uses only words from that level.",
        site + LEARN_URL, css, body), encoding="utf-8")
    return urls
