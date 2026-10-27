"""Vietnamese-language pages at /vi/, built from data/vi/ and templates/vi/ (see VI.md for the plan).

Outputs:
  vi/index.html                         the level checker in Vietnamese, with Vietnamese meanings for HSK 1-5
  vi/hsk-N-word-list/index.html         HSK 1-5 word lists with Vietnamese meanings
  vi/chinese-character-worksheets/      the worksheet maker in Vietnamese
  vi/hsk-N-character-worksheets/        preset to the characters of HSK N (1-3: strokes/hskN.json; 4-5: new characters)
  vi/about/index.html                   about the site
  vi/learn/, vi/learn/<slug>/           grammar pages and their worksheets, from data/vi/learn/ (tools/learn_vi.py)
  vi/learn/<slug>/practice/             grammar practice online (tools/grammar_practice.py)
  vi/hsk-flashcards/ and the practice tools (test, daily quiz, listening, pinyin and tones, tracing): see
                                        tools/vi_tools.py
  vi/reading/                           graded stories with Vietnamese glosses (tools/reading.py)
  vi/chinese-measure-words/, vi/old-hsk-to-new-hsk/, vi/yct/...: see tools/rest_vi.py

data/vi/hskN_vi.tsv has two columns, word and Vietnamese meaning, in exactly the order of data/hskN.tsv. The build
stops if a file is out of order or incomplete, or if a meaning holds a tab or a Chinese character. No Vietnamese page
is built until all five files exist.

The worksheet pages are the English template (templates/worksheet_body.html) with its interface text swapped for
Vietnamese; the build stops if an English string to swap is not found. The checker, word list and about pages have
their own templates in templates/vi/, made from the Thai ones.

Called from tools/build.py; returns the URLs it wrote so they go into sitemap.xml.
"""
import html
import json
import pathlib
import re

import grammar_practice
import hsk4
import hsk5
import learn_vi
import reading
import rest_vi
import vi_tools
import worksheets_th

VI_URL = "/vi/"
VI_ABOUT_URL = "/vi/about/"
VI_WS_URL = "/vi/chinese-character-worksheets/"
LEVELS = (1, 2, 3, 4, 5)
_ROOT = pathlib.Path(__file__).resolve().parent.parent
HAN = re.compile(r"[㐀-鿿豈-﫿]")

FOOT = ('\n<footer class="site-foot">hskcheck.com · <a href="/vi/about/">Giới thiệu</a> · '
        '<a href="/terms/" hreflang="en">Điều khoản sử dụng</a> · '
        '<a href="/privacy/" hreflang="en">Chính sách quyền riêng tư</a></footer>')

# Bottom bar on phones (see build.tab_bar): flashcards, word lists, checker.
TABS = [(vi_tools.STUDY_URL, "Flashcard", "cards"), ("/vi/hsk-1-word-list/", "Từ vựng", "read"),
        (VI_URL, "Kiểm tra", "check")]


def tab_on(path, href):
    if href in (VI_URL, vi_tools.STUDY_URL):
        return path == href
    return bool(re.fullmatch(r"/vi/hsk-\d-word-list/", path))


def zh(s):
    return f'<span class="zh-inline">{s}</span>'


