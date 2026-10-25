import sys
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b=p.chromium.launch(); pg=b.new_page()
    pg.goto('file://'+sys.argv[1]); pg.wait_for_timeout(800)
    # overflow check: content taller than page
    bad=pg.evaluate("""[...document.querySelectorAll('.page')].map((s,i)=>{const inn=s.querySelector('.inner');return inn.scrollHeight>s.clientHeight-30?i+1:0}).filter(Boolean)""")
    print('overflow pages',bad)
    pg.pdf(path=sys.argv[2],format='A4',print_background=True,prefer_css_page_size=True)
    b.close()
