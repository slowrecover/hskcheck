"""Write the stroke centre lines (medians) the character tracing page checks strokes against.

Usage:  python3 tools/make_median_data.py /path/to/makemeahanzi

Reads graphics.txt from Make Me a Hanzi (the same data as strokes/x/, see tools/make_stroke_data.py) and writes
  strokes/m/00.json ... 7f.json   every character in the data set, sharded by code point % 128 like strokes/x/

Each entry is  "字": [[x0, y0, x1, y1, ...], ...]  with one list of points per stroke, in stroke order, from where the
stroke starts to where it ends. Points are in the 1024-unit box of the stroke outlines but already flipped to screen
direction (y grows downwards), so they line up with an outline drawn with transform="scale(1,-1) translate(0,-900)"
without any further transform. The script stops if a character's stroke count differs from strokes/x/.
Stroke data: Arphic Public License. See strokes/LICENSE.md.
"""
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SHARDS = 128


def main(src):
    src = pathlib.Path(src)
    medians = {}
    for line in (src / "graphics.txt").read_text(encoding="utf-8").splitlines():
        d = json.loads(line)
        if len(d["medians"]) != len(d["strokes"]):
            raise SystemExit(f"{d['character']}: {len(d['medians'])} medians for {len(d['strokes'])} strokes")
        medians[d["character"]] = [[v for x, y in m for v in (int(round(x)), int(round(900 - y)))] for m in d["medians"]]
    out = ROOT / "strokes" / "m"
    out.mkdir(exist_ok=True)
    for i in range(SHARDS):
        name = f"{i:02x}.json"
        outlines = json.loads((ROOT / "strokes" / "x" / name).read_text(encoding="utf-8"))
        shard = {}
        for c, e in outlines.items():
            if c not in medians or len(medians[c]) != len(e["s"]):
                raise SystemExit(f"{c}: no medians, or a stroke count that differs from strokes/x/{name}")
            shard[c] = medians[c]
        (out / name).write_text(json.dumps(shard, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"{sum(1 for _ in out.glob('*.json'))} median shards written")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    main(sys.argv[1])
