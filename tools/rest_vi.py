"""The rest of the Vietnamese pages under /vi/ (VI.md, Phase 2 step 4). Called from tools/build_vi.py.

  vi/chinese-measure-words/              measure word finder (data as the English page, Vietnamese text from
                                         data/vi/measure_words_vi.tsv and data/vi/classifiers_vi.tsv; template
                                         templates/vi/measure_body.html)
  vi/old-hsk-to-new-hsk/                 old HSK -> new HSK, the English template with its text swapped for Vietnamese
                                         (as tools/upgrade_th.py does for Thai); Vietnamese meanings for new HSK 1-5
  vi/yct/                                YCT overview, yct-N-word-list/, yct-N-character-worksheets/,
                                         yct-N-vocabulary-worksheets/ (tools/yct_ws.py) and yct-vs-hsk/ (tools/yct.py),
                                         with Vietnamese meanings from data/vi/yct/yctN_vi.tsv
  vi/reading/                            graded stories with Vietnamese glosses (tools/reading.py)

Data files (the build stops if one does not line up with the English data):
  data/vi/measure_words_vi.tsv   noun<TAB>Vietnamese meaning[<TAB>Vietnamese note], the nouns of data/measure_words.tsv
                                 in order; a note exactly where the English has one
  data/vi/classifiers_vi.tsv     measure word<TAB>what it counts, in the order of data/classifiers.tsv
  data/vi/yct/yctN_vi.tsv        word<TAB>Vietnamese meaning, in the order of data/yct/yctN.tsv; a word that appears at
                                 several levels has the same meaning at each
No Vietnamese text may hold a tab; meanings and uses may not hold Chinese characters (notes may, for examples).
"""
import html
import json
import re
import unicodedata

import reading
import upgrade_th
import worksheets_th
import yct
import yct_ws

V = "/vi/"
MW_URL = V + "chinese-measure-words/"
UP_URL = V + "old-hsk-to-new-hsk/"
YCT_URL = V + "yct/"
HAN = re.compile(r"[㐀-鿿豈-﫿]")

NAV_TOOLS = [(MW_URL, "Lượng từ"), (UP_URL, "HSK cũ → mới")]
NAV_YCT = [(YCT_URL, "YCT")]


def zh(s):
    return f'<span class="zh-inline">{s}</span>'


def _rows(root, rel, ncols, han_ok=()):
    """Rows of a data/vi/ file, checked: ncols (min, max) columns, no empty field, no Chinese outside han_ok columns."""
    path = root / rel
    rows = []
    for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        parts = [p.strip() for p in line.split("\t")]
        if not (ncols[0] <= len(parts) <= ncols[1]) or not all(parts):
            raise SystemExit(f"{rel} line {i}: wrong number of columns or an empty field")
        for k, p in enumerate(parts[1:], 1):
            if k not in han_ok and HAN.search(p):
                raise SystemExit(f"{rel} line {i}: Chinese characters in column {k + 1}")
        rows.append(parts)
    return rows


def available(root):
    return all((root / "data" / "vi" / f).exists() for f in ("measure_words_vi.tsv", "classifiers_vi.tsv")) and \
        all((root / "data" / "vi" / "yct" / f"yct{n}_vi.tsv").exists() for n in yct.LEVELS)


# --- measure words ---------------------------------------------------------------------------------------------------

