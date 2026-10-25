# Practice tools queue

Interactive practice tools that bring learners back to the site. One tool per run, built in the order below, each in
English and in Thai (under `/th/`). A tool is done when its English page exists (`<url>/index.html`); take the first
one that is not done.

| # | Tool | English URL | Thai URL |
|---|------|-------------|----------|
| 1 | HSK practice test | `/hsk-practice-test/` | `/th/hsk-practice-test/` |
| 2 | Grammar practice online | `/learn/<slug>/practice/` | `/th/learn/<slug>/practice/` |
| 3 | Daily HSK quiz | `/daily-hsk-quiz/` | `/th/daily-hsk-quiz/` |
| 4 | Listening practice | `/chinese-listening-practice/` | `/th/chinese-listening-practice/` |
| 5 | Pinyin and tone practice | `/pinyin-tone-practice/` | `/th/pinyin-tone-practice/` |
| 6 | Character tracing | `/chinese-character-tracing/` | `/th/chinese-character-tracing/` |

For tool 2, "done" means `/learn/ba-sentences/practice/index.html` exists (it is built for every grammar page at once).

## Rules for every tool

- **Useful, accurate, no filler.** A page must work fully and help a learner practise. No thin or near-duplicate pages,
  no keyword variations of the same page: Google demotes whole sites for scaled low-value content.
- **Content comes from data that is already checked**: the word lists (`data/hskN.tsv`, Thai in `data/th/`), the
  grammar pages and their worksheets (`data/learn/`, `data/th/learn/`), the stories (`data/stories/`), the stroke data
  (`strokes/`), the tone data (`tones/words.json`). Do not invent new Chinese sentences unless the tool needs them; if
  it does, check them with `tools/check_vocab.py` and add a build check that stops on words above the level.
- **Questions are generated in the browser** from small JSON files written at build time (like the flashcards'
  `hsk-flashcards/hskN.json`). Distractors come from the same level. Never two correct answers: a distractor may not
  share the answer's meaning, pinyin (ignoring tones, where that matters) or characters in a way that makes it also right.
- **No accounts, no tracking of answers.** Progress (scores, streaks) stays in the learner's browser with
  `localStorage`, wrapped in try/catch so the page still works without it. Nothing is sent anywhere.
- **Phone first.** Big tap targets, works at 360px wide, no horizontal scroll. Keyboard works on desktop.
- **Audio** uses the browser's speech synthesis (`zh-CN` voice) the same way the flashcards' Listen button does; hide
  audio questions when no Chinese voice is available.
- **Code layout** follows the site: a `tools/<name>.py` module with a docstring describing the data files and outputs,
  a template in `templates/` (CSS in its own file), called from `tools/build.py`; the Thai page is the English template
  with its text swapped for Thai (see `tools/study.py`), and the build stops if a string is not found. Add the page to
  the site nav, sitemap and hreflang alternates the way existing tools do. Add one line about it to README.md.
- **Thai** text is natural Thai for Thai learners (look at `templates/th/` and `data/th/learn/` for tone); Thai pages
  use Thai meanings where the data has them and English only where Thai does not exist yet.
- **Titles and descriptions** are written the way a learner would search (e.g. "HSK 1 Practice Test Online: Free
  Quiz with Answers"), titles under 65 characters, descriptions under 160. Never call anything an "official" or "real"
  HSK test: say practice test.

## The tools

### 1. HSK practice test
One page with a level picker (HSK 1-5). A test is 20 questions drawn at random for that level, mixing:
- see the word, choose its meaning (4 options);
- see the meaning, choose the word (4 options);
- see the word, choose the pinyin (4 options, distractors with similar syllables or other tones);
- listen, choose the word (only when a Chinese voice is available);
- fill the gap in a sentence: use the "choose" items of the grammar worksheets and the example sentences of the
  grammar pages for HSK 1-3 (gap the target word; options from the same worksheet or level).
After each answer show right/wrong and the correct answer with pinyin and meaning. At the end: score, the words
missed (with a link to add them to the flashcards page for that level), "Try again" and "Next level". Keep the best
score per level in `localStorage`. Link to it from each HSK word list page and the flashcards page.

### 2. Grammar practice online
For every grammar page that has a worksheet, an interactive version of the same exercises at
`/learn/<slug>/practice/`: "choose" items as tap-to-choose, "order" items as tap-the-words-in-order (accept every
answer listed), "fix" items as choose-the-correct-sentence (the wrong sentence plus the listed correct version and up
to two plausible wrong versions built from the same words; if you cannot build wrong versions that are certainly
wrong, show the sentence and reveal the answer instead). Instant feedback, a score at the end. Link from the grammar
page and its printable worksheet. Thai versions use the Thai worksheet text.

### 3. Daily HSK quiz
Ten questions a day per level, the same for every learner that day (seeded by the date), drawn from the same question
types as tool 1. Shows the streak of days completed and the result of the last 7 days, all in `localStorage`.
"Come back tomorrow" when done, with links to the practice test and flashcards.

### 4. Listening practice
Per level: hear a word (or a short sentence from the grammar examples and stories for HSK 1-4) and choose what was
said, from 4 options in characters with pinyin; a "slow" replay button; a mode that hides the characters and shows
only pinyin options. Show a clear notice and a link to the practice test if the device has no Chinese voice.

### 5. Pinyin and tone practice
Two modes: (a) see a character or word, type its pinyin (accept tone numbers like ni3hao3 and tone marks; ü as v or
u:), checked against the dictionary readings in the word lists; (b) hear or see a word and choose its tones (e.g. 3-3,
2-4), using `tones/words.json`, with a note on tone changes linking to `/mandarin-tone-changes/`.

### 6. Character tracing
Trace a character with a finger or mouse on a tian grid, stroke by stroke, using the stroke data in `strokes/`: show
the next stroke as a hint, accept a stroke when it follows the right path and direction, and show a mistake gently.
Pick characters by HSK level (the same sets as the character worksheets) or type any characters. Link from every
character worksheet page.

## Checking a tool before publishing

1. `python3 tools/build.py` finishes without errors.
2. Open the English and Thai pages in the pre-installed Chromium with Playwright at 390px and 1280px wide: answer a
   full round, check there are no console errors, every question has exactly one correct option, the score is right,
   and nothing overflows. Try it once with `localStorage` blocked.
3. Check the sitemap lists the new URLs and the English page has a `hreflang="th"` link to the Thai page.
4. Commit as "Add practice tool: <tool name>" (generated HTML, JSON and sitemap.xml included) and push to main.
