"""Printable packs sold on the site, the packs index page, and the Terms of Service page.

Each pack has its own page at /upgrade-packs/<slug>/ with what's inside, a few preview images (JPEGs kept in that
folder, made from the PDF), the price and a checkout link. The PDF itself is NOT kept in this repository: everything
here is public on hskcheck.com. While "checkout" is empty (before the payment provider approves the store) the page
shows "Checkout opens soon" instead of a buy button.

Outputs:
  /upgrade-packs/                     list of packs
  /upgrade-packs/<slug>/index.html    one page per pack
  /terms/index.html                   Terms of Service, with the refund policy
  /th/upgrade-packs/...               Thai editions (TH_PACKS), built by build_th() from tools/build_th.py; each is
                                      its own product with its own checkout link and preview images in its folder

Called from tools/build.py (English) and tools/build_th.py (Thai); each returns the URLs it wrote.
"""
import html

INDEX_URL = "/upgrade-packs/"
TERMS_URL = "/terms/"
TERMS_UPDATED = "2026-10-25"
CONTACT = "willowbewater@gmail.com"
OPERATOR = "OUYUN QIQIKE"  # legal name of the individual who runs the site; must match the Creem onboarding details
REFUND_DAYS = 14

PACKS = [
    {
        "slug": "old-hsk-1-to-new-hsk-1",
        "name": "Old HSK 1 → New HSK 1 Upgrade Pack",
        "short": "Old HSK 1 → New HSK 1",
        "price": "$3.99",
        "pages": 60,
        "checkout": "https://www.creem.io/payment/prod_5Nvf2dQ07MmAfG19A1v9O6",  # Creem checkout link
        "title": "Old HSK 1 to New HSK 1 Upgrade Pack: Printable PDF for HSK 3.0",
        "description": ("Studied the old HSK 1? Learn the 155 new HSK 1 words you haven't met yet: example sentences, "
                        "writing practice for 74 new characters, quizzes and answers. Printable PDF, $3.99."),
        "lede": ("Studied the old HSK 1? The new HSK 1 has 300 words, and 155 of them were not in old HSK 1. "
                 "This printable pack teaches you those 155 words in ten short lessons."),
        "inside": [
            "All 155 words with pinyin and meaning, each with an example sentence that uses only new HSK 1 words, "
            "with pinyin and English",
            "Stroke order and tracing practice for the 74 characters that were not in old HSK 1",
            "A quiz after every lesson, a 20-question final check, and all the answers",
            "A 10-day study plan and a word index",
            "60 pages, A4. It prints on US Letter paper too: choose \"fit to page\" when you print.",
        ],
        "previews": [
            ("page-1.jpg", "The cover"),
            ("page-3.jpg", "Every word with an example sentence"),
            ("page-5.jpg", "Writing practice for each new character"),
            ("page-6.jpg", "A quiz after every lesson"),
        ],
        "free_url": "/old-hsk-to-new-hsk/#old=1&new=1",
        "free_text": ("The free Old HSK → New HSK tool lists the same 155 words with pinyin and meaning, and exports them to "
                      "Anki or Pleco. The pack adds example sentences, writing practice and quizzes, laid out to print."),
    },
]

CSS = """
/* Printable pack pages */
.buy { grid-template-columns: minmax(0, 1fr) auto; align-items: center; gap: 10px 16px; }
.price { font: 500 34px/1.1 var(--f-num); letter-spacing: -.01em; }
.price-note { font-size: 14px; color: var(--muted); }
.buy .hint { grid-column: 1 / -1; font-size: 13px; color: var(--muted); margin: 0; }
@media (max-width: 420px) { .buy { grid-template-columns: 1fr; } }
.button { display: inline-block; text-decoration: none; font: 500 15px var(--f-ui); padding: 10px 18px; border-radius: 999px;
  border: 1px solid var(--accent); background: var(--accent); color: var(--accent-ink); cursor: pointer; text-align: center; }
.button.ghost { background: transparent; color: var(--accent); }
.button[aria-disabled="true"] { opacity: .5; cursor: default; }
.inside { margin: 0; padding-left: 20px; display: grid; gap: 6px; }
.previews { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 16px; }
.previews figure { margin: 0; display: grid; gap: 6px; }
.previews img { width: 100%; height: auto; border: 1px solid var(--rule); border-radius: 6px; background: #fff; }
.previews figcaption { font-size: 13px; color: var(--muted); }
.prose { display: grid; gap: 12px; max-width: 68ch; }
.prose h2 { font-size: 20px; letter-spacing: -.005em; }
.prose h3 { margin: 0 0 4px; font-size: 16px; font-weight: 600; }
.prose p { margin: 0; }
.pack-list { display: grid; gap: 12px; }
.pack-item { display: grid; grid-template-columns: 96px minmax(0, 1fr); gap: 14px; align-items: start; text-decoration: none; color: inherit; }
.pack-item img { width: 96px; height: auto; border: 1px solid var(--rule); border-radius: 4px; }
.pack-item b { display: block; color: var(--accent); }
.pack-item span { font-size: 14px; color: var(--muted); }
"""

