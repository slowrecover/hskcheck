"""Thai versions of the grammar explainers at /th/learn/<slug>/, built from data/th/learn/<slug>.json.

A Thai file translates an English page in data/learn/<slug>.json. The Chinese sentences and pinyin
always come from the English page (so they are level-checked once and never drift apart); the Thai
file only holds the Thai text, in the same order:

  {
    "slug": "dates-in-chinese",         same as the file name and the English page
    "published": "2026-10-18",
    "title": "...", "description": "...", "h1": "...", "lede": "...",
    "sections": [                       one per English section, same order
      {"h2": "...", "paras": ["..."], "examples": ["Thai translation of example 1", "..."]}
    ],
    "worksheet": {                      required when the English page has a worksheet
      "title": "...", "description": "...",
      "exercises": [                    one per English exercise, same order
        {"h2": "...", "instructions": "...", "items": ["Thai translation of item 1", "..."]}
      ]
    }
  }

The build stops if a Thai file has no English page, or if its sections, paragraphs, examples,
exercises or items don't line up with the English page one for one.
"""
import copy
import datetime
import html
import json

import learn

TH_LEARN_URL = "/th/learn/"
REQUIRED = ("slug", "published", "title", "description", "h1", "lede", "sections")


def slugs(root):
    folder = root / "data" / "th" / "learn"
    return sorted(p.stem for p in folder.glob("*.json")) if folder.exists() else []


def load_pages(root):
    """Merged pages: the English page with every English text field replaced by its Thai translation."""
    english = {p["slug"]: p for p in learn.load_pages()}
    pages = []
    for slug in slugs(root):
        name = f"data/th/learn/{slug}.json"
        t = json.loads((root / "data" / "th" / "learn" / f"{slug}.json").read_text(encoding="utf-8"))
        missing = [k for k in REQUIRED if not t.get(k)]
        if missing:
            raise SystemExit(f"{name}: missing {missing}")
        if t["slug"] != slug or slug not in english:
            raise SystemExit(f"{name}: slug must match the file name and an English page in data/learn/")
        datetime.date.fromisoformat(t["published"])
        en = english[slug]
        p = copy.deepcopy(en)
        for k in ("published", "title", "description", "h1", "lede"):
            p[k] = t[k]
        if len(t["sections"]) != len(en["sections"]):
            raise SystemExit(f"{name}: has {len(t['sections'])} sections, the English page has {len(en['sections'])}")
        for i, (ts, s) in enumerate(zip(t["sections"], p["sections"]), 1):
            if not ts.get("h2"):
                raise SystemExit(f"{name}: section {i} needs h2")
            if len(ts.get("paras", [])) != len(s.get("paras", [])):
                raise SystemExit(f"{name}: section {i} needs {len(s.get('paras', []))} paras")
            exs = s.get("examples", [])
            if len(ts.get("examples", [])) != len(exs) or not all(ts.get("examples", [])):
                raise SystemExit(f"{name}: section {i} needs {len(exs)} example translations")
            s["h2"], s["paras"] = ts["h2"], ts.get("paras", [])
            for ex, th in zip(exs, ts.get("examples", [])):
                ex["en"] = th
        if en.get("worksheet"):
            tw = t.get("worksheet")
            if not tw or not all(tw.get(k) for k in ("title", "description", "exercises")):
                raise SystemExit(f"{name}: the English page has a worksheet, so this file needs worksheet "
                                 "title, description and exercises")
            w = p["worksheet"]
            if len(tw["exercises"]) != len(w["exercises"]):
                raise SystemExit(f"{name}: worksheet needs {len(w['exercises'])} exercises")
            w["title"], w["description"] = tw["title"], tw["description"]
            for i, (te, ex) in enumerate(zip(tw["exercises"], w["exercises"]), 1):
                if not te.get("h2") or not te.get("instructions"):
                    raise SystemExit(f"{name}: worksheet exercise {i} needs h2 and instructions")
                if len(te.get("items", [])) != len(ex["items"]) or not all(te.get("items", [])):
                    raise SystemExit(f"{name}: worksheet exercise {i} needs {len(ex['items'])} item translations")
                ex["h2"], ex["instructions"] = te["h2"], te["instructions"]
                for it, th in zip(ex["items"], te["items"]):
                    it["en"] = th
        elif t.get("worksheet"):
            raise SystemExit(f"{name}: has a worksheet but the English page does not")
        pages.append(p)
    pages.sort(key=lambda p: (p["level"], p["published"], p["slug"]))
    return pages


def alternates(root):
    """English path -> Thai path for the grammar pages that have a Thai version."""
    pairs = {}
    english = {p.stem: json.loads(p.read_text(encoding="utf-8")) for p in (root / "data" / "learn").glob("*.json")}
    for slug in slugs(root):
        if slug not in english:
            continue
        pairs[f"{learn.LEARN_URL}{slug}/"] = f"{TH_LEARN_URL}{slug}/"
        if english[slug].get("worksheet"):
            pairs[f"{learn.LEARN_URL}{slug}/worksheet/"] = f"{TH_LEARN_URL}{slug}/worksheet/"
    if pairs:
        pairs[learn.LEARN_URL] = TH_LEARN_URL
    return pairs