LEVEL_COPY = {
    1: {
        "lede": "Toàn bộ 300 từ HSK 1 theo đề cương HSK 3.0 (HSK mới), có pinyin và nghĩa tiếng Việt. "
                "Tra được bằng chữ Hán, pinyin hoặc tiếng Việt (gõ có dấu hay không dấu đều được).",
        "prose": [
            "HSK 1 là cấp đầu tiên trong 9 cấp của HSK 3.0. 300 từ của cấp này gồm số đếm, gia đình, thời gian, đồ ăn, "
            "địa điểm và những động từ thông dụng nhất, đủ cho các trao đổi ngắn hằng ngày.",
            "Mỗi cấp sau đều xây trên danh sách này: HSK 2 thêm 200 từ, tổng cộng 500 từ; HSK 3 thêm 500 từ nữa, "
            "tổng cộng 1.000 từ.",
            f"Một vài mục dễ bị bỏ sót vì đề cương liệt kê từ chứ không phải chữ. {zh('杯子')} (cái cốc) có trong danh "
            f"sách, nhưng lượng từ {zh('杯')} thì không, nên {zh('一杯茶')} vượt cấp HSK 1.",
        ],
    },
    2: {
        "lede": "200 từ mới của HSK 2 theo đề cương HSK 3.0 (HSK mới), có pinyin và nghĩa tiếng Việt. Cộng với HSK 1 "
                "là 500 từ. Tra được bằng chữ Hán, pinyin hoặc tiếng Việt.",
        "prose": [
            "HSK 2 thêm 200 từ vào 300 từ của HSK 1, gồm phương hướng, đi lại, mua sắm, thời tiết, sức khỏe và những "
            f"cảm xúc đơn giản, cùng các từ nối ý như {zh('因为')}, {zh('所以')} và {zh('虽然')}.",
            f"Đề cương liệt kê {zh('过')} và {zh('花')} hai lần, mỗi lần cho một cách dùng chính. Trang này ghi mỗi từ "
            "một lần kèm cả hai nghĩa, nên bảng có 198 dòng.",
            f"Một số chữ của HSK 1 trở lại trong từ mới hoặc cách dùng mới: {zh('点')} với nghĩa gọi món, và các trợ "
            f"từ {zh('得')} và {zh('地')}.",
        ],
    },
    3: {
        "lede": "500 từ mới của HSK 3 theo đề cương HSK 3.0 (HSK mới), có pinyin và nghĩa tiếng Việt. Cộng với HSK 1 "
                "và 2 là 1.000 từ. Tra được bằng chữ Hán, pinyin hoặc tiếng Việt.",
        "prose": [
            "HSK 3 tăng gấp đôi vốn từ, thêm 500 từ để đạt tổng cộng 1.000 từ. Đây là cấp người học bắt đầu nói sâu "
            "hơn về các chủ đề hằng ngày: học tập và công việc, du lịch, sức khỏe, thời tiết và các mùa, cùng ý kiến "
            "của bản thân.",
            f"Nhiều chữ quen thuộc trở lại với cách đọc hoặc nghĩa mới: {zh('还')} đọc là huán (trả lại), {zh('长')} "
            f"đọc là zhǎng (lớn lên), và {zh('只')} đọc là zhī làm lượng từ cho con vật.",
            f"Đề cương liệt kê {zh('得')} hai lần, cho dé (được, đạt được) và děi (phải). Trang này ghi một lần kèm cả "
            "hai cách đọc, nên bảng có 499 dòng.",
        ],
    },
    4: {
        "lede": "1.000 từ mới của HSK 4 theo đề cương HSK 3.0 (HSK mới), có pinyin và nghĩa tiếng Việt. Cộng với "
                "HSK 1–3 là 2.000 từ. Tra được bằng chữ Hán, pinyin hoặc tiếng Việt.",
        "prose": [
            "HSK 4 lại tăng gấp đôi vốn từ, thêm 1.000 từ để đạt tổng cộng 2.000 từ. Ở cấp này người học chuyển từ "
            "tiếng Trung giao tiếp cơ bản sang công việc, học tập và đời sống xã hội: xin việc, bàn về tin tức, kế "
            "hoạch du lịch, cảm xúc và ý kiến.",
            f"Nhiều từ HSK 4 được ghép từ những chữ bạn đã biết, như {zh('网友')} (bạn trên mạng) từ {zh('网')} và "
            f"{zh('友')}. Các từ hiện đại như {zh('扫码')} (quét mã), {zh('线上')} (trực tuyến) và {zh('动车')} "
            "(tàu cao tốc) là từ mới trong đề cương 2025.",
            f"Đề cương liệt kê {zh('重')}, {zh('空')} và {zh('生')} hai lần, mỗi lần cho một cách đọc hoặc cách dùng. "
            "Trang này ghi mỗi từ một lần, nên bảng có 997 dòng cho 1.000 mục trong đề cương.",
        ],
    },
    5: {
        "lede": "1.600 từ mới của HSK 5 theo đề cương HSK 3.0 (HSK mới), có pinyin và nghĩa tiếng Việt. Cộng với "
                "HSK 1–4 là 3.600 từ. Tra được bằng chữ Hán, pinyin hoặc tiếng Việt.",
        "prose": [
            "HSK 5 thêm 1.600 từ vào 2.000 từ của HSK 1–4, tổng cộng 3.600 từ. Ở cấp này người học đọc tin tức, nghe "
            "những bài nói dài hơn và thảo luận về công việc, xã hội, ý tưởng, nên các từ trừu tượng như "
            f"{zh('趋势')} (xu hướng), {zh('措施')} (biện pháp) và {zh('本质')} (bản chất) xuất hiện thường xuyên.",
            f"Đời sống hiện đại cũng có nhiều từ: {zh('二维码')} (mã QR), {zh('点赞')} (bấm thích), {zh('直播')} "
            f"(phát trực tiếp) và {zh('充值')} (nạp tiền) đều là từ HSK 5 trong đề cương 2025.",
            f"Đề cương liệt kê {zh('处')}, {zh('调')} và {zh('系')} hai lần, mỗi lần cho một cách đọc, và vài từ như "
            f"{zh('为')} (wéi) xuất hiện lại với cách dùng mới. Trang này ghi mỗi từ một lần, nên bảng có 1.595 dòng "
            "cho 1.600 mục trong đề cương.",
        ],
    },
}