def build_measure(*, root, tpl, site, write, nav, css, measure, level_table, search_key, vi_key):
    classifiers = measure["read_classifiers"]()
    entries = measure["read_measure_words"](classifiers)
    nouns = _rows(root, "data/vi/measure_words_vi.tsv", (2, 3), han_ok=(2,))
    mws = _rows(root, "data/vi/classifiers_vi.tsv", (2, 2))
    if [r[0] for r in nouns] != [e[0] for e in entries]:
        raise SystemExit("data/vi/measure_words_vi.tsv does not match data/measure_words.tsv noun for noun")
    if [r[0] for r in mws] != list(classifiers):
        raise SystemExit("data/vi/classifiers_vi.tsv does not match data/classifiers.tsv")
    for e, r in zip(entries, nouns):
        if bool(e[4]) != (len(r) == 3):
            raise SystemExit(f"data/vi/measure_words_vi.tsv: {e[0]} needs a note exactly when the English has one")
    use = {r[0]: r[1] for r in mws}
    levels = level_table()
    yi_before, zh_spans, squash = measure["yi_before"], measure["zh_spans"], measure["squash"]

    data, rows, by_mw = [], [], {m: [] for m in classifiers}
    for (word, pinyin, meaning, word_mws, _), r in zip(entries, nouns):
        vi = r[1]
        note = r[2] if len(r) == 3 else ""
        items = []
        for m in word_mws:
            mpy = classifiers[m][0]
            items.append({"c": m, "ex": f"一{m}{word}", "expy": f"{yi_before(mpy)} {mpy} {pinyin}"})
            by_mw[m].append(word)
        keys = [squash(pinyin), squash(unicodedata.normalize("NFD", pinyin.lower()).replace("ü", "v"))]
        data.append({"w": word, "p": pinyin, "en": vi, "lv": levels.get(word), "m": items,
                     "note": zh_spans(note) if note else "", "keys": keys})
        if word_mws:
            first = classifiers[word_mws[0]][0]
            others = "、".join(word_mws[1:])
            cell = f"{word_mws[0]} <small>{html.escape(first)}</small>" + (f" <small>hoặc {others}</small>" if others else "")
        else:
            cell = "<small>không cần</small>"
        key = html.escape(search_key(word, pinyin, meaning) + "|" + vi_key(vi) + "|" + "".join(word_mws), quote=True)
        rows.append(f'          <tr data-w="{html.escape(word)}" data-k="{key}"><td class="hz"><b>{html.escape(word)}</b>'
                    f'<span>{html.escape(pinyin)}</span></td><td class="en">{html.escape(vi)}</td><td class="mw">{cell}</td></tr>')

    mw_json = {m: {"p": p, "e": use[m]} for m, (p, _) in classifiers.items()}
    index = []
    for m, (p, _) in classifiers.items():
        links = "、".join(f'<a href="#{html.escape(w)}">{html.escape(w)}</a>' for w in by_mw[m])
        index.append(f'      <div><dt>{m}<span>{html.escape(p)}</span></dt><dd><span class="use">{html.escape(use[m])}</span>'
                     f'<span class="nouns">{links}</span></dd></div>')
    body = (tpl / "vi" / "measure_body.html").read_text(encoding="utf-8")
    body = (body.replace("__NAV__", nav(MW_URL))
            .replace("__ROWS__", "\n".join(rows))
            .replace("__INDEX__", "\n".join(index))
            .replace("__NOUNCOUNT__", str(len(entries)))
            .replace("__MWCOUNT__", str(len(classifiers)))
            .replace("__DATA_JSON__", json.dumps(data, ensure_ascii=False, separators=(",", ":")))
            .replace("__MW_JSON__", json.dumps(mw_json, ensure_ascii=False, separators=(",", ":"))))
    ld = json.dumps({
        "@context": "https://schema.org", "@type": "WebApplication", "name": "Tra lượng từ tiếng Trung",
        "url": site + MW_URL, "inLanguage": "vi", "applicationCategory": "EducationalApplication",
        "operatingSystem": "Any", "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"},
        "description": "Tra lượng từ tiếng Trung (量词) đi với danh từ, kèm pinyin, ví dụ và cấp HSK.",
    }, ensure_ascii=False)
    write(MW_URL, "Lượng từ tiếng Trung (量词): danh từ nào đi với lượng từ nào",
          f"Tra lượng từ tiếng Trung (量词) cho {len(entries)} danh từ thông dụng bằng chữ Hán, pinyin hoặc tiếng Việt, "
          "kèm ví dụ và cấp HSK 3.0. Miễn phí.",
          css, body, f'<script type="application/ld+json">{ld}</script>')


# --- old HSK -> new HSK ----------------------------------------------------------------------------------------------

