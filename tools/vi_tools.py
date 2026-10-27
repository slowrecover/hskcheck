"""Vietnamese flashcards and practice tools under /vi/ (VI.md, Phase 2 step 2). Called from tools/build_vi.py.

  vi/hsk-flashcards/               flashcards with spaced review (tools/study.py, templates/study_body.html)
  vi/hsk-practice-test/            HSK practice test (tools/practice.py)
  vi/daily-hsk-quiz/               daily HSK quiz, loading the files of vi/hsk-practice-test/ (tools/daily.py)
  vi/chinese-listening-practice/   listening practice (tools/listening.py)
  vi/pinyin-tone-practice/         pinyin and tone practice (tools/pinyin_practice.py)
  vi/chinese-character-tracing/    character tracing (tools/tracing.py; strokes shared with the English page)

Each page is the English template with its text swapped for Vietnamese (the build stops if a string is not found),
and each tool's JSON files are written by the same code and with the same checks as the English and Thai ones, with
the Vietnamese meanings of data/vi/ in place of the English.

Grammar sentences join with the Vietnamese grammar pages (VI.md step 3): the gap sentences of the practice test and
the daily quiz (data/practice/gaps.tsv, checked by tools/practice.py) and the grammar example sentences of the
listening practice are used only for the grammar pages that have a Vietnamese file (data/vi/learn/<slug>.json, see
tools/learn_vi.py), with the Vietnamese of that file, so these pages never show a sentence without a Vietnamese
meaning. The text of the pages names the levels that have gap sentences. The listening practice uses the story sentences of data/practice/listening_stories.tsv, with
their Vietnamese in data/vi/practice/listening_stories_vi.tsv (slug, sentence, Vietnamese; same order, checked).

The practice test keeps two words apart as wrong options when the English and Thai pages do (their meanings overlap
in English or Thai) and also when their Vietnamese meanings overlap: a shared sense, or one sense inside another
(see vi_conflicts).
"""
import json
import re
import unicodedata

import daily
import learn_vi
import listening
import pinyin_practice
import practice
import study
import tracing

V = "/vi/"
STUDY_URL = V + "hsk-flashcards/"
PRACTICE_URL = V + "hsk-practice-test/"
DAILY_URL = V + "daily-hsk-quiz/"
LISTEN_URL = V + "chinese-listening-practice/"
PINYIN_URL = V + "pinyin-tone-practice/"
TRACE_URL = V + "chinese-character-tracing/"
LEVELS = (1, 2, 3, 4, 5)
HAN = re.compile(r"[㐀-鿿豈-﫿]")

NAV = [(STUDY_URL, "Flashcard"), (PRACTICE_URL, "Thi thử HSK"), (DAILY_URL, "Trắc nghiệm mỗi ngày"),
       (LISTEN_URL, "Luyện nghe"), (PINYIN_URL, "Pinyin và thanh điệu")]
NAV_AFTER_WS = [(TRACE_URL, "Tập tô chữ")]

EYEBROW = ('<span>New HSK · 2025 syllabus</span><span class="chip">Levels 1–5</span><span class="chip">Free</span>',
           '<span>HSK mới · Đề cương 2025</span><span class="chip">Cấp 1–5</span><span class="chip">Miễn phí</span>')
PICK = ('<h2 id="pick-title" class="visually-hidden">Choose a level</h2>',
        '<h2 id="pick-title" class="visually-hidden">Chọn cấp độ</h2>')
LEVELS_PT = ('<div class="levels pt-levels" role="group" aria-label="Level">\n      <span class="lbl">Level</span>',
             '<div class="levels pt-levels" role="group" aria-label="Cấp độ">\n      <span class="lbl">Cấp</span>')
WORDS_NOTE = ('Từ vựng HSK 3.0 (HSK mới), đề cương 2025, giống các '
              f'<a href="{V}hsk-1-word-list/">trang danh sách từ</a>, có nghĩa tiếng Việt cho cả HSK 1–5.')
NO_VOICE_HELP = ("Hầu hết điện thoại và máy tính đều thêm được giọng tiếng Trung miễn phí trong phần cài đặt chuyển văn "
                 "bản thành giọng nói hoặc cài đặt ngôn ngữ")

# --- flashcards ------------------------------------------------------------------------------------------------------

STUDY_UI = {
    "started": "từ đã học", "strong": "từ đã thuộc", "day": "ngày", "days": "ngày", "streak": "liên tiếp",
    "newWord": "Từ mới", "review": "Ôn tập", "show": "Xem đáp án", "know": "Tôi biết từ này rồi",
    "again": "Chưa nhớ", "got": "Nhớ rồi", "listen": "Nghe",
    "doneHead": "Hôm nay bạn đã học xong", "doneSub": "Ngày mai quay lại để ôn tập và học thêm từ mới nhé.",
    "more": "Học thêm từ mới", "allSeen": "Bạn đã bắt đầu học tất cả các từ của cấp này.",
    "loading": "Đang tải từ vựng…", "loadFail": "Không tải được danh sách từ. Hãy kiểm tra kết nối mạng rồi thử lại.",
    "resetAsk": "Xóa toàn bộ tiến độ học HSK {n}? Bạn sẽ không khôi phục lại được.",
    "installHead": "Ngày mai mở ngay từ màn hình chính",
    "installText": "Thêm flashcard vào màn hình chính để mở như một ứng dụng, mỗi ngày chỉ cần một chạm.",
    "installBtn": "Thêm vào màn hình chính",
    "pickHead": "Bạn đang học HSK cấp mấy?",
    "pickSub": "Mới bắt đầu học tiếng Trung? Hãy chọn HSK 1. Bạn có thể đổi cấp bất cứ lúc nào.",
    "storyHead": "Giờ hãy đọc một truyện ngắn HSK", "readBase": V + "reading/", "titleKey": "vi",
    "iosTip": "Trên iPhone: chạm nút Chia sẻ trong Safari, rồi chọn “Thêm vào MH chính”. Flashcard sẽ mở như một ứng dụng.",
}

STUDY_SWAPS = [
    EYEBROW,
    ('<h1><span class="zh">背词</span>HSK Flashcards</h1>', '<h1><span class="zh">背词</span>Flashcard từ vựng HSK</h1>'),
    ('<p class="lede">A few minutes a day. You get new words and the ones you are due to review, and your progress is saved '
     'on this device, with no account.</p>',
     '<p class="lede">Mỗi ngày vài phút. Bạn học từ mới và ôn lại những từ đến hạn ôn; tiến độ được lưu ngay trên thiết bị '
     'này, không cần tài khoản.</p>'),
    ('<h2 id="pick-title" class="visually-hidden">Choose a level</h2>',
     '<h2 id="pick-title" class="visually-hidden">Chọn cấp độ</h2>'),
    ('<div class="levels" role="group" aria-label="Level">\n      <span class="lbl">Level</span>',
     '<div class="levels" role="group" aria-label="Cấp độ">\n      <span class="lbl">Cấp</span>'),
    ('<h2 id="card-title">Today</h2>', '<h2 id="card-title">Hôm nay</h2>'),
    ('<p class="empty" id="loading">Loading words…</p>', '<p class="empty" id="loading">Đang tải từ vựng…</p>'),
    ('<a id="test-link" href="/hsk-practice-test/">Test yourself: take the HSK practice test →</a>',
     f'<a id="test-link" href="{PRACTICE_URL}">Tự kiểm tra: làm bài thi thử HSK →</a>'),
    ('<a id="quiz-link" href="/daily-hsk-quiz/">Ten questions a day: today\'s HSK quiz →</a>',
     f'<a id="quiz-link" href="{DAILY_URL}">Mỗi ngày 10 câu: làm bài trắc nghiệm HSK hôm nay →</a>'),
    ('<h2 id="set-title">Settings</h2>', '<h2 id="set-title">Cài đặt</h2>'),
    ('<label class="fc-set">New words a day', '<label class="fc-set">Số từ mới mỗi ngày'),
    ('<input type="checkbox" id="show-pinyin"> Show pinyin on the front</label>',
     '<input type="checkbox" id="show-pinyin"> Hiện pinyin ở mặt trước</label>'),
    ('<button type="button" class="ghost" id="reset-btn">Reset this level</button>',
     '<button type="button" class="ghost" id="reset-btn">Học lại cấp này từ đầu</button>'),
    ('This browser is not letting the page save, so your progress will be lost when you close it.',
     'Trình duyệt này không cho trang lưu dữ liệu, nên tiến độ sẽ mất khi bạn đóng trang.'),
    ('<h2 id="guide-title">How it works</h2>', '<h2 id="guide-title">Cách học</h2>'),
    ('<h3>New words and reviews</h3>', '<h3>Từ mới và từ cần ôn</h3>'),
    ('<p>Each day you get a few new words from your level, in syllabus order, plus the words you are due to review. '
     'Say the meaning to yourself, then tap <b>Show answer</b>.</p>',
     '<p>Mỗi ngày bạn nhận vài từ mới của cấp đang học, theo thứ tự trong đề cương, cùng những từ đã đến hạn ôn. '
     'Hãy tự nói nghĩa của từ trước, rồi chạm <b>Xem đáp án</b>.</p>'),
    ('<h3>Got it, or again</h3>', '<h3>Nhớ rồi, hay chưa nhớ</h3>'),
    ("<p>If you knew it, the word comes back later: after 1 day, then 3, 7, 14 and 30 days. If not, it comes back at the "
     "end of today's session and again tomorrow. Words you already know can be skipped with <b>I know this word</b>.</p>",
     "<p>Nếu bạn nhớ, từ đó sẽ quay lại sau: sau 1 ngày, rồi 3, 7, 14 và 30 ngày. Nếu chưa nhớ, từ đó quay lại ở cuối "
     "buổi học hôm nay và cả ngày mai. Từ nào đã biết rồi thì bỏ qua bằng nút <b>Tôi biết từ này rồi</b>.</p>"),
    ('<h3>Where is my progress kept?</h3>', '<h3>Tiến độ của tôi được lưu ở đâu?</h3>'),
    ('<p>In this browser on this device. Nothing is sent to us. Clearing your browser data, or using another phone or '
     'computer, starts you from the beginning.</p>',
     '<p>Trong trình duyệt trên thiết bị này. Không có gì được gửi cho chúng tôi. Nếu xóa dữ liệu trình duyệt, hoặc dùng '
     'điện thoại hay máy tính khác, bạn sẽ bắt đầu lại từ đầu.</p>'),
    ('<p><b>Word lists.</b> HSK 3.0 (New HSK) vocabulary, 2025 syllabus, the same lists as the '
     '<a href="/hsk-1-word-list/">word list pages</a>. Pronunciation uses your device\'s Chinese voice when it has one.</p>',
     f'<p><b>Danh sách từ.</b> {WORDS_NOTE} Phát âm dùng giọng tiếng Trung có sẵn trên thiết bị của bạn (nếu có).</p>'),
]

