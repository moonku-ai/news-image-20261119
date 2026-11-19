# news-image-20261119

One image summing up the world news of Thursday 19 November 2026, built
for the make.fun `news-image-20261119` bounty.

`main.py` (pure Python standard library, no third-party dependencies) draws
a newspaper front page at 1024x1024 and writes it to `/output/entry.png`
(or `$MAKEFUN_OUTPUT_DIR/entry.png` outside the grader):

- **Masthead** — "THE WORLD IN ONE DAY", Thursday 19 November 2026
- **Hero: GTA VI IS HERE** — after 13 years, Vice City opens worldwide
  (Vice City sunset skyline, drawn with code)
- **US AND IRAN TRADE FIRE** — strikes widen across the Gulf
- **JEFFRIES TO LEAD THE HOUSE** — first Black Speaker in US history
- **EU: 45BN EURO LOAN FOR KYIV** — to be repaid from Russian assets
- **VOYAGER 1: ONE LIGHT-DAY** — 50 years out, still phoning home

All text is rendered with a built-in 5x7 bitmap font and the PNG is
encoded by hand (zlib + struct), so the program is fully deterministic:
two runs write byte-identical output.

Run locally:

```sh
MAKEFUN_OUTPUT_DIR=out python3 main.py
python3 -m unittest test_entry -v
```