# Vietnamese for each English string that tools/upgrade_th.py swaps, in the same order (zipped with upgrade_th.UI).
UP_VI = [
    '<span class="chip">Miễn phí</span>',
    '<h1><span class="zh">新旧</span>HSK cũ sang HSK mới</h1>',
    '<p class="lede">Bạn từng học HSK cũ 6 cấp? Chọn cấp bạn đã học xong và cấp HSK mới bạn muốn đạt. Trang chỉ hiện '
    "những từ bạn chưa học, các chữ Hán mới trong những từ đó, và một tệp để nhập vào Anki hoặc Pleco.</p>",
    '<h2 id="pick-title" class="visually-hidden">Chọn cấp độ</h2>',
    '<label for="old-level">Tôi đã học HSK cũ</label>',
    '<option value="0">Chưa học</option>',
    "HSK cũ 1 (150 từ)", "HSK cũ 2 (300 từ)", "HSK cũ 3 (600 từ)", "HSK cũ 4 (1.200 từ)", "HSK cũ 5 (2.500 từ)",
    "HSK cũ 6 (5.000 từ)",
    '<label for="new-level">Mục tiêu HSK mới</label>',
    ">HSK mới 1<", ">HSK mới 2<", ">HSK mới 3<", ">HSK mới 4<", ">HSK mới 5<", ">HSK mới 6<", ">HSK mới 7–9<",
    '<h2 id="sum-title">Những gì bạn còn cần học</h2>',
    '<p class="pack-cta" id="pack-cta" hidden><b>Muốn có danh sách này trên giấy?</b> '
    '<a href="/upgrade-packs/old-hsk-1-to-new-hsk-1/" hreflang="en">Bộ tài liệu HSK 1 cũ → HSK 1 mới</a> (bằng tiếng '
    "Anh) có đúng các từ này kèm câu ví dụ, phần luyện viết chữ mới và bài kiểm tra, sẵn sàng để in. $3.99.</p>",
    '<p class="status" id="load-status">Đang tải danh sách từ…</p>',
    "<span>từ cần học</span>",
    "<span>chữ Hán mới</span>",
    "<span>từ bạn đã học</span>",
    '<th scope="col">Cấp mới</th><th scope="col" class="num">Số từ</th><th scope="col" class="num">Đã học</th>'
    '<th scope="col" class="num">Cần học</th>',
    '<h2 id="words-title">Từ cần học</h2>',
    'aria-label="Chọn nhóm từ để hiển thị"',
    '<span id="g-hard">Chữ mới</span>',
    '<span id="g-easy">Chữ đã biết</span>',
    '<span id="g-all">Tất cả</span>',
    '<p class="hint" id="group-hint"></p>',
    '<label class="visually-hidden" for="word-search">Tìm trong các từ này</label>',
    'placeholder="Tìm: 学, xue hoặc học"',
    '<th scope="col">Từ</th><th scope="col">Pinyin</th><th scope="col">Nghĩa</th><th scope="col" class="lv">Cấp</th>',
    '<p class="empty" id="no-words" hidden>Không có từ nào ở đây.</p>',
    'id="more-btn" hidden>Xem thêm</button>',
    'id="dl-btn">Tải về cho Anki / Pleco</button>',
    'id="copy-words">Sao chép các từ</button>',
    '<p class="hint">Tệp tải về là tệp .txt phân cách bằng tab (từ, pinyin, nghĩa) gồm các từ đang hiện ở trên. Anki: '
    "File → Import. Pleco: Flashcards → Import Cards. Nút “Sao chép các từ” cho mỗi từ một dòng, Skritter và phần lớn "
    "ứng dụng đều nhận được.</p>",
    '<h2 id="chars-title">Chữ Hán mới</h2>',
    '<p class="hint">Các chữ Hán trong những từ này chưa từng xuất hiện trong từ nào của cấp HSK cũ bạn đã học, xếp theo '
    "thứ tự bạn sẽ gặp.</p>",
    '<p class="empty" id="no-chars" hidden>Không có chữ mới. Mọi từ trong danh sách của bạn đều dùng những chữ bạn đã '
    "biết.</p>",
    '<a class="button" id="ws-link" href="/vi/chinese-character-worksheets/">In phiếu tập viết</a>',
    'id="copy-chars">Sao chép các chữ</button>',
    "Trang tạo phiếu tập viết nhận tối đa 400 chữ mỗi lần, nên liên kết mở 400 chữ đầu tiên. Hãy sao chép phần còn lại "
    "và dán vào sau.",
    '<h2 id="about-title">Danh sách từ HSK cũ và mới khác nhau thế nào</h2>',
    "<h3>Vì sao từ HSK cũ không chuyển sang HSK mới theo đúng từng cấp</h3>",
    "<p>HSK cũ có 6 cấp và khoảng 5.000 từ. HSK 3.0 có 9 cấp, và đề cương 2025 phân bổ từ vựng theo cách khác: nhiều từ "
    "chuyển xuống cấp thấp hơn, nhiều từ là từ mới, và một số từ cũ bị bỏ. Đỗ HSK 4 cũ không có nghĩa là bạn đã biết các "
    "từ của HSK 4 mới.</p>",
    "<h3>Một ví dụ</h3>",
    "<h3>“Chữ mới” và “chữ đã biết”</h3>",
    f"<p>Nhiều từ trông như từ mới thật ra được ghép từ những chữ bạn đã biết. Danh sách cũ có {zh('这')} và {zh('个')}, "
    f"danh sách mới tính {zh('这个')} là một từ riêng. Những từ như vậy nằm trong nhóm “chữ đã biết” và thường học rất "
    "nhanh. Từ có chữ bạn chưa học bao giờ nằm trong nhóm “chữ mới”: hãy bắt đầu từ nhóm này.</p>",
    "<p><b>Cách tính.</b> Mỗi từ của các cấp HSK mới bạn chọn được tra trong danh sách HSK cũ. Nếu từ đó có ở cấp cũ bạn "
    "chọn hoặc thấp hơn, từ được tính là đã học. Từ được so sánh đúng như cách viết, nên một từ chỉ được tính là đã học "
    f"khi danh sách cũ có đúng từ đó. Từ kết thúc bằng {zh('儿')} cũng khớp với cùng từ đó khi không có 儿, và một từ nằm "
    f"trong một mục của danh sách cũ cũng được tính là đã học ({zh('篮球')} trong {zh('打篮球')}).</p>",
    "<p><b>Nguồn.</b> HSK mới 1–4: danh sách của chính trang này theo đề cương 2025, HSK 1–3 đã đối chiếu với hai bản "
    "sao được công bố và HSK 4 với một bản. HSK mới 5–9 và HSK cũ 1–6: bộ dữ liệu mở "
    '<a href="https://github.com/drkameleon/complete-hsk-vocabulary" hreflang="en">complete-hsk-vocabulary</a> (giấy '
    "phép MIT), nghĩa lấy từ CC-CEDICT. Cấp 5–9 chưa được đối chiếu. Từ HSK mới 1–5 có nghĩa tiếng Việt; cấp 6–9 hiện "
    "vẫn ghi nghĩa tiếng Anh.</p>",
    "<p><b>Quyền riêng tư.</b> Mọi thứ chạy trong trình duyệt của bạn. Những gì bạn chọn không được gửi đi đâu cả.</p>",
    # script
    '  let result = { hard: [], easy: [], chars: "" }, shown = PAGE;\n  const VI = __VI_JSON__;\n'
    "  const mean = x => VI[x[0]] || x[2];",
    'const norm = s => s.toLowerCase().replace(/đ/g, "d").normalize("NFD").replace(/[\\u0300-\\u036f]/g, "")'
    '.replace(/[\\s\'’-]/g, "");',
    '"|" + norm(x[2]) + "|" + norm(mean(x)) };',
    '$("summary-line").textContent = "HSK mới " + (T === 1 ? "1" : T === 7 ? "1–9" : "1–" + T) + " có " + fmt(total) '
    '+ " từ. " +\n'
    '      (O ? "Bạn đã học " + fmt(total - todo) + " từ trong số đó ở HSK cũ 1" + (O > 1 ? "–" + O : "") + ". " : "") +\n'
    '      "Trong những từ còn lại, " + fmt(hard.length) + " từ có chữ bạn chưa học; " + fmt(easy.length) + '
    '" từ chỉ dùng những chữ bạn đã biết.";',
    '$("g-hard").textContent = "Chữ mới (" + fmt(hard.length) + ")";',
    '$("g-easy").textContent = "Chữ đã biết (" + fmt(easy.length) + ")";',
    '$("g-all").textContent = "Tất cả (" + fmt(todo) + ")";',
    'ws.href = "/vi/chinese-character-worksheets/#c="',
    '    hard: "Những từ có ít nhất một chữ bạn chưa học. Chữ mới được tô đỏ.",\n'
    '    easy: "Những từ chỉ gồm các chữ bạn đã biết từ HSK cũ, như 这个 từ 这 và 个. Thường học rất nhanh.",\n'
    '    all: "Tất cả các từ bạn còn cần học, gộp cả hai nhóm.",',
    '<td class="en">${esc(mean(x))}</td>',
    '$("word-count").textContent = list.length > shown ? "Đang hiện " + fmt(shown) + "/" + fmt(list.length) + " từ" '
    ': fmt(list.length) + " từ";',
    '$("load-status").textContent = "Đang tải từ HSK 7–9…";',
    '$("load-status").textContent = "Không tải được danh sách từ. Hãy kiểm tra kết nối mạng rồi tải lại trang.";',
    'flash(id, "Đã sao chép " + what + ".");',
    'flash(id, "Không sao chép được. Hãy chọn văn bản và tự sao chép.");',
    "const lines = list.map(({ x }) => [x[0], x[1], mean(x)]",
    'flash("words-status", "Đã tải về " + fmt(list.length) + " từ.");',
    '"words-status", "các từ"));',
    '"chars-status", fmt(result.chars.length) + " chữ"));',
]
UP_EXTRA = [('const fmt = n => n.toLocaleString("en-US");', 'const fmt = n => n.toLocaleString("vi-VN");')]


