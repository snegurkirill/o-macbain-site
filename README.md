# O. MACBAIN — site

Static site, no build step. Every path is relative, so it runs at a domain root
or a subpath on any host unchanged. Same system as the Andrey Novitskiy
catalogue (`../Andrey Novitskiy, site`).

## Updating the works

Card data lives in `works.json`. After editing it, regenerate the grid:

    python3 build.py

To set a status, give the work `"status": "reserved"` (Забронирована, blue dot)
or `"sold"` (Приобретена, red dot); `null` clears it. The head, wordmark and bio
in `index.html` are edited by hand — `build.py` only rewrites the cards.

To replace a picture, drop the new file into `Works/` under the same name and
run `build.py`: it remakes the web copy in `assets/works/` when the original is
newer.

## Data

`works.json` is the catalogue, read from the artist's Google Doc
(`source/o-macbain-works.docx`). The images in `Works/` are the copies embedded
in that doc: Google caps them at 2048px and re-compresses them, so they are not
the camera originals. The page uses 900px copies (1400px for wide works) in
`assets/works/`. `source/` and `Works/` stay local — see `.gitignore`.
