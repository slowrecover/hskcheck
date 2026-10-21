"""Build tones/words.json, the pinyin dictionary used by the tone change page.

Source: complete-hsk-vocabulary (https://github.com/drkameleon/complete-hsk-vocabulary, MIT),
the same data used for strokes/. Pass the path to its complete.json:

    python3 tools/make_tone_data.py /path/to/complete-hsk-vocabulary/complete.json

Output: {"w": {word: "syllables with tone numbers"}} for every word in the list, plus a default
reading for every single character. Readings are the dictionary (citation) tones; the page
works out the spoken tones. Words and characters with more than one reading use the rules below.
"""
import json
import pathlib
import re
import sys
import unicodedata

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "tones" / "words.json"

# Default reading when a character stands on its own. Chosen for everyday use; everything
# else falls back to the reading the character has most often inside words.
CHAR = {
    "上": "shang4", "个": "ge4", "了": "le5", "会": "hui4", "几": "ji3", "分": "fen1", "只": "zhi3", "号": "hao4",
    "吗": "ma5", "吧": "ba5", "听": "ting1", "呢": "ne5", "和": "he2", "哪": "na3", "喂": "wei4", "大": "da4",
    "好": "hao3", "少": "shao3", "的": "de5", "看": "kan4", "给": "gei3", "要": "yao4", "见": "jian4", "说": "shuo1",
    "读": "du2", "车": "che1", "边": "bian1", "还": "hai2", "都": "dou1", "雨": "yu3", "万": "wan4", "别": "bie2",
    "啊": "a5", "地": "de5", "头": "tou2", "得": "de5", "打": "da3", "教": "jiao1", "正": "zheng4", "着": "zhe5",
    "离": "li2", "累": "lei4", "跑": "pao3", "过": "guo4", "远": "yuan3", "长": "chang2", "间": "jian1", "中": "zhong1",
    "为": "wei4", "刷": "shua1", "卡": "ka3", "发": "fa1", "可": "ke3", "子": "zi3", "差": "cha4", "干": "gan4",
    "扫": "sao3", "把": "ba3", "更": "geng4", "种": "zhong3", "胖": "pang4", "脏": "zang1", "节": "jie2", "行": "xing2",
    "角": "jiao3", "难": "nan2", "页": "ye4", "骑": "qi2", "与": "yu3", "乘": "cheng2", "俩": "lia3", "倒": "dao4",
    "假": "jia3", "凉": "liang2", "厂": "chang3", "压": "ya1", "咳": "ke2", "嗯": "en5", "场": "chang3", "将": "jiang1",
    "底": "di3", "弄": "nong4", "弹": "tan2", "强": "qiang2", "当": "dang1", "待": "dai4", "提": "ti2", "数": "shu4",
    "汗": "han4", "汤": "tang1", "片": "pian4", "省": "sheng3", "稍": "shao1", "空": "kong1", "答": "da2", "约": "yue1",
    "背": "bei4", "落": "luo4", "赚": "zhuan4", "趟": "tang4", "转": "zhuan3", "通": "tong1", "重": "zhong4", "量": "liang4",
    "降": "jiang4", "鲜": "xian1", "亲": "qin1", "令": "ling4", "传": "chuan2", "便": "bian4", "冲": "chong1", "切": "qie1",
    "划": "hua2", "匹": "pi3", "占": "zhan4", "同": "tong2", "哈": "ha1", "哦": "o4", "唉": "ai1", "处": "chu4",
    "广": "guang3", "度": "du4", "扇": "shan4", "抢": "qiang3", "挑": "tiao1", "挡": "dang3", "挣": "zheng4", "据": "ju4",
    "曾": "ceng2", "朝": "chao2", "浅": "qian3", "涨": "zhang3", "炸": "zha4", "称": "cheng1", "系": "xi4", "结": "jie2",
    "臭": "chou4", "薄": "bao2", "藏": "cang2", "调": "diao4", "追": "zhui1", "乐": "le4", "价": "jia4", "作": "zuo4",
    "咱": "zan2", "没": "mei2", "觉": "jue2", "色": "se4", "应": "ying1", "担": "dan1", "恶": "e4", "供": "gong1",
    "露": "lu4", "解": "jie3", "识": "shi2", "足": "zu2", "率": "lü4", "曲": "qu3", "散": "san4", "尽": "jin4",
    "属": "shu3", "折": "zhe2", "服": "fu2", "漂": "piao1", "盛": "sheng4", "钻": "zuan1", "铺": "pu1", "横": "heng2",
    "晕": "yun1", "夹": "jia1", "圈": "quan1", "塞": "sai1", "埋": "mai2", "吐": "tu3", "吓": "xia4", "啦": "la5",
    "嘛": "ma5", "哇": "wa5", "卷": "juan3", "刺": "ci4", "泡": "pao4", "缝": "feng2", "磨": "mo2", "闷": "men4",
    "喝": "he1", "喂": "wei2", "尺": "chi3", "拾": "shi2", "扛": "kang2", "拽": "zhuai4", "搂": "lou3", "攒": "zan3",
    "熨": "yun4", "眯": "mi1", "翘": "qiao4", "削": "xiao1", "剥": "bao1", "呛": "qiang1", "咽": "yan4", "揣": "chuai1",
    "虾": "xia1", "逮": "dai3", "驮": "tuo2", "炮": "pao4", "粥": "zhou1", "糊": "hu2", "涌": "yong3",
}