def up_template(tpl):
    if len(UP_VI) != len(upgrade_th.UI):
        raise SystemExit("rest_vi: UP_VI must have one Vietnamese text for each entry of upgrade_th.UI")
    body = (tpl / "upgrade_body.html").read_text(encoding="utf-8")
    for en, vi in [(en, vi) for (en, _), vi in zip(upgrade_th.UI, UP_VI)] + UP_EXTRA:
        if body.count(en) != 1:
            raise SystemExit(f"rest_vi: expected the English text once in templates/upgrade_body.html: {en[:70]}")
        body = body.replace(en, vi)
    return body


def up_example(words):
    oc = words["oc"]
    old4 = set("".join(oc[1:5]))
    gap = [x for x in words["w"] if x[3] <= 4 and not (x[4] and x[4] <= 4)]
    hard = sum(1 for x in gap if any(c not in old4 for c in x[0] if "一" <= c <= "鿿"))
    total4 = sum(1 for x in words["w"] if x[3] <= 4)
    n = lambda k: f"{k:,}".replace(",", ".")  # noqa: E731
    return (f"HSK mới 1–4 có {n(total4)} từ. Người đã học hết HSK cũ 1–4 đã gặp {n(total4 - len(gap))} từ trong số đó, "
            f"nên còn {n(len(gap))} từ cần học. {n(hard)} từ trong số này có ít nhất một chữ chưa từng xuất hiện trong "
            "các từ HSK cũ 1–4.")


