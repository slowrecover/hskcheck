"""Vietnamese versions of the grammar explainers at /vi/learn/<slug>/, built from data/vi/learn/<slug>.json
(VI.md, Phase 2 step 3). Called from tools/build_vi.py.

A Vietnamese file has exactly the format of a Thai one (see tools/learn_th.py): only the Vietnamese text, in the
order of the English page in data/learn/<slug>.json, which supplies the Chinese and pinyin. The same checks apply
(learn_th.load_pages with lang="vi"): the build stops if a file has no English page or its sections, paragraphs,
examples, exercises or items do not line up with the English page one for one.

The worksheet title must read "Bài tập <name> HSK <level> có đáp án, in miễn phí": the grammar practice page
(tools/grammar_practice.py) takes the name from it.

Outputs:
  vi/learn/index.html                      the list of Vietnamese grammar pages
  vi/learn/<slug>/index.html               one page per file
  vi/learn/<slug>/worksheet/index.html     its printable worksheet (when the English page has one)
"""
import html
import json

import learn
import learn_th

VI_LEARN_URL = "/vi/learn/"


def slugs(root):
    return learn_th.slugs(root, "vi")


def load_pages(root):
    return learn_th.load_pages(root, "vi")


def ws_title(name, level):
    return f"Bài tập {name} HSK {level} có đáp án, in miễn phí"


def alternates(root):
    """English path -> Vietnamese path for the grammar pages that have a Vietnamese version."""
    pairs = {}
    english = {p.stem: json.loads(p.read_text(encoding="utf-8")) for p in (root / "data" / "learn").glob("*.json")}
    for slug in slugs(root):
        if slug not in english:
            continue
        pairs[f"{learn.LEARN_URL}{slug}/"] = f"{VI_LEARN_URL}{slug}/"
        if english[slug].get("worksheet"):
            pairs[f"{learn.LEARN_URL}{slug}/worksheet/"] = f"{VI_LEARN_URL}{slug}/worksheet/"
    if pairs:
        pairs[learn.LEARN_URL] = VI_LEARN_URL
    return pairs


def worksheet_cta(p, url):
    if not p.get("worksheet"):
        return ""
    n = sum(len(ex["items"]) for ex in p["worksheet"]["exercises"])
    return ('<section class="sheet learn">\n    <h2>Bài tập in được</h2>\n'
            f'    <p>Luyện điểm ngữ pháp này trên giấy: {n} câu bài tập chỉ dùng từ vựng HSK {p["level"]}, đáp án in ở '
            'trang riêng. In và photo miễn phí cho lớp học.</p>\n'
            f'    <div class="cta"><a class="button" href="{url}worksheet/">Mở bài tập</a>'
            f'<a class="button ghost" href="{url}practice/">Làm bài online</a></div>\n  </section>\n')


def _ld(data):
    return f'<script type="application/ld+json">{json.dumps(data, ensure_ascii=False)}</script>'