SOURCE = {
    "two": "<p><b>Nguồn.</b> Từ và thứ tự từ theo danh sách HSK 3.0 cấp {n} trong đề cương thi năm 2025, đã đối "
           "chiếu với hai bản sao được công bố độc lập.</p>",
    "one": "<p><b>Nguồn.</b> Từ và thứ tự từ theo danh sách HSK 3.0 cấp {n} trong đề cương thi năm 2025, đã đối "
           "chiếu với một bản sao được công bố độc lập.</p>",
    "parser": "<p><b>Nguồn.</b> Từ và thứ tự từ theo danh sách HSK 3.0 cấp {n} trong đề cương thi năm 2025, theo "
              "bản chép của dự án mở hsk-syllabus-vocabulary-parser; bản chép này khớp từng từ với danh sách HSK 1–4 "
              "của trang.</p>",
}
LEVEL_SOURCE = {1: "two", 2: "two", 3: "two", 4: "one", 5: "parser"}

# English text in templates/worksheet_body.html -> Vietnamese. Every key must occur in the template.
WS_UI = [
    ('aria-label="Worksheet settings"', 'aria-label="Cài đặt phiếu tập viết"'),
    ('<label for="chars">Characters</label>', '<label for="chars">Chữ Hán</label>'),
    ("Type or paste any Chinese text. Each character is used once, in order.",
     "Gõ hoặc dán bất kỳ đoạn văn tiếng Trung nào. Mỗi chữ chỉ dùng một lần, theo thứ tự."),
    ("<legend>Grid</legend>", "<legend>Ô kẻ</legend>"),
    ("<span>田 Tian</span>", "<span>田 Chữ điền</span>"),
    ("<span>米 Mi</span>", "<span>米 Chữ mễ</span>"),
    ("<span>Plain</span>", "<span>Ô trơn</span>"),
    ("<legend>Tracing</legend>", "<legend>Chữ mờ để tô</legend>"),
    ("<span>None</span>", "<span>Không</span>"),
    ("<span>Full row</span>", "<span>Cả dòng</span>"),
    ("<legend>Rows per character</legend>", "<legend>Số dòng mỗi chữ</legend>"),
    ("<legend>Show</legend>", "<legend>Hiển thị</legend>"),
    ("checked> Stroke order</label>", "checked> Thứ tự nét</label>"),
    ("checked> Pinyin</label>", "checked> Pinyin</label>"),
    (">Print or save as PDF</button>", ">In hoặc lưu thành PDF</button>"),
    ('href="/chinese-character-tracing/" data-base="/chinese-character-tracing/">Trace them on screen</a>',
     f'href="{vi_tools.TRACE_URL}" data-base="{vi_tools.TRACE_URL}">Tập tô trên màn hình</a>'),
    ('aria-label="Worksheet preview"', 'aria-label="Xem trước phiếu tập viết"'),
    ("Name ______________________ &nbsp; Date ____________", "Họ tên ______________________ &nbsp; Ngày ____________"),
    ("Free worksheets and the HSK level checker at hskcheck.com", "Phiếu tập viết chữ Hán miễn phí tại hskcheck.com/vi/"),
    ("<p><b>Printing.</b> Use your browser's print dialog to print or to save the sheet as a PDF. "
     "Choose A4 or US Letter; the grid is sized to fit both.</p>",
     "<p><b>In phiếu.</b> Dùng hộp thoại in của trình duyệt để in hoặc lưu phiếu thành tệp PDF. Chọn khổ A4 hay "
     "US Letter đều được; ô kẻ vừa với cả hai khổ giấy.</p>"),
    ("<p><b>Stroke data.</b> Stroke outlines and pinyin come from",
     "<p><b>Dữ liệu nét chữ.</b> Hình nét và pinyin lấy từ"),
    ("(Arphic Public License and GNU LGPL, see <a href=\"/strokes/LICENSE.md\">licence</a>). "
     "Stroke order follows mainland China standards for simplified characters.</p>",
     "(giấy phép Arphic Public License và GNU LGPL, xem <a href=\"/strokes/LICENSE.md\" hreflang=\"en\">giấy phép</a>). "
     "Thứ tự nét theo chuẩn chữ giản thể của Trung Quốc đại lục.</p>"),
    ('n + (n === 1 ? " stroke" : " strokes")', 'n + " nét"'),
    ('status.textContent = chars.length ? "Loading…" : "";', 'status.textContent = chars.length ? "Đang tải…" : "";'),
    ('"Could not load stroke data. Check your connection and try again."',
     '"Không tải được dữ liệu nét chữ. Hãy kiểm tra kết nối mạng rồi thử lại."'),
    ('ok.length + (ok.length === 1 ? " character" : " characters")', 'ok.length + " chữ"'),
    ('"no stroke data for "', '"không có dữ liệu nét chữ cho "'),
    ('"Type some Chinese characters above."', '"Hãy gõ vài chữ Hán vào ô ở trên."'),
]


