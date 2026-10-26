"""Check that Chinese sentences use only words up to a given HSK 3.0 level.

Usage:
  python3 tools/check_vocab.py --level 1 "我想喝茶。" "我要一杯茶。"
  python3 tools/check_vocab.py --level 2 --file sentences.txt   (one sentence per line)
  python3 tools/check_vocab.py --yct 2 "我有一个妹妹。"           (YCT 1-2 words only, data/yct/yct2.tsv)

Splits each sentence with the same rule as the site: the split with the fewest
unknown characters, then the fewest pieces. Exits with status 1 if any sentence
contains a word above the level.
"""
import argparse
import pathlib
import re
import sys

DATA = pathlib.Path(__file__).resolve().parent.parent / "data"
HAN = re.compile(r"[㐀-鿿豈-﫿]")


def allowed_words(level):
    words = set()
    for n in range(1, level + 1):
        raw = (DATA / f"hsk{n}_words.txt").read_text(encoding="utf-8").replace("，", ",")
        words |= {w.strip() for w in raw.split(",") if w.strip()}
    for w in list(words):
        if len(w) >= 3 and w.endswith("儿"):
            words.add(w[:-1])
    return words


def allowed_yct(level):
    """The YCT lists are cumulative: data/yct/yctN.tsv already holds every word of YCT 1..N."""
    words = {l.split("\t")[0] for l in (DATA / "yct" / f"yct{level}.tsv").read_text(encoding="utf-8").splitlines() if l.strip()}
    for w in list(words):
        if "…" in w:  # pattern words such as 不但……而且…… count as their parts
            words |= {p for p in w.split("…") if p}
        if len(w) >= 2 and w.endswith("儿"):
            words.add(w[:-1])
    return words


def split_run(run, words, max_len):
    n = len(run)
    best = [None] * (n + 1)
    best[0] = (0, 0, -1, None, True)
    for i in range(n):
        if best[i] is None:
            continue
        unk, cnt = best[i][0], best[i][1]
        for size in range(min(max_len, n - i), 0, -1):
            piece = run[i:i + size]
            known = piece in words
            if not known and size > 1:
                continue
            cand = (unk + (0 if known else 1), cnt + 1, i, piece, known)
            cur = best[i + size]
            if cur is None or cand[:2] < cur[:2]:
                best[i + size] = cand
    out, j = [], n
    while j > 0:
        out.append((best[j][3], best[j][4]))
        j = best[j][2]
    return out[::-1]


def check(sentence, words, max_len):
    tokens, bad = [], []
    for run in re.findall(r"[㐀-鿿豈-﫿]+", sentence):
        for piece, known in split_run(run, words, max_len):
            tokens.append(piece if known else f"[{piece}]")
            if not known:
                bad.append(piece)
    return tokens, bad


def main():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--level", type=int, choices=[1, 2, 3], help="HSK 3.0 level")
    g.add_argument("--yct", type=int, choices=[1, 2, 3, 4], help="YCT level")
    ap.add_argument("--file")
    ap.add_argument("sentences", nargs="*")
    args = ap.parse_args()
    sentences = list(args.sentences)
    if args.file:
        sentences += [l.strip() for l in open(args.file, encoding="utf-8") if l.strip()]
    words = allowed_yct(args.yct) if args.yct else allowed_words(args.level)
    label = f"YCT {args.yct}" if args.yct else f"HSK {args.level}"
    max_len = max(len(w) for w in words)
    failed = 0
    for s in sentences:
        tokens, bad = check(s, words, max_len)
        failed += bool(bad)
        print(("OK  " if not bad else "OUT ") + s + "   " + " / ".join(tokens))
    print(f"\n{len(sentences)} checked, {failed} above {label}")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
