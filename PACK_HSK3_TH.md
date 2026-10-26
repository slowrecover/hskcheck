# Thai HSK 3 vocabulary workbook (paid pack)

A printable PDF for Thai learners: all 499 words of the new HSK 3 list (data/hsk3.tsv), in 25 short lessons, with
Thai meanings, an example sentence for every word (pinyin + Thai translation), writing practice for every character
that is not in HSK 1-2 (284 characters), a quiz after every lesson, a final check and answers. Price $3.99. Lesson 1
is also given away free as its own small PDF on the site so learners can try it.

Thai learners search for "hsk3 คำศัพท์" more than anything else on hskcheck.com; the free Thai HSK 3 word list
(/th/hsk-3-word-list/) brings them in, and this workbook is the paid step after it. The owner does not want to review
drafts: quality has to be right without her.

The work is done in runs by a scheduled task. Each run does the first step below that is not done yet, checks it,
commits and pushes. A step is done when the file it names exists (and, for step 2, covers the lessons it says).

## Step 1. Lesson plan: `data/packs/hsk3_th_plan.json`

Group all 499 HSK 3 words into 25 lessons by everyday topic (school, work and office, home and housework, food and
drink, shopping and money, travel and transport, weather and seasons, health and the body, feelings, time words,
places and directions, hobbies and sport, technology, people and relationships, connecting words such as 不但…而且,
如果, 虽然; etc.). 18-22 words per lesson; put grammar/connecting words together in 2-3 lessons late in the book, after
the learner has met enough nouns and verbs. Every word of data/hsk3.tsv appears exactly once, spelled exactly as
there. Format:

    {"lessons": [{"title_th": "<Thai topic title>", "words": ["阿姨", "爱人", ...]}, ...]}

Check with a short script that the 25 lessons cover all 499 words once each, then commit
"Add Thai HSK 3 workbook lesson plan".

## Step 2. Sentences: `data/packs/hsk3_th_lessons/NN.json` (01 to 25), five lessons per run

For each word in the lesson, in plan order:

    {"title_th": "...", "words": [{"w": "阿姨", "zh": "<sentence>", "py": "<pinyin>", "th": "<Thai translation>"}, ...]}

- `zh`: a short, natural, everyday sentence a native speaker would say, containing the word exactly as written, that
  shows its most common meaning (the one in data/hsk3.tsv; where a word has two senses, the first unless the second
  is far more common for learners). 5-14 characters is ideal. Vary the sentences: no two in a lesson with the same
  pattern. Use ONLY HSK 1-3 words: test every sentence with `python3 tools/check_vocab.py --level 3 "..."` and rewrite
  any marked OUT.
- `py`: correct pinyin with tone marks, words joined as in the site's other data (look at tools/pack_pdf/content.py),
  tone changes shown as spoken (不 bú before 4th tone, 一 yí/yì), neutral tones unmarked, sentence capitalised and
  punctuated.
- `th`: natural Thai a Thai learner would write, not word-for-word; the meaning must be unambiguous for the quiz
  (the fill-in-the-blank quiz shows the sentence with the word blanked and the Thai underneath, so the Thai must point
  to exactly one word of the lesson). Thai meanings of the words themselves come from data/th/hsk3_th.tsv and are not
  repeated here.
- Before committing, re-read the batch once as a strict Chinese teacher (pinyin, tones, naturalness, sense) and once
  as a strict Thai editor. Commit "Add Thai HSK 3 workbook lessons N-M".

## Step 3. Build and publish (done when `th/upgrade-packs/hsk-3-vocabulary-workbook/index.html` exists)