def num(n):
    """1600 -> 1.600 (Vietnamese thousands separator)."""
    return f"{n:,}".replace(",", ".")


def read_meanings(root, n, words):
    """Vietnamese meanings for level n, checked against the words of data/hskN.tsv in order. None if the file is missing."""
    path = root / "data" / "vi" / f"hsk{n}_vi.tsv"
    if not path.exists():
        return None
    rows = []
    for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        parts = line.split("\t")
        if len(parts) != 2 or not parts[1].strip():
            raise SystemExit(f"data/vi/hsk{n}_vi.tsv line {i}: expected word<TAB>Vietnamese meaning")
        if HAN.search(parts[1]):
            raise SystemExit(f"data/vi/hsk{n}_vi.tsv line {i}: Chinese characters in the meaning")
        rows.append((parts[0].strip(), parts[1].strip()))
    got = [w for w, _ in rows]
    if got != words:
        bad = next((i for i, w in enumerate(got) if i >= len(words) or w != words[i]), len(got))
        raise SystemExit(f"data/vi/hsk{n}_vi.tsv line {bad + 1}: "
                         f"{got[bad] if bad < len(got) else 'end of file'} out of order or missing; expected "
                         f"{words[bad] if bad < len(words) else 'end of file'}")
    return [m for _, m in rows]


def word_rows(root, n):
    """[(word, pinyin, English)] for level n from data/hskN.tsv (HSK 4 and 5 through their modules' checks)."""
    if n == 4:
        return [tuple(r) for r in hsk4.read(root)[1]]
    if n == 5:
        return [tuple(r) for r in hsk5.read(root)[1]]
    rows = []
    for line in (root / "data" / f"hsk{n}.tsv").read_text(encoding="utf-8").splitlines():
        if line.strip():
            w, p, e = line.split("\t")
            rows.append((w.strip(), p.strip(), e.strip()))
    return rows


def load(root):
    """level -> list of (word, pinyin, English, Vietnamese); empty while any level has no Vietnamese file."""
    out = {}
    for n in LEVELS:
        rows = word_rows(root, n)
        vi = read_meanings(root, n, [r[0] for r in rows])
        if vi is None:
            return {}
        out[n] = [r + (m,) for r, m in zip(rows, vi)]
    return out