def build_upgrade(*, root, tpl, site, write, nav, css, meanings):
    data = root / "old-hsk-to-new-hsk" / "words.json"
    if not data.exists():
        return
    words = json.loads(data.read_text(encoding="utf-8"))
    body = (up_template(tpl).replace("__NAV__", nav(UP_URL)).replace("__EXAMPLE__", up_example(words))
            .replace("__VI_JSON__", json.dumps(meanings, ensure_ascii=False, separators=(",", ":"))))
    ld = json.dumps({
        "@context": "https://schema.org", "@type": "WebApplication", "name": "HSK cũ sang HSK mới",
        "url": site + UP_URL, "inLanguage": "vi", "applicationCategory": "EducationalApplication",
        "operatingSystem": "Any", "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"},
        "description": "Xem bạn còn cần học những từ và chữ Hán HSK 3.0 nào sau khi đã học HSK 2.0 cũ.",
    }, ensure_ascii=False)
    write(UP_URL, "HSK cũ sang HSK mới (HSK 3.0): còn phải học những từ nào",
          "Đã học HSK 2.0 cũ? Chọn cấp cũ và cấp HSK 3.0 mục tiêu để xem riêng những từ và chữ Hán bạn chưa học. "
          "Miễn phí, xuất được sang Anki và Pleco.",
          css, body, f'<script type="application/ld+json">{ld}</script>')


# --- YCT -------------------------------------------------------------------------------------------------------------

LEDE = {
    1: "Toàn bộ 80 từ YCT cấp 1, cấp đầu tiên của kỳ thi tiếng Trung dành cho học sinh, có pinyin và nghĩa tiếng Việt. "
       "Tra được bằng chữ Hán, pinyin hoặc tiếng Việt.",
    2: "Toàn bộ 150 từ YCT cấp 2, có pinyin và nghĩa tiếng Việt. Danh sách gồm cả 80 từ của YCT 1; đánh dấu “Chỉ từ mới” "
       "để xem 70 từ thêm vào ở cấp này.",
    3: "Toàn bộ 300 từ YCT cấp 3, có pinyin và nghĩa tiếng Việt. Danh sách gồm cả 150 từ của YCT 1 và 2; đánh dấu “Chỉ "
       "từ mới” để xem 150 từ thêm vào ở cấp này.",
    4: "Toàn bộ 600 từ YCT cấp 4, cấp cao nhất của kỳ thi tiếng Trung dành cho học sinh, có pinyin và nghĩa tiếng Việt. "
       "Danh sách gồm cả 300 từ của YCT 1–3; đánh dấu “Chỉ từ mới” để xem các từ thêm vào ở cấp này.",
}

