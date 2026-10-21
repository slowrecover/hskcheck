"""HSK 3.0 handwriting characters: a checker plus the full list, built to /hsk-handwriting-characters/.

Data (from the 2025 HSK syllabus, 新版HSK考试大纲):
  data/hsk_handwriting.tsv   level <tab> characters   the 1,200 characters a learner must write by hand
  data/hsk_hanzi.tsv         level <tab> characters   the 3,088 characters a learner must read

Levels are 1-2, 3, 4, 5, 6, 7-9 for writing and 1, 2, 3, 4, 5, 6, 7-9 for reading.
The build stops if a list repeats a character, if the totals change, or if a character
must be written at a level before it has to be read.
"""
import html
import json

URL = "/hsk-handwriting-characters/"
WRITE_LEVELS = ("1-2", "3", "4", "5", "6", "7-9")
READ_LEVELS = ("1", "2", "3", "4", "5", "6", "7-9")
WRITE_TOTAL = 1200
READ_TOTAL = 3088


def _top(level):
    """Highest numeric level a label covers: '1-2' -> 2, '7-9' -> 9, '3' -> 3."""
    return int(level.split("-")[-1])


def _read(path, levels, total):
    rows = {}
    for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        level, chars = line.split("\t")
        if level not in levels:
            raise SystemExit(f"{path.name} line {i}: unknown level {level}")
        rows[level] = chars.strip()
    if tuple(rows) != levels:
        raise SystemExit(f"{path.name}: expected levels {levels}, got {tuple(rows)}")
    every = "".join(rows.values())
    if len(every) != total or len(set(every)) != total:
        raise SystemExit(f"{path.name}: expected {total} different characters, got {len(every)} ({len(set(every))} different)")
    return rows


def load(data):
    write = _read(data / "hsk_handwriting.tsv", WRITE_LEVELS, WRITE_TOTAL)
    read = _read(data / "hsk_hanzi.tsv", READ_LEVELS, READ_TOTAL)
    read_at = {c: lv for lv, cs in read.items() for c in cs}
    late = [c for lv, cs in write.items() for c in cs if c not in read_at or _top(read_at[c]) > _top(lv)]
    if late:
        raise SystemExit(f"hsk_handwriting.tsv: written before they are read: {''.join(late)}")
    return write, read


def build(root, pages, nav, render, base_css, tpl, site):
    write, read = load(root / "data")

    groups, rows = [], []
    running = 0
    for lv in WRITE_LEVELS:
        chars = write[lv]
        running += len(chars)
        label = f"HSK {lv.replace('-', '–')}"
        cells = "".join(f"<li>{html.escape(c)}</li>" for c in chars)
        groups.append(
            f'    <section class="hw-group" id="hsk-{lv}" aria-labelledby="g-{lv}">\n'
            f'      <div class="tools-row"><h3 id="g-{lv}">{label}</h3>'
            f'<span class="count">{len(chars)} new · {running:,} in total</span>'
            f'<a class="ws-link" href="/chinese-character-worksheets/#c={chars}">Print worksheet</a></div>\n'
            f'      <ul class="hw-grid" lang="zh-Hans">{cells}</ul>\n'
            f"    </section>"
        )
        rows.append(f'<tr><td><a href="#hsk-{lv}">{label}</a></td><td class="num">{len(chars)}</td><td class="num">{running:,}</td></tr>')

    read_total = 0
    read_rows = []
    for lv in READ_LEVELS:
        read_total += len(read[lv])
        read_rows.append((lv, read_total))
    read_cum = dict(read_rows)

    body = (tpl / "handwriting_body.html").read_text(encoding="utf-8")
    body = (body.replace("__NAV__", nav(pages, URL))
            .replace("__GROUPS__", "\n".join(groups))
            .replace("__COUNT_ROWS__", "\n".join(f"              {r}" for r in rows))
            .replace("__READ_3__", f"{read_cum['3']:,}")
            .replace("__READ_6__", f"{read_cum['6']:,}")
            .replace("__WRITE_LEVELS__", json.dumps(list(WRITE_LEVELS)))
            .replace("__WRITE_JSON__", json.dumps(write, ensure_ascii=False, separators=(",", ":")))
            .replace("__READ_JSON__", json.dumps(read, ensure_ascii=False, separators=(",", ":"))))

    description = "Check which Chinese characters you must be able to write by hand at each HSK 3.0 level."
    ld = json.dumps({
        "@context": "https://schema.org", "@type": "WebApplication", "name": "HSK Handwriting Character Checker",
        "url": site + URL, "applicationCategory": "EducationalApplication", "operatingSystem": "Any",
        "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"},
        "description": description,
    }, ensure_ascii=False)
    out = render(
        "HSK Handwriting Characters: Which 1,200 Characters You Must Write (HSK 3.0)",
        "HSK 3.0 asks you to read 3,088 characters but write only 1,200. Paste any Chinese text to see which characters "
        "you must be able to write at your level, and print practice sheets for each level. Free.",
        site + URL,
        base_css + (tpl / "checker.css").read_text(encoding="utf-8") + (tpl / "handwriting.css").read_text(encoding="utf-8"),
        body,
        f'<script type="application/ld+json">{ld}</script>',
    )
    target = root / URL.strip("/")
    target.mkdir(exist_ok=True)
    (target / "index.html").write_text(out, encoding="utf-8")
    return [URL]