def ws_levels(root):
    return [n for n in LEVELS if n >= 4 or (root / "strokes" / f"hsk{n}.json").exists()]


def alternates(root):
    """English path -> Vietnamese path, for pages that exist in both languages."""
    if not load(root):
        return {}
    pairs = {"/": VI_URL}
    pairs.update({f"/hsk-{n}-word-list/": f"{VI_URL}hsk-{n}-word-list/" for n in LEVELS})
    pairs["/chinese-character-worksheets/"] = VI_WS_URL
    pairs.update({f"/hsk-{n}-character-worksheets/": f"{VI_URL}hsk-{n}-character-worksheets/" for n in ws_levels(root)})
    pairs["/about/"] = VI_ABOUT_URL
    pairs.update(vi_tools.alternates())
    pairs.update(learn_vi.alternates(root))
    pairs.update(grammar_practice.alternates_vi(root))
    pairs.update(rest_vi.alternates(root))
    return pairs


def vi_key(text, squash):
    """Vietnamese is matched without tone marks or spaces, đ as d (mirrors the word list page's search normaliser)."""
    return squash(text).replace("đ", "d")


def swap(body, pairs, what):
    for a, b in pairs:
        if a not in body:
            raise SystemExit(f"build_vi: text not found in {what}: {a[:60]}")
        body = body.replace(a, b)
    return body


def ws_links(current, levels):
    return rest_vi.ws_links(current, levels)


def range_select(total):
    options = [f'<option value="all">Tất cả {total} chữ</option>']
    for a in range(1, total + 1, 30):
        b = min(a + 29, total)
        options.append(f'<option value="{a}-{b}">Chữ {a}–{b}</option>')
    return ('<div class="field"><label for="range">Chữ cần in</label>'
            f'<select id="range">{"".join(options)}</select></div>')


def char_table(title, rows):
    return (f'  <section class="sheet char-table no-print" aria-labelledby="chars-title">\n'
            f'    <h2 id="chars-title">{title}</h2>\n'
            f'    <div class="table-wrap"><table><thead><tr><th scope="col">#</th><th scope="col">Chữ</th>'
            f'<th scope="col">Từ đầu tiên trong danh sách</th></tr></thead><tbody>\n'
            + "\n".join(rows) + "\n    </tbody></table></div>\n  </section>")


def level_chars(root, n, data):
    """The characters of the HSK n worksheet, in order: as the English pages pick them."""
    if n <= 3:
        return list(json.loads((root / "strokes" / f"hsk{n}.json").read_text(encoding="utf-8")))
    lower = [r[0] for m in range(1, n) for r in data[m]]
    rows = [r[:3] for r in data[n]]
    return (hsk4 if n == 4 else hsk5).new_chars(rows, lower)


