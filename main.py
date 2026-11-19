#!/usr/bin/env python3
"""news-image-20261119: sum up the world news of Thursday 19 November 2026
in one 1024x1024 image.

Pure Python standard library only (zlib + struct for the PNG encoder).
The image is a newspaper front page: a masthead naming the day, one big
hero story (GTA VI launches worldwide) and four more stories in a grid
(US-Iran strikes widen, Jeffries to lead the House, the EU's 45bn euro
Ukraine loan, Voyager 1 reaching one light-day). All text is drawn with a
built-in 5x7 bitmap font, so the program is fully deterministic: two runs
write byte-identical PNGs.

Run:  MAKEFUN_OUTPUT_DIR=out python3 main.py   (writes out/entry.png)
"""
import math
import os
import struct
import zlib

W = 1024
H = 1024

# --- palette (newsprint front page) -------------------------------------
PAPER = (246, 241, 229)
INK = (22, 35, 63)          # deep navy ink
RED = (179, 39, 30)
GOLD = (217, 164, 65)
TEAL = (14, 124, 107)
BLUE = (46, 111, 176)
PURPLE = (91, 42, 134)
ORANGE = (232, 106, 28)
SUNSET = (245, 183, 76)
SEA = (20, 60, 90)
WHITE = (255, 255, 255)
SKY_DARK = (58, 32, 86)
CARD = (255, 253, 247)

# --- 5x7 bitmap font (rows are 5-bit values, MSB = leftmost pixel) ------
FONT = {
    " ": (0, 0, 0, 0, 0, 0, 0),
    "A": (0x0E, 0x11, 0x11, 0x1F, 0x11, 0x11, 0x11),
    "B": (0x1E, 0x11, 0x11, 0x1E, 0x11, 0x11, 0x1E),
    "C": (0x0E, 0x11, 0x10, 0x10, 0x10, 0x11, 0x0E),
    "D": (0x1E, 0x11, 0x11, 0x11, 0x11, 0x11, 0x1E),
    "E": (0x1F, 0x10, 0x10, 0x1E, 0x10, 0x10, 0x1F),
    "F": (0x1F, 0x10, 0x10, 0x1E, 0x10, 0x10, 0x10),
    "G": (0x0E, 0x11, 0x10, 0x17, 0x11, 0x11, 0x0F),
    "H": (0x11, 0x11, 0x11, 0x1F, 0x11, 0x11, 0x11),
    "I": (0x0E, 0x04, 0x04, 0x04, 0x04, 0x04, 0x0E),
    "J": (0x07, 0x02, 0x02, 0x02, 0x02, 0x12, 0x0C),
    "K": (0x11, 0x12, 0x14, 0x18, 0x14, 0x12, 0x11),
    "L": (0x10, 0x10, 0x10, 0x10, 0x10, 0x10, 0x1F),
    "M": (0x11, 0x1B, 0x15, 0x15, 0x11, 0x11, 0x11),
    "N": (0x11, 0x19, 0x15, 0x13, 0x11, 0x11, 0x11),
    "O": (0x0E, 0x11, 0x11, 0x11, 0x11, 0x11, 0x0E),
    "P": (0x1E, 0x11, 0x11, 0x1E, 0x10, 0x10, 0x10),
    "Q": (0x0E, 0x11, 0x11, 0x11, 0x15, 0x12, 0x0D),
    "R": (0x1E, 0x11, 0x11, 0x1E, 0x14, 0x12, 0x11),
    "S": (0x0F, 0x10, 0x10, 0x0E, 0x01, 0x01, 0x1E),
    "T": (0x1F, 0x04, 0x04, 0x04, 0x04, 0x04, 0x04),
    "U": (0x11, 0x11, 0x11, 0x11, 0x11, 0x11, 0x0E),
    "V": (0x11, 0x11, 0x11, 0x11, 0x11, 0x0A, 0x04),
    "W": (0x11, 0x11, 0x11, 0x15, 0x15, 0x1B, 0x11),
    "X": (0x11, 0x11, 0x0A, 0x04, 0x0A, 0x11, 0x11),
    "Y": (0x11, 0x11, 0x0A, 0x04, 0x04, 0x04, 0x04),
    "Z": (0x1F, 0x01, 0x02, 0x04, 0x08, 0x10, 0x1F),
    "0": (0x0E, 0x11, 0x13, 0x15, 0x19, 0x11, 0x0E),
    "1": (0x04, 0x0C, 0x04, 0x04, 0x04, 0x04, 0x0E),
    "2": (0x0E, 0x11, 0x01, 0x06, 0x08, 0x10, 0x1F),
    "3": (0x1F, 0x02, 0x04, 0x02, 0x01, 0x11, 0x0E),
    "4": (0x02, 0x06, 0x0A, 0x12, 0x1F, 0x02, 0x02),
    "5": (0x1F, 0x10, 0x1E, 0x01, 0x01, 0x11, 0x0E),
    "6": (0x06, 0x08, 0x10, 0x1E, 0x11, 0x11, 0x0E),
    "7": (0x1F, 0x01, 0x02, 0x04, 0x08, 0x08, 0x08),
    "8": (0x0E, 0x11, 0x11, 0x0E, 0x11, 0x11, 0x0E),
    "9": (0x0E, 0x11, 0x11, 0x0F, 0x01, 0x02, 0x0C),
    ".": (0, 0, 0, 0, 0, 0x0C, 0x0C),
    ",": (0, 0, 0, 0, 0x0C, 0x04, 0x08),
    ":": (0, 0x0C, 0x0C, 0, 0x0C, 0x0C, 0),
    "-": (0, 0, 0, 0x0E, 0, 0, 0),
    "!": (0x04, 0x04, 0x04, 0x04, 0x04, 0, 0x04),
    "?": (0x0E, 0x11, 0x01, 0x02, 0x04, 0, 0x04),
    "/": (0x01, 0x01, 0x02, 0x04, 0x08, 0x10, 0x10),
    "(": (0x02, 0x04, 0x08, 0x08, 0x08, 0x04, 0x02),
    ")": (0x08, 0x04, 0x02, 0x02, 0x02, 0x04, 0x08),
    "'": (0x04, 0x04, 0x08, 0, 0, 0, 0),
    "$": (0x04, 0x0F, 0x14, 0x0E, 0x05, 0x1E, 0x04),
    "%": (0x19, 0x19, 0x02, 0x04, 0x08, 0x13, 0x13),
    "&": (0x0C, 0x12, 0x14, 0x08, 0x15, 0x12, 0x0D),
    "+": (0, 0x04, 0x04, 0x1F, 0x04, 0x04, 0),
    "=": (0, 0, 0x1F, 0, 0x1F, 0, 0),
}


