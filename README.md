# hskcheck

Source for [hskcheck.com](https://hskcheck.com): a free HSK 3.0 level checker and word lists. Paste Chinese text and see which words are above a learner's level.

## How the site is built

Pages are generated, not edited by hand. Change the data or templates, then run:

```
python3 tools/build.py
```

This writes `index.html`, one `hsk-N-word-list/index.html` per level that has data, and `sitemap.xml`.

- `data/hskN_words.txt` — official HSK 3.0 word list for level N (2025 syllabus), in syllabus order. Levels 1–3 cross-checked against two independently published copies.
- `data/hskN.tsv` — word, pinyin, English for the level's word list page. Must match `hskN_words.txt` exactly; the build stops if it doesn't.
- `templates/` — page layout, shared styles, checker and word list page bodies.
- `tools/check_vocab.py` — checks that example sentences use only words from a given level.

Hosted on GitHub Pages; `CNAME` points the site to hskcheck.com. `.nojekyll` serves files as they are.