# --- practice test ---------------------------------------------------------------------------------------------------

PRACTICE_UI = {
    "q": "Câu", "of": "/", "best": "Cao nhất", "start": "Bắt đầu bài thi thử HSK {n}",
    "startSub": "20 câu hỏi: {parts}. Khoảng 5 phút.", "pMeaning": "nghĩa của từ", "pWord": "chọn từ theo nghĩa",
    "pPinyin": "pinyin", "pListen": "nghe", "pGap": "điền từ vào câu", "sep": ", ", "and": " và ",
    "askMeaning": "Từ này nghĩa là gì?", "askWord": "Từ nào có nghĩa này?",
    "askPinyin": "Từ này đọc thế nào?", "askListen": "Hãy nghe. Bạn nghe thấy từ nào?",
    "askGap": "Chọn từ điền vào chỗ trống.", "play": "Nghe lại", "slow": "Chậm",
    "right": "Đúng rồi!", "wrong": "Chưa đúng.", "answer": "Đáp án", "next": "Câu tiếp theo", "finish": "Xem điểm",
    "grammar": "Đọc về điểm ngữ pháp này", "learnBase": V + "learn/",
    "scoreHead": "Điểm của bạn", "bestNew": "Điểm cao nhất mới cho HSK {n}!", "bestOld": "Điểm cao nhất của bạn ở HSK {n}: {b} / 20",
    "msg4": "Xuất sắc. Bạn nắm chắc từ vựng HSK {n}: hãy thử cấp tiếp theo.",
    "msg3": "Làm tốt lắm. Ôn lại các từ bên dưới rồi làm lại nhé.",
    "msg2": "Cố lên. Học các từ bên dưới bằng flashcard, rồi làm lại.",
    "msg1": "HSK {n} vẫn còn mới với bạn. Flashcard là nơi bắt đầu tốt.",
    "missedHead": "Từ cần ôn lại", "noMissed": "Bạn trả lời đúng tất cả các câu.",
    "add": "Thêm các từ này vào flashcard HSK {n} của tôi", "added": "Đã thêm. Các từ này sẽ hiện trước trong lần học flashcard tới.",
    "openCards": "Mở flashcard HSK {n} →", "cardsBase": STUDY_URL,
    "again": "Làm lại", "nextLevel": "Cấp tiếp theo: HSK {m}",
    "loading": "Đang tải bài thi…", "loadFail": "Không tải được bài thi. Hãy kiểm tra kết nối mạng rồi thử lại.",
    "noVoice": "Thiết bị của bạn không có giọng tiếng Trung, nên bài thi này không có câu nghe.",
}


def hsk_range(levels):
    """[1] -> HSK 1, [1, 2, 3] -> HSK 1–3 (the levels that have gap sentences)."""
    levels = sorted(levels)
    return f"HSK {levels[0]}" if len(levels) == 1 else f"HSK {levels[0]}–{levels[-1]}"


def practice_swaps(gap_levels):
    has_gaps = bool(gap_levels)
    what = ("nghĩa của từ, pinyin, nghe và ngữ pháp" if has_gaps else "nghĩa của từ, pinyin và nghe")
    inside = ("Bạn chọn nghĩa của một từ, chọn từ theo nghĩa, chọn pinyin đúng và nghe rồi chọn từ vừa nghe; ở "
              f'{hsk_range(gap_levels) if has_gaps else ""} còn có câu điền từ vào chỗ trống lấy từ các '
              f'<a href="{V}learn/">bài ngữ pháp</a>.' if has_gaps else
              "Bạn chọn nghĩa của một từ, chọn từ theo nghĩa, chọn pinyin đúng và nghe rồi chọn từ vừa nghe.")
    return [
        EYEBROW,
        ('<h1><span class="zh">测试</span>HSK Practice Test</h1>', '<h1><span class="zh">测试</span>Thi thử HSK online</h1>'),
        ('<p class="lede">Choose your level and answer 20 questions on the HSK 3.0 words: meanings, pinyin, listening and '
         'grammar. You see the right answer after every question, and the words you missed at the end.</p>',
         f'<p class="lede">Chọn cấp độ và trả lời 20 câu hỏi về từ vựng HSK 3.0: {what}. Sau mỗi câu bạn thấy ngay '
         'đáp án đúng, và cuối bài là danh sách những từ bạn trả lời sai.</p>'),
        PICK, LEVELS_PT,
        ('<h2 id="test-title" class="visually-hidden">Test</h2>', '<h2 id="test-title" class="visually-hidden">Bài thi</h2>'),
        ('<p class="empty" id="loading">Loading the test…</p>', '<p class="empty" id="loading">Đang tải bài thi…</p>'),
        ('This browser is not letting the page save, so your best scores will not be kept.',
         'Trình duyệt này không cho trang lưu dữ liệu, nên điểm cao nhất sẽ không được giữ lại.'),
        ('<a id="quiz-link" href="/daily-hsk-quiz/">Ten new questions every day: the daily HSK quiz →</a>',
         f'<a id="quiz-link" href="{DAILY_URL}">Mỗi ngày 10 câu mới: trắc nghiệm HSK mỗi ngày →</a>'),
        ('<a id="listen-link" href="/chinese-listening-practice/">Train your ear: Chinese listening practice →</a>',
         f'<a id="listen-link" href="{LISTEN_URL}">Luyện tai: luyện nghe tiếng Trung →</a>'),
        ('<a id="pinyin-link" href="/pinyin-tone-practice/">Get the tones right: pinyin and tone practice →</a>',
         f'<a id="pinyin-link" href="{PINYIN_URL}">Đọc đúng thanh điệu: luyện pinyin và thanh điệu →</a>'),
        ('<h2 id="guide-title">About this practice test</h2>', '<h2 id="guide-title">Về bài thi thử này</h2>'),
        ('<h3>What is in the test?</h3>', '<h3>Bài thi có những gì?</h3>'),
        ('<p>Twenty questions drawn at random from the words of the level you choose, so every test is different. You '
         'choose the meaning of a word, the word for a meaning, and the right pinyin; you hear a word and pick it out; and '
         'at HSK 1–3 you fill the gap in a sentence from the <a href="/learn/">grammar pages</a>.</p>',
         f'<p>20 câu hỏi được chọn ngẫu nhiên từ từ vựng của cấp bạn chọn, nên mỗi lần làm là một đề khác. {inside}</p>'),
        ('<h3>Is this the HSK exam?</h3>', '<h3>Đây có phải là đề thi HSK thật không?</h3>'),
        ('<p>No. It is a practice test for the vocabulary of each level, made from the HSK 3.0 word lists. The exam itself '
         'has its own listening, reading and writing papers. A good score here means you know the words that the exam '
         'expects at your level.</p>',
         '<p>Không. Đây là bài thi thử từ vựng của từng cấp, soạn từ danh sách từ HSK 3.0. Kỳ thi HSK có các phần nghe, '
         'đọc và viết riêng. Đạt điểm cao ở đây nghĩa là bạn đã nắm được những từ mà kỳ thi yêu cầu ở cấp của bạn.</p>'),
        ('<h3>Where is my score kept?</h3>', '<h3>Điểm của tôi được lưu ở đâu?</h3>'),
        ('<p>Your best score for each level is kept in this browser on this device. Your answers are not sent anywhere. '
         'Words you miss can go straight into the <a href="/hsk-flashcards/">flashcards</a>, which bring them back for '
         'review.</p>',
         '<p>Điểm cao nhất của từng cấp được lưu trong trình duyệt trên thiết bị này. Câu trả lời của bạn không được gửi đi '
         f'đâu cả. Những từ làm sai có thể thêm ngay vào <a href="{STUDY_URL}">flashcard</a> để được ôn lại.</p>'),
        ('<p><b>Words.</b> HSK 3.0 (New HSK) vocabulary, 2025 syllabus, the same lists as the '
         '<a href="/hsk-1-word-list/">word list pages</a>. Listening questions use your device\'s Chinese voice and appear '
         'only when it has one.</p>',
         f'<p><b>Từ vựng.</b> {WORDS_NOTE} Câu nghe dùng giọng tiếng Trung của thiết bị và chỉ xuất hiện khi thiết bị có '
         'giọng này.</p>'),
    ]


