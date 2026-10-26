# Thai YCT workbooks (paid packs)

Printable PDF workbooks for Thai children learning for the YCT (Youth Chinese Test), one per level, plus a bundle of all
four. /th/yct/ is the page that brings the most search clicks on hskcheck.com, so these are the paid step after the free
Thai YCT word lists and worksheets. The owner does not review drafts: quality has to be right without her.

Each workbook teaches the words that are **new at that level** (the YCT lists are cumulative, see tools/yct.py):

| Level | New words | Lessons | Price |
|-------|-----------|---------|-------|
| YCT 1 | 80  | 5  (16 each)  | $1.99 |
| YCT 2 | 70  | 5  (14 each)  | $1.99 |
| YCT 3 | 150 | 10 (15 each)  | $2.99 |
| YCT 4 | 298 | 15 (19-20 each) | $3.99 |
| YCT 1-4 bundle (all four PDFs in one) | 598 | 35 | $6.99 |
| Class licence for the bundle (copy for one teacher's classes) | | | $9.99 |

Lesson 1 of each level is free as its own small PDF on the level's page.

## Data: `data/packs/yct_th/yctN.json`

    {"lessons": [{"title_th": "<Thai topic title>", "words": [{"w": "爸爸", "zh": "...", "py": "...", "th": "..."}, ...]}, ...]}

- Every new word of the level appears exactly once, spelled exactly as in data/yct/yctN.tsv; lessons grouped by topic
  a child knows (family, body, animals, food, school, colours, weather, numbers and time, toys and play, ...), grammar
  words (了, 呢, 比, 把, 因为…所以 ...) late in the level.
- `zh`: a short, natural sentence a Chinese child or teacher would say, about a child's world (home, school, friends,
  pets, games, food). 4-12 characters. It uses ONLY words of YCT 1..N: check with
  `python3 tools/check_vocab.py --yct N "..."`. The word's first occurrence in the sentence is the word itself (the quiz
  blanks the first match). Varied patterns within a lesson.
- `py`: correct pinyin with tone marks, conventions as in data/packs/hsk3_th_lessons (words joined, tone changes of
  一 and 不 as spoken, neutral tones unmarked, verb-了 attached, sentence-final le and locatives li/shang separate,
  sentence capitalised and punctuated). Word pinyin comes from data/yct/yctN.tsv.
- `th`: simple, natural Thai a Thai child understands, pointing to exactly one word of the lesson (the fill-in quiz shows
  the sentence with the word blanked and the Thai underneath). Word meanings come from data/th/yct/yctN_th.tsv.

## Build: `tools/pack_pdf/build_yct_th.py`

Same page types and pack.css as build_hsk3_th.py, with bigger type and bigger writing cells for children: cover,
how to use + lesson plan, per lesson word pages, writing pages (characters not in a lower YCT level and not taught
earlier; stroke data strokes/x/), quiz (A match, B fill in with word bank, C pinyin; GROUPS of near-synonyms so every
question has one answer), final check, answers, word index, "what next" page pointing to the free Thai YCT pages.
Outputs `tools/pack_pdf/yctN_th.html` and `yctN_th_lesson1.html` (never committed). Free lesson 1 PDFs are committed as
`th/upgrade-packs/yct-N-workbook/yct-N-lesson-1-free.pdf`. The full PDFs and the bundle PDF are never committed.

## Pages

TH_PACKS entries `yct-N-workbook` (N = 1-4) and `yct-1-4-workbook-bundle` (with the class licence as a second button),
each with four 620x878 preview JPEGs and checkout "" until the owner creates the Creem products. Each Thai YCT word
list page /th/yct/yct-N-word-list/ gets one short box linking its free lesson and workbook.
