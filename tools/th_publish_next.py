"""Publish at most one reviewed Thai grammar draft on each scheduled run.

The queue is prewritten: no AI API calls, no fabricated exam levels, no cost.
Run via GitHub Actions schedule or manually. Does not delete pages or change URLs.
"""
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "data" / "th" / "usage_published.txt"
QUEUE = ROOT / "data" / "th" / "usage_queue.txt"


def entries(path):
    return [v.strip() for v in path.read_text(encoding="utf-8").splitlines()
            if v.strip() and not v.lstrip().startswith("#")]


def main():
    published = set(entries(MANIFEST))
    for slug in entries(QUEUE):
        if slug in published:
            continue
        draft = ROOT / "data" / "th" / "usage" / f"{slug}.json"
        if not draft.is_file():
            raise SystemExit(f"Missing reviewed Thai content: {draft}")
        if (ROOT / "data" / "th" / "learn" / f"{slug}.json").exists():
            raise SystemExit(f"Existing grammar slug collision: {slug}")
        # Any build error leaves the manifest unchanged: do not accidentally
        # advance the queue past a malformed or unverifiable draft.
        before = MANIFEST.read_text(encoding="utf-8")
        try:
            with MANIFEST.open("a", encoding="utf-8") as f:
                f.write(slug + "\n")
            subprocess.run([sys.executable, str(ROOT / "tools" / "build.py")],
                           cwd=ROOT, check=True)
        except BaseException:
            MANIFEST.write_text(before, encoding="utf-8")
            raise
        print("Published Thai usage page: /th/learn/" + slug + "/")
        return
    print("No missing Thai vocabulary (YCT written 1–4 complete), no pending reviewed usage drafts.")


if __name__ == "__main__":
    main()