# --- daily quiz ------------------------------------------------------------------------------------------------------

DAILY_UI = {
    "locale": "vi-VN", "days": ["CN", "T2", "T3", "T4", "T5", "T6", "T7"],
    "q": "Câu", "of": "/", "start": "Bắt đầu bài HSK {n} hôm nay", "resume": "Làm tiếp: câu {k} / {t}",
    "startSub": "10 câu về từ vựng HSK {n}. Khoảng 2 phút.",
    "askMeaning": "Từ này nghĩa là gì?", "askWord": "Từ nào có nghĩa này?",
    "askPinyin": "Từ này đọc thế nào?", "askListen": "Hãy nghe. Bạn nghe thấy từ nào?",
    "askGap": "Chọn từ điền vào chỗ trống.", "play": "Nghe lại", "slow": "Chậm",
    "right": "Đúng rồi!", "wrong": "Chưa đúng.", "next": "Câu tiếp theo", "finish": "Xem điểm",
    "grammar": "Đọc về điểm ngữ pháp này", "learnBase": V + "learn/",
    "scoreHead": "Bài trắc nghiệm HSK {n} hôm nay",
    "msg4": "Xuất sắc. Bạn nắm chắc các từ HSK {n} này.", "msg3": "Làm tốt lắm. Ôn lại các từ bên dưới nhé.",
    "msg2": "Cố lên. Học các từ bên dưới bằng flashcard.",
    "msg1": "HSK {n} vẫn còn mới với bạn. Flashcard là nơi bắt đầu tốt.",
    "missedHead": "Từ cần ôn lại", "noMissed": "Bạn trả lời đúng tất cả các câu.",
    "add": "Thêm các từ này vào flashcard HSK {n} của tôi", "added": "Đã thêm. Các từ này sẽ hiện trước trong lần học flashcard tới.",
    "tomorrow": "Ngày mai quay lại nhé", "tomorrowSub": "Bài mới sẵn sàng lúc nửa đêm. Trong lúc chờ, bạn có thể luyện tiếp:",
    "testLink": "Thi thử HSK {n}", "testBase": PRACTICE_URL,
    "cardsLink": "Flashcard HSK {n}", "cardsBase": STUDY_URL,
    "streak0": "Làm xong bài hôm nay để bắt đầu chuỗi ngày học.", "streak1": "Chuỗi: 1 ngày",
    "streakN": "Chuỗi: {n} ngày liên tiếp",
    "weekScore": "{s}/{t} ở HSK {n}", "weekOther": "đã làm ở cấp khác", "weekNone": "chưa làm",
    "loading": "Đang tải bài hôm nay…", "loadFail": "Không tải được bài trắc nghiệm. Hãy kiểm tra kết nối mạng rồi thử lại.",
}


def daily_swaps(gap_levels):
    has_gaps = bool(gap_levels)
    what = ("nghĩa của một từ, từ có nghĩa cho trước, pinyin đúng, một từ bạn nghe được, và ở "
            f'{hsk_range(gap_levels) if has_gaps else ""} có câu điền từ vào chỗ trống lấy từ các '
            f'<a href="{V}learn/">bài ngữ pháp</a>' if has_gaps else
            "nghĩa của một từ, từ có nghĩa cho trước, pinyin đúng và một từ bạn nghe được")
    return [
        EYEBROW,
        ('<h1><span class="zh">每日</span>Daily HSK Quiz</h1>', '<h1><span class="zh">每日</span>Trắc nghiệm HSK mỗi ngày</h1>'),
        ('<p class="lede">Ten questions a day for your level, new every day and the same for every learner. Answer them in '
         'two minutes, keep your streak going, and come back tomorrow.</p>',
         '<p class="lede">Mỗi ngày 10 câu hỏi theo cấp của bạn, đổi mới mỗi ngày và giống nhau cho mọi người học. Làm xong '
         'trong hai phút, giữ chuỗi ngày học, rồi ngày mai quay lại.</p>'),
        PICK, LEVELS_PT,
        ('<ol class="dq-week" id="week" aria-label="The last 7 days">', '<ol class="dq-week" id="week" aria-label="7 ngày qua">'),
        ('<h2 id="quiz-title" class="visually-hidden">Today\'s quiz</h2>',
         '<h2 id="quiz-title" class="visually-hidden">Bài hôm nay</h2>'),
        ('<p class="empty" id="loading">Loading today\'s quiz…</p>', '<p class="empty" id="loading">Đang tải bài hôm nay…</p>'),
        ('This browser is not letting the page save, so your streak and results will not be kept.',
         'Trình duyệt này không cho trang lưu dữ liệu, nên chuỗi ngày học và kết quả sẽ không được giữ lại.'),
        ('<h2 id="guide-title">About the daily quiz</h2>', '<h2 id="guide-title">Về bài trắc nghiệm mỗi ngày</h2>'),
        ('<h3>What is in the quiz?</h3>', '<h3>Bài trắc nghiệm có những gì?</h3>'),
        ('<p>Ten questions on the HSK 3.0 words of your level: the meaning of a word, the word for a meaning, the right pinyin, '
         'a word you hear, and at HSK 1–3 a gap to fill in a sentence from the <a href="/learn/">grammar pages</a>. You see '
         'the answer after every question.</p>',
         f'<p>10 câu hỏi về từ vựng HSK 3.0 của cấp bạn chọn: {what}. Sau mỗi câu bạn thấy ngay đáp án.</p>'),
        ('<h3>Why is it the same for everyone?</h3>', '<h3>Vì sao ai cũng có cùng một đề?</h3>'),
        ('<p>The questions are picked from the date, so everyone at the same level gets the same quiz on the same day, and a '
         'new one at midnight. Compare your score with a classmate, or do it together with your teacher.</p>',
         '<p>Câu hỏi được chọn theo ngày, nên mọi người cùng cấp có cùng một đề trong cùng một ngày, và có đề mới lúc nửa '
         'đêm. Bạn có thể so điểm với bạn cùng lớp, hoặc làm cùng giáo viên trên lớp.</p>'),
        ('<h3>How does the streak work?</h3>', '<h3>Chuỗi ngày học được tính thế nào?</h3>'),
        ('<p>Finish a quiz at any level and the day counts. Your streak is the number of days in a row you have finished one, '
         'and the week shows your score at the level you have chosen. It is all kept in this browser on this device; nothing '
         'is sent anywhere.</p>',
         '<p>Làm xong một bài ở bất kỳ cấp nào là ngày đó được tính. Chuỗi ngày học là số ngày liên tiếp bạn làm xong bài, '
         'còn hàng 7 ngày cho thấy điểm của bạn ở cấp đang chọn. Mọi thứ được lưu trong trình duyệt trên thiết bị này, không '
         'gửi đi đâu cả.</p>'),
        ('<h3>Want more practice?</h3>', '<h3>Muốn luyện thêm?</h3>'),
        ('<p>Take a longer <a href="/hsk-practice-test/">HSK practice test</a> of 20 questions as often as you like, or learn '
         'new words every day with the <a href="/hsk-flashcards/">flashcards</a>.</p>',
         f'<p>Làm <a href="{PRACTICE_URL}">bài thi thử HSK</a> dài hơn, 20 câu, bao nhiêu lần tùy thích, hoặc học từ mới '
         f'mỗi ngày bằng <a href="{STUDY_URL}">flashcard</a>.</p>'),
        ('<p><b>Words.</b> HSK 3.0 (New HSK) vocabulary, 2025 syllabus, the same lists as the '
         '<a href="/hsk-1-word-list/">word list pages</a> and the practice test. Listening questions use your device\'s '
         'Chinese voice; without one, you choose the word for its meaning instead.</p>',
         f'<p><b>Từ vựng.</b> {WORDS_NOTE} Câu nghe dùng giọng tiếng Trung của thiết bị; nếu thiết bị không có giọng này, '
         'bạn sẽ chọn từ theo nghĩa thay vào đó.</p>'),
    ]


# --- listening -------------------------------------------------------------------------------------------------------

STORY_TITLES = {
    "tea-at-the-little-shop": "Trà ở quán nhỏ",
    "the-teachers-birthday": "Sinh nhật cô giáo",
    "the-grandma-downstairs": "Bà cụ tầng dưới",
    "the-video": "Một đoạn video",
}