def worksheet_cta(p, url):
    if not p.get("worksheet"):
        return ""
    n = sum(len(ex["items"]) for ex in p["worksheet"]["exercises"])
    return ('<section class="sheet learn">\n    <h2>แบบฝึกหัดพิมพ์ได้</h2>\n'
            f'    <p>ฝึกไวยากรณ์ข้อนี้บนกระดาษ: แบบฝึกหัด {n} ข้อ ใช้เฉพาะคำศัพท์ HSK {p["level"]} '
            'พร้อมเฉลยแยกหน้า พิมพ์และถ่ายเอกสารแจกในชั้นเรียนได้ฟรี</p>\n'
            f'    <div class="cta"><a class="button" href="{url}worksheet/">เปิดแบบฝึกหัด</a></div>\n  </section>\n')


def build(*, root, tpl, site, css, ws_css, render, nav, font_link, foot):
    """Write /th/learn/, one page per Thai file and its worksheet. Returns the URLs written."""
    pages = load_pages(root)
    if not pages:
        return []
    body_tpl = (tpl / "th" / "learn_body.html").read_text(encoding="utf-8")
    ws_tpl = (tpl / "th" / "learn_worksheet_body.html").read_text(encoding="utf-8")
    urls = []
    for p in pages:
        url = f"{TH_LEARN_URL}{p['slug']}/"
        lv = p["level"]
        others = [q for q in pages if q is not p]
        others.sort(key=lambda q: (q["level"] != lv, abs(q["level"] - lv), q["slug"]))
        more = "".join(
            f'<li><a href="{TH_LEARN_URL}{q["slug"]}/"><span class="zh-inline">{html.escape(q["zh"])}</span> '
            f'{learn.zh_spans(q["h1"])}</a> <span class="lv">HSK {q["level"]}</span></li>'
            for q in others[:6]
        )
        body = (body_tpl.replace("__NAV__", nav(TH_LEARN_URL))
                .replace("__LEVEL__", str(lv))
                .replace("__ZH__", html.escape(p["zh"]))
                .replace("__H1__", learn.zh_spans(p["h1"]))
                .replace("__LEDE__", learn.zh_spans(p["lede"]))
                .replace("__SECTIONS__", "\n".join(learn.section_html(s) for s in p["sections"]))
                .replace("__MORE__", f'<ul class="more">{more}</ul>' if more else "")
                .replace("__WORKSHEET__", worksheet_cta(p, url)))
        ld = json.dumps({
            "@context": "https://schema.org", "@type": "Article", "headline": p["title"],
            "description": p["description"], "datePublished": p["published"],
            "inLanguage": "th", "about": "ไวยากรณ์ภาษาจีน (HSK 3.0)", "url": site + url,
            "publisher": {"@type": "Organization", "name": "hskcheck.com", "url": site + "/"},
        }, ensure_ascii=False)
        target = root / url.strip("/")
        target.mkdir(parents=True, exist_ok=True)
        (target / "index.html").write_text(
            render(p["title"], p["description"], site + url, css, body,
                   font_link + f'\n<script type="application/ld+json">{ld}</script>', lang="th", foot=foot),
            encoding="utf-8")
        urls.append(url)
        if p.get("worksheet"):
            urls.append(write_worksheet(p, url, ws_tpl, ws_css, nav, render, site, root, font_link, foot))

    groups = []
    for lv in (1, 2, 3):
        items = [p for p in pages if p["level"] == lv]
        if not items:
            continue
        lis = "".join(
            f'<li><a href="{TH_LEARN_URL}{p["slug"]}/"><span class="zh-inline">{html.escape(p["zh"])}</span> '
            f'{learn.zh_spans(p["h1"])}</a></li>' for p in items
        )
        groups.append(f'  <section class="sheet learn"><h2>HSK {lv}</h2><ul class="more">{lis}</ul></section>')
    body = (tpl / "th" / "learn_index_body.html").read_text(encoding="utf-8")
    body = (body.replace("__NAV__", nav(TH_LEARN_URL))
            .replace("__COUNT__", str(len(pages)))
            .replace("__GROUPS__", "\n".join(groups)))
    target = root / TH_LEARN_URL.strip("/")
    target.mkdir(parents=True, exist_ok=True)
    (target / "index.html").write_text(render(
        "ไวยากรณ์ HSK ภาษาจีน: อธิบายเป็นภาษาไทย พร้อมตัวอย่างประโยค",
        "คำอธิบายไวยากรณ์ภาษาจีน HSK 1-3 ตามหลักสูตร HSK 3.0 เป็นภาษาไทย "
        "ตัวอย่างทุกประโยคใช้เฉพาะคำศัพท์ในระดับนั้น พร้อมพินอินและคำแปล",
        site + TH_LEARN_URL, css, body, font_link, lang="th", foot=foot), encoding="utf-8")
    urls.insert(0, TH_LEARN_URL)
    return urls


def write_worksheet(p, url, tpl, css, nav, render, site, root, font_link, foot):
    w = p["worksheet"]
    ws_url = f"{url}worksheet/"
    exercises, key = learn.worksheet_html(p)
    n = sum(len(ex["items"]) for ex in w["exercises"])
    body = (tpl.replace("__NAV__", nav(TH_LEARN_URL))
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
        "educationalLevel": f"HSK {p['level']}", "inLanguage": ["th", "zh-Hans"], "isAccessibleForFree": True,
        "url": site + ws_url, "isPartOf": site + url,
        "publisher": {"@type": "Organization", "name": "hskcheck.com", "url": site + "/"},
    }, ensure_ascii=False)
    target = root / ws_url.strip("/")
    target.mkdir(parents=True, exist_ok=True)
    (target / "index.html").write_text(
        render(w["title"], w["description"], site + ws_url, css, body,
               font_link + f'\n<script type="application/ld+json">{ld}</script>', lang="th", foot=foot),
        encoding="utf-8")
    return ws_url