1. `tools/pack_pdf/build_hsk3_th.py`: build the PDF the same way as tools/pack_pdf/build_pack.py and
   build_pack_th.py (same pack.css, same page types, same helper functions copied or imported; Thai text throughout;
   Noto Sans Thai font; output tools/pack_pdf/hsk3_th.html, never committed). Pages: cover (HSK 3 คำศัพท์ครบ 499 คำ,
   25 บทเรียน, ตัวอักษรใหม่ 284 ตัว, made by hskcheck.com), how to use + 25-lesson plan table, then for each lesson:
   word pages (word, pinyin, Thai meaning, sentence with the word highlighted, pinyin, Thai), writing pages for the
   lesson's characters that are not in HSK 1-2 and not taught in an earlier lesson (stroke data strokes/hsk3.json),
   a quiz page (A match word to Thai meaning, B fill the blanks with a word bank, C write the pinyin; same rules as
   build_pack.py: no two options that could both be right, using a GROUPS list of near-synonyms you write for HSK 3,
   e.g. 常/常常, 刚/刚才/刚刚, 或/或者, 可/可是, 总/总是, 收/收到, 受/受到, 选/选择, 季/季节, 会/会议, 变/变化, 字典/词典,
   照相/拍照, 聊/聊天儿, 练/练习, 得到/得, 认得/认识). Then a 30-question final check, answers, a word index in pinyin
   order with the lesson number, and a "what next" page pointing to the free Thai tools (hskcheck.com/th/...). Assert
   the counts (499 words, 284 new characters, 25 lessons). Run tools/pack_pdf/topdf.py: it must report no overflow
   pages; render pages with pdftoppm and look at the cover, a word page, a writing page and a quiz page.
2. Free sample: build lesson 1 alone (cover-style title page "บทที่ 1 ทดลองเรียนฟรี", its word pages, writing pages,
   quiz and its answers, and a last page saying the full workbook has all 25 lessons for $3.99 with the page URL) as
   `th/upgrade-packs/hsk-3-vocabulary-workbook/hsk3-lesson-1-free.pdf` (this one IS committed; keep it under 2 MB).
3. Sales page: add to TH_PACKS in tools/packs.py, slug `hsk-3-vocabulary-workbook`, `en_slug` none (there is no
   English edition: make th_alternates() skip packs without `en_slug`), price "$3.99", price_thb "ประมาณ 130 บาท",
   checkout "" (the owner creates the Creem product afterwards), name "สมุดแบบฝึกคำศัพท์ HSK 3 (499 คำ)", a Thai
   title a learner would search ("คำศัพท์ HSK 3 ครบ 499 คำ สมุดแบบฝึก PDF พิมพ์ได้" or similar, under 65
   characters), description under 160 characters, lede, inside list, four preview JPEGs (620x878, from the full PDF)
   and free_url/free_text pointing to the free lesson 1 PDF ("ดาวน์โหลดบทที่ 1 ฟรี"). Do not change how the HSK 1
   pack page looks.
4. Link it: on /th/hsk-3-word-list/ add one short Thai box near the top of the page content linking the free lesson
   and the workbook page (do it in tools/build_th.py for level 3 only; do not change other levels or the English
   pages).
5. `TZ=UTC python3 tools/build.py`, check the new page at 360px and 1200px with Playwright (no horizontal scroll, no
   console errors, the free PDF link works), check sitemap.xml lists it. Commit "Add Thai HSK 3 vocabulary workbook".
6. Send the owner the full PDF: it is not committed, so attach nothing; instead write it to the Notion page the
   owner uses for hskcheck progress if you can reach it, otherwise just say in the notification that the PDF is built
   by `python3 tools/pack_pdf/build_hsk3_th.py` and she can ask Claude in chat for the file.

## Rules for every run

- Never invent meanings: the Thai meanings come from data/th/hsk3_th.tsv. Never guess pinyin: check every syllable.
- Only HSK 1-3 words in sentences (tools/check_vocab.py --level 3).
- Do not change other packs, other pages' content, or the English site, except where step 3 says.
- Rebase on origin/main before pushing; other scheduled tasks push too. If a rebase conflicts only in generated files
  (HTML, JSON outputs, sitemap.xml), take main's version, finish the rebase, rerun `TZ=UTC python3 tools/build.py`
  and commit.
