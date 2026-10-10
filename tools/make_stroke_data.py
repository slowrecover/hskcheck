"""Turn the Make Me a Hanzi data into the stroke files the worksheet pages load.

Usage:  python3 tools/make_stroke_data.py /path/to/makemeahanzi /path/to/complete-hsk-vocabulary/complete.min.json

Writes:
  strokes/hsk1.json, hsk2.json, hsk3.json   characters first used in that level's words, in syllabus order
  strokes/x/00.json ... 7f.json             every character in the data set, sharded by code point % 128

For HSK characters, "p" lists the readings the character has in the HSK 1-3 words (from data/hskN.tsv),
in order of first use, with the tone changes of 一 and 不 undone and neutral-tone-only characters given
their dictionary reading (友 in 朋友 -> yǒu); syllables are split using the readings in
complete-hsk-vocabulary (CC-CEDICT based). Other characters keep the Make Me a Hanzi reading.

Each entry is  "字": {"p": ["zì"], "s": ["M..Z", ...]}  with stroke outlines in the 1024-unit
Make Me a Hanzi coordinate system (draw with transform="scale(1,-1) translate(0,-900)").
Stroke data: Arphic Public License. Pinyin: GNU LGPL. See strokes/LICENSE.md.
"""
import json
import pathlib
import re
import sys
import unicodedata

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "strokes"
SHARDS = 128


def compact(path):
    path = re.sub(r"\s+", " ", path.strip())
    return re.sub(r" ?([MQLZC]) ?", r"\1", path)


def toneless(s):
    return "".join(c for c in unicodedata.normalize("NFD", s) if not unicodedata.combining(c) or c == "\u0308")


def nfc_letters(s):
    """Lowercase, drop separators; one code point per letter so toned and toneless strings line up."""
    s = unicodedata.normalize("NFC", s.lower())
    return re.sub(r"[\s'’\-]", "", s)


def split_syllables(word, pinyin, cands):
    """Split a word's pinyin into one syllable per character, guided by each character's known readings."""
    toned = nfc_letters(pinyin)
    plain = unicodedata.normalize("NFC", toneless(toned))
    if len(plain) != len(toned):
        return None

    def go(i, pos):
        if i == len(word):
            return [] if pos == len(toned) else None
        options = sorted({unicodedata.normalize("NFC", toneless(r.lower())) for r in cands.get(word[i], [])} | ({"r"} if word[i] == "儿" else set()),
                         key=len, reverse=True)
        for opt in options:
            if opt and plain.startswith(opt, pos):
                rest = go(i + 1, pos + len(opt))
                if rest is not None:
                    return [toned[pos:pos + len(opt)]] + rest
        return None

    return go(0, 0)


def hsk_readings(cedict_path):
    cands = {}
    for e in json.loads(pathlib.Path(cedict_path).read_text(encoding="utf-8")):
        for f in e["f"]:
            sy = f["i"]["y"].split()
            if len(sy) == len(e["s"]):
                for c, r in zip(e["s"], sy):
                    cands.setdefault(c, set()).add(r)
    base = {"一": "yī", "不": "bù"}
    readings, failed = {}, []
    for n in (1, 2, 3):
        for line in (ROOT / "data" / f"hsk{n}.tsv").read_text(encoding="utf-8").splitlines():
            word, pinyin = line.split("\t")[:2]
            variants = [v.strip() for v in pinyin.split(";")]
            for v in (variants if len(word) == 1 else variants[:1]):
                parts = split_syllables(word, v, cands)
                if parts is None:
                    failed.append(word)
                    continue
                for c, r in zip(word, parts):
                    r = base.get(c, r)
                    lst = readings.setdefault(c, [])
                    if r not in lst:
                        lst.append(r)
    # Show citation readings: drop a neutral-tone syllable when the same syllable with a tone is listed
    # (少 shao in 多少 -> shǎo), except 得, whose neutral de is its own use. Drop erhua r.
    for c, lst in readings.items():
        toned = {toneless(r) for r in lst if toneless(r) != r}
        keep = [r for r in lst if r != "r" and not (toneless(r) == r and r in toned and c != "得")]
        readings[c] = keep or lst
    return readings, failed


PARTICLES = set("吧的吗们呢么啊了着得地过")


def cite_neutral(readings, main_pinyin):
    """A character only ever neutral in the HSK words (友 in 朋友) gets its dictionary reading (yǒu)."""
    for c, lst in readings.items():
        if c in PARTICLES:
            continue
        fixed = []
        for r in lst:
            if toneless(r) == r:
                main = next((m for m in main_pinyin.get(c, []) if toneless(m) == r and m != r), None)
                r = main or r
            if r not in fixed:
                fixed.append(r)
        readings[c] = fixed


def main(src, cedict_path):
    src = pathlib.Path(src)
    hsk_pinyin, failed = hsk_readings(cedict_path)
    if failed:
        print("could not split pinyin for:", " ".join(failed))
    pinyin = {}
    for line in (src / "dictionary.txt").read_text(encoding="utf-8").splitlines():
        d = json.loads(line)
        pinyin[d["character"]] = d.get("pinyin") or []
    cite_neutral(hsk_pinyin, pinyin)
    strokes = {}
    for line in (src / "graphics.txt").read_text(encoding="utf-8").splitlines():
        d = json.loads(line)
        strokes[d["character"]] = [compact(s) for s in d["strokes"]]

    def entry(c):
        return {"p": (hsk_pinyin.get(c) or pinyin.get(c, []))[:3], "s": strokes[c]}

    OUT.mkdir(exist_ok=True)
    seen = set()
    for n in (1, 2, 3):
        level = {}
        for line in (ROOT / "data" / f"hsk{n}.tsv").read_text(encoding="utf-8").splitlines():
            for c in line.split("\t")[0]:
                if c in seen or c not in strokes:
                    continue
                seen.add(c)
                level[c] = entry(c)
        (OUT / f"hsk{n}.json").write_text(json.dumps(level, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
        print(f"hsk{n}: {len(level)} characters")

    shard_dir = OUT / "x"
    shard_dir.mkdir(exist_ok=True)
    shards = [{} for _ in range(SHARDS)]
    for c in strokes:
        shards[ord(c) % SHARDS][c] = entry(c)
    for i, shard in enumerate(shards):
        (shard_dir / f"{i:02x}.json").write_text(json.dumps(shard, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"{len(strokes)} characters in {SHARDS} shards")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    main(sys.argv[1], sys.argv[2])