E = html.escape


def url(p):
    return f"{INDEX_URL}{p['slug']}/"


def buy_button(p):
    if p["checkout"]:
        return f'<a class="button" href="{E(p["checkout"])}">Buy for {p["price"]}</a>'
    return '<span class="button" aria-disabled="true">Checkout opens soon</span>'


def pack_body(p, nav_html):
    inside = "".join(f"<li>{E(x)}</li>" for x in p["inside"])
    figs = "".join(
        f'<figure><img src="{url(p)}{f}" width="620" height="878" loading="lazy" alt="{E(cap)}"><figcaption>{E(cap)}</figcaption></figure>'
        for f, cap in p["previews"])
    return f"""<div class="wrap">
  <header>
    {nav_html}
    <div class="eyebrow"><span>Printable pack</span><span class="chip">PDF · {p['pages']} pages</span><span class="chip">{p['price']}</span></div>
    <h1><span class="zh">补差</span>{E(p['name'])}</h1>
    <p class="lede">{E(p['lede'])}</p>
  </header>

  <section class="sheet buy" aria-label="Price">
    <div><div class="price">{p['price']}</div><div class="price-note">One-time payment · instant PDF download</div></div>
    <div>{buy_button(p)}</div>
    <p class="hint">If the pack isn't useful to you, email us within {REFUND_DAYS} days for a full refund. See the <a href="{TERMS_URL}">Terms</a>.</p>
  </section>

  <section class="sheet" aria-labelledby="inside-title">
    <h2 id="inside-title">What's inside</h2>
    <ul class="inside">{inside}</ul>
  </section>

  <section class="sheet" aria-labelledby="look-title">
    <h2 id="look-title">Look inside</h2>
    <div class="previews">{figs}</div>
  </section>

  <section class="sheet" aria-labelledby="free-title">
    <h2 id="free-title">Try the free version first</h2>
    <p class="price-note">{E(p['free_text'])}</p>
    <p><a class="button ghost" href="{p['free_url']}">Open the free word gap tool</a></p>
  </section>

  <section class="prose" aria-labelledby="faq-title">
    <h2 id="faq-title">Questions</h2>
    <div>
      <h3>Is this the official word list?</h3>
      <p>The words follow the 2025 HSK 3.0 syllabus, the same lists used on the rest of hskcheck.com. The pack is made by
      hskcheck.com and is not affiliated with or endorsed by the organisers of the HSK exam.</p>
    </div>
    <div>
      <h3>How do I get the file?</h3>
      <p>Right after you pay, you get a download link, and a copy of it by email. Payments are handled by Creem, our
      online reseller, which also sends your receipt.</p>
    </div>
    <div>
      <h3>Who runs hskcheck.com?</h3>
      <p>hskcheck.com and its printable packs are made and sold by {OPERATOR}, an individual. Contact:
      <a href="mailto:{CONTACT}">{CONTACT}</a>.</p>
    </div>
    <div>
      <h3>Can I use it with my class?</h3>
      <p>The pack is for one learner's own study. Teachers who would like to use it with a class can email
      <a href="mailto:{CONTACT}">{CONTACT}</a>.</p>
    </div>
    <div>
      <h3>I found a mistake.</h3>
      <p>Please tell us at <a href="mailto:{CONTACT}">{CONTACT}</a>. We fix it and send you the corrected file.</p>
    </div>
  </section>
</div>"""


def index_body(nav_html):
    items = "".join(
        f'<a class="pack-item" href="{url(p)}"><img src="{url(p)}{p["previews"][0][0]}" width="620" height="878" alt="" loading="lazy">'
        f'<div><b>{E(p["name"])}</b><span>{E(p["lede"])} {p["price"]}.</span></div></a>' for p in PACKS)
    return f"""<div class="wrap">
  <header>
    {nav_html}
    <div class="eyebrow"><span>hskcheck.com</span></div>
    <h1>Printable packs</h1>
    <p class="lede">Low-cost printable workbooks that go with the free tools on this site. Everything else on hskcheck.com stays free.</p>
  </header>
  <section class="sheet"><div class="pack-list">{items}</div></section>
</div>"""