PROSE = {
    1: [
        f"YCT 1 là cấp khởi đầu của YCT ({zh('中小学生汉语考试')}), kỳ thi năng lực tiếng Trung dành cho học sinh tiểu "
        "học và trung học có tiếng mẹ đẻ không phải tiếng Trung.",
        "80 từ của cấp này là những từ các em gặp đầu tiên: số đếm từ một đến mười, người trong gia đình, các bộ phận "
        f"trên khuôn mặt, con vật nuôi, đồ ăn thức uống đơn giản, thứ và ngày, cùng các động từ như {zh('吃')}, "
        f"{zh('喝')} và {zh('喜欢')}.",
        f"Đề cương ghi {zh('这')}, {zh('那')} và {zh('哪')} cùng với dạng chỉ nơi chốn {zh('这儿')}, {zh('那儿')} và "
        f"{zh('哪儿')}, nên các từ này cũng thuộc YCT 1.",
    ],
    2: [
        "YCT 2 có 150 từ: 80 từ của YCT 1 cộng 70 từ mới. Từ mới gồm đồ dùng học tập như "
        f"{zh('铅笔')} và {zh('书包')}, màu sắc, thời tiết, câu nói lịch sự như {zh('对不起')} và {zh('没关系')}, "
        f"và từ để hỏi như {zh('怎么')} và {zh('多少')}.",
        f"Cấp này cũng bắt đầu có những từ ngữ pháp ngoài phần cơ bản: {zh('了')}, {zh('呢')}, {zh('也')} và "
        f"{zh('比')} để so sánh.",
    ],
    3: [
        "YCT 3 tăng gấp đôi vốn từ, lên 300 từ. Các em đã có thể kể về một ngày của mình, trường lớp và thể thao, sức "
        f"khỏe, mua sắm và thời tiết, và nêu lý do đơn giản với {zh('因为')} và {zh('所以')}.",
        f"Các từ ngữ pháp mới ở cấp này gồm {zh('把')}, {zh('过')}, {zh('得')} và {zh('吧')}.",
    ],
    4: [
        "YCT 4 là cấp cao nhất của bài thi viết, có 600 từ: 300 từ của YCT 1–3 và 300 từ mới. Cấp này đi sâu hơn vào "
        "đời sống hằng ngày, từ du lịch và sở thích đến cảm xúc, kết quả học tập và tin tức.",
        f"Cấp này thêm các cấu trúc đi cặp như {zh('不但……而且……')}, {zh('如果……那么……')} và "
        f"{zh('一边……一边……')}, cùng các từ ngữ pháp như {zh('被')}, {zh('着')} và {zh('地')}.",
        f"Đề cương ghi {zh('对')} hai lần (tính từ và giới từ) và {zh('还')} hai lần (hái và huán). Trang này ghi mỗi "
        "từ một lần kèm cả hai cách dùng, nên bảng có 598 dòng cho 600 mục trong đề cương.",
    ],
}


def read_yct(root, n, rows):
    vi = _rows(root, f"data/vi/yct/yct{n}_vi.tsv", (2, 2))
    if [r[0] for r in vi] != [r[0] for r in rows]:
        raise SystemExit(f"data/vi/yct/yct{n}_vi.tsv does not match data/yct/yct{n}.tsv word for word")
    return [r[1] for r in vi]


def yct_data(root):
    """level -> [(word, pinyin, English, Vietnamese)]; the same word has the same meaning at every level."""
    out, seen = {}, {}
    for n in yct.LEVELS:
        rows = yct.read_level(root, n)
        vi = read_yct(root, n, rows)
        for r, m in zip(rows, vi):
            if seen.setdefault(r[0], m) != m:
                raise SystemExit(f"data/vi/yct/yct{n}_vi.tsv: {r[0]} has a different meaning than at a lower level")
        out[n] = [r + (m,) for r, m in zip(rows, vi)]
    return out


def ws_links(current, hsk_levels):
    items = [(f"{V}hsk-{n}-character-worksheets/", f"HSK {n}") for n in hsk_levels]
    items += [(f"{YCT_URL}yct-{n}-character-worksheets/", f"YCT {n}") for n in yct.LEVELS]
    items.append((f"{V}chinese-character-worksheets/", "Chữ bất kỳ"))
    out = []
    for url, label in items:
        cur = ' aria-current="page"' if url == current else ""
        out.append(f'<a href="{url}"{cur}>{label}</a>')
    return '<nav class="level-links" aria-label="Bộ chữ"><span>Bắt đầu từ:</span>' + "".join(out) + "</nav>"


