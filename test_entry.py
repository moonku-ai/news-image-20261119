"""Tests for the news-image-20261119 entry program (pure Python stdlib).

Run:  python3 -m unittest test_entry -v
"""
import os
import struct
import subprocess
import sys
import tempfile
import unittest
import zlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import main


class TestFont(unittest.TestCase):
    def test_glyph_a_has_full_middle_row(self):
        # 'A' crossbar is row 3, all 5 pixels set -> 0x1F
        self.assertEqual(main.FONT["A"][3], 0x1F)

    def test_glyphs_are_seven_rows_of_five_bits(self):
        for ch, rows in main.FONT.items():
            self.assertEqual(len(rows), 7, ch)
            for row in rows:
                self.assertTrue(0 <= row <= 0x1F, (ch, row))

    def test_unknown_char_maps_to_blank(self):
        self.assertEqual(main.glyph("~"), main.FONT[" "])


class TestCanvas(unittest.TestCase):
    def test_text_width_scales(self):
        # 5 px glyph + 1 px gap per char, times scale
        self.assertEqual(main.text_width("AB", 2), 2 * 6 * 2)

    def test_draw_text_sets_pixels(self):
        c = main.Canvas(60, 20)
        c.draw_text(0, 0, "A", scale=1, color=main.INK)
        self.assertGreater(c.count_color(main.INK), 0)

    def test_wrap_text_breaks_at_word_boundary(self):
        lines = main.wrap_text("US AND IRAN TRADE FIRE", 11)
        self.assertEqual(lines, ["US AND IRAN", "TRADE FIRE"])

    def test_fill_rect_clips_to_canvas(self):
        c = main.Canvas(10, 10)
        c.fill_rect(-5, -5, 20, 20, main.RED)
        self.assertEqual(c.count_color(main.RED), 100)


class TestPngEncoder(unittest.TestCase):
    def test_png_is_valid_1024(self):
        data = main.render_png()
        self.assertTrue(data.startswith(b"\x89PNG\r\n\x1a\n"))
        # Walk chunks: signature + IHDR + IDAT(s) + IEND, CRCs valid
        pos = 8
        types = []
        while pos < len(data):
            length = struct.unpack(">I", data[pos:pos + 4])[0]
            ctype = data[pos + 4:pos + 8]
            chunk = data[pos + 8:pos + 8 + length]
            crc_stored = struct.unpack(">I", data[pos + 8 + length:pos + 12 + length])[0]
            crc_calc = zlib.crc32(ctype + chunk) & 0xFFFFFFFF
            self.assertEqual(crc_stored, crc_calc, ctype)
            types.append(ctype)
            pos += 12 + length
        self.assertEqual(pos, len(data))
        self.assertEqual(types[0], b"IHDR")
        self.assertEqual(types[-1], b"IEND")
        w, h, depth, ctype = struct.unpack(">IIBB", data[16:26])
        self.assertEqual((w, h), (1024, 1024))
        self.assertEqual((depth, ctype), (8, 2))  # 8-bit RGB

    def test_png_decodes_to_1024_rows(self):
        data = main.render_png()
        pos = 8
        idat = b""
        while pos < len(data):
            length = struct.unpack(">I", data[pos:pos + 4])[0]
            ctype = data[pos + 4:pos + 8]
            if ctype == b"IDAT":
                idat += data[pos + 8:pos + 8 + length]
            pos += 12 + length
        raw = zlib.decompress(idat)
        self.assertEqual(len(raw), 1024 * (1 + 1024 * 3))
        # every scanline filter byte is 0
        for y in range(1024):
            self.assertEqual(raw[y * (1 + 3072)], 0)

    def test_png_under_1mib(self):
        self.assertLessEqual(len(main.render_png()), 1048576)


class TestDeterminism(unittest.TestCase):
    def test_two_runs_write_identical_bytes(self):
        with tempfile.TemporaryDirectory() as d1, tempfile.TemporaryDirectory() as d2:
            for d in (d1, d2):
                env = dict(os.environ, MAKEFUN_OUTPUT_DIR=d)
                r = subprocess.run(
                    [sys.executable, "main.py"], cwd=os.path.dirname(os.path.abspath(__file__)),
                    env=env, capture_output=True, text=True, timeout=120,
                )
                self.assertEqual(r.returncode, 0, r.stderr)
            with open(os.path.join(d1, "entry.png"), "rb") as f:
                b1 = f.read()
            with open(os.path.join(d2, "entry.png"), "rb") as f:
                b2 = f.read()
            self.assertEqual(b1, b2)
            self.assertLessEqual(len(b1), 1048576)


if __name__ == "__main__":
    unittest.main()