def terms_body(nav_html):
    return f"""<div class="wrap">
  <header>
    {nav_html}
    <div class="eyebrow"><span>hskcheck.com</span></div>
    <h1>Terms of Service</h1>
    <p class="lede">Last updated: {TERMS_UPDATED}</p>
  </header>

  <section class="sheet policy">
    <h2>About these terms</h2>
    <p>These terms cover hskcheck.com and the printable packs sold on it. By using the site or buying a pack, you agree to them.
    hskcheck.com is operated by {OPERATOR}, an individual. "We" and "us" in these terms mean {OPERATOR}.</p>

    <h2>The free tools and pages</h2>
    <p>The tools, word lists, grammar pages and worksheets on hskcheck.com are free to use and print, including for a class.
    We check the word lists and example sentences carefully, but we can't promise they are free of mistakes. hskcheck.com is
    an independent site and is not affiliated with or endorsed by the organisers of the HSK or YCT exams.</p>

    <h2>Printable packs</h2>
    <p>A printable pack is a PDF file. What each pack contains is described on its page. Prices are in US dollars; any
    sales tax or VAT for your country is added at checkout.</p>

    <h2>Payment and delivery</h2>
    <p>Orders are processed by our online reseller, Creem (creem.io), which is the merchant of record for all orders. Creem
    takes the payment, handles sales tax and sends your receipt. Right after payment you get a link to download the PDF,
    and the link is also sent to your email address.</p>

    <h2>How you may use a pack</h2>
    <p>A pack is for one person's own study, and you may print it as often as you like. Please don't share, upload or resell
    the file. Teachers who want to use a pack with a class can email us for permission.</p>

    <h2>Refunds</h2>
    <p>If a pack isn't useful to you, email <a href="mailto:{CONTACT}">{CONTACT}</a> within {REFUND_DAYS} days of buying it
    and we will refund you in full. You don't need to give a reason. Refunds go back to your original payment method through Creem.</p>

    <h2>Mistakes</h2>
    <p>If you find a mistake in a pack, tell us and we will send you a corrected version at no cost.</p>

    <h2>Contact</h2>
    <p>hskcheck.com is operated by {OPERATOR}. Questions about these terms or an order: <a href="mailto:{CONTACT}">{CONTACT}</a>.</p>

    <h2>Changes</h2>
    <p>If these terms change, the new version will be posted on this page with a new date.</p>
  </section>
</div>"""


def build(root, pages, nav, render, base_css, site):
    css = base_css + CSS
    urls = []
    for p in PACKS:
        target = root / url(p).strip("/")
        target.mkdir(parents=True, exist_ok=True)
        for f, _ in p["previews"]:
            if not (target / f).exists():
                raise SystemExit(f"packs: missing preview image {target / f}")
        (target / "index.html").write_text(render(
            p["title"], p["description"], site + url(p), css, pack_body(p, nav(pages, url(p)))), encoding="utf-8")
        urls.append(url(p))

    target = root / INDEX_URL.strip("/")
    (target / "index.html").write_text(render(
        "Printable HSK Packs | hskcheck.com",
        "Low-cost printable HSK workbooks that go with the free tools on hskcheck.com.",
        site + INDEX_URL, css, index_body(nav(pages, INDEX_URL))), encoding="utf-8")
    urls.append(INDEX_URL)

    target = root / TERMS_URL.strip("/")
    target.mkdir(exist_ok=True)
    (target / "index.html").write_text(render(
        "Terms of Service | hskcheck.com",
        "Terms for using hskcheck.com and buying its printable packs, including payment, delivery and refunds.",
        site + TERMS_URL, base_css, terms_body(nav(pages, TERMS_URL))), encoding="utf-8")
    urls.append(TERMS_URL)
    return urls


# ---- Thai editions ------------------------------------------------------------------------------------------------
TH_INDEX_URL = "/th/upgrade-packs/"