LISTEN_UI = {
    "q": "Câu", "of": "/", "best": "Cao nhất", "start": "Bắt đầu luyện nghe: HSK {n}",
    "startSub": "10 câu: {what}. Hãy bật âm thanh.", "wMix": "từ và câu ngắn", "wWords": "từ",
    "wSent": "câu ngắn", "ask": "Hãy nghe. Bạn nghe thấy gì?", "play": "Nghe lại", "slow": "Chậm",
    "playFirst": "Nghe", "right": "Đúng rồi!", "wrong": "Chưa đúng.", "next": "Câu tiếp theo", "finish": "Xem điểm",
    "fromG": "Trích từ bài ngữ pháp", "fromS": "Trích từ truyện", "learnBase": V + "learn/", "readBase": V + "reading/",
    "scoreHead": "Điểm của bạn", "bestNew": "Điểm cao nhất mới cho HSK {n}!",
    "bestOld": "Điểm cao nhất của bạn ở HSK {n} ({what}): {b} / {t}",
    "msg4": "Xuất sắc. Tai bạn đã quen với HSK {n}: hãy thử cấp tiếp theo.",
    "msg3": "Làm tốt lắm. Nghe lại các câu bên dưới, rồi luyện thêm một lượt.",
    "msg2": "Cố lên. Hãy thử nút Chậm, và học các từ bên dưới bằng flashcard.",
    "msg1": "Tai bạn chưa quen với HSK {n}. Hãy luyện với chữ Hán và pinyin, và dùng nút Chậm.",
    "missedHead": "Nghe lại", "noMissed": "Bạn trả lời đúng tất cả các câu.",
    "add": "Thêm các từ nghe sai vào flashcard HSK {n} của tôi",
    "added": "Đã thêm. Các từ này sẽ hiện trước trong lần học flashcard tới.",
    "cardsBase": STUDY_URL, "again": "Luyện thêm lượt nữa", "nextLevel": "Cấp tiếp theo: HSK {m}",
    "testLink": "Làm bài thi thử HSK {n}", "testBase": PRACTICE_URL,
    "loading": "Đang tải…", "loadFail": "Không tải được câu hỏi. Hãy kiểm tra kết nối mạng rồi thử lại.",
    "noSent": "HSK 5 chưa có câu nghe, nên lượt này chỉ có từ.",
}


def listen_swaps(has_grammar):
    src = (f'các câu ví dụ trong <a href="{V}learn/">bài ngữ pháp</a> và trong các <a href="{V}reading/">truyện '
           'đọc theo cấp độ</a>' if has_grammar else
           f'các <a href="{V}reading/">truyện đọc theo cấp độ</a> của trang')
    return [
        EYEBROW,
        ('<h1><span class="zh">听力</span>Chinese Listening Practice</h1>',
         '<h1><span class="zh">听力</span>Luyện nghe tiếng Trung</h1>'),
        ('<p class="lede">Hear a word or a short sentence from your HSK level and choose what was said. Replay it as often as '
         'you like, slow it down, or hide the characters and listen with pinyin only.</p>',
         '<p class="lede">Nghe một từ hoặc một câu ngắn theo cấp HSK của bạn rồi chọn đúng điều vừa nghe. Nghe lại bao nhiêu '
         'lần tùy thích, cho đọc chậm, hoặc ẩn chữ Hán và chỉ luyện với pinyin.</p>'),
        PICK, LEVELS_PT,
        ('<div class="levels lp-set" role="group" aria-label="What to hear" id="kind-set">\n      <span class="lbl">Hear</span>',
         '<div class="levels lp-set" role="group" aria-label="Nghe gì" id="kind-set">\n      <span class="lbl">Nghe</span>'),
        ('data-kind="mix" aria-pressed="false">Words and sentences</button>', 'data-kind="mix" aria-pressed="false">Từ và câu</button>'),
        ('data-kind="words" aria-pressed="false">Words</button>', 'data-kind="words" aria-pressed="false">Từ</button>'),
        ('data-kind="sent" aria-pressed="false">Sentences</button>', 'data-kind="sent" aria-pressed="false">Câu</button>'),
        ('<div class="levels lp-set" role="group" aria-label="Answers in">\n      <span class="lbl">Answers</span>',
         '<div class="levels lp-set" role="group" aria-label="Đáp án hiện bằng">\n      <span class="lbl">Đáp án</span>'),
        ('data-py="0" aria-pressed="false">Characters and pinyin</button>',
         'data-py="0" aria-pressed="false">Chữ Hán và pinyin</button>'),
        ('data-py="1" aria-pressed="false">Pinyin only</button>', 'data-py="1" aria-pressed="false">Chỉ pinyin</button>'),
        ('<h2 id="test-title" class="visually-hidden">Listening</h2>', '<h2 id="test-title" class="visually-hidden">Luyện nghe</h2>'),
        ('<p class="empty" id="loading">Loading…</p>', '<p class="empty" id="loading">Đang tải…</p>'),
        ('<p class="v">Your device has no Chinese voice</p>', '<p class="v">Thiết bị của bạn không có giọng tiếng Trung</p>'),
        ('<p>This page uses the Mandarin Chinese voice of your phone or computer to read the words, and none was found. Most '
         'phones and computers can add one for free in their text-to-speech or language settings; then reload this page. '
         'Until then, you can practise the same words without sound:</p>',
         '<p>Trang này dùng giọng tiếng Trung phổ thông của điện thoại hoặc máy tính để đọc từ, nhưng không tìm thấy giọng '
         f'nào. {NO_VOICE_HELP}; thêm xong thì tải lại trang này. Trong lúc đó, bạn có thể luyện chính những từ này mà '
         'không cần âm thanh:</p>'),
        ('<a class="button" href="/hsk-practice-test/" id="novoice-link">HSK practice test</a>',
         f'<a class="button" href="{PRACTICE_URL}" id="novoice-link">Thi thử HSK</a>'),
        ('This browser is not letting the page save, so your best scores and settings will not be kept.',
         'Trình duyệt này không cho trang lưu dữ liệu, nên điểm cao nhất và cài đặt sẽ không được giữ lại.'),
        ('<h2 id="guide-title">About listening practice</h2>', '<h2 id="guide-title">Về phần luyện nghe</h2>'),
        ('<h3>What will I hear?</h3>', '<h3>Tôi sẽ nghe những gì?</h3>'),
        ('<p>Words from the HSK 3.0 list of your level and, at HSK 1–4, short sentences from the example sentences of the '
         '<a href="/learn/">grammar pages</a> and from the <a href="/reading/">graded stories</a>. Every sentence uses only '
         'words of its level. The four answers never sound alike, so there is always one right answer.</p>',
         f'<p>Các từ trong danh sách HSK 3.0 của cấp bạn chọn, và ở HSK 1–4 có thêm câu ngắn lấy từ {src}. Mỗi câu chỉ '
         'dùng từ của cấp đó. Bốn đáp án không bao giờ đọc giống nhau, nên luôn chỉ có một đáp án đúng.</p>'),
        ('<h3>How should I practise?</h3>', '<h3>Nên luyện thế nào?</h3>'),
        ('<p>Listen first, before you read the answers. If you are not sure, press Slow and listen again. When the characters '
         'start to feel easy, switch to pinyin only: then you have to recognise the sounds, not the characters, which is '
         'closer to what the listening paper of the exam asks.</p>',
         '<p>Hãy nghe trước rồi mới đọc các đáp án. Nếu chưa chắc, bấm Chậm và nghe lại. Khi thấy chọn theo chữ Hán đã dễ, '
         'hãy chuyển sang Chỉ pinyin: lúc đó bạn phải nhận ra âm chứ không dựa vào mặt chữ, gần với yêu cầu của phần thi '
         'nghe hơn.</p>'),
        ('<h3>Why does the voice sound different on my phone?</h3>', '<h3>Vì sao giọng đọc trên điện thoại của tôi nghe khác?</h3>'),
        ('<p>The words are read by the Chinese voice built into your device, so the voice depends on your phone or computer. '
         'Words that a voice can easily misread on their own, such as single characters with two readings, are left out. '
         'For written and spoken tones, see <a href="/mandarin-tone-changes/">tone changes</a>.</p>',
         '<p>Từ được đọc bằng giọng tiếng Trung có sẵn trong thiết bị, nên giọng đọc tùy vào điện thoại hoặc máy tính của '
         'bạn. Những từ mà giọng máy dễ đọc sai khi đứng một mình, như chữ đơn có hai cách đọc, đã được bỏ ra. Về khác biệt '
         'giữa thanh điệu khi viết và khi nói, xem trang <a href="/mandarin-tone-changes/" hreflang="en">biến điệu</a> '
         '(tiếng Anh).</p>'),
        ('<h3>Where is my score kept?</h3>', '<h3>Điểm của tôi được lưu ở đâu?</h3>'),
        ('<p>Your best score for each level is kept in this browser on this device, and nothing is sent anywhere. Words you '
         'miss can go straight into the <a href="/hsk-flashcards/">flashcards</a>. For a mixed test of meanings, pinyin and '
         'grammar, try the <a href="/hsk-practice-test/">HSK practice test</a>.</p>',
         '<p>Điểm cao nhất của từng cấp được lưu trong trình duyệt trên thiết bị này, không gửi đi đâu cả. Những từ nghe sai '
         f'có thể thêm ngay vào <a href="{STUDY_URL}">flashcard</a>. Muốn kiểm tra tổng hợp nghĩa, pinyin và '
         f'{"ngữ pháp" if has_grammar else "nghe"}, hãy làm <a href="{PRACTICE_URL}">bài thi thử HSK</a>.</p>'),
        ('<p><b>Words and sentences.</b> HSK 3.0 (New HSK) vocabulary, 2025 syllabus, the same lists as the '
         '<a href="/hsk-1-word-list/">word list pages</a>. Sentences come from this site\'s grammar pages and stories, with '
         'pinyin checked against the word lists. Audio uses your device\'s Chinese voice.</p>',
         f'<p><b>Từ và câu.</b> {WORDS_NOTE} Câu nghe lấy từ {"bài ngữ pháp và truyện" if has_grammar else "truyện"} '
         'của trang này, pinyin đã được đối chiếu với danh sách từ. Âm thanh dùng giọng tiếng Trung của thiết bị.</p>'),
    ]


# --- pinyin and tones ------------------------------------------------------------------------------------------------