# Words whose dictionary entry has more than one reading: the everyday one.
WORD = {
    "便宜": "pian2 yi5", "大夫": "dai4 fu5", "东西": "dong1 xi5", "地方": "di4 fang5", "当时": "dang1 shi2",
    "当年": "dang1 nian2", "当天": "dang1 tian1", "出来": "chu1 lai2", "多少": "duo1 shao5", "分量": "fen4 liang5",
    "高中": "gao1 zhong1", "告诉": "gao4 su5", "故事": "gu4 shi5", "工夫": "gong1 fu5", "得了": "de2 le5",
    "罢了": "ba4 le5", "大意": "da4 yi4", "大方": "da4 fang5", "倒车": "dao4 che1", "播种": "bo1 zhong3",
    "背着": "bei1 zhe5", "本事": "ben3 shi5", "地道": "di4 dao5", "恶心": "e3 xin1", "大都": "da4 dou1",
    "澄清": "cheng2 qing1", "本色": "ben3 se4",
}

TONE_MARKS = {"ā": ("a", 1), "á": ("a", 2), "ǎ": ("a", 3), "à": ("a", 4), "ē": ("e", 1), "é": ("e", 2), "ě": ("e", 3),
              "è": ("e", 4), "ī": ("i", 1), "í": ("i", 2), "ǐ": ("i", 3), "ì": ("i", 4), "ō": ("o", 1), "ó": ("o", 2),
              "ǒ": ("o", 3), "ò": ("o", 4), "ū": ("u", 1), "ú": ("u", 2), "ǔ": ("u", 3), "ù": ("u", 4), "ǖ": ("ü", 1),
              "ǘ": ("ü", 2), "ǚ": ("ü", 3), "ǜ": ("ü", 4)}
SYL = re.compile(r"^[a-zü]+[1-5]$")
HAN = re.compile(r"^[一-鿿]+$")


def clean(numeric):
    """'Lü4 se4' -> 'lü4 se4'; returns None if a syllable is malformed."""
    parts = numeric.lower().replace("u:", "ü").replace("v", "ü").split()
    return " ".join(parts) if parts and all(SYL.match(p) for p in parts) else None


def from_marks(pinyin, n):
    """Tone-marked syllables split by spaces, as a fallback for malformed numeric entries."""
    out = []
    for syl in pinyin.lower().split():
        tone, plain = 5, ""
        for ch in unicodedata.normalize("NFC", syl):
            if ch in TONE_MARKS:
                base, tone = TONE_MARKS[ch]
                plain += base
            else:
                plain += ch
        out.append(plain + str(tone))
    joined = " ".join(out)
    return joined if len(out) == n and all(SYL.match(p) for p in out) else None


def readings(entry):
    word = entry["simplified"]
    found = []
    for form in entry["forms"]:
        tr = form["transcriptions"]
        if tr["numeric"][:1].isupper():
            continue  # surnames and place names
        meanings = form.get("meanings", [])
        if meanings and all("variant of" in m for m in meanings):
            continue
        r = clean(tr["numeric"]) or from_marks(tr["pinyin"], len(word))
        if r and len(r.split()) == len(word) and r not in found:
            found.append(r)
    return found


def main(src):
    data = json.loads(pathlib.Path(src).read_text(encoding="utf-8"))
    words, inside = {}, {}
    for entry in data:
        word = entry["simplified"]
        if not HAN.match(word):
            continue
        rs = readings(entry)
        if not rs:
            continue
        if len(word) > 1:
            if word in WORD:
                pick = WORD[word]
            elif len(rs) > 1:
                # Same syllables except a neutral tone: the neutral form is the everyday reading.
                neutral = [r for r in rs if r.endswith("5")]
                pick = neutral[0] if neutral else rs[0]
            else:
                pick = rs[0]
            words[word] = pick
            for c, s in zip(word, pick.split()):
                inside.setdefault(c, {}).setdefault(s, 0)
                inside[c][s] += 1
        else:
            words.setdefault(word, None)
            inside.setdefault(word, {})
            for r in rs:
                inside[word].setdefault(r, 0)
            if word in CHAR:
                if CHAR[word] not in rs:
                    raise SystemExit(f"{word}: default {CHAR[word]} is not one of its readings {rs}")
                words[word] = CHAR[word]
            elif len(rs) == 1:
                words[word] = rs[0]
            else:
                words[word] = ("multi", rs)
    # Characters with several readings and no default: the one used most inside words.
    for c, v in list(words.items()):
        if v is None or isinstance(v, tuple):
            options = v[1] if isinstance(v, tuple) else list(inside.get(c, {}))
            counts = inside.get(c, {})
            words[c] = max(options, key=lambda r: (counts.get(r, 0), -options.index(r))) if options else None
    # Characters that only appear inside words.
    for c, counts in inside.items():
        if c not in words and counts:
            words[c] = max(counts, key=counts.get)
    words = {w: r for w, r in words.items() if r}
    for c, r in CHAR.items():
        if words.get(c) != r:
            raise SystemExit(f"default for {c} not applied")
    for w, r in WORD.items():
        if w in words and words[w] != r:
            raise SystemExit(f"default for {w} not applied")
    OUT.parent.mkdir(exist_ok=True)
    ordered = dict(sorted(words.items(), key=lambda kv: (len(kv[0]), kv[0])))
    OUT.write_text(json.dumps({"w": ordered}, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    singles = sum(1 for w in words if len(w) == 1)
    print(f"wrote {OUT.relative_to(ROOT)}: {len(words) - singles} words, {singles} characters, "
          f"{OUT.stat().st_size // 1024} KB")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    main(sys.argv[1])
