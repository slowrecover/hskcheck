# hskcheck

Source for [hskcheck.com](https://hskcheck.com): a free HSK 3.0 level checker, word lists, printable character writing worksheets, and an old HSK → new HSK word gap tool. Paste Chinese text and see which words are above a learner's level, or print stroke-order practice sheets for any characters.

## How the site is built

Pages are generated, not edited by hand. Change the data or templates, then run:

```
python3 tools/build.py
```

This writes `index.html`, one `hsk-N-word-list/index.html` per level that has data, the worksheet maker at `chinese-character-worksheets/`, one `hsk-N-character-worksheets/` page per level, the measure word finder at `chinese-measure-words/`, the old-to-new HSK page at `old-hsk-to-new-hsk/`, and `sitemap.xml`.

- `data/hskN_words.txt` — official HSK 3.0 word list for level N (2025 syllabus), in syllabus order. Levels 1–3 cross-checked against two independently published copies.
- `data/hskN.tsv` — word, pinyin, English for the level's word list page. Must match `hskN_words.txt` exactly; the build stops if it doesn't.
- `data/measure_words.tsv` — noun, pinyin, English, measure words (most common first, comma separated), optional note. Every measure word must be in `data/classifiers.tsv` (measure word, pinyin, what it is used for).
- `templates/` — page layout, shared styles, checker and word list page bodies.
- `data/hsk4_words.txt`, `data/hsk4.tsv` — HSK 4 (2025 syllabus, 1,000 entries / 997 rows), built to `hsk-4-word-list/` and `hsk-4-character-worksheets/` by `tools/hsk4.py`. The level checker covers HSK 1–5 (`CHECKER_LEVELS` in `tools/build.py`).
- `data/hsk5_words.txt`, `data/hsk5.tsv` — HSK 5 (2025 syllabus, 1,600 entries / 1,595 rows), built to `hsk-5-word-list/` and `hsk-5-character-worksheets/` by `tools/hsk5.py` (source and selection rule in that file). English meanings written for this site. `data/th/hsk5_th.tsv` holds the Thai HSK 5 meanings the same way (written in batches; the Thai HSK 5 pages at `th/hsk-5-word-list/` and `th/hsk-5-character-worksheets/` are built once it covers every word). `data/th/hsk4_th.tsv` holds the Thai meanings, in the same order; it may be written in batches, and the Thai HSK 4 pages are built only once it covers every word.
- `data/learn/<slug>.json` — grammar explainers built to `learn/<slug>/` (format in `tools/learn.py`). The build stops if an example sentence uses a word above the page's level. A page can also carry an optional `worksheet` (choose / order / fix exercises), built to a printable `learn/<slug>/worksheet/` with an answer key; its sentences are level-checked the same way. `data/learn_queue.tsv` lists the pages still to write, in order.
- `data/th/learn/<slug>.json` — Thai translation of a grammar page (and its worksheet), built to `th/learn/<slug>/`. It holds only the Thai text; the Chinese and pinyin come from the English page, and the build stops if the two don't line up (format in `tools/learn_th.py`).
- `data/yct/yctN.tsv` — YCT (Youth Chinese Test) word lists for levels 1–4: word, pinyin, English, in alphabetical order of pinyin. Built to `yct/` (format in `tools/yct.py`): one word list and one character worksheet page per level. Words and pinyin follow the official YCT syllabus, cross-checked against an independently published copy.
- `data/th/yct/yctN_th.tsv` — Thai meanings for the YCT word lists (word, Thai), in the same order as `data/yct/yctN.tsv`; built to `th/yct/`. The build stops if the words don't match.
- `tools/worksheets_th.py` — Thai worksheet maker and HSK/YCT worksheet presets under `th/`, made from the English worksheet template with its interface text swapped for Thai (the build stops if the English template changes and a string is no longer found).
- `data/th/measure_words_th.tsv`, `data/th/classifiers_th.tsv` — Thai text for the measure word finder, built to `th/chinese-measure-words/` (format in `tools/measure_th.py`). `tools/upgrade_th.py` builds the Thai old → new HSK page at `th/old-hsk-to-new-hsk/` from the English template.
- `tools/packs.py` — the printable packs: the list at `upgrade-packs/`, one page per pack at `upgrade-packs/<slug>/` (with preview images kept in that folder), and the Terms of Service at `terms/`. A pack's PDF is never kept in this repository, because everything here is public on the site. Put the checkout link in the pack's `checkout` field once the payment provider has approved the store; until then the page says "Checkout opens soon".
- `data/stories/<slug>.json` — graded reading stories, built to `reading/<slug>/` and `th/reading/<slug>/` by `tools/reading.py` (format and cast in that file; writing rules in `STORIES.md`). The build stops if a story uses a word above its HSK level. Also writes `reading/index.json`, read by the flashcards page.
- `VI.md` — the plan for the Vietnamese version under `/vi/`: Vietnamese word meanings in `data/vi/` first, then the pages, one step per run.
- `TOOLS.md` — the queue and rules for the interactive practice tools (practice test, grammar practice, daily quiz, listening, pinyin and tones, tracing), built one at a time.
- `tools/study.py` — the flashcards at `hsk-flashcards/` and `th/hsk-flashcards/`, with one word file per level; progress stays in the browser.
- `tools/practice.py` — the HSK practice test at `hsk-practice-test/` and `th/hsk-practice-test/`: 20 questions per level drawn in the browser from one JSON file per level (meanings, pinyin, listening, and grammar gaps from the hand-checked sentences in `data/practice/gaps.tsv`); best scores stay in the browser.
- `tools/check_vocab.py` — checks that example sentences use only words from a given level.
- `old-hsk-to-new-hsk/words.json`, `words-7-9.json` — data for the old HSK → new HSK page, generated by `tools/make_upgrade_data.py` from `data/hskN.tsv` (new HSK 1–4) and [complete-hsk-vocabulary](https://github.com/drkameleon/complete-hsk-vocabulary) (new HSK 5–9, old HSK 1–6; MIT). Rerun it after changing `data/hskN.tsv`, then run the build.
- `data/hsk_handwriting.tsv`, `data/hsk_hanzi.tsv` — the HSK 3.0 handwriting (1,200) and reading (3,088) character lists by level, from the 2025 syllabus. Built to `hsk-handwriting-characters/` (checks in `tools/handwriting.py`).
- `tones/words.json` — pinyin with dictionary tones for the HSK vocabulary, loaded by `mandarin-tone-changes/`. Generated by `tools/make_tone_data.py` from [complete-hsk-vocabulary](https://github.com/drkameleon/complete-hsk-vocabulary) (MIT); the default readings for characters with several readings are set in that script.
- `strokes/` — stroke outlines and pinyin loaded by the worksheet pages, generated by `tools/make_stroke_data.py` from [Make Me a Hanzi](https://github.com/skishore/makemeahanzi) and [complete-hsk-vocabulary](https://github.com/drkameleon/complete-hsk-vocabulary). Licences in `strokes/LICENSE.md`.

Hosted on GitHub Pages; `CNAME` points the site to hskcheck.com. `.nojekyll` serves files as they are.