def build_yct(*, root, tpl, site, write, nav, wl_css, ws_css, vocab_css, ws_tpl, hsk_levels, range_select, char_table,
              search_key, vi_key):
    data = yct_data(root)
    first = {}
    for n in yct.LEVELS:
        for r in data[n]:
            first.setdefault(r[0], n)

    # Word lists
    wl_body = (tpl / "vi" / "yct_wordlist_body.html").read_text(encoding="utf-8")
    for n in yct.LEVELS:
        url = f"{YCT_URL}yct-{n}-word-list/"
        rows = []
        for i, (word, pinyin, en, vi) in enumerate(data[n], 1):
            key = html.escape(search_key(word, pinyin, en) + "|" + vi_key(vi), quote=True)
            lv = first[word]
            rows.append(f'          <tr data-k="{key}" data-new="{1 if lv == n else 0}"><td class="n">{i}</td>'
                        f'<td class="hz">{html.escape(word)}</td><td class="py">{html.escape(pinyin)}</td>'
                        f'<td class="en">{html.escape(vi)}</td><td class="lv"><span class="lv lv{lv}" title="YCT {lv}">'
                        f'{lv}</span></td></tr>')
        toggle = (f'<label class="new-toggle"><input type="checkbox" id="only-new"> Chỉ từ mới của YCT {n}</label>'
                  if n > 1 else "")
        body = (wl_body.replace("__NAV__", nav(YCT_URL))
                .replace("__ROWS__", "\n".join(rows))
                .replace("__PROSE__", "\n".join(f"    <p>{p}</p>" for p in PROSE[n]))
                .replace("__LEDE__", LEDE[n])
                .replace("__NEW_TOGGLE__", toggle)
                .replace("__ROWCOUNT__", str(len(rows)))
                .replace("__COUNT__", str(yct.OFFICIAL[n]))
                .replace("__LEVEL__", str(n)))
        write(url, f"Từ vựng YCT {n}: đủ {yct.OFFICIAL[n]} từ có pinyin và nghĩa tiếng Việt",
              f"Danh sách từ vựng YCT cấp {n}: đủ {yct.OFFICIAL[n]} từ, có pinyin và nghĩa tiếng Việt. Tra cứu nhanh, "
              "miễn phí, kèm phiếu tập viết chữ Hán in được.", wl_css, body)

    # Character worksheets: the characters new at each level
    seen = set()
    for n in yct.LEVELS:
        url = f"{YCT_URL}yct-{n}-character-worksheets/"
        order = []
        for r in data[n]:
            for c in yct.hanzi(r[0]):
                if c not in seen:
                    seen.add(c)
                    order.append(c)
        rows = []
        for i, c in enumerate(order, 1):
            w, p, _, vi = next(r for r in data[n] if c in r[0])
            rows.append(f'<tr><td class="n">{i}</td><td class="hz">{html.escape(c)}</td><td class="w">'
                        f'{zh(html.escape(w))} {html.escape(p)} <small>{html.escape(vi)}</small></td></tr>')
        total = len(order)
        what = "các chữ trong từ vựng YCT 1" if n == 1 else f"các chữ mới của YCT {n} (không lặp lại chữ của cấp thấp hơn)"
        prose = [f"Đề cương YCT liệt kê từ, không phải từng chữ. Trang này lấy mọi chữ trong từ vựng YCT {n} và ghi mỗi "
                 "chữ một lần, theo thứ tự lần đầu xuất hiện trong danh sách từ."]
        if n > 1:
            prose.append("Chữ đã dùng ở cấp YCT thấp hơn không được lặp lại, nên bốn trang cộng lại có đủ các chữ trong "
                         "từ vựng YCT 1–4 mà không trùng chữ nào.")
        prose.append("Với trẻ em, luyện mỗi ngày một ít là hiệu quả nhất: mỗi chữ một hai dòng, rồi cuối tuần luyện lại "
                     f'chính tờ đó. Dùng cùng với <a href="{YCT_URL}yct-{n}-word-list/">từ vựng YCT {n}</a>.')
        body = worksheets_th.fill(
            ws_tpl, nav=nav(YCT_URL), eyebrow="YCT · Kỳ thi tiếng Trung cho học sinh",
            chips=[f"Cấp {n}", f"{total} chữ"], h1=f"Phiếu tập viết chữ Hán YCT {n}",
            lede=f"Phiếu tập viết {what}, tổng cộng {total} chữ, có thứ tự nét, pinyin và ô để tô. In cả cấp hoặc mỗi "
                 "lần 30 chữ. Phù hợp cho giáo viên và phụ huynh.",
            links=ws_links(url, hsk_levels), chars="".join(order), preset=0, range_html=range_select(total),
            sheet_title=f"Chữ Hán YCT {n}", chartable=char_table(f"Toàn bộ {total} chữ mới của YCT {n}", rows),
            about_title="Về bộ chữ này", prose=prose,
        )
        write(url, f"Phiếu tập viết chữ Hán YCT {n} miễn phí, có thứ tự nét",
              f"Phiếu tập viết {total} chữ Hán YCT cấp {n} in miễn phí: thứ tự nét, pinyin, chữ mờ để tô và ô chữ điền. "
              "Cho học sinh, giáo viên và phụ huynh.", ws_css, body)

    # Vocabulary worksheets
    for n in yct.LEVELS:
        url = f"{YCT_URL}yct-{n}-vocabulary-worksheets/"
        rows = [r[:3] for r in data[n]]
        body, sets, words = yct_ws.page(n, "vi", rows, first, [r[3] for r in data[n]], site, nav(YCT_URL),
                                        f"{YCT_URL}yct-{n}-character-worksheets/", url)
        t = yct_ws.T["vi"]
        write(url, t["doc_title"].format(n=n), t["doc_desc"].format(n=n, sets=sets, words=words),
              vocab_css + yct_ws.CSS, body)

    # Comparison with HSK
    cmp = yct.comparison(root)
    if cmp:
        d4 = cmp[4]
        body = yct.compare_body(cmp, "vi", nav(YCT_URL), [r[3] for r in data[4]])
        write(YCT_URL + yct.COMPARE, "So sánh YCT và HSK: mỗi cấp YCT tương đương HSK cấp mấy",
              f"So sánh từ vựng YCT 1–4 với HSK 3.0: YCT 4 có {sum(d4['covers'])} trong số {sum(d4['hsk_sizes'])} từ "
              "HSK 1–3. Kèm danh sách các từ YCT 4 cao hơn HSK 3.", wl_css, body)

    # Overview
    seen, new_chars = set(), {}
    for n in yct.LEVELS:
        count = 0
        for r in data[n]:
            for c in yct.hanzi(r[0]):
                if c not in seen:
                    seen.add(c)
                    count += 1
        new_chars[n] = count
    rows = []
    for n in yct.LEVELS:
        new = yct.OFFICIAL[n] - (yct.OFFICIAL[n - 1] if n > 1 else 0)
        rows.append(f'<tr><th scope="row">YCT {n}</th><td>{yct.OFFICIAL[n]} <small>({new} từ mới)</small></td>'
                    f'<td><a href="{YCT_URL}yct-{n}-word-list/">Danh sách từ</a><br>'
                    f'<a href="{YCT_URL}yct-{n}-vocabulary-worksheets/">Phiếu bài tập từ vựng</a><br>'
                    f'<a href="{YCT_URL}yct-{n}-character-worksheets/">Tập viết {new_chars[n]} chữ</a></td></tr>')
    body = ((tpl / "vi" / "yct_index_body.html").read_text(encoding="utf-8")
            .replace("__NAV__", nav(YCT_URL)).replace("__ROWS__", "\n".join(rows)))
    write(YCT_URL, "Từ vựng YCT 1–4 và phiếu tập viết, có nghĩa tiếng Việt",
          "Danh sách từ YCT cấp 1–4 có pinyin và nghĩa tiếng Việt, cùng phiếu tập viết chữ Hán và phiếu bài tập từ vựng "
          "in miễn phí cho từng cấp.", wl_css, body)


# --- alternates and build --------------------------------------------------------------------------------------------

def alternates(root):
    """English path -> Vietnamese path for the pages of this module."""
    if not available(root):
        return {}
    import vi_tools
    pairs = {"/chinese-measure-words/": MW_URL}
    if (root / "old-hsk-to-new-hsk" / "words.json").exists():
        pairs["/old-hsk-to-new-hsk/"] = UP_URL
    pairs[yct.YCT_URL] = YCT_URL
    for n in yct.LEVELS:
        for page in ("word-list", "character-worksheets", "vocabulary-worksheets"):
            pairs[f"{yct.YCT_URL}yct-{n}-{page}/"] = f"{YCT_URL}yct-{n}-{page}/"
    if yct.comparison(root):
        pairs[yct.YCT_URL + yct.COMPARE] = YCT_URL + yct.COMPARE
    pairs.update(reading.alternates_vi(root, vi_tools.STORY_TITLES))
    return pairs
