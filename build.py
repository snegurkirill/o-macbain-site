#!/usr/bin/env python3
"""Regenerate the works grid in index.html from works.json.

Only the cards between <div class="grid"> and its closing tag are rewritten;
the head, masthead and bio stay hand-edited in the HTML.

filled-images/index.html is the same page with the other grid: every work
fills its card's width at its own height, no mat, in plain rows. It is made
from index.html each run, never edited by hand.

A work with "stretch": <id> in works.json is drawn on that page in the
proportions of work <id>, so it matches that work's height beside it.

Web copies in assets/works/ are made from the originals in Works/ when they
are missing or older than the original.

To mark a work, set its "status" in works.json to "reserved" or "sold"
(or null to clear it), then run:  python3 build.py
"""
import json
import math
import re
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).parent
NB = " "
# Russian prepositions, short conjunctions and particles, bound to the next
# word so none hangs at a line end
SHORT_WORD = re.compile(r"(?<![\w-])(без|в|во|для|до|за|из|изо|к|ко|на|над|о|об|обо|"
                        r"от|ото|перед|по|под|при|про|с|со|у|через|"
                        r"а|и|но|или|да|ни|не)\s+", re.I)
WIDE_RATIO = 1.4  # wider than this spans both columns
MAT = 8           # least margin around a work on its mat, design px
CARD = 202        # card width, design px
SIDE = 900        # longest side of a web copy, px
SIDE_WIDE = 1400  # a wide work is shown at twice the width


def esc(text):
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def web_copy(work):
    original = ROOT / work["image"]
    copy = ROOT / "assets" / "works" / f"{original.stem}.jpg"
    if original.exists() and (not copy.exists()
                              or copy.stat().st_mtime < original.stat().st_mtime):
        im = Image.open(original).convert("RGB")
        side = SIDE_WIDE if im.width / im.height > WIDE_RATIO else SIDE
        im.thumbnail((side, side), Image.LANCZOS)
        copy.parent.mkdir(parents=True, exist_ok=True)
        im.save(copy, quality=86, optimize=True, progressive=True)
    return copy


def card(work, statuses, hung, by_id):
    copy = web_copy(work)
    src = copy.relative_to(ROOT).as_posix()
    w, h = Image.open(copy).size
    title = esc(work["title"] + (f" ({work['note']})" if work["note"] else ""))
    title = SHORT_WORD.sub(rf"\1{NB}", title)
    details = esc(f"{work['size']}, {work['medium']}").replace(" см", NB + "см")
    price = f"{work['price']:,}".replace(",", NB) + NB + "₽"
    wide = " work--wide" if w / h > WIDE_RATIO else ""
    stretch = ""
    if work.get("stretch"):
        sw, sh = Image.open(web_copy(by_id[work["stretch"]])).size
        wide += " work--stretch"
        stretch = f' style="--stretch: {sw} / {sh}"'
    scale = ""
    if work["id"] in hung:
        sw, sh = hung[work["id"]]
        scale = f' style="--w: {sw:.1f}; --h: {sh:.1f}"'

    status = ""
    if work.get("status"):
        key = work["status"]
        if key not in statuses:
            raise SystemExit(f"work {work['id']}: unknown status {key!r}")
        status = (f'\n            <span class="work__status work__status--{key}">'
                  f"{statuses[key]}</span>")

    return f"""        <figure class="work{wide}"{stretch}>
          <img src="{src}" alt="{title}" width="{w}" height="{h}"{scale} loading="lazy" decoding="async">
          <figcaption>
            <span class="work__title">{title}</span>
            <span class="work__price">{price}</span>
            <span class="work__details">{details}</span>{status}
          </figcaption>
        </figure>"""


def long_side_cm(work):
    return max(float(n.replace(",", ".")) for n in re.findall(r"\d+(?:[.,]\d+)?", work["size"]))


def hang(works):
    """Size every one-column work by its real size, on a mat that holds them all.

    A work's long side on screen grows with the square root of its long side
    in cm, so a bigger canvas reads bigger without the small ones shrinking to
    stamps. One factor serves every work: the largest that keeps the widest
    of them inside the mat's CARD - 2*MAT. The mat is then as short as the
    tallest work plus MAT above and below.

    Returns the mat height and {id: (width, height)} on screen, design px.
    """
    shapes = {}
    for w in works:
        width, height = Image.open(web_copy(w)).size
        if width / height <= WIDE_RATIO:
            shapes[w["id"]] = (width / height, math.sqrt(long_side_cm(w)))
    def size(ratio, root, k):
        long = k * root
        return (long * ratio, long) if ratio < 1 else (long, long / ratio)
    inner = CARD - 2 * MAT
    k = min(inner / size(ratio, root, 1)[0] for ratio, root in shapes.values())
    hung = {i: size(ratio, root, k) for i, (ratio, root) in shapes.items()}
    return math.ceil(max(h for _, h in hung.values())) + 2 * MAT, hung


def filled_page(html):
    """index.html with the pinboard grid, one folder down."""
    html = re.sub(r'(src|href)="(?!https?:|#)([^"]+)"', r'\1="../\2"', html)
    html = re.sub(r'<div class="grid"[^>]*>', '<div class="grid grid--filled">', html)
    html = re.sub(r' style="--w: [^"]*"', "", html)
    return html


def main():
    data = json.loads((ROOT / "works.json").read_text())
    mat_h, hung = hang(data["works"])
    by_id = {w["id"]: w for w in data["works"]}
    cards = "\n".join(card(w, data["statuses"], hung, by_id) for w in data["works"])
    grid = f'<div class="grid" style="--mat-h: {mat_h}">\n'

    page = ROOT / "index.html"
    html = page.read_text()
    html, n = re.subn(r'<div class="grid"[^>]*>\n.*?(\n      </div>\n  </main>)',
                      lambda m: grid + cards + m.group(1), html, flags=re.S)
    if n != 1:
        raise SystemExit("grid block not found in index.html")
    page.write_text(html)

    filled = ROOT / "filled-images" / "index.html"
    filled.parent.mkdir(exist_ok=True)
    filled.write_text(filled_page(html))

    marked = [f"{w['title']}: {w['status']}" for w in data["works"] if w.get("status")]
    print(f"{len(data['works'])} cards written" + (f"; {', '.join(marked)}" if marked else ""))


if __name__ == "__main__":
    main()
