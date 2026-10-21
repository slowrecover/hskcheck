"""Baduanjin (八段锦) follow-along page, built to /baduanjin/ from data/baduanjin.json.

The build stops if the set does not have an opening, eight movements and a closing, or if a
movement is missing its text or poses.
"""
import html
import json

URL = "/baduanjin/"
NORMAL_PACE = 4  # seconds per half breath, the page default


def load(data):
    stages = json.loads((data / "baduanjin.json").read_text(encoding="utf-8"))["stages"]
    if len(stages) != 10 or stages[0]["id"] != "opening" or stages[-1]["id"] != "closing":
        raise SystemExit("baduanjin.json: expected an opening, eight movements and a closing")
    for st in stages:
        for key in ("zh", "py", "en", "meaning", "steps", "tip", "a", "b", "reps", "cue_a", "cue_b"):
            if not st.get(key):
                raise SystemExit(f"baduanjin.json: {st.get('id')} has no {key}")
        for p in (st["a"], st["b"]):
            if "hipY" not in p or "hl" not in p or "hr" not in p:
                raise SystemExit(f"baduanjin.json: {st['id']} pose needs hipY, hl and hr")
    return stages


def minutes(stages, pace=NORMAL_PACE):
    """Length of the set at a given pace, matching the page's timeline."""
    total = 0
    for i, st in enumerate(stages):
        if i:
            total += pace
        if st.get("mode") == "in":
            total += pace + pace * 2 * st.get("hold", 1)
            continue
        sides = 2 if st["sides"] else 1
        per = 2 * pace + (pace * 2 * st["hold"] if st.get("hold") else 0)
        total += st["reps"] * sides * per
    return round(total / 60)


def build(root, pages, nav, render, base_css, tpl, site):
    stages = load(root / "data")
    moves = []
    for i, st in enumerate(stages):
        label = "Opening" if i == 0 else "Closing" if i == len(stages) - 1 else f"Movement {i}"
        sides = 2 if st["sides"] else 1
        if st.get("mode") == "in" or i == len(stages) - 1:
            reps = "Do once, then breathe calmly for a moment."
        elif sides == 2:
            reps = f"{st['reps']} rounds, each round once to each side."
        else:
            reps = f"{st['reps']} times."
        steps = "".join(f"<li>{html.escape(s)}</li>" for s in st["steps"])
        moves.append(
            f'      <article class="bd-move" id="{st["id"]}">\n'
            f'        <svg class="bd-thumb" viewBox="0 0 200 250" data-pose="{i}" role="img" aria-label="{html.escape(st["en"])}"></svg>\n'
            f'        <div>\n'
            f'          <p class="bd-step">{label}</p>\n'
            f'          <h3><span class="zh">{html.escape(st["zh"])}</span> {html.escape(st["en"])}</h3>\n'
            f'          <p class="bd-py">{html.escape(st["py"])} · <i>{html.escape(st["meaning"])}</i></p>\n'
            f"          <ol>{steps}</ol>\n"
            f'          <p class="bd-reps"><b>{html.escape(reps)}</b> {html.escape(st["tip"])}</p>\n'
            f"        </div>\n"
            f"      </article>"
        )
    mins = minutes(stages)
    body = (tpl / "baduanjin_body.html").read_text(encoding="utf-8")
    body = (body.replace("__NAV__", nav(pages, URL))
            .replace("__MOVES__", "\n".join(moves))
            .replace("__MINUTES__", str(mins))
            .replace("__STAGES_JSON__", json.dumps(stages, ensure_ascii=False, separators=(",", ":"))))
    description = "Follow the Baduanjin (Eight Brocades) qigong routine with an animated guide, breathing pace and voice cues."
    ld = json.dumps({
        "@context": "https://schema.org", "@type": "WebApplication", "name": "Baduanjin Follow-Along",
        "url": site + URL, "applicationCategory": "HealthApplication", "operatingSystem": "Any",
        "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"},
        "description": description,
    }, ensure_ascii=False)
    out = render(
        "Baduanjin (Eight Brocades) Qigong: Free Follow-Along Routine",
        f"Do the Baduanjin (八段锦, Eight Brocades) qigong routine with an animated guide that moves with your breath, "
        f"counts the rounds and gives voice cues. All 8 movements step by step, about {mins} minutes. Free.",
        site + URL,
        base_css + (tpl / "checker.css").read_text(encoding="utf-8") + (tpl / "baduanjin.css").read_text(encoding="utf-8"),
        body,
        f'<script type="application/ld+json">{ld}</script>',
    )
    target = root / URL.strip("/")
    target.mkdir(exist_ok=True)
    (target / "index.html").write_text(out, encoding="utf-8")
    return [URL]