PINYIN_UI = {
    "q": "Câu", "of": "/", "best": "Cao nhất", "start": "Bắt đầu: HSK {n}",
    "subType": "10 từ: gõ pinyin kèm thanh điệu.", "subSee": "10 từ: chọn thanh điệu của từng từ.",
    "subHear": "10 từ: nghe rồi chọn thanh điệu. Hãy bật âm thanh.",
    "askType": "Gõ pinyin của từ này, kèm thanh điệu.", "askSee": "Từ này mang những thanh điệu nào?",
    "askHear": "Hãy nghe. Bạn nghe thấy những thanh điệu nào?",
    "hint": "Gõ số thanh điệu (ni3hao3) hoặc dấu thanh (nǐhǎo). Gõ ü là v. Thanh nhẹ: số 5 hoặc không ghi số.",
    "inputLabel": "Pinyin", "check": "Kiểm tra", "dunno": "Xem đáp án", "play": "Nghe lại", "slow": "Chậm",
    "listen": "Nghe", "right": "Đúng rồi!", "wrong": "Chưa đúng.",
    "noTones": "Hãy thêm thanh điệu: một con số sau mỗi âm tiết (ni3hao3) hoặc dấu thanh (nǐhǎo).",
    "badChars": "Hãy gõ pinyin bằng chữ cái Latinh, kèm số hoặc dấu thanh điệu.",
    "tonesWrong": "Âm tiết đã đúng, nhưng chưa đúng hết thanh điệu.",
    "spoken": "Khi nói đúng là đọc như vậy, nhưng pinyin ghi thanh điệu gốc. Xem phần biến điệu.",
    "toneLink": "/mandarin-tone-changes/", "yourAnswer": "Bạn đã gõ", "neutral": "5 = thanh nhẹ",
    "next": "Câu tiếp theo", "finish": "Xem điểm",
    "scoreHead": "Điểm của bạn", "bestNew": "Điểm cao nhất mới cho HSK {n}!",
    "bestOld": "Điểm cao nhất của bạn ở HSK {n} ({what}): {b} / {t}",
    "wType": "gõ pinyin", "wSee": "chọn thanh điệu", "wHear": "nghe thanh điệu",
    "msg4": "Xuất sắc. Pinyin HSK {n} của bạn rất chắc: hãy thử cấp tiếp theo.",
    "msg3": "Làm tốt lắm. Xem lại các từ bên dưới, rồi luyện thêm một lượt.",
    "msg2": "Cố lên. Đọc to các từ bên dưới kèm thanh điệu, và học chúng bằng flashcard.",
    "msg1": "Thanh điệu cần thời gian. Đọc to từng từ bên dưới kèm thanh điệu, rồi làm lại.",
    "missedHead": "Từ cần ôn lại", "noMissed": "Bạn trả lời đúng tất cả các câu.",
    "add": "Thêm các từ làm sai vào flashcard HSK {n} của tôi",
    "added": "Đã thêm. Các từ này sẽ hiện trước trong lần học flashcard tới.",
    "cardsBase": STUDY_URL, "again": "Luyện thêm lượt nữa", "nextLevel": "Cấp tiếp theo: HSK {m}",
    "testLink": "Làm bài thi thử HSK {n}", "testBase": PRACTICE_URL,
    "loading": "Đang tải…", "loadFail": "Không tải được từ vựng. Hãy kiểm tra kết nối mạng rồi thử lại.",
}

PINYIN_SWAPS = [
    EYEBROW,
    ('<h1><span class="zh">拼音</span>Pinyin and Tone Practice</h1>',
     '<h1><span class="zh">拼音</span>Luyện pinyin và thanh điệu</h1>'),
    ('<p class="lede">Type the pinyin of the words of your HSK level, or see or hear a word and choose its tones. '
     'Every answer shows the right pinyin, so you learn the tones as you go.</p>',
     '<p class="lede">Gõ pinyin của các từ theo cấp HSK của bạn, hoặc nhìn hay nghe một từ rồi chọn thanh điệu của nó. '
     'Mỗi câu đều hiện pinyin đúng, nên bạn nhớ thanh điệu ngay trong lúc luyện.</p>'),
    PICK, LEVELS_PT,
    ('<div class="levels lp-set" role="group" aria-label="Practice">\n        <span class="lbl">Practice</span>',
     '<div class="levels lp-set" role="group" aria-label="Kiểu luyện">\n        <span class="lbl">Luyện</span>'),
    ('data-mode="type" aria-pressed="false">Type the pinyin</button>', 'data-mode="type" aria-pressed="false">Gõ pinyin</button>'),
    ('data-mode="tones" aria-pressed="false">Choose the tones</button>',
     'data-mode="tones" aria-pressed="false">Chọn thanh điệu</button>'),
    ('<div class="levels lp-set" role="group" aria-label="Tones from" id="how-set">\n        <span class="lbl">Word</span>',
     '<div class="levels lp-set" role="group" aria-label="Cách hiện từ" id="how-set">\n        <span class="lbl">Từ</span>'),
    ('data-hear="0" aria-pressed="false">See it</button>', 'data-hear="0" aria-pressed="false">Nhìn từ</button>'),
    ('data-hear="1" aria-pressed="false">Hear it</button>', 'data-hear="1" aria-pressed="false">Nghe từ</button>'),
    ('<p class="pt-note" id="novoice-note" hidden>Your device has no Chinese voice, so the words can only be seen, '
     'not heard. Most phones and computers can add one for free in their text-to-speech or language settings.</p>',
     '<p class="pt-note" id="novoice-note" hidden>Thiết bị của bạn không có giọng tiếng Trung, nên chỉ nhìn được từ, '
     f'không nghe được. {NO_VOICE_HELP}.</p>'),
    ('<h2 id="test-title" class="visually-hidden">Practice</h2>', '<h2 id="test-title" class="visually-hidden">Luyện tập</h2>'),
    ('<p class="empty" id="loading">Loading…</p>', '<p class="empty" id="loading">Đang tải…</p>'),
    ('This browser is not letting the page save, so your best scores and settings will not be kept.',
     'Trình duyệt này không cho trang lưu dữ liệu, nên điểm cao nhất và cài đặt sẽ không được giữ lại.'),
    ('<h2 id="guide-title">About pinyin and tone practice</h2>', '<h2 id="guide-title">Về phần luyện pinyin và thanh điệu</h2>'),
    ('<h3>How do I type the tones?</h3>', '<h3>Gõ thanh điệu thế nào?</h3>'),
    ('<p>Put a number after each syllable: 1 for the first tone (mā), 2 for the second (má), 3 for the third (mǎ), '
     '4 for the fourth (mà), and 5 or nothing for the neutral tone, so 你好 is ni3hao3 and 朋友 is peng2you5 or '
     'peng2you. Tone marks work too, if your keyboard has them. Type ü as v (女 is nv3) or u:. Spaces, apostrophes '
     'and capital letters do not matter. On a phone, the buttons under the box add the numbers and ü.</p>',
     '<p>Ghi một con số sau mỗi âm tiết: 1 cho thanh 1 (mā), 2 cho thanh 2 (má), 3 cho thanh 3 (mǎ), 4 cho thanh 4 '
     '(mà), và 5 hoặc không ghi gì cho thanh nhẹ. Ví dụ 你好 gõ là ni3hao3, 朋友 gõ là peng2you5 hoặc peng2you. Nếu bàn '
     'phím có dấu thanh thì gõ dấu cũng được. Gõ ü là v (女 là nv3) hoặc u:. Dấu cách, dấu nháy và chữ hoa không ảnh '
     'hưởng. Trên điện thoại, các nút dưới ô nhập giúp thêm số và chữ ü.</p>'),
    ('<h3>Which pinyin counts as right?</h3>', '<h3>Pinyin thế nào thì được tính là đúng?</h3>'),
    ('<p>The readings of the HSK 3.0 word list, the same as on the <a href="/hsk-1-word-list/">word list pages</a>. '
     'Pinyin writes each syllable with its own tone, so 你好 is nǐ hǎo even though it is said ní hǎo. The one '
     'exception is 一 and 不: the word lists write their changed tones (一起 yìqǐ, 不客气 bú kèqi), and the original '
     'tones (yīqǐ, bù kèqi) are accepted too.</p>',
     '<p>Cách đọc theo danh sách từ HSK 3.0, giống trên các <a href="/vi/hsk-1-word-list/">trang danh sách từ</a>. '
     'Pinyin ghi mỗi âm tiết với thanh điệu gốc của nó, nên 你好 viết là nǐ hǎo dù khi nói đọc là ní hǎo. Ngoại lệ duy '
     'nhất là 一 và 不: danh sách từ ghi thanh điệu đã biến đổi (一起 yìqǐ, 不客气 bú kèqi), và gõ thanh điệu gốc '
     '(yīqǐ, bù kèqi) cũng được tính là đúng.</p>'),
    ('<h3>What do the tone numbers mean?</h3>', '<h3>Các con số thanh điệu nghĩa là gì?</h3>'),
    ('<p>In "Choose the tones", 3-3 means two third tones, like 你好 nǐ hǎo, and 5 is the neutral tone, like the '
     'second syllable of 朋友 péngyou. The answer is the tones as written. When you hear a word, words whose tones '
     'change in speech (a third tone before a third tone, 一 and 不) are left out, so what you hear is what is '
     'written. Read more about <a href="/mandarin-tone-changes/">tone changes</a>.</p>',
     '<p>Trong phần "Chọn thanh điệu", 3-3 nghĩa là hai thanh 3, như 你好 nǐ hǎo, còn 5 là thanh nhẹ, như âm tiết thứ '
     'hai của 朋友 péngyou. Đáp án là thanh điệu theo cách viết. Khi luyện nghe, những từ có thanh điệu thay đổi lúc '
     'nói (thanh 3 đứng trước thanh 3, 一 và 不) đã được bỏ ra, nên điều bạn nghe luôn khớp với cách viết. Xem thêm về '
     '<a href="/mandarin-tone-changes/" hreflang="en">biến điệu</a> (tiếng Anh).</p>'),
    ('<h3>Where is my score kept?</h3>', '<h3>Điểm của tôi được lưu ở đâu?</h3>'),
    ('<p>Your best score for each level and mode is kept in this browser on this device, and nothing is sent '
     'anywhere. Words you miss can go straight into the <a href="/hsk-flashcards/">flashcards</a>. To train your '
     'ear with whole sentences, try the <a href="/chinese-listening-practice/">listening practice</a>.</p>',
     '<p>Điểm cao nhất của từng cấp và từng kiểu luyện được lưu trong trình duyệt trên thiết bị này, không gửi đi đâu '
     f'cả. Những từ làm sai có thể thêm ngay vào <a href="{STUDY_URL}">flashcard</a>. Muốn luyện tai với cả câu, hãy '
     f'thử phần <a href="{LISTEN_URL}">luyện nghe</a>.</p>'),
    ('<p><b>Words and tones.</b> HSK 3.0 (New HSK) vocabulary, 2025 syllabus, the same lists as the '
     '<a href="/hsk-1-word-list/">word list pages</a>. Tones checked against '
     '<a href="https://github.com/drkameleon/complete-hsk-vocabulary">complete-hsk-vocabulary</a> (MIT). Audio uses '
     'your device\'s Chinese voice.</p>',
     f'<p><b>Từ và thanh điệu.</b> {WORDS_NOTE} Thanh điệu được đối chiếu với '
     '<a href="https://github.com/drkameleon/complete-hsk-vocabulary" hreflang="en">complete-hsk-vocabulary</a> (MIT). '
     'Âm thanh dùng giọng tiếng Trung của thiết bị.</p>'),
]

