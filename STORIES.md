# Writing a graded reading story

Stories live in `data/stories/<slug>.json` (format in `tools/reading.py`). One new story per run.

## Choosing what to write
- Rotate levels: write for the HSK level (1–4) that has the fewest stories; on a tie, the lowest level.
- `episode` is the next number for that level. `published` is today's date (YYYY-MM-DD).
- The slug is the English title in lowercase words joined by hyphens, and must be unique.

## Length
- HSK 1: 90–130 Chinese characters · HSK 2: 140–200 · HSK 3: 220–300 · HSK 4: 300–400.
- 5–8 short paragraphs. Three comprehension questions, each with three options, written in Chinese at the same level.

## The cast (keep them consistent)
- 大卫 (Dàwèi): a British university student learning Chinese; kind, a little clumsy, curious.
- 小雨 (Xiǎoyǔ): works at the milk tea shop by the school gate; quick, funny, helps 大卫.
- 王老师: 大卫's Chinese teacher, who is 小雨's mother (revealed in HSK 2 episode 1).
- 李奶奶: the grandmother downstairs from 大卫, who sings every morning.
New side characters are fine; add every name and place to `names`.

## What makes a story worth reading
- An everyday situation a learner might really meet in China: ordering, transport, shopping, renting, doctors, phones and apps, festivals, friends.
- A small turn or surprise at the end, or a warm moment. No lecture, no moral at the end, no summary sentence.
- Natural Chinese a native speaker would write. If a natural sentence needs a word above the level, change the sentence, not the level.
- Don't repeat the plot of an earlier story; read the list in `reading/index.json` first.

## Checking
1. Run `python3 tools/build.py`. It stops and names any word above the story's level. Rewrite until it builds.
2. Read the story once more as a learner: is every sentence natural and is the turn at the end clear?
3. Commit with a message like "Add HSK 2 story: <English title>" and push to main.