def glyph(ch):
    """Bitmap rows for one character; unknown characters render blank."""
    return FONT.get(ch, FONT[" "])


def text_width(text, scale):
    """Pixel width of text drawn at the given scale."""
    return len(text) * 6 * scale


def wrap_text(text, max_chars):
    """Greedy word wrap into lines of at most max_chars characters."""
    lines = []
    current = ""
    for word in text.split(" "):
        if not current:
            current = word
        elif len(current) + 1 + len(word) <= max_chars:
            current += " " + word
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


class Canvas:
    """An RGB pixel buffer with simple vector drawing primitives."""

    def __init__(self, width, height, bg=PAPER):
        self.w = width
        self.h = height
        self.px = bytearray(bg * width * height)

    def _set(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i:i + 3] = bytes(color)

    def count_color(self, color):
        n = 0
        for i in range(0, len(self.px), 3):
            if tuple(self.px[i:i + 3]) == color:
                n += 1
        return n

    def fill_rect(self, x, y, w, h, color):
        x0 = max(0, x)
        y0 = max(0, y)
        x1 = min(self.w, x + w)
        y1 = min(self.h, y + h)
        row = bytes(color) * (x1 - x0)
        for yy in range(y0, y1):
            i = (yy * self.w + x0) * 3
            self.px[i:i + len(row)] = row

    def draw_line(self, x0, y0, x1, y1, color, thick=1):
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        while True:
            self.fill_rect(x0 - thick // 2, y0 - thick // 2, thick, thick, color)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def fill_circle(self, cx, cy, r, color):
        for dy in range(-r, r + 1):
            dx = int(math.sqrt(max(0, r * r - dy * dy)))
            self.fill_rect(cx - dx, cy + dy, 2 * dx + 1, 1, color)

    def fill_triangle(self, x0, y0, x1, y1, x2, y2, color):
        pts = sorted([(x0, y0), (x1, y1), (x2, y2)], key=lambda p: p[1])
        (ax, ay), (bx, by), (cx, cy) = pts
        if ay == cy:
            return
        for y in range(ay, cy + 1):
            t1 = (y - ay) / (cy - ay) if cy != ay else 0
            xa = ax + (cx - ax) * t1
            if y < by:
                t2 = (y - ay) / (by - ay) if by != ay else 0
                xb = ax + (bx - ax) * t2
            else:
                t2 = (y - by) / (cy - by) if cy != by else 0
                xb = bx + (cx - bx) * t2
            self.fill_rect(int(min(xa, xb)), y, int(abs(xa - xb)) + 1, 1, color)

    def draw_text(self, x, y, text, scale, color):
        cx = x
        for ch in text:
            rows = glyph(ch)
            for r in range(7):
                bits = rows[r]
                for c in range(5):
                    if bits & (1 << (4 - c)):
                        self.fill_rect(cx + c * scale, y + r * scale,
                                       scale, scale, color)
            cx += 6 * scale
        return cx

    def draw_text_centered(self, cx, y, text, scale, color):
        self.draw_text(cx - text_width(text, scale) // 2, y, text, scale, color)


# --- the day's stories ----------------------------------------------------
# (accent colour, icon kind, headline lines, summary lines)
STORIES = [
    (RED, "burst",
     ["US AND IRAN", "TRADE FIRE"],
     ["STRIKES WIDEN ACROSS", "THE GULF"]),
    (INK, "capitol",
     ["JEFFRIES TO", "LEAD THE HOUSE"],
     ["FIRST BLACK SPEAKER", "IN US HISTORY"]),
    (BLUE, "stars",
     ["EU: 45BN EURO", "LOAN FOR KYIV"],
     ["TO BE REPAID FROM", "RUSSIAN ASSETS"]),
    (TEAL, "probe",
     ["VOYAGER 1:", "ONE LIGHT-DAY"],
     ["50 YEARS OUT, STILL", "PHONING HOME"]),
]


def draw_burst_icon(c, x, y, s, color):
    """Explosion starburst for the US-Iran strikes story."""
    cx, cy = x + s // 2, y + s // 2
    for k in range(8):
        ang = k * math.pi / 4
        tx = cx + int(math.cos(ang) * s * 0.48)
        ty = cy + int(math.sin(ang) * s * 0.48)
        c.draw_line(cx, cy, tx, ty, color, thick=6)
    c.fill_circle(cx, cy, s // 6, GOLD)
    c.fill_circle(cx, cy, s // 12, WHITE)


def draw_capitol_icon(c, x, y, s, color):
    """US Capitol dome for the Jeffries story."""
    cx = x + s // 2
    base_y = y + s - 14
    # dome: a true semicircle (circle with its lower half covered)
    dome_r = s // 4
    dome_cy = base_y - 26
    c.fill_circle(cx, dome_cy, dome_r, color)
    c.fill_rect(cx - dome_r, dome_cy, 2 * dome_r, dome_r, CARD)
    # drum + base
    c.fill_rect(cx - s // 4, base_y - 26, s // 2, 26, color)
    c.fill_rect(x + 8, base_y, s - 16, 14, color)
    # columns
    for i in range(5):
        col_x = cx - s // 4 + 4 + i * (s // 2 - 8) // 4
        c.fill_rect(col_x, base_y - 24, 4, 24, PAPER)
    # flag on the dome top
    c.draw_line(cx, dome_cy - dome_r - 18, cx, dome_cy - dome_r + 4, color, thick=3)
    c.fill_triangle(cx, dome_cy - dome_r - 18, cx + 18, dome_cy - dome_r - 13,
                    cx, dome_cy - dome_r - 8, RED)


def draw_stars_icon(c, x, y, s, color):
    """Ring of EU stars around '45' for the Ukraine loan story."""
    cx, cy = x + s // 2, y + s // 2
    c.fill_circle(cx, cy, s // 2 - 4, color)
    for k in range(12):
        ang = k * math.pi / 6 - math.pi / 2
        sx = cx + int(math.cos(ang) * (s // 2 - 16))
        sy = cy + int(math.sin(ang) * (s // 2 - 16))
        c.fill_circle(sx, sy, 4, GOLD)
    c.draw_text_centered(cx, cy - 21, "45", 6, WHITE)


def draw_probe_icon(c, x, y, s, color):
    """Voyager 1 probe against stars."""
    c.fill_rect(x, y, s, s, (10, 16, 34))
    star_pts = [(12, 18), (40, 8), (70, 26), (96, 12), (118, 40),
                (24, 52), (58, 66), (92, 58), (30, 96), (66, 104),
                (110, 92), (14, 122), (48, 128), (100, 126)]
    for sx, sy in star_pts:
        c.fill_rect(x + sx, y + sy, 3, 3, WHITE)
    cx, cy = x + s // 2, y + s // 2 + 6
    # dish
    c.fill_circle(cx - 18, cy - 6, 26, GOLD)
    c.fill_circle(cx - 18, cy - 6, 18, (240, 200, 110))
    # body + boom
    c.draw_line(cx + 6, cy, cx + 44, cy + 18, WHITE, thick=4)
    c.fill_rect(cx + 2, cy - 8, 22, 16, WHITE)
    c.fill_rect(cx + 44, cy + 12, 10, 12, RED)


def draw_icon(c, kind, x, y, s, color):
    if kind == "burst":
        draw_burst_icon(c, x, y, s, color)
    elif kind == "capitol":
        draw_capitol_icon(c, x, y, s, color)
    elif kind == "stars":
        draw_stars_icon(c, x, y, s, color)
    elif kind == "probe":
        draw_probe_icon(c, x, y, s, color)


def draw_skyline(c, x0, y0, w, base_y):
    """Vice City skyline silhouettes with lit windows."""
    buildings = [(0, 90, 150), (96, 70, 210), (172, 110, 120), (288, 80, 190),
                 (374, 100, 140), (480, 66, 220), (552, 96, 160), (654, 80, 200),
                 (740, 110, 130), (856, 70, 180)]
    for bx, bw, bh in buildings:
        c.fill_rect(x0 + bx, base_y - bh, bw, bh, (26, 36, 64))
        # lit windows: fixed grid, every other one lit
        for wy in range(base_y - bh + 12, base_y - 8, 22):
            for wx in range(x0 + bx + 10, x0 + bx + bw - 8, 20):
                if ((wx // 20) + (wy // 22)) % 2 == 0:
                    c.fill_rect(wx, wy, 5, 7, GOLD)


def draw_palm(c, x, base_y, h, color):
    """A simple palm tree: leaning trunk, five fronds."""
    top_x, top_y = x + 14, base_y - h
    c.draw_line(x, base_y, top_x, top_y, color, thick=7)
    for k, (dx, dy) in enumerate([(-34, -6), (-26, -22), (-6, -30),
                                  (16, -26), (34, -10)]):
        c.draw_line(top_x, top_y, top_x + dx, top_y + dy, color, thick=4)


def draw_hero(c):
    """The big GTA VI panel: Vice City sunset, skyline, headline strip."""
    x0, y0, x1 = 24, 136, 1000
    # sunset sky: horizontal bands, purple to orange to gold
    bands = [(SKY_DARK, 136, 190), (PURPLE, 190, 240),
             (ORANGE, 240, 300), (SUNSET, 300, 356)]
    for color, ya, yb in bands:
        c.fill_rect(x0, ya, x1 - x0, yb - ya, color)
    # sun
    c.fill_circle(800, 250, 62, (255, 214, 130))
    c.fill_circle(800, 250, 46, (255, 236, 180))
    # sea
    c.fill_rect(x0, 356, x1 - x0, 24, SEA)
    c.fill_rect(x0, 364, x1 - x0, 2, (120, 170, 200))
    c.fill_rect(x0, 372, x1 - x0, 2, (120, 170, 200))
    # skyline + palms
    draw_skyline(c, x0, y0, x1 - x0, 380)
    draw_palm(c, 60, 380, 96, (16, 44, 30))
    draw_palm(c, 900, 380, 84, (16, 44, 30))
    # headline strip
    c.fill_rect(x0, 380, x1 - x0, 90, INK)
    c.draw_text_centered(512, 392, "GTA VI IS HERE", 6, WHITE)
    c.draw_text_centered(512, 442, "AFTER 13 YEARS, VICE CITY OPENS WORLDWIDE",
                         2, GOLD)


def draw_story_panel(c, x, y, w, h, accent, kind, headline, summary):
    """One grid panel: accent strip, icon, headline, summary."""
    c.fill_rect(x, y, w, h, CARD)
    c.fill_rect(x, y, w, 10, accent)
    # border
    c.fill_rect(x, y, w, 2, INK)
    c.fill_rect(x, y + h - 2, w, 2, INK)
    c.fill_rect(x, y, 2, h, INK)
    c.fill_rect(x + w - 2, y, 2, h, INK)
    # icon
    draw_icon(c, kind, x + 16, y + 30, 140, accent)
    # headline + summary
    tx = x + 172
    ty = y + 34
    for line in headline:
        c.draw_text(tx, ty, line, 3, INK)
        ty += 30
    ty += 8
    for line in summary:
        c.draw_text(tx, ty, line, 2, (90, 90, 88))
        ty += 20


def draw_image():
    """Compose the whole 1024x1024 front page."""
    c = Canvas(W, H)
    # masthead
    c.fill_rect(24, 24, 976, 94, INK)
    c.draw_text_centered(512, 36, "THE WORLD IN ONE DAY", 5, WHITE)
    c.draw_text_centered(512, 84, "THURSDAY 19 NOVEMBER 2026", 3, GOLD)
    c.fill_rect(24, 118, 976, 6, RED)
    # hero + grid + footer
    draw_hero(c)
    positions = [(24, 486), (524, 486), (24, 698), (524, 698)]
    for (accent, kind, headline, summary), (px, py) in zip(STORIES, positions):
        draw_story_panel(c, px, py, 476, 196, accent, kind, headline, summary)
    c.fill_rect(24, 910, 976, 90, INK)
    c.draw_text_centered(512, 932,
                         "FIVE STORIES. ONE DAY.", 3, WHITE)
    c.draw_text_centered(512, 968,
                         "THE WORLD, 19 NOVEMBER 2026", 2, GOLD)
    return c


def png_bytes(canvas):
    """Encode a Canvas as a deterministic 8-bit RGB PNG (filter 0)."""
    raw = bytearray()
    for y in range(canvas.h):
        raw.append(0)
        start = y * canvas.w * 3
        raw += canvas.px[start:start + canvas.w * 3]
    idat = zlib.compress(bytes(raw), 9)

    def chunk(ctype, data):
        return (struct.pack(">I", len(data)) + ctype + data +
                struct.pack(">I", zlib.crc32(ctype + data) & 0xFFFFFFFF))

    ihdr = struct.pack(">IIBBBBB", canvas.w, canvas.h, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) +
            chunk(b"IDAT", idat) + chunk(b"IEND", b""))


def render_png():
    return png_bytes(draw_image())


def main():
    outdir = os.environ.get("MAKEFUN_OUTPUT_DIR")
    if not outdir:
        outdir = "/output" if os.path.isdir("/output") else "out"
    os.makedirs(outdir, exist_ok=True)
    data = render_png()
    with open(os.path.join(outdir, "entry.png"), "wb") as f:
        f.write(data)
    print(f"wrote {os.path.join(outdir, 'entry.png')} ({len(data)} bytes)")


if __name__ == "__main__":
    main()
