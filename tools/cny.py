"""Chinese New Year greetings page, built to /chinese-new-year-greetings/ from data/cny.json.

data/cny.json holds the page text: title, description, h1, zh, lede and sections, each with
h2, paras (HTML allowed) and optional examples {"zh", "py", "en", "keys"}. "keys" are the words in
the example to tag with their HSK 3.0 level (HSK 1-5 word lists); the build stops if a key is not
in the example. Keys outside HSK 1-5 are shown as "beyond HSK 5".
"""
import html
import json

URL = "/chinese-new-year-greetings/"

CSS = """
.learn p { margin: 0; max-width: 68ch; }
.examples { list-style: none; margin: 0; padding: 0; display: grid; }
.examples li { display: grid; gap: 3px; padding: 12px 0; border-top: 1px solid var(--rule); }
.examples li:first-child { border-top: 0; padding-top: 2px; }
.ex-zh { font-family: var(--f-zh); font-size: 22px; line-height: 1.5; }
.ex-py { color: var(--accent); font-size: 14px; }
.ex-en { color: var(--muted); font-size: 14px; }
.words { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 4px; }
.words a, .words span { font-size: 12px; text-decoration: none; border-radius: 999px; padding: 1px 8px; }
.words .zh-inline { font-size: 13px; margin-right: 3px; }
.words .w1 { color: var(--l1); background: var(--l1-bg); }
.words .w2 { color: var(--l2); background: var(--l2-bg); }
.words .w3 { color: var(--l3); background: var(--l3-bg); }
.words .w4 { color: var(--l4); background: var(--l4-bg); }
.words .w5 { color: var(--l5); background: var(--l5-bg); }
.words .w0 { color: var(--muted); border: 1px solid var(--rule); }
.cta { display: flex; gap: 10px; align-items: center; flex-wrap: wrap; }
.cta a.button { display: inline-block; text-decoration: none; font: 500 14px var(--f-ui); padding: 9px 16px; border-radius: 999px; background: var(--accent); color: var(--accent-ink); }
.cta a.button.ghost { background: transparent; color: var(--accent); border: 1px solid var(--accent); }
"""


def _levels(root):
    levels = {}
    for n in (5, 4, 3, 2, 1):  # lowest level wins
        path = root / "data" / f"hsk{n}.tsv"
        if path.exists():
            for line in path.read_text(encoding="utf-8").splitlines():
                word = line.split("\t")[0].strip()
                if word:
                    levels[word] = n
    return levels


def _chips(keys, levels):
    out = []
    for k in keys:
        n = levels.get(k)
        if n:
            out.append(f'<a class="w{n}" href="/hsk-{n}-word-list/"><span class="zh-inline">{html.escape(k)}</span>HSK {n}</a>')
        else:
            out.append(f'<span class="w0"><span class="zh-inline">{html.escape(k)}</span>beyond HSK 5</span>')
    return f'<span class="words">{"".join(out)}</span>' if out else ""


def build(root, pages, nav, render, base_css, tpl, site):
    data = json.loads((root / "data" / "cny.json").read_text(encoding="utf-8"))
    levels = _levels(root)
    parts = []
    for s in data["sections"]:
        out = ['  <section class="sheet learn">', f"    <h2>{html.escape(s['h2'])}</h2>"]
        out += [f"    <p>{p}</p>" for p in s.get("paras", [])]
        if s.get("examples"):
            out.append('    <ol class="examples">')
            for ex in s["examples"]:
                for k in ex.get("keys", []):
                    if k not in ex["zh"]:
                        raise SystemExit(f"data/cny.json: key {k} is not in {ex['zh']}")
                out.append(
                    f'      <li><span class="ex-zh" lang="zh-Hans">{html.escape(ex["zh"])}</span>'
                    f'<span class="ex-py">{html.escape(ex["py"])}</span>'
                    f'<span class="ex-en">{html.escape(ex["en"])}</span>{_chips(ex.get("keys", []), levels)}</li>')
            out.append("    </ol>")
        out.append("  </section>")
        parts.append("\n".join(out))
    parts.append(
        '  <section class="sheet learn">\n    <h2>Learn the words behind the greetings</h2>\n'
        "    <p>Tap a coloured word above to open its HSK word list. To check a message you wrote yourself, "
        "paste it into the level checker and see which words are above your level.</p>\n"
        '    <div class="cta"><a class="button" href="/">Open the level checker</a>'
        '<a class="button ghost" href="/hsk-flashcards/">HSK flashcards</a></div>\n  </section>')
    body = ('<div class="wrap">\n  <header>\n    ' + nav(pages, URL) +
            '\n    <div class="eyebrow"><span>Chinese New Year 2027</span><span class="chip">Year of the Goat</span></div>\n'
            f'    <h1><span class="zh">{html.escape(data["zh"])}</span>{html.escape(data["h1"])}</h1>\n'
            f'    <p class="lede">{html.escape(data["lede"])}</p>\n  </header>\n\n'
            + "\n\n".join(parts) + "\n</div>")
    ld = json.dumps({
        "@context": "https://schema.org", "@type": "Article", "headline": data["title"],
        "url": site + URL, "inLanguage": "en", "description": data["description"],
        "publisher": {"@type": "Organization", "name": "hskcheck.com", "url": site + "/"},
    }, ensure_ascii=False)
    out = render(data["title"], data["description"], site + URL, base_css + CSS, body,
                 f'<script type="application/ld+json">{ld}</script>')
    target = root / URL.strip("/")
    target.mkdir(exist_ok=True)
    (target / "index.html").write_text(out, encoding="utf-8")
    return [URL]