TH_PACKS = [
    {
        "slug": "old-hsk-1-to-new-hsk-1",
        "en_slug": "old-hsk-1-to-new-hsk-1",  # the English edition of the same pack (for hreflang)
        "name": "ชุดอัปเกรด HSK 1 เก่า → HSK 1 ใหม่",
        "price": "$2.99",
        "price_thb": "ประมาณ 100 บาท",
        "pages": 60,
        "checkout": "https://www.creem.io/payment/prod_5JCsd550YCeXi0s97jsTKF",  # Creem checkout link of the Thai product
        "title": "ชุดอัปเกรด HSK 1 เก่า → HSK 1 ใหม่ PDF ภาษาไทย พิมพ์ได้",
        "description": ("เคยเรียน HSK 1 แบบเก่า? เรียนคำศัพท์ HSK 1 ใหม่อีก 155 คำ พร้อมประโยคตัวอย่างแปลไทย "
                        "ฝึกเขียนตัวอักษรใหม่ 74 ตัว แบบทดสอบและเฉลย PDF พิมพ์ได้ $2.99"),
        "lede": ("เคยเรียน HSK 1 แบบเก่ามาแล้ว? HSK 1 ใหม่มีคำศัพท์ 300 คำ และ 155 คำในนั้นไม่มีใน HSK 1 เก่า "
                 "ชุดแบบฝึกพิมพ์ได้นี้สอน 155 คำนั้นใน 10 บทเรียนสั้น ๆ พร้อมคำอธิบายภาษาไทยทั้งเล่ม"),
        "inside": [
            "คำศัพท์ทั้ง 155 คำ พร้อมพินอินและความหมายภาษาไทย ทุกคำมีประโยคตัวอย่างที่ใช้เฉพาะคำศัพท์ HSK 1 ใหม่ "
            "พร้อมพินอินและคำแปลภาษาไทย",
            "ลำดับขีดและช่องฝึกเขียนตามรอย สำหรับตัวอักษร 74 ตัวที่ไม่มีใน HSK 1 เก่า",
            "แบบทดสอบท้ายทุกบท แบบทดสอบรวม 20 ข้อ และเฉลยทั้งหมด",
            "แผนเรียน 10 วัน และดัชนีคำศัพท์",
            "60 หน้า ขนาด A4",
        ],
        "previews": [
            ("page-1.jpg", "หน้าปก"),
            ("page-3.jpg", "ทุกคำมีประโยคตัวอย่าง พร้อมคำแปลภาษาไทย"),
            ("page-5.jpg", "ฝึกเขียนตัวอักษรใหม่ทุกตัว"),
            ("page-6.jpg", "แบบทดสอบท้ายทุกบท"),
        ],
        "free_url": "/th/old-hsk-to-new-hsk/#old=1&new=1",
        "free_text": ("เครื่องมือ HSK เก่า → ใหม่ (ฟรี) แสดงคำศัพท์ 155 คำเดียวกันพร้อมพินอินและความหมายภาษาไทย "
                      "ชุดแบบฝึกเพิ่มประโยคตัวอย่าง แบบฝึกเขียน และแบบทดสอบ จัดหน้าพร้อมพิมพ์"),
    },
    {
        "slug": "hsk-3-vocabulary-workbook",
        "en_slug": None,  # Thai only: no English edition
        "zh": "词汇",
        "name": "สมุดแบบฝึกคำศัพท์ HSK 3 (499 คำ)",
        "price": "$3.99",
        "price_thb": "ประมาณ 130 บาท",
        "pages": 185,
        "checkout": "",  # Creem checkout link of the Thai product, once the owner creates it
        "title": "คำศัพท์ HSK 3 ครบ 499 คำ สมุดแบบฝึก PDF พิมพ์ได้ พร้อมคำแปลไทย",
        "description": ("คำศัพท์ HSK 3 ครบ 499 คำ ใน 25 บทเรียน ทุกคำมีพินอิน ความหมายไทย ประโยคตัวอย่างแปลไทย "
                        "ฝึกเขียนตัวอักษรใหม่ 284 ตัว แบบทดสอบและเฉลย"),
        "lede": ("คำศัพท์ HSK 3 ใหม่ (หลักสูตรปี 2025) ครบทั้ง 499 คำ จัดเป็น 25 บทเรียนตามหัวข้อในชีวิตประจำวัน "
                 "ทุกคำมีประโยคตัวอย่างพร้อมคำแปลภาษาไทย ฝึกเขียนตัวอักษรใหม่ และทำแบบทดสอบท้ายบท พิมพ์ใช้ได้ทันที"),
        "inside": [
            "คำศัพท์ HSK 3 ทั้ง 499 คำ พร้อมพินอินและความหมายภาษาไทย ทุกคำมีประโยคตัวอย่างที่ใช้เฉพาะคำศัพท์ HSK 1–3 "
            "พร้อมพินอินและคำแปลภาษาไทย",
            "ลำดับขีดและช่องฝึกเขียนตามรอย สำหรับตัวอักษร 284 ตัวที่ไม่มีในคำศัพท์ HSK 1–2",
            "แบบทดสอบท้ายทุกบท (จับคู่ความหมาย เติมคำ เขียนพินอิน) แบบทดสอบรวม 30 ข้อ และเฉลยทั้งหมด",
            "แผนเรียน 25 บท และดัชนีคำศัพท์เรียงตามพินอิน",
            "185 หน้า ขนาด A4",
        ],
        "previews": [
            ("page-1.jpg", "หน้าปก"),
            ("page-4.jpg", "ทุกคำมีประโยคตัวอย่าง พร้อมคำแปลภาษาไทย"),
            ("page-7.jpg", "ฝึกเขียนตัวอักษรใหม่ทุกตัว"),
            ("page-9.jpg", "แบบทดสอบท้ายทุกบท"),
        ],
        "free_url": "/th/upgrade-packs/hsk-3-vocabulary-workbook/hsk3-lesson-1-free.pdf",
        "free_button": "ดาวน์โหลดบทที่ 1 ฟรี",
        "free_text": ("ดาวน์โหลดบทที่ 1 (ผู้คนและความสัมพันธ์ 20 คำ) ไปลองใช้ได้ฟรี เป็น PDF 9 หน้า "
                      "มีหน้าคำศัพท์ แบบฝึกเขียน แบบทดสอบ และเฉลย แบบเดียวกับฉบับเต็ม"),
    },
]


