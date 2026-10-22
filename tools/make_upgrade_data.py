"""Build the data file for the Old HSK -> New HSK page.

Usage:  python3 tools/make_upgrade_data.py /path/to/complete-hsk-vocabulary

Writes, in old-hsk-to-new-hsk/:
  words.json      {"w": [[word, pinyin, meaning, new_level, old_level], ...],   new HSK 1-6
                   "oc": ["", chars first used in old HSK 1 words, ..., in old HSK 6 words]}
  words-7-9.json  {"w": [...]}   new HSK 7-9 (new_level 7), loaded only when someone picks 7-9
  old_level is 1-6, or 0 if the word is in none of the old HSK lists.

New HSK (3.0, 2025 syllabus):
  levels 1-4  from data/hskN.tsv (the site's own cross-checked lists)
  levels 5-9  from complete-hsk-vocabulary wordlists/exclusive/newest/ (MIT licence)
  (That data set lacks some 2025 HSK 4 words, such as 扫码, 网购 and 线上, so level 4 comes from data/hsk4.tsv.)
Old HSK (2.0, levels 1-6) from the old-N tags in complete-hsk-vocabulary complete.json.

Words are compared as written. A word ending in 儿 (3+ characters) also matches the same word without it,
as on the level checker. A word of two or more characters also counts as met when it is part of an old
HSK entry (篮球 in 打篮球, 照相 in 照相机). Each word is listed once, at its lowest new level.
"""
import json
import pathlib
import re
import sys
import unicodedata

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "old-hsk-to-new-hsk"
SKIP = re.compile(r"^(surname|variant of|old variant|archaic variant|used in|see |also written|also pr\.|abbr\. for|CL:)", re.I)


# The data set splits the old HSK 2 entry 踢足球 into 踢 alone; restore the 足球 part.
OLD_PATCH = {"足球": 2}


def key(w):
    return w[:-1] if len(w) >= 3 and w.endswith("儿") else w


def join_pinyin(p):
    """'Xī ān' -> 'xī'ān', 'ài qíng' -> 'àiqíng' (site style: no spaces, apostrophe before a/e/o)."""
    out = ""
    for i, s in enumerate(p.split()):
        base = unicodedata.normalize("NFD", s.lower())[:1]
        if i and base in "aeo":
            out += "'"
        out += s
    return out


def describe(entry):
    readings, meanings = [], []
    # Common-word readings before proper names (丰满 fēngmǎn before Fēngmǎn, a district).
    forms = sorted(entry["forms"], key=lambda f: f["transcriptions"]["pinyin"][:1].isupper())
    for f in forms:
        ms = [m for m in f["meanings"] if not SKIP.match(m)]
        proper = f["transcriptions"]["pinyin"][:1].isupper()
        if not ms or (proper and readings):
            continue
        p = join_pinyin(f["transcriptions"]["pinyin"])
        if p not in readings:
            readings.append(p)
        for m in ms:
            if len("; ".join(meanings + [m])) > 70 and meanings:
                break
            if m not in meanings:
                meanings.append(m)
        if len(readings) >= 2:
            break
    if not readings:  # only surname/variant senses: fall back to the first form
        f = entry["forms"][0]
        readings = [join_pinyin(f["transcriptions"]["pinyin"])]
        meanings = f["meanings"][:1]
    return "; ".join(readings), "; ".join(meanings)


def main(src):
    src = pathlib.Path(src)
    complete = json.loads((src / "complete.json").read_text(encoding="utf-8"))

    old_level = {}
    for e in complete:
        lv = [int(l[4:]) for l in e["level"] if l.startswith("old-")]
        if lv:
            k = key(e["simplified"])
            old_level[k] = min(lv + ([old_level[k]] if k in old_level else []))

    for w, n in OLD_PATCH.items():
        old_level.setdefault(w, n)
    old_words = sorted(old_level.items(), key=lambda kv: kv[1])

    def met_in(w):
        k = key(w)
        if k in old_level:
            return old_level[k]
        if len(k) >= 2:
            return next((n for ow, n in old_words if k in ow), 0)
        return 0

    words, seen = [], set()

    def add(w, p, m, n):
        k = key(w)
        if k in seen:
            return
        seen.add(k)
        words.append([w, p, m, n, met_in(w)])

    for n in (1, 2, 3, 4):
        for line in (ROOT / "data" / f"hsk{n}.tsv").read_text(encoding="utf-8").splitlines():
            if line.strip():
                w, p, m = (x.strip() for x in line.split("\t"))
                add(w, p, m, n)
    for n in (5, 6, 7):
        for e in json.loads((src / "wordlists" / "exclusive" / "newest" / f"{n}.json").read_text(encoding="utf-8")):
            p, m = describe(e)
            add(e["simplified"], p, m, n)

    oc, used = [""], set()
    for n in range(1, 7):
        chars = []
        level_words = [e["simplified"] for e in complete if f"old-{n}" in e["level"]]
        level_words += [w for w, m in OLD_PATCH.items() if m == n]
        for w in level_words:
            for c in w:
                if c not in used and "\u4e00" <= c <= "\u9fff":
                    used.add(c)
                    chars.append(c)
        oc.append("".join(chars))

    OUT.mkdir(exist_ok=True)
    dump = lambda obj: json.dumps(obj, ensure_ascii=False, separators=(",", ":"))
    (OUT / "words.json").write_text(dump({"w": [x for x in words if x[3] < 7], "oc": oc}), encoding="utf-8")
    (OUT / "words-7-9.json").write_text(dump({"w": [x for x in words if x[3] == 7]}), encoding="utf-8")
    by_level = {n: sum(1 for x in words if x[3] == n) for n in range(1, 8)}
    print("new words by level:", by_level, "total", len(words))
    print("old chars by level:", [len(s) for s in oc[1:]])


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    main(sys.argv[1])