# --- tracing ---------------------------------------------------------------------------------------------------------

TRACE_UI = {
    "of": "/", "charN": "Chữ {i} / {n}", "strokeN": "Nét {i} / {n}", "set": "Chữ {a}–{b}",
    "traced": "Đã tô {d} / {n} chữ", "loading": "Đang tải…",
    "loadFail": "Không tải được dữ liệu nét chữ. Hãy kiểm tra kết nối mạng rồi thử lại.",
    "start": "Bắt đầu từ dấu chấm và đi theo mũi tên.", "startNoHint": "Hãy viết nét đầu tiên.",
    "goOn": "Tốt lắm. Giờ đến nét tiếp theo.", "goOnNoHint": "Tốt lắm. Giờ đến nét tiếp theo.",
    "wrong": "Chưa đúng. Bắt đầu từ dấu chấm và đi theo mũi tên.",
    "wrongAgain": "Xem nét này được viết thế nào, rồi thử lại.",
    "tooShort": "Hãy vẽ trọn cả nét trong một lần, không nhấc ngón tay.",
    "done": "Giỏi lắm!", "doneMistakes": "Xong, sai {m} lần.", "mistake": "", "mistakes": "",
    "showMe": "Xem cách viết", "restart": "Viết lại", "next": "Chữ tiếp theo", "skip": "Bỏ qua", "finish": "Xem kết quả",
    "boardLabel": "Ô tập tô chữ {c}. Vẽ từng nét bằng ngón tay hoặc chuột.",
    "sumHead": "Xong một bộ", "sumLine": "Bạn đã tô {t} / {n} chữ, trong đó {c} chữ không sai nét nào.",
    "skipped": "bỏ qua", "noMistake": "không sai",
    "again": "Tô lại bộ này", "nextSet": "10 chữ tiếp theo", "nextLevel": "Cấp tiếp theo: HSK {m}",
    "print": "In các chữ này thành phiếu tập viết", "printBase": V + "chinese-character-worksheets/",
    "mineEmpty": "Hãy gõ vài chữ Hán trước.", "mineNone": "Không có dữ liệu nét chữ cho: {c}",
    "mineCount": "{n} chữ, chia thành các bộ 10 chữ.", "mineSet": "Chữ của tôi",
}

TRACE_SWAPS = [
    EYEBROW,
    ('<h1><span class="zh">描红</span>Chinese Character Tracing</h1>',
     '<h1><span class="zh">描红</span>Tập tô chữ Hán theo thứ tự nét</h1>'),
    ('<p class="lede">Write Chinese characters stroke by stroke with your finger or a mouse. Each stroke is checked as '
     'you write it: where it starts, the way it goes and the path it follows. Pick an HSK level or type your own '
     'characters.</p>',
     '<p class="lede">Viết chữ Hán từng nét bằng ngón tay hoặc chuột. Mỗi nét được kiểm tra ngay khi bạn viết: điểm bắt '
     'đầu, hướng đi và đường nét. Chọn một cấp HSK hoặc tự gõ những chữ bạn muốn luyện.</p>'),
    ('<h2 id="pick-title" class="visually-hidden">Choose the characters</h2>',
     '<h2 id="pick-title" class="visually-hidden">Chọn chữ</h2>'),
    ('<div class="levels tr-levels" role="group" aria-label="Characters">\n      <span class="lbl">Characters</span>',
     '<div class="levels tr-levels" role="group" aria-label="Chữ">\n      <span class="lbl">Chữ</span>'),
    ('data-level="0" aria-pressed="false">My characters</button>', 'data-level="0" aria-pressed="false">Chữ của tôi</button>'),
    ('<label for="tr-set">Set</label>', '<label for="tr-set">Bộ</label>'),
    ('<label for="tr-mine">Characters to trace</label>', '<label for="tr-mine">Chữ cần tô</label>'),
    ('id="tr-mine-go">Start tracing</button>', 'id="tr-mine-go">Bắt đầu tô</button>'),
    ('<div class="tr-switches" role="group" aria-label="Show">', '<div class="tr-switches" role="group" aria-label="Hiển thị">'),
    ('aria-pressed="true">Show the character</button>', 'aria-pressed="true">Hiện chữ mờ</button>'),
    ('aria-pressed="true">Show the next stroke</button>', 'aria-pressed="true">Gợi ý nét tiếp theo</button>'),
    ('<h2 id="board-title" class="visually-hidden">Tracing</h2>', '<h2 id="board-title" class="visually-hidden">Tập tô</h2>'),
    ('<p class="empty" id="loading">Loading…</p>', '<p class="empty" id="loading">Đang tải…</p>'),
    ('<p class="tr-keys">Keys: H shows the next stroke, R starts the character again, Enter goes to the next one.</p>',
     '<p class="tr-keys">Phím tắt: H xem nét tiếp theo, R viết lại chữ này, Enter sang chữ tiếp theo.</p>'),
    ('This browser is not letting the page save, so the characters you trace and your settings will not be kept.',
     'Trình duyệt này không cho trang lưu dữ liệu, nên các chữ đã tô và cài đặt sẽ không được giữ lại.'),
    ('<h2 id="guide-title">About character tracing</h2>', '<h2 id="guide-title">Về phần tập tô chữ</h2>'),
    ('<h3>How do I trace a character?</h3>', '<h3>Tô chữ thế nào?</h3>'),
    ('<p>Draw each stroke in one go, from where it starts to where it ends, without lifting your finger. The dot shows '
     'where the next stroke starts and the arrow shows which way it goes. A stroke that follows the right path in the '
     'right direction turns dark. If it does not, it fades away and you try it again; after three tries the page '
     'shows you how the stroke is written. Turn the hints off when you know the character, and turn the grey '
     'character off to write it from memory.</p>',
     '<p>Vẽ mỗi nét liền một lần, từ điểm đầu đến điểm cuối, không nhấc ngón tay. Dấu chấm cho biết nét tiếp theo bắt '
     'đầu ở đâu, mũi tên cho biết hướng đi. Nét đi đúng đường, đúng hướng sẽ chuyển sang màu đậm. Nếu chưa đúng, nét đó '
     'mờ dần và bạn thử lại; sau ba lần thử, trang sẽ cho bạn xem cách viết nét đó. Khi đã thuộc chữ, hãy tắt gợi ý, rồi '
     'tắt cả chữ mờ để viết theo trí nhớ.</p>'),
    ('<h3>Why does stroke order matter?</h3>', '<h3>Vì sao thứ tự nét quan trọng?</h3>'),
    ('<p>Stroke order is the way characters are written by hand. It makes them quicker to write, neater, and easier to '
     'remember. A few rules cover most characters: top before bottom (<span class="zh-inline">三</span>), left before '
     'right (<span class="zh-inline">川</span>), horizontal before vertical (<span class="zh-inline">十</span>), the '
     'stroke to the left before the stroke to the right (<span class="zh-inline">人</span>), the middle before the '
     'sides (<span class="zh-inline">小</span>), and the outside before the inside, closing the box last '
     '(<span class="zh-inline">日</span>).</p>',
     '<p>Thứ tự nét là cách viết chữ Hán bằng tay. Viết đúng thứ tự giúp viết nhanh hơn, đẹp hơn và dễ nhớ chữ hơn. Vài '
     'quy tắc đã đủ cho phần lớn các chữ: trên trước dưới sau (<span class="zh-inline">三</span>), trái trước phải sau '
     '(<span class="zh-inline">川</span>), ngang trước sổ sau (<span class="zh-inline">十</span>), phẩy trước mác sau '
     '(<span class="zh-inline">人</span>), giữa trước hai bên sau (<span class="zh-inline">小</span>), ngoài trước '
     'trong sau, đóng khung sau cùng (<span class="zh-inline">日</span>).</p>'),
    ('<h3>Which characters are in each level?</h3>', '<h3>Mỗi cấp gồm những chữ nào?</h3>'),
    ('<p>The same sets as the <a href="/hsk-1-character-worksheets/">character worksheets</a>: every character used in '
     'the words of that HSK 3.0 level, once, in the order it first appears in the word list. Characters already used '
     'at a lower level are not repeated. Each character comes with the first word of the level that uses it. To '
     'trace anything else, choose My characters and type or paste any Chinese text.</p>',
     f'<p>Giống các bộ chữ của <a href="{V}hsk-1-character-worksheets/">phiếu tập viết</a>: mọi chữ xuất hiện trong từ '
     'vựng của cấp HSK 3.0 đó, mỗi chữ một lần, theo thứ tự lần đầu xuất hiện trong danh sách từ. Chữ đã có ở cấp thấp '
     'hơn không được lặp lại. Mỗi chữ đi kèm từ đầu tiên của cấp có dùng chữ đó. Muốn tô chữ khác, hãy chọn "Chữ của '
     'tôi" rồi gõ hoặc dán bất kỳ đoạn văn tiếng Trung nào.</p>'),
    ('<h3>Is my progress kept?</h3>', '<h3>Tiến độ của tôi có được lưu không?</h3>'),
    ('<p>The characters you have traced, and your settings, are kept in this browser on this device, and nothing is '
     'sent anywhere. Writing on paper helps too: print the same characters as a '
     '<a href="/chinese-character-worksheets/">writing worksheet</a>, and learn the words they come from with the '
     '<a href="/hsk-flashcards/">flashcards</a>.</p>',
     '<p>Các chữ đã tô và cài đặt được lưu trong trình duyệt trên thiết bị này, không gửi đi đâu cả. Viết trên giấy cũng '
     f'rất có ích: in chính những chữ này thành <a href="{V}chinese-character-worksheets/">phiếu tập viết</a>, và học '
     f'các từ chứa chúng bằng <a href="{STUDY_URL}">flashcard</a>.</p>'),
    ('<p><b>Stroke data.</b> Stroke outlines, stroke centre lines and character readings come from '
     '<a href="https://github.com/skishore/makemeahanzi">Make Me a Hanzi</a> (Arphic Public License and GNU LGPL, see '
     '<a href="/strokes/LICENSE.md">licence</a>). Stroke order follows mainland China standards for simplified '
     'characters. Words: HSK 3.0 (New HSK) vocabulary, 2025 syllabus, the same lists as the '
     '<a href="/hsk-1-word-list/">word list pages</a>.</p>',
     '<p><b>Dữ liệu nét chữ.</b> Hình nét, đường tâm của nét và cách đọc chữ lấy từ '
     '<a href="https://github.com/skishore/makemeahanzi" hreflang="en">Make Me a Hanzi</a> (giấy phép Arphic Public '
     'License và GNU LGPL, xem <a href="/strokes/LICENSE.md" hreflang="en">giấy phép</a>). Thứ tự nét theo chuẩn chữ '
     f'giản thể của Trung Quốc đại lục. Từ vựng: {WORDS_NOTE}</p>'),
]