def th_url(p):
    return f"{TH_INDEX_URL}{p['slug']}/"


def th_buy_button(p):
    if p["checkout"]:
        return f'<a class="button" href="{E(p["checkout"])}">ซื้อในราคา {p["price"]}</a>'
    return '<span class="button" aria-disabled="true">เปิดให้ซื้อเร็ว ๆ นี้</span>'


def th_pack_body(p, nav_html):
    inside = "".join(f"<li>{E(x)}</li>" for x in p["inside"])
    figs = "".join(
        f'<figure><img src="{th_url(p)}{f}" width="620" height="878" loading="lazy" alt="{E(cap)}"><figcaption>{E(cap)}</figcaption></figure>'
        for f, cap in p["previews"])
    return f"""<div class="wrap">
  <header>
    {nav_html}
    <div class="eyebrow"><span>ชุดแบบฝึกพิมพ์ได้</span><span class="chip">PDF · {p['pages']} หน้า</span><span class="chip">{p['price']}</span></div>
    <h1><span class="zh">{p.get('zh', '补差')}</span>{E(p['name'])}</h1>
    <p class="lede">{E(p['lede'])}</p>
  </header>

  <section class="sheet buy" aria-label="ราคา">
    <div><div class="price">{p['price']}</div><div class="price-note">{E(p['price_thb'])} · จ่ายครั้งเดียว · ดาวน์โหลด PDF ได้ทันที</div></div>
    <div>{th_buy_button(p)}</div>
    <p class="hint">ชำระได้ด้วยบัตรเครดิตหรือบัตรเดบิต Apple Pay Google Pay หรือ Alipay
    ถ้าชุดนี้ไม่มีประโยชน์กับคุณ อีเมลหาเราภายใน {REFUND_DAYS} วันเพื่อขอเงินคืนเต็มจำนวน
    ดู<a href="{TERMS_URL}" hreflang="en">ข้อกำหนดการใช้งาน</a> (ภาษาอังกฤษ)</p>
  </section>

  <section class="sheet" aria-labelledby="inside-title">
    <h2 id="inside-title">ในชุดนี้มีอะไรบ้าง</h2>
    <ul class="inside">{inside}</ul>
  </section>

  <section class="sheet" aria-labelledby="look-title">
    <h2 id="look-title">ตัวอย่างหน้าด้านใน</h2>
    <div class="previews">{figs}</div>
  </section>

  <section class="sheet" aria-labelledby="free-title">
    <h2 id="free-title">ลองเวอร์ชันฟรีก่อน</h2>
    <p class="price-note">{E(p['free_text'])}</p>
    <p><a class="button ghost" href="{p['free_url']}">{E(p.get('free_button', 'เปิดเครื่องมือเทียบคำศัพท์ฟรี'))}</a></p>
  </section>

  <section class="prose" aria-labelledby="faq-title">
    <h2 id="faq-title">คำถามที่พบบ่อย</h2>
    <div>
      <h3>เป็นรายการคำศัพท์ทางการหรือไม่</h3>
      <p>คำศัพท์อ้างอิงหลักสูตร HSK 3.0 ปี 2025 ชุดเดียวกับที่ใช้ทั้งเว็บไซต์ hskcheck.com ชุดแบบฝึกนี้จัดทำโดย hskcheck.com
      ไม่มีส่วนเกี่ยวข้องและไม่ได้รับการรับรองจากผู้จัดสอบ HSK</p>
    </div>
    <div>
      <h3>จะได้รับไฟล์อย่างไร</h3>
      <p>ทันทีที่ชำระเงิน คุณจะได้ลิงก์ดาวน์โหลด และได้รับลิงก์ทางอีเมลด้วย การชำระเงินดำเนินการโดย Creem
      ผู้จัดจำหน่ายออนไลน์ของเรา ซึ่งจะส่งใบเสร็จให้คุณ</p>
    </div>
    <div>
      <h3>ใครเป็นผู้ดูแล hskcheck.com</h3>
      <p>hskcheck.com และชุดแบบฝึกจัดทำและจำหน่ายโดย {OPERATOR} (บุคคลธรรมดา) ติดต่อ:
      <a href="mailto:{CONTACT}">{CONTACT}</a></p>
    </div>
    <div>
      <h3>ใช้กับนักเรียนทั้งห้องได้ไหม</h3>
      <p>ชุดนี้สำหรับผู้เรียนหนึ่งคนใช้เรียนด้วยตนเอง ครูที่อยากใช้กับนักเรียนทั้งห้อง อีเมลมาที่
      <a href="mailto:{CONTACT}">{CONTACT}</a></p>
    </div>
    <div>
      <h3>พบข้อผิดพลาด</h3>
      <p>บอกเราได้ที่ <a href="mailto:{CONTACT}">{CONTACT}</a> เราจะแก้ไขและส่งไฟล์ที่แก้แล้วให้คุณ</p>
    </div>
  </section>
</div>"""


