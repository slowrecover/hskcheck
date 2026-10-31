"""Thai-only Chinese usage explainers (HSK 1–3), using existing Thai grammar template.

Only slugs in data/th/usage_published.txt are built. Draft JSON files are not
published until the daily queue advances. Never fabricate YCT 5 or YCT 6:
the official YCT written exam has only four levels.
"""
import datetime
import html
import json
import re

import learn

BASE = "/th/learn/"
SLUG = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def published_pages(root):
    manifest = root / "data" / "th" / "usage_published.txt"
    if not manifest.exists():
        return []
    pages = []
    seen = set()
    for raw in manifest.read_text(encoding="utf-8").splitlines():
        slug = raw.strip()
        if not slug or slug.startswith("#"):
            continue
        if not SLUG.fullmatch(slug) or slug in seen:
            raise ValueError(f"Invalid or duplicate Thai usage slug: {slug}")
        seen.add(slug)
        path = root / "data" / "th" / "usage" / f"{slug}.json"
        page = json.loads(path.read_text(encoding="utf-8"))
        required = ("slug", "level", "published", "zh", "title",
                    "description", "h1", "lede", "sections")
        if any(not page.get(key) for key in required) or page["slug"] != slug:
            raise ValueError(f"{path}: incomplete content or wrong slug")
        if page["level"] not in (1, 2, 3) or "ใช้ยังไง" not in page["title"]:
            raise ValueError(f"{path}: invalid level or missing Thai search phrase")
        datetime.date.fromisoformat(page["published"])
        if (root / "data" / "th" / "learn" / f"{slug}.json").exists():
            raise ValueError(f"{slug}: clashes with existing bilingual grammar page")
        examples = 0
        for section in page["sections"]:
            if not section.get("h2") or not section.get("paras"):
                raise ValueError(f"{path}: section missing heading or explanation")
            for ex in section.get("examples", []):
                if not all(ex.get(k) for k in ("zh", "py", "en")):
                    raise ValueError(f"{path}: incomplete Chinese/pinyin/Thai example")
                examples += 1
        if examples < 6:
            raise ValueError(f"{path}: fewer than six verified example translations")
        pages.append(page)
    return pages


def build(*, root, tpl, site, css, render, nav, font_link, foot):
    pages = published_pages(root)
    if not pages:
        return []
    template = (tpl / "th" / "learn_body.html").read_text(encoding="utf-8")
    urls = []
    for page in pages:
        url = f"{BASE}{page['slug']}/"
        more = (
            '<ul class="more">'
            '<li><a href="/th/yct/yct-3-word-list/">คำศัพท์ YCT 3 พร้อมคำแปลไทย</a></li>'
            '<li><a href="/th/yct/yct-4-word-list/">คำศัพท์ YCT 4 พร้อมคำแปลไทย</a></li>'
            '<li><a href="/th/learn/">ไวยากรณ์ภาษาจีนทั้งหมด</a></li>'
            '</ul>'
        )
        body = (template.replace("__NAV__", nav(BASE))
                .replace("__LEVEL__", str(page["level"]))
                .replace("__ZH__", html.escape(page["zh"]))
                .replace("__H1__", learn.zh_spans(page["h1"]))
                .replace("__LEDE__", learn.zh_spans(page["lede"]))
                .replace("__SECTIONS__", "\n".join(learn.section_html(s) for s in page["sections"]))
                .replace("__MORE__", more)
                .replace("__WORKSHEET__", "")
                .replace("__WORKBOOK__", ""))
        ld = json.dumps({
            "@context": "https://schema.org", "@type": "Article",
            "headline": page["title"], "description": page["description"],
            "datePublished": page["published"], "inLanguage": "th",
            "about": "ไวยากรณ์ภาษาจีน HSK 1–3",
            "url": site + url,
            "publisher": {"@type": "Organization", "name": "hskcheck.com", "url": site + "/"}
        }, ensure_ascii=False)
        target = root / url.strip("/")
        target.mkdir(parents=True, exist_ok=True)
        (target / "index.html").write_text(
            render(page["title"], page["description"], site + url, css, body,
                   font_link + '\n<script type="application/ld+json">' + ld + '</script>',
                   lang="th", foot=foot),
            encoding="utf-8")
        urls.append(url)
    return urls