def build(*, root, tpl, site, base_css, render, word_lists, read_words, search_key, squash, checker_level_table,
          measure):
    """Write the Vietnamese pages. Returns the URLs written."""
    data = load(root)
    if not data:
        return []
    for n in (1, 2, 3):  # the English pages and this module must read the same lists
        if n in word_lists and [r[:3] for r in data[n]] != list(word_lists[n]):
            raise SystemExit(f"build_vi: HSK {n} rows differ from build.read_tsv")

    pages = [(VI_URL, "Kiểm tra cấp độ")]
    pages += [(f"{VI_URL}hsk-{n}-word-list/", f"Từ vựng HSK {n}") for n in LEVELS]
    pages += vi_tools.NAV
    rest = rest_vi.available(root)
    if rest:
        pages.append((reading.VI_URL, "Đọc truyện"))
    pages.append((VI_WS_URL, "Phiếu tập viết"))
    pages += vi_tools.NAV_AFTER_WS
    if rest:
        pages += rest_vi.NAV_TOOLS
    if learn_vi.slugs(root):
        pages.append((learn_vi.VI_LEARN_URL, "Ngữ pháp"))
    if rest:
        pages += rest_vi.NAV_YCT

    def nav(current):
        links = []
        for url, label in pages:
            cur = ' aria-current="page"' if url == current else ""
            links.append(f'<a href="{url}"{cur}>{label}</a>')
        return ('<nav class="site-nav" aria-label="Menu trang"><button type="button" class="nav-toggle" '
                'aria-expanded="false">Menu</button><div class="nav-links">' + "".join(links)
                + "</div><!--lang-switch--></nav>")

    vi_css = (tpl / "vi" / "vi.css").read_text(encoding="utf-8")
    urls = []

    def write(url, title, description, css, body, head_extra=""):
        if len(title) > 65 or len(description) > 160:
            raise SystemExit(f"build_vi: title or description too long for {url}")
        target = root / url.strip("/")
        target.mkdir(parents=True, exist_ok=True)
        (target / "index.html").write_text(render(title, description, site + url, css, body, head_extra,
                                                  lang="vi", foot=FOOT), encoding="utf-8")
        urls.append(url)

    # Level checker
    meanings = {}
    for n in LEVELS:
        for word, _, _, vi in data[n]:
            meanings.setdefault(word, vi)
    for w, m in list(meanings.items()):
        if len(w) >= 3 and w.endswith("儿"):
            meanings.setdefault(w[:-1], m)
    ld = json.dumps({
        "@context": "https://schema.org", "@type": "WebApplication", "name": "Kiểm tra từ vượt cấp HSK 3.0",
        "url": site + VI_URL, "inLanguage": "vi", "applicationCategory": "EducationalApplication",
        "operatingSystem": "Any", "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"},
        "description": "Dán đoạn văn tiếng Trung và xem từ nào vượt cấp HSK 3.0 của bạn, kèm nghĩa tiếng Việt.",
    }, ensure_ascii=False)
    body = (tpl / "vi" / "checker_body.html").read_text(encoding="utf-8")
    body = (body.replace("__NAV__", nav(VI_URL))
            .replace("__LEVELS_JSON__", json.dumps(checker_level_table(), ensure_ascii=False, separators=(",", ":")))
            .replace("__MEANINGS_JSON__", json.dumps(meanings, ensure_ascii=False, separators=(",", ":"))))
    write(VI_URL, "Kiểm tra từ vượt cấp HSK 3.0 (超纲词) có nghĩa tiếng Việt",
          "Dán đoạn văn tiếng Trung để biết ngay từ nào vượt cấp HSK 3.0 của bạn, kèm nghĩa tiếng Việt. Miễn phí, "
          "chạy trong trình duyệt, không cần đăng ký.",
          base_css + (tpl / "checker.css").read_text(encoding="utf-8") + vi_css, body,
          f'<script type="application/ld+json">{ld}</script>')

    # Word lists
    wl_tpl = (tpl / "vi" / "wordlist_body.html").read_text(encoding="utf-8")
    wl_css = base_css + (tpl / "wordlist.css").read_text(encoding="utf-8") + vi_css
    official = {n: len(read_words(n)) for n in (1, 2, 3)}
    official.update({4: hsk4.OFFICIAL, 5: hsk5.OFFICIAL})
    for n in LEVELS:
        rows = []
        for i, (word, pinyin, en, vi) in enumerate(data[n], 1):
            key = html.escape(search_key(word, pinyin, en) + "|" + vi_key(vi, squash), quote=True)
            rows.append(f'          <tr data-k="{key}"><td class="n">{i}</td><td class="hz">{html.escape(word)}</td>'
                        f'<td class="py">{html.escape(pinyin)}</td><td class="en">{html.escape(vi)}</td></tr>')
        url = f"{VI_URL}hsk-{n}-word-list/"
        copy = LEVEL_COPY[n]
        body = (wl_tpl.replace("__NAV__", nav(url))
                .replace("__ROWS__", "\n".join(rows))
                .replace("__PROSE__", "\n".join(f"    <p>{p}</p>" for p in copy["prose"]))
                .replace("__LEDE__", copy["lede"])
                .replace("__SOURCE__", SOURCE[LEVEL_SOURCE[n]].format(n=n))
                .replace("__ROWCOUNT__", num(len(data[n])))
                .replace("__COUNT__", num(official[n]))
                .replace("__LEVEL__", str(n)))
        write(url, f"Từ vựng HSK {n} (HSK 3.0) {num(official[n])} từ có nghĩa tiếng Việt",
              f"{'Toàn bộ' if n == 1 else 'Danh sách'} {num(official[n])} từ HSK {n} theo đề cương HSK 3.0 (HSK mới), "
              "có pinyin và nghĩa tiếng Việt. Tra cứu nhanh, miễn phí.",
              wl_css, body)

    # Worksheet maker and one preset per level
    ws_tpl = swap((tpl / "worksheet_body.html").read_text(encoding="utf-8"), WS_UI, "templates/worksheet_body.html")
    ws_css = base_css + (tpl / "worksheet.css").read_text(encoding="utf-8") + vi_css
    levels = ws_levels(root)
    body = worksheets_th.fill(
        ws_tpl, nav=nav(VI_WS_URL), eyebrow="Miễn phí · In được", chips=[],
        h1='<span class="zh">字帖</span>Tạo phiếu tập viết chữ Hán',
        lede="Tạo phiếu tập viết chữ Hán để in cho bất kỳ chữ nào: thứ tự nét, chữ mẫu, chữ mờ để tô và ô trống để "
             "luyện viết trên ô chữ điền hoặc chữ mễ. Hoặc bắt đầu từ các chữ của từng cấp HSK.",
        links=ws_links(VI_WS_URL, levels), chars="你好我爱学中文", preset=0, range_html="",
        sheet_title="Luyện viết chữ Hán", chartable="", about_title="Cách dùng phiếu tập viết",
        prose=[
            "Bắt đầu mỗi chữ với dải thứ tự nét: nét mới nhất màu đen, các nét trước màu xám. Sau đó tô lên các chữ "
            "mờ màu xám, rồi tự viết vào ô trống mà không nhìn mẫu.",
            f"Ô chữ điền ({zh('田')}) chia mỗi ô thành bốn phần, ô chữ mễ ({zh('米')}) thêm hai đường chéo. Cả hai "
            "giúp bạn đặt đúng vị trí từng bộ phận của chữ, điều quan trọng hơn tốc độ khi mới bắt đầu.",
            "Viết một chữ vài lần trong nhiều ngày hiệu quả hơn viết kín cả trang trong một lần. Mỗi chữ in một hoặc "
            "hai dòng, rồi vài hôm sau quay lại luyện tiếp chính tờ đó.",
        ],
    )
    write(VI_WS_URL, "Tạo phiếu tập viết chữ Hán miễn phí, có thứ tự nét",
          "Tạo phiếu tập viết chữ Hán miễn phí để in: thứ tự nét, pinyin, chữ mờ để tô, ô chữ điền hoặc chữ mễ. "
          "Gõ chữ bất kỳ hoặc chọn theo cấp HSK.", ws_css, body)

    for n in levels:
        url = f"{VI_URL}hsk-{n}-character-worksheets/"
        order = level_chars(root, n, data)
        rows = []
        for i, c in enumerate(order, 1):
            w, p, _, vi = next(r for r in data[n] if c in r[0])
            cell = f'{zh(html.escape(w))} {html.escape(p)} <small>{html.escape(vi)}</small>'
            rows.append(f'<tr><td class="n">{i}</td><td class="hz">{html.escape(c)}</td><td class="w">{cell}</td></tr>')
        total = len(order)
        if n == 1:
            what, table_title = "các chữ trong từ vựng HSK 1", f"Toàn bộ {total} chữ trong từ vựng HSK 1"
        else:
            what = f"các chữ mới của HSK {n} (không lặp lại chữ đã có ở HSK 1{'' if n == 2 else '–' + str(n - 1)})"
            table_title = f"Toàn bộ {total} chữ mới trong từ vựng HSK {n}"
        prose = [f"Đề cương HSK 3.0 liệt kê từ, không phải từng chữ. Trang này lấy mọi chữ xuất hiện trong từ vựng "
                 f"HSK {n} và ghi mỗi chữ một lần, theo thứ tự lần đầu xuất hiện trong danh sách từ."]
        if n > 1:
            prose.append("Chữ đã dùng ở cấp thấp hơn không được lặp lại, nên năm trang HSK 1–5 cộng lại có đủ các chữ "
                         "trong từ vựng HSK 1–5 mà không trùng chữ nào.")
        prose.append("Đề cương HSK 3.0 còn có danh sách chữ Hán riêng, có thể hơi khác bộ chữ này. Hãy dùng các phiếu "
                     f'này cùng với <a href="{VI_URL}hsk-{n}-word-list/">từ vựng HSK {n}</a> mà bạn đang học.')
        body = worksheets_th.fill(
            ws_tpl, nav=nav(VI_WS_URL), eyebrow="HSK mới · Đề cương 2025", chips=[f"Cấp {n}", f"{num(total)} chữ"],
            h1=f"Phiếu tập viết chữ Hán HSK {n}",
            lede=f"Phiếu tập viết {what}, tổng cộng {num(total)} chữ, có thứ tự nét, pinyin và ô để tô. In cả cấp "
                 "hoặc mỗi lần 30 chữ.",
            links=ws_links(url, levels), chars="".join(order), preset=n if n <= 3 else 0,
            range_html=range_select(total), sheet_title=f"Chữ Hán HSK {n}",
            chartable=char_table(table_title, rows), about_title="Về bộ chữ này", prose=prose,
        )
        write(url, f"Phiếu tập viết chữ Hán HSK {n} miễn phí, có thứ tự nét",
              f"Phiếu tập viết {num(total)} chữ Hán HSK {n} theo đề cương HSK 3.0, in miễn phí: thứ tự nét, pinyin, "
              "chữ mờ để tô và ô chữ điền.", ws_css, body)

    # Flashcards and practice tools
    urls += vi_tools.build(root=root, tpl=tpl, write=write, nav=nav, base_css=base_css, vi_css=vi_css, data=data)

    # Grammar pages, their worksheets and grammar practice online
    learn_vi.build(root=root, tpl=tpl, site=site, write=write, nav=nav, base_css=base_css, vi_css=vi_css)
    grammar_practice.build_vi(root=root, tpl=tpl, site=site, write=write, nav=nav, base_css=base_css, vi_css=vi_css)

    # Graded reading, measure words, old -> new HSK and YCT (tools/rest_vi.py)
    if rest:
        reading.build_vi(root=root, tpl=tpl, write=write, nav=nav, base_css=base_css, vi_css=vi_css,
                         vi={n: [r[3] for r in data[n]] for n in LEVELS}, titles=vi_tools.STORY_TITLES)
        key = lambda text: vi_key(text, squash)  # noqa: E731
        rest_vi.build_measure(root=root, tpl=tpl, site=site, write=write, nav=nav,
                              css=base_css + (tpl / "measure.css").read_text(encoding="utf-8") + vi_css,
                              measure=dict(measure, squash=squash), level_table=checker_level_table,
                              search_key=search_key, vi_key=key)
        rest_vi.build_upgrade(root=root, tpl=tpl, site=site, write=write, nav=nav,
                              css=base_css + (tpl / "upgrade.css").read_text(encoding="utf-8") + vi_css,
                              meanings=meanings)
        rest_vi.build_yct(root=root, tpl=tpl, site=site, write=write, nav=nav,
                          wl_css=wl_css + (tpl / "yct.css").read_text(encoding="utf-8"), ws_css=ws_css,
                          vocab_css=base_css + (tpl / "learn_worksheet.css").read_text(encoding="utf-8") + vi_css,
                          ws_tpl=ws_tpl, hsk_levels=levels, range_select=range_select, char_table=char_table,
                          search_key=search_key, vi_key=key)

    # About
    body = (tpl / "vi" / "about_body.html").read_text(encoding="utf-8").replace("__NAV__", nav(VI_ABOUT_URL))
    write(VI_ABOUT_URL, "Giới thiệu hskcheck.com: công cụ HSK 3.0 và YCT miễn phí",
          "Giới thiệu hskcheck.com: danh sách từ, ngữ pháp, phiếu tập viết và công cụ miễn phí cho người học và "
          "giáo viên HSK 3.0, YCT. Nội dung được làm thế nào.", base_css + vi_css, body)
    return urls