# --- data ------------------------------------------------------------------------------------------------------------

def _plain(s):
    """Lowercase, no brackets."""
    return re.sub(r"\s+", " ", re.sub(r"\([^)]*\)", " ", s.lower())).strip()


def vi_senses(m):
    """A Vietnamese meaning as a list of senses, each a tuple of syllables."""
    out = []
    for part in re.split(r"[;,/]", _plain(m)):
        syl = tuple(x for x in re.split(r"[\s.!?…:“”\"']+", part) if x)
        if syl:
            out.append(syl)
    return out


def _inside(a, b):
    return any(b[k:k + len(a)] == a for k in range(len(b) - len(a) + 1))


def vi_conflicts(en, vi):
    """For each word, the words of the same level whose meaning overlaps in English (as on the English page) or in
    Vietnamese: the same sense, or one sense found whole inside another (vui inside vui vẻ)."""
    ent = [practice._en_tokens(m) for m in en]
    vis = [vi_senses(m) for m in vi]
    out = [[] for _ in en]
    for i in range(len(en)):
        for j in range(i + 1, len(en)):
            hit = bool(ent[i] & ent[j]) or en[i] == en[j] or vi[i] == vi[j]
            if not hit:
                hit = any(a == b or _inside(a, b) or _inside(b, a) for a in vis[i] for b in vis[j])
            if hit:
                out[i].append(j)
                out[j].append(i)
    return out


def _meanings(root, data):
    """{level: [Vietnamese meaning, ...]} in the order of data/hskN.tsv (as tools/practice.py reads it)."""
    out = {}
    for n in LEVELS:
        rows = practice._rows(root, n)
        if [r[0] for r in rows] != [r[0] for r in data[n]]:
            raise SystemExit(f"vi_tools: HSK {n} words differ between data/hsk{n}.tsv and the Vietnamese list")
        out[n] = [r[3] for r in data[n]]
    return out


def _story_sentences(root):
    """{level: [[sentence, pinyin, Vietnamese, "s", slug, Vietnamese title], ...]} from the listening story lines."""
    en_path = root / "data" / "practice" / "listening_stories.tsv"
    vi_path = root / "data" / "vi" / "practice" / "listening_stories_vi.tsv"
    en = [l.split("\t") for l in en_path.read_text(encoding="utf-8").splitlines() if l.strip()]
    vi = [l.split("\t") for l in vi_path.read_text(encoding="utf-8").splitlines() if l.strip()]
    if len(en) != len(vi):
        raise SystemExit(f"{vi_path.relative_to(root)}: {len(vi)} lines, expected {len(en)}")
    levels = {}
    for path in (root / "data" / "stories").glob("*.json"):
        s = json.loads(path.read_text(encoding="utf-8"))
        levels[s["slug"]] = s["level"]
    out, seen = {}, set()
    for i, (e, v) in enumerate(zip(en, vi), 1):
        where = f"data/vi/practice/listening_stories_vi.tsv line {i}"
        if len(v) != 3 or (v[0], v[1]) != (e[0], e[1]) or not v[2].strip():
            raise SystemExit(f"{where}: expected {e[0]}<TAB>{e[1]}<TAB>Vietnamese")
        if HAN.search(v[2]):
            raise SystemExit(f"{where}: Chinese characters in the Vietnamese")
        if v[0] not in STORY_TITLES:
            raise SystemExit(f"{where}: no Vietnamese title for the story {v[0]} in tools/vi_tools.py")
        key = listening._key(e[2])
        if key in seen:
            continue
        seen.add(key)
        out.setdefault(levels[v[0]], []).append(
            [e[1], unicodedata.normalize("NFC", e[2]), v[2].strip(), "s", v[0], STORY_TITLES[v[0]]])
    return out


def _vi_pages(root):
    return {p["slug"]: p for p in learn_vi.load_pages(root)}


def _vi_gaps(root, gaps):
    """{level: [[before, after, answer, options, Vietnamese, answer pinyin, sentence pinyin, slug], ...]}: the checked gap
    sentences of tools/practice.py whose grammar page has a Vietnamese file, with the Vietnamese of that file. A level
    gets gap sentences only once they come from at least two Vietnamese grammar pages (the rule of daily._check_data):
    until then its questions are meanings, pinyin and listening only."""
    pages = _vi_pages(root)
    out = {}
    for n, items in gaps.items():
        for x in items:
            p = pages.get(x["slug"])
            if not p:
                continue
            kind, a, b = x["loc"]
            if kind == "w":
                it = p["worksheet"]["exercises"][a]["items"][b]
                if it["zh"] != x["before"] + practice.BLANK + x["after"]:
                    raise SystemExit(f"vi_tools: gap sentence not found on data/vi/learn/{x['slug']}.json")
            else:
                it = p["sections"][a]["examples"][b]
                if it["zh"] != x["before"] + x["answer"] + x["after"]:
                    raise SystemExit(f"vi_tools: gap sentence not found on data/vi/learn/{x['slug']}.json")
            vi = it["en"]  # learn_vi merges the Vietnamese into the "en" field of the English page
            if HAN.search(vi):
                raise SystemExit(f"vi_tools: Chinese characters in the Vietnamese of a gap sentence on {x['slug']}")
            out.setdefault(n, []).append(
                [x["before"], x["after"], x["answer"], x["options"], vi, x["apy"], x["spy"], x["slug"]])
    return {n: items for n, items in out.items() if len({g[7] for g in items}) >= 2}


def _grammar_sentences(root):
    """{level: [[sentence, pinyin, Vietnamese, "g", slug, Vietnamese heading], ...]}: the example sentences of the
    Vietnamese grammar pages that the listening practice can use (the same rule as tools/listening.py, whose build
    checks their words and pinyin)."""
    out = {}
    for slug, p in sorted(_vi_pages(root).items()):
        n = p["level"]
        if n not in listening.SENTENCE_LEVELS:
            continue
        for s in p["sections"]:
            for e in s.get("examples", []):
                if not listening.SENTENCE_OK.match(e["zh"]) or len(listening.HAN.findall(e["zh"])) > listening.MAX_HAN:
                    continue
                if HAN.search(e["en"]):
                    raise SystemExit(f"vi_tools: Chinese characters in the Vietnamese of an example on {slug}")
                out.setdefault(n, []).append([e["zh"], e["py"], e["en"], "g", slug, p["h1"]])
    return out