def build(*, root, tpl, site, write, nav, base_css, vi_css):
    """Write /vi/learn/, one page per Vietnamese file and its worksheet. write(url, title, description, css, body,
    head_extra) is build_vi's writer. Returns the URLs written."""
    pages = load_pages(root)
    if not pages:
        return []
    css = base_css + (tpl / "learn.css").read_text(encoding="utf-8") + vi_css
    ws_css = base_css + (tpl / "learn_worksheet.css").read_text(encoding="utf-8") + vi_css
    body_tpl = (tpl / "vi" / "learn_body.html").read_text(encoding="utf-8")
    ws_tpl = (tpl / "vi" / "learn_worksheet_body.html").read_text(encoding="utf-8")
    urls = [VI_LEARN_URL]
    for p in pages:
        url = f"{VI_LEARN_URL}{p['slug']}/"
        lv = p["level"]
        others = [q for q in pages if q is not p]
        others.sort(key=lambda q: (q["level"] != lv, abs(q["level"] - lv), q["slug"]))
        more = "".join(
            f'<li><a href="{VI_LEARN_URL}{q["slug"]}/"><span class="zh-inline">{html.escape(q["zh"])}</span> '
            f'{learn.zh_spans(q["h1"])}</a> <span class="lv">HSK {q["level"]}</span></li>'
            for q in others[:6]
        )
        body = (body_tpl.replace("__NAV__", nav(VI_LEARN_URL))
                .replace("__LEVEL__", str(lv))
                .replace("__ZH__", html.escape(p["zh"]))
                .replace("__H1__", learn.zh_spans(p["h1"]))
                .replace("__LEDE__", learn.zh_spans(p["lede"]))
                .replace("__SECTIONS__", "\n".join(learn.section_html(s) for s in p["sections"]))
                .replace("__MORE__", f'<ul class="more">{more}</ul>' if more else "")
                .replace("__WORKSHEET__", worksheet_cta(p, url)))
        write(url, p["title"], p["description"], css, body, _ld({
            "@context": "https://schema.org", "@type": "Article", "headline": p["title"],
            "description": p["description"], "datePublished": p["published"],
            "inLanguage": "vi", "about": "Ngữ pháp tiếng Trung (HSK 3.0)", "url": site + url,
            "publisher": {"@type": "Organization", "name": "hskcheck.com", "url": site + "/"},
        }))
        if not p.get("worksheet"):
            continue
        w = p["worksheet"]
        if not w["title"].startswith("Bài tập ") or not w["title"].endswith(f" HSK {lv} có đáp án, in miễn phí"):
            raise SystemExit(f"data/vi/learn/{p['slug']}.json: worksheet title must read '{ws_title('<name>', lv)}'")
        ws_url = f"{url}worksheet/"
        exercises, key = learn.worksheet_html(p)
        n = sum(len(ex["items"]) for ex in w["exercises"])
        body = (ws_tpl.replace("__NAV__", nav(VI_LEARN_URL))
                .replace("__LEVEL__", str(lv))
                .replace("__ZH__", html.escape(p["zh"]))
                .replace("__COUNT__", str(n))
                .replace("__URL__", url)
                .replace("__SITE_URL__", (site + url).replace("https://", ""))
                .replace("__EXERCISES__", exercises)
                .replace("__KEY__", key))
        write(ws_url, w["title"], w["description"], ws_css, body, _ld({
            "@context": "https://schema.org", "@type": "LearningResource", "name": w["title"],
            "description": w["description"], "learningResourceType": "Worksheet",
            "educationalLevel": f"HSK {lv}", "inLanguage": ["vi", "zh-Hans"], "isAccessibleForFree": True,
            "url": site + ws_url, "isPartOf": site + url,
            "publisher": {"@type": "Organization", "name": "hskcheck.com", "url": site + "/"},
        }))

    groups = []
    for lv in (1, 2, 3):
        items = [p for p in pages if p["level"] == lv]
        if not items:
            continue
        lis = "".join(
            f'<li><a href="{VI_LEARN_URL}{p["slug"]}/"><span class="zh-inline">{html.escape(p["zh"])}</span> '
            f'{learn.zh_spans(p["h1"])}</a></li>' for p in items
        )
        groups.append(f'  <section class="sheet learn"><h2>HSK {lv}</h2><ul class="more">{lis}</ul></section>')
    body = (tpl / "vi" / "learn_index_body.html").read_text(encoding="utf-8")
    body = (body.replace("__NAV__", nav(VI_LEARN_URL))
            .replace("__COUNT__", str(len(pages)))
            .replace("__GROUPS__", "\n".join(groups)))
    write(VI_LEARN_URL, "Ngữ pháp HSK giải thích bằng tiếng Việt, có ví dụ và bài tập",
          "Giải thích ngữ pháp tiếng Trung HSK 1–3 theo đề cương HSK 3.0 bằng tiếng Việt. Câu ví dụ chỉ dùng từ của cấp "
          "đó, có pinyin, nghĩa và bài tập.", css, body)
    return urls
