# Vietnamese version plan

Vietnam has the most HSK test takers of any country (about 146,000 in 2025, ahead of Thailand), and demand is
growing with jobs at Chinese companies. The Vietnamese pages live under `/vi/` and follow the Thai version (`/th/`)
page for page. Work is done in steps, one step per run, in the order below; each step says how to tell it is done.

## Phase 1: word meanings (data only, no code or pages)

Write Vietnamese meanings for the HSK word lists, 400 rows per run, in this order, continuing where the last run
stopped (if fewer than 450 rows remain in the whole phase, finish them all):

| File | Follows | Rows |
|------|---------|------|
| `data/vi/hsk1_vi.tsv` | `data/hsk1.tsv` | 300 |
| `data/vi/hsk2_vi.tsv` | `data/hsk2.tsv` | 198 |
| `data/vi/hsk3_vi.tsv` | `data/hsk3.tsv` | 499 |
| `data/vi/hsk4_vi.tsv` | `data/hsk4.tsv` | 997 |
| `data/vi/hsk5_vi.tsv` | `data/hsk5.tsv` | 1,595 |

- Format: `word<TAB>Vietnamese meaning`, one line per row, in exactly the order of the English file, the word column
  identical to it. A batch may run across two files (finish one, start the next).
- Style: a good Vietnamese learner's dictionary. The most common senses only, separated by `; `. No English, no
  Chinese characters, no HTML, no tabs. Use the pinyin and English to pick the right sense; where a row gives two
  readings, give both senses in the order of the pinyin column; where it gives one reading of a character with
  several, give only that reading's sense. Measure words: say what they count, with the usual Vietnamese classifier in
  brackets, e.g. "lượng từ cho cây (cây)". Particles and grammar words: describe the function briefly.
- Do not add Hán-Việt readings (they are easy to get wrong and are not needed for the meaning).
- Phase 1 is done when all five files have every row. Check each file after writing: same words in the same order as
  the English file (a short Python check), no empty meanings, no tabs or Chinese characters in the meanings.
- Commit as "Add Vietnamese meanings for HSK N words A–B" (row numbers within that level's file; name both levels if
  the batch spans two).

## Phase 2: pages (starts only when Phase 1 is done AND every tool in TOOLS.md is done)

Waiting for TOOLS.md keeps two scheduled tasks from changing the build, the nav and every page at the same time.
Until both conditions hold, a run that has no Phase 1 work left makes no changes.

Each step is one run. Build each the way the Thai version is built (`tools/build_th.py`, `tools/*_th.py`,
`templates/th/`), sharing code where that is simpler than copying, without changing what the English or Thai pages
show. The build must stop if a Vietnamese data file is out of order or a template string to swap is not found.

1. **Languages and home** — done when `/vi/index.html` exists. Turn the single Thai alternate into a list of
   languages: every page that exists in several languages gets `hreflang` links to all of them (and `x-default` to
   English), and the language link in the nav becomes a small language switcher (English · ภาษาไทย · Tiếng Việt).
   Then the Vietnamese level checker at `/vi/` with Vietnamese meanings, the HSK 1–5 word lists at
   `/vi/hsk-N-word-list/`, the character worksheet maker and HSK 1–5 character worksheets, and `/vi/about/`.
2. **Flashcards and practice tools** — done when `/vi/hsk-flashcards/index.html` exists. Vietnamese flashcards and a
   Vietnamese version of every practice tool in TOOLS.md.
3. **Grammar pages** — five per run, in the order of `data/learn_queue.tsv`, as `data/vi/learn/<slug>.json` in the
   format of `tools/learn_th.py` (with the worksheet). Done when every English grammar page has a Vietnamese file.
4. **The rest** — done when `/vi/chinese-measure-words/index.html` exists: measure word finder, old → new HSK,
   YCT word lists and worksheets, graded reading with Vietnamese glosses.

When step 4 is done, the plan is complete.

## Rules for Vietnamese text

- Natural Vietnamese for Vietnamese learners of Chinese, with full diacritics, not word-for-word English. Many readers
  study for work: plain, practical wording.
- Titles as a Vietnamese learner would search, e.g. "Từ vựng HSK 1 (HSK 3.0) 300 từ có nghĩa tiếng Việt", under 65
  characters; descriptions under 160. Never call anything an "official" HSK test.
- Keep the Chinese and pinyin exactly as in the English data.

## Checking before publishing

1. `python3 tools/build.py` finishes without errors, and for Phase 2 the sitemap lists the new URLs and the English
   pages carry `hreflang="vi"` links to them.
2. For Phase 2, open the new pages in the pre-installed Chromium with Playwright at 390px and 1280px wide: no console
   errors, nothing overflows, search and interactive parts work.
3. Re-read the new Vietnamese once as a strict Vietnamese editor and Chinese teacher and fix anything wrong.
4. Commit (generated HTML, JSON and sitemap.xml included) and push to main.