def th_index_body(nav_html):
    items = "".join(
        f'<a class="pack-item" href="{th_url(p)}"><img src="{th_url(p)}{p["previews"][0][0]}" width="620" height="878" alt="" loading="lazy">'
        f'<div><b>{E(p["name"])}</b><span>{E(p["lede"])} {p["price"]}</span></div></a>' for p in TH_PACKS)
    return f"""<div class="wrap">
  <header>
    {nav_html}
    <div class="eyebrow"><span>hskcheck.com</span></div>
    <h1>ชุดแบบฝึกพิมพ์ได้</h1>
    <p class="lede">สมุดแบบฝึกราคาประหยัดที่ใช้คู่กับเครื่องมือฟรีบนเว็บไซต์นี้ เนื้อหาอื่นทั้งหมดบน hskcheck.com ยังคงฟรี</p>
  </header>
  <section class="sheet"><div class="pack-list">{items}</div></section>
</div>"""


def th_alternates():
    """English path -> Thai path for packs that have a Thai edition."""
    pairs = {INDEX_URL: TH_INDEX_URL} if TH_PACKS else {}
    pairs.update({f"{INDEX_URL}{p['en_slug']}/": th_url(p) for p in TH_PACKS if p.get("en_slug")})
    return pairs


def build_th(*, root, site, render, nav, font_link, foot, css):
    css = css + CSS
    urls = []
    for p in TH_PACKS:
        target = root / th_url(p).strip("/")
        target.mkdir(parents=True, exist_ok=True)
        for f, _ in p["previews"]:
            if not (target / f).exists():
                raise SystemExit(f"packs: missing preview image {target / f}")
        (target / "index.html").write_text(render(
            p["title"], p["description"], site + th_url(p), css, th_pack_body(p, nav(th_url(p))),
            font_link, lang="th", foot=foot), encoding="utf-8")
        urls.append(th_url(p))
    if TH_PACKS:
        (root / TH_INDEX_URL.strip("/") / "index.html").write_text(render(
            "ชุดแบบฝึก HSK พิมพ์ได้ ภาษาไทย | hskcheck.com",
            "สมุดแบบฝึก HSK ราคาประหยัด พิมพ์ได้ พร้อมคำอธิบายภาษาไทย ใช้คู่กับเครื่องมือฟรีบน hskcheck.com",
            site + TH_INDEX_URL, css, th_index_body(nav(TH_INDEX_URL)), font_link, lang="th", foot=foot), encoding="utf-8")
        urls.append(TH_INDEX_URL)
    return urls
