"""Thai measure word finder at /th/chinese-measure-words/.

Built from the same data as the English page (data/measure_words.tsv and data/classifiers.tsv), with Thai text from
  data/th/measure_words_th.tsv   noun<TAB>Thai meaning[<TAB>Thai note], same nouns in the same order;
                                 a note is required exactly where the English file has one
  data/th/classifiers_th.tsv     measure word<TAB>Thai use, same order as data/classifiers.tsv
The build stops if either file does not line up with the English data.

Called from tools/build_th.py; returns the URLs it wrote.
"""
import html
import json
import unicodedata

TH_MW_URL = "/th/chinese-measure-words/"
EN_MW_URL = "/chinese-measure-words/"


def _rows(path, ncols):
    rows = []
    for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        parts = [p.strip() for p in line.split("\t")]
        if not (ncols[0] <= len(parts) <= ncols[1]) or not all(parts[:2]):
            raise SystemExit(f"{path.name} line {i}: wrong number of columns")
        rows.append(parts)
    return rows


def available(root):
    return all((root / "data" / "th" / f).exists() for f in ("measure_words_th.tsv", "classifiers_th.tsv"))


def build(*, root, tpl, site, css, render, nav, font_link, foot, read_classifiers, read_measure_words, level_table,
          yi_before, zh_spans, search_key, thai_key, squash):
    if not available(root):
        return []
    classifiers = read_classifiers()
    entries = read_measure_words(classifiers)
    th_nouns = _rows(root / "data" / "th" / "measure_words_th.tsv", (2, 3))
    th_mws = _rows(root / "data" / "th" / "classifiers_th.tsv", (2, 2))
    if [r[0] for r in th_nouns] != [e[0] for e in entries]:
        raise SystemExit("data/th/measure_words_th.tsv does not match data/measure_words.tsv noun for noun")
    if [r[0] for r in th_mws] != list(classifiers):
        raise SystemExit("data/th/classifiers_th.tsv does not match data/classifiers.tsv")
    for e, r in zip(entries, th_nouns):
        if bool(e[4]) != (len(r) == 3 and bool(r[2])):
            raise SystemExit(f"data/th/measure_words_th.tsv: {e[0]} needs a Thai note exactly when the English has one")
    th_use = {r[0]: r[1] for r in th_mws}
    levels = level_table()

    data, rows, by_mw = [], [], {m: [] for m in classifiers}
    for (word, pinyin, meaning, mws, _), r in zip(entries, th_nouns):
        th = r[1]
        note = r[2] if len(r) == 3 else ""
        items = []
        for m in mws:
            mpy = classifiers[m][0]
            items.append({"c": m, "ex": f"一{m}{word}", "expy": f"{yi_before(mpy)} {mpy} {pinyin}"})
            by_mw[m].append(word)
        keys = [squash(pinyin), squash(unicodedata.normalize("NFD", pinyin.lower()).replace("ü", "v"))]
        data.append({"w": word, "p": pinyin, "en": th, "lv": levels.get(word), "m": items,
                     "note": zh_spans(note) if note else "", "keys": keys})
        if mws:
            first = classifiers[mws[0]][0]
            others = "、".join(mws[1:])
            mw_cell = f"{mws[0]} <small>{html.escape(first)}</small>" + (f" <small>หรือ {others}</small>" if others else "")
        else:
            mw_cell = "<small>ไม่ต้องใช้</small>"
        key = html.escape(search_key(word, pinyin, meaning) + "|" + thai_key(th) + "|" + "".join(mws), quote=True)
        rows.append(
            f'          <tr data-w="{html.escape(word)}" data-k="{key}"><td class="hz"><b>{html.escape(word)}</b>'
            f'<span>{html.escape(pinyin)}</span></td><td class="en">{html.escape(th)}</td><td class="mw">{mw_cell}</td></tr>'
        )

    mw_json = {m: {"p": p, "e": th_use[m]} for m, (p, _) in classifiers.items()}
    index = []
    for m, (p, _) in classifiers.items():
        nouns = "、".join(f'<a href="#{html.escape(w)}">{html.escape(w)}</a>' for w in by_mw[m])
        index.append(
            f'      <div><dt>{m}<span>{html.escape(p)}</span></dt><dd><span class="use">{html.escape(th_use[m])}</span>'
            f'<span class="nouns">{nouns}</span></dd></div>'
        )
    body = (tpl / "th" / "measure_body.html").read_text(encoding="utf-8")
    body = (body.replace("__NAV__", nav(TH_MW_URL))
            .replace("__ROWS__", "\n".join(rows))
            .replace("__INDEX__", "\n".join(index))
            .replace("__NOUNCOUNT__", str(len(entries)))
            .replace("__MWCOUNT__", str(len(classifiers)))
            .replace("__DATA_JSON__", json.dumps(data, ensure_ascii=False, separators=(",", ":")))
            .replace("__MW_JSON__", json.dumps(mw_json, ensure_ascii=False, separators=(",", ":"))))
    ld = json.dumps({
        "@context": "https://schema.org", "@type": "WebApplication", "name": "ค้นหาลักษณนามภาษาจีน",
        "url": site + TH_MW_URL, "inLanguage": "th", "applicationCategory": "EducationalApplication",
        "operatingSystem": "Any", "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"},
        "description": "ค้นหาลักษณนามภาษาจีน (量词) ที่ใช้กับคำนาม พร้อมพินอิน ตัวอย่าง และระดับ HSK",
    }, ensure_ascii=False)
    out = render(
        "ลักษณนามภาษาจีน (量词): คำนามนี้ใช้ลักษณนามอะไร",
        f"ค้นหาลักษณนามภาษาจีน (量词) ของคำนามที่ใช้บ่อย {len(entries)} คำ ค้นหาด้วยภาษาจีน พินอิน หรือภาษาไทย "
        "พร้อมตัวอย่างและระดับ HSK 3.0 ฟรี",
        site + TH_MW_URL, css, body, font_link + f'\n<script type="application/ld+json">{ld}</script>', lang="th", foot=foot,
    )
    target = root / TH_MW_URL.strip("/")
    target.mkdir(parents=True, exist_ok=True)
    (target / "index.html").write_text(out, encoding="utf-8")
    return [TH_MW_URL]


def alternates(root):
    return {EN_MW_URL: TH_MW_URL} if available(root) else {}