def _sentences(root):
    """Grammar sentences first, then story sentences (as on the English page); one of each set of sentences that sound
    the same, tones aside: the first."""
    out = {}
    for src in (_grammar_sentences(root), _story_sentences(root)):
        for n, items in src.items():
            for x in items:
                out.setdefault(n, []).append(x)
    for n in out:
        seen, keep = set(), []
        for x in out[n]:
            k = listening._key(x[1])
            if k not in seen:
                seen.add(k)
                keep.append(x)
        out[n] = keep
    return out


def _json(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")


def _swap(body, pairs, what):
    for a, b in pairs:
        if body.count(a) != 1:
            raise SystemExit(f"vi_tools: English text not found once in {what}: {a[:60]}")
        body = body.replace(a, b)
    return body


def _ld(name, url, desc):
    return (f'<script type="application/ld+json">'
            + json.dumps({"@context": "https://schema.org", "@type": "WebApplication", "name": name, "url": url,
                          "inLanguage": "vi", "applicationCategory": "EducationalApplication", "operatingSystem": "Any",
                          "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"}, "description": desc},
                         ensure_ascii=False) + "</script>")


def _css(tpl, *names):
    return "".join((tpl / n).read_text(encoding="utf-8") for n in names)


def build(*, root, tpl, write, nav, base_css, vi_css, data):
    """Write the Vietnamese tool pages and their JSON. write(url, title, description, css, body, head_extra)."""
    meanings = _meanings(root, data)

    # Flashcards
    for n in LEVELS:
        rows = study._english(root, n)
        _json(root / STUDY_URL.strip("/") / f"hsk{n}.json", [[w, p, m] for (w, p, _), m in zip(rows, meanings[n])])
    body = _swap(study._body(tpl, nav(STUDY_URL), STUDY_UI, STUDY_URL), STUDY_SWAPS, "templates/study_body.html")
    desc = ("Flashcard từ vựng HSK 3.0 cấp 1–5 miễn phí, có nghĩa tiếng Việt và lịch ôn tập mỗi ngày. Không cần đăng "
            "ký, tiến độ lưu trên máy bạn.")
    write(STUDY_URL, "Flashcard HSK 1–5: học từ vựng HSK mỗi ngày, có nghĩa tiếng Việt", desc,
          base_css + _css(tpl, "checker.css", "study.css") + vi_css, body, _ld("Flashcard HSK", STUDY_URL, desc))

    # Practice test (gap sentences only from the grammar pages that have a Vietnamese file: see the docstring)
    levels, gaps = practice._level_data(root)
    vgaps = _vi_gaps(root, gaps)
    gap_levels = [n for n in LEVELS if vgaps.get(n)]
    for n in LEVELS:
        rows = levels[n]["words"]
        conf = vi_conflicts([r[2] for r in rows], meanings[n])
        # also keep apart the words the English and Thai pages keep apart (c): never fewer checks than there
        words = [[w, p, meanings[n][i], wp, audio, sorted(set(c) | set(conf[i]))]
                 for i, (w, p, m, wp, audio, c) in enumerate(rows)]
        practice._check_level(n, words)
        _json(root / PRACTICE_URL.strip("/") / f"hsk{n}.json", {"w": words, "g": vgaps.get(n, [])})
    body = _swap(practice._body(tpl, nav(PRACTICE_URL), PRACTICE_UI, PRACTICE_URL), practice_swaps(gap_levels),
                 "templates/practice_body.html")
    parts = "nghĩa, pinyin, nghe và ngữ pháp" if gap_levels else "nghĩa, pinyin và nghe"
    desc = (f"Thi thử HSK online miễn phí cho HSK 1–5 (HSK 3.0): 20 câu về {parts}, có nghĩa tiếng Việt và "
            "đáp án sau mỗi câu.")
    write(PRACTICE_URL, "Thi thử HSK online miễn phí: trắc nghiệm HSK 1–5 có đáp án", desc,
          base_css + _css(tpl, "checker.css", "practice.css") + vi_css, body, _ld("Thi thử HSK", PRACTICE_URL, desc))

    # Daily quiz (loads the practice test's files)
    daily._check_data(root, PRACTICE_URL, need_gaps=False)  # levels with gaps need at least two grammar pages
    body = _swap(daily._body(tpl, nav(DAILY_URL), DAILY_UI, PRACTICE_URL), daily_swaps(gap_levels),
                 "templates/daily_body.html")
    desc = (f"Mỗi ngày một bài trắc nghiệm HSK 10 câu mới cho HSK 1–5 (HSK 3.0): {parts}, có đáp án. Giữ "
            "chuỗi ngày học. Miễn phí.")
    write(DAILY_URL, "Trắc nghiệm HSK mỗi ngày: 10 câu miễn phí cho HSK 1–5", desc,
          base_css + daily._css(tpl) + vi_css, body, _ld("Trắc nghiệm HSK mỗi ngày", DAILY_URL, desc))

    # Listening (words of every level; story sentences at HSK 1-4)
    listening._data(root)  # checks every sentence of the English page, story lines included
    sents = _sentences(root)
    for n in LEVELS:
        words = [[w, p, meanings[n][i]] for i, (w, p, m, _wp, audio, _c) in enumerate(levels[n]["words"]) if audio]
        if len(words) < 50:
            raise SystemExit(f"vi_tools: listening HSK {n} has only {len(words)} words a voice can say")
        s = sents.get(n, [])
        if s and len(s) < 6:
            raise SystemExit(f"vi_tools: listening HSK {n} needs at least 6 sentences for wrong options")
        if n in listening.SENTENCE_LEVELS and not s:
            raise SystemExit(f"vi_tools: listening HSK {n} has no sentences")
        _json(root / LISTEN_URL.strip("/") / f"hsk{n}.json", {"w": words, "s": s})
    has_grammar = any(x[3] == "g" for n in sents for x in sents[n])
    body = _swap(listening._body(tpl, nav(LISTEN_URL), LISTEN_UI, LISTEN_URL), listen_swaps(has_grammar),
                 "templates/listening_body.html")
    desc = ("Luyện nghe tiếng Trung miễn phí cho HSK 1–5 (HSK 3.0): nghe từ hoặc câu ngắn rồi chọn đáp án. Nghe chậm, "
            "chế độ chỉ pinyin, nghĩa tiếng Việt.")
    write(LISTEN_URL, "Luyện nghe tiếng Trung HSK 1–5 online miễn phí, có đáp án", desc,
          base_css + listening._css(tpl) + vi_css, body, _ld("Luyện nghe tiếng Trung", LISTEN_URL, desc))

    # Pinyin and tones
    pdata, _levels = pinyin_practice._data(root)
    for n in LEVELS:
        words, _ = pdata[n]
        words = [[w, p, meanings[n][i], acc, tone, hear, audio] for w, p, m, acc, tone, hear, audio, i in words]
        pinyin_practice._check(n, words)
        _json(root / PINYIN_URL.strip("/") / f"hsk{n}.json", {"w": words})
    body = _swap(pinyin_practice._body(tpl, nav(PINYIN_URL), PINYIN_UI, PINYIN_URL), PINYIN_SWAPS,
                 "templates/pinyin_body.html")
    desc = ("Luyện pinyin và thanh điệu tiếng Trung miễn phí cho HSK 1–5 (HSK 3.0): gõ pinyin của từ, hoặc nhìn, nghe "
            "rồi chọn thanh điệu.")
    write(PINYIN_URL, "Luyện pinyin và thanh điệu tiếng Trung HSK 1–5 online", desc,
          base_css + pinyin_practice._css(tpl) + vi_css, body, _ld("Luyện pinyin và thanh điệu", PINYIN_URL, desc))

    # Character tracing (stroke files shared with the English page)
    sets, rows, strokes, _thai = tracing._data(root)
    for n in LEVELS:
        if [r[0] for r in rows[n]] != [r[0] for r in data[n]]:
            raise SystemExit(f"vi_tools: tracing HSK {n} rows differ from the Vietnamese list")
        out = []
        for c, i in sets[n]:
            w, p, _m = rows[n][i]
            out.append([c, " / ".join(strokes[c]["p"]), w, p, meanings[n][i]])
        _json(root / TRACE_URL.strip("/") / f"hsk{n}.json", {"c": out})
    body = _swap(tracing._body(tpl, nav(TRACE_URL), TRACE_UI, TRACE_URL, tracing._counts(sets)), TRACE_SWAPS,
                 "templates/tracing_body.html")
    desc = ("Tập tô chữ Hán từng nét trên ô chữ điền bằng ngón tay hoặc chuột, có gợi ý nét tiếp theo. Chọn chữ theo cấp "
            "HSK 1–5 hoặc tự gõ. Miễn phí.")
    write(TRACE_URL, "Tập tô chữ Hán online theo thứ tự nét, HSK 1–5 miễn phí", desc,
          base_css + tracing._css(tpl) + vi_css, body, _ld("Tập tô chữ Hán", TRACE_URL, desc))

    return [STUDY_URL, PRACTICE_URL, DAILY_URL, LISTEN_URL, PINYIN_URL, TRACE_URL]


def alternates():
    return {study.URL: STUDY_URL, practice.URL: PRACTICE_URL, daily.URL: DAILY_URL, listening.URL: LISTEN_URL,
            pinyin_practice.URL: PINYIN_URL, tracing.URL: TRACE_URL}
