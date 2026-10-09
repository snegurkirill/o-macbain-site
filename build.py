#!/usr/bin/env python3
"""Regenerate the works grid in index.html from works.json.

Only the cards between <div class="grid"> and its closing tag are rewritten;
the head, masthead and bio stay hand-edited in the HTML.

Web copies in assets/works/ are made from the originals in Works/ when they
are missing or older than the original.

To mark a work, set its "status" in works.json to "reserved" or "sold"
(or null to clear it), then run:  python3 build.py
"""
import json
import re
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).parent
NB = " "
WIDE_RATIO = 1.4  # wider than this spans both columns
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


def card(work, statuses):
    copy = web_copy(work)
    src = copy.relative_to(ROOT).as_posix()
    w, h = Image.open(copy).size
    title = esc(work["title"] + (f" ({work['note']})" if work["note"] else ""))
    details = esc(f"{work['size']}, {work['medium']}").replace(" см", NB + "см")
    price = f"{work['price']:,}".replace(",", NB) + NB + "₽"
    wide = " work--wide" if w / h > WIDE_RATIO else ""

    status = ""
    if work.get("status"):
        key = work["status"]
        if key not in statuses:
            raise SystemExit(f"work {work['id']}: unknown status {key!r}")
        status = (f'\n            <span class="work__status work__status--{key}">'
                  f"{statuses[key]}</span>")

    return f"""        <figure class="work{wide}">
          <img src="{src}" alt="{title}" width="{w}" height="{h}" loading="lazy" decoding="async">
          <figcaption>
            <span class="work__title">{title}</span>
            <span class="work__price">{price}</span>
            <span class="work__details">{details}</span>{status}
          </figcaption>
        </figure>"""


def main():
    data = json.loads((ROOT / "works.json").read_text())
    cards = "\n".join(card(w, data["statuses"]) for w in data["works"])

    page = ROOT / "index.html"
    html = page.read_text()
    html, n = re.subn(r'(<div class="grid">\n).*?(\n      </div>\n  </main>)',
                      lambda m: m.group(1) + cards + m.group(2), html, flags=re.S)
    if n != 1:
        raise SystemExit("grid block not found in index.html")
    page.write_text(html)

    marked = [f"{w['title']}: {w['status']}" for w in data["works"] if w.get("status")]
    print(f"{len(data['works'])} cards written" + (f"; {', '.join(marked)}" if marked else ""))


if __name__ == "__main__":
    main()
