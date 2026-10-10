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
    ]
  }

Text fields are plain text: Chinese in them is wrapped for the Chinese font, nothing else
is treated as HTML. The build stops if any example sentence uses a word above the page's
level, judged with the same splitter as tools/check_vocab.py and the level checker.
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
        pages.append(p)
    pages.sort(key=lambda p: (p["level"], p["published"], p["slug"]))
    return pages


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


def build(pages_nav, nav, render, base_css, tpl_dir, site):
    """Write /learn/ and one page per JSON file. Returns the URLs written."""
    pages = load_pages()
    if not pages:
        return []
    css = base_css + (tpl_dir / "learn.css").read_text(encoding="utf-8")
    body_tpl = (tpl_dir / "learn_body.html").read_text(encoding="utf-8")
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
                .replace("__MORE__", f'<ul class="more">{more}</ul>' if more else ""))
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
