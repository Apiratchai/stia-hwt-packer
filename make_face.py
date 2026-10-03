#!/usr/bin/env python3
"""ClaudeFit-Pixel generator for Huawei Watch Fit 1 (280x456, HWHD06).

Terminal/Claude-CLI style, adapted from the supplied round-watch reference.
Dynamic values: 24h time (59–62), weekday (52), day digits (70–71),
month name (51), heart rate (2), steps (0), battery percentage (9).
Run: python3 make_face.py   (needs Pillow)  -> res/*.png + face.json + preview
Then:  node pack.js         -> claude-fit-pixel.hwt (compiled, sideload-ready)
"""
import os, json
from datetime import date
from PIL import Image, ImageDraw, ImageFont

W, H = 280, 456
ROOT = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(ROOT, "res")
for d in (RES,):
    os.makedirs(d, exist_ok=True)

BG = (8, 8, 10, 255)
WHITE = (242, 242, 240, 255)
ORANGE = (255, 132, 66, 255)
DIM = (170, 163, 157, 255)
RED, YEL, GRN = (255, 59, 48, 255), (255, 204, 0, 255), (52, 199, 89, 255)

F = {
 '0': ["111","101","101","101","111"], '1': ["010","110","010","010","111"],
 '2': ["111","001","111","100","111"], '3': ["111","001","111","001","111"],
 '4': ["101","101","111","001","001"], '5': ["111","100","111","001","111"],
 '6': ["111","100","111","101","111"], '7': ["111","001","010","010","010"],
 '8': ["111","101","111","101","111"], '9': ["111","101","111","001","111"],
 'A': ["010","101","111","101","101"], 'B': ["110","101","110","101","110"],
 'C': ["011","100","100","100","011"], 'D': ["110","101","101","101","110"],
 'E': ["111","100","110","100","111"], 'F': ["111","100","110","100","100"],
 'G': ["011","100","101","101","011"], 'H': ["101","101","111","101","101"],
 'I': ["111","010","010","010","111"], 'J': ["001","001","001","101","010"], 'K': ["101","101","110","101","101"],
 'L': ["100","100","100","100","111"], 'N': ["110","101","101","101","101"],
 'O': ["010","101","101","101","010"], 'P': ["111","101","111","100","100"],
 'R': ["110","101","110","101","101"], 'S': ["011","100","010","001","110"],
 'T': ["111","010","010","010","010"], 'U': ["101","101","101","101","111"], 'V': ["101","101","101","101","010"],
 'Y': ["101","101","010","010","010"], 'X': ["101","101","010","101","101"],
 'Q': ["010","101","101","010","001"], 'Z': ["111","001","010","100","111"],
 'M': ["10001","11011","10101","10001","10001"],
 'W': ["10001","10001","10101","11011","10001"],
 '>': ["100","010","001","010","100"], '-': ["000","000","111","000","000"],
 '.': ["000","000","000","000","010"], '%': ["101","001","010","100","101"],
 '(': ["001","010","010","010","001"], ')': ["100","010","010","010","100"],
 ' ': ["000","000","000","000","000"],
}
# Claude pixel mascot (rounded blob, two eyes, feet) 15x11
CLAUDE = [".XXXXXXXXXXXXX.",
          "XXXXXXXXXXXXXXX",
          "XXXXXXXXXXXXXXX",
          "XXXX.XXXXX.XXXX",
          "XXXX.XXXXX.XXXX",
          "XXXXXXXXXXXXXXX",
          "XXXXXXXXXXXXXXX",
          "XXXXXXXXXXXXXXX",
          "XXXXXXXXXXXXXXX",
          ".XX........XX.."]
HEART = [".XX.XX.", "XXXXXXX", "XXXXXXX", ".XXXXX.", "..XXX..", "...X..."]
PAW = ["..X...X..", "..X...X..", ".XXXXX..", "XXXXXXX.", "XXXXXXX.", ".XXXXX.."]
FLAME = ["...X...", "..XX...", "..XXX..", ".XXXXX.", ".XXXXX.", "XXXXXXX", "XXXXXXX", ".XXXXX."]

def glyph(draw, x, y, ch, u, color):
    g = F[ch]
    for r, row in enumerate(g):
        for c, bit in enumerate(row):
            if bit == '1':
                draw.rectangle([x + c * u, y + r * u, x + c * u + u - 2, y + r * u + u - 2], fill=color)
    return len(g[0]) * u

def draw_text(draw, x, y, s, u, color):
    for ch in s:
        x += glyph(draw, x, y, ch, u, color) + 1

def text_w(s, u):
    return sum(len(F[ch][0]) * u + 1 for ch in s) - 1

def matrix(draw, x, y, mat, cell, color):
    for r, row in enumerate(mat):
        for c, bit in enumerate(row):
            if bit in 'X1':
                draw.rectangle([x + c * cell, y + r * cell, x + (c + 1) * cell - 1, y + (r + 1) * cell - 1], fill=color)

# --- geometry (mirrored into face.json for pack.js) ---
U_BIG, ADV_BIG = 15, 52
TX0, TY0 = 24, 148
D = [TX0, TX0 + ADV_BIG, TX0 + 2 * ADV_BIG + 30, TX0 + 3 * ADV_BIG + 30]
COLON_X = TX0 + 2 * ADV_BIG + 8
ROW_Y = 290
HR_X, STEP_X, CAL_X = 42, 94, 170
WEEK_X, WEEK_Y, WEEK_W = 48, 326, 44
DAY_X, DAY_Y = 98, 326
MONTH_X, MONTH_Y, MONTH_W = 138, 326, 42
FONT_PATH = os.path.join(ROOT, "fonts", "LiberationSans-Bold.ttf")
LABEL_FONT = ImageFont.truetype(FONT_PATH, 16)
SMALL_FONT = ImageFont.truetype(FONT_PATH, 20)
# ponytail: Fit 1 spec has no year value; rebuild annually for the year suffix.
BUILD_YEAR = date.today().strftime("%y")

bg = Image.new("RGBA", (W, H), BG)
d = ImageDraw.Draw(bg)
# Reference silhouette: raised flat crown, wide body, four distinct feet.
d.rectangle([100, 46, 179, 53], fill=ORANGE)
d.rectangle([92, 54, 187, 101], fill=ORANGE)
for x in (100, 116, 156, 172):
    d.rectangle([x, 102, x + 7, 109], fill=ORANGE)
for x in (116, 156):
    d.rectangle([x, 68, x + 7, 81], fill=BG)
for cx, color in ((122, RED), (140, YEL), (158, GRN)):
    d.ellipse([cx - 3, 31, cx + 3, 37], fill=color)
for yy in (TY0 + 21, TY0 + 49):
    d.ellipse([COLON_X - 1, yy, COLON_X + 12, yy + 13], fill=ORANGE)
# Three metrics, with labels below, as in the reference.
matrix(d, 18, 261, HEART, 2, ORANGE)
# Side view sneaker, with a raised heel, toe and separate sole.
d.polygon([(94, 259), (100, 259), (100, 263), (105, 266),
           (109, 266), (112, 269), (112, 271), (94, 271)], fill=ORANGE)
d.line([(94, 274), (112, 274)], fill=ORANGE, width=2)
d.line([(100, 264), (102, 262)], fill=BG, width=1)
d.line([(103, 266), (105, 264)], fill=BG, width=1)
matrix(d, 202, 258, FLAME, 2, ORANGE)
d.rectangle([198, 26, 213, 35], outline=ORANGE, width=2)
d.rectangle([214, 29, 216, 32], fill=ORANGE)
d.text((261, 31), "%", font=ImageFont.truetype(FONT_PATH, 13), fill=DIM, anchor="mm")
for x, label in ((53, "bpm"), (145, "steps"), (235, "kcal")):
    d.text((x, 298), label, font=ImageFont.truetype(FONT_PATH, 13), fill=DIM, anchor="mm")
d.rectangle([20, 316, 260, 361], outline=(83, 57, 43, 255), width=1)
d.text((32, 339), ">", font=SMALL_FONT, fill=ORANGE, anchor="mm")
d.text((201, 339), BUILD_YEAR, font=SMALL_FONT, fill=WHITE, anchor="mm")
d.rectangle([238, 328, 246, 348], fill=ORANGE)
terminal_font = ImageFont.truetype(os.path.join(ROOT, "fonts", "LiberationMono-Regular.ttf"), 12)
d.rectangle([20, 373, 260, 432], outline=(83, 57, 43, 255), width=1)
d.text((32, 388), "> weather", font=terminal_font, fill=ORANGE, anchor="lm")
bg.save(os.path.join(RES, "A100_001.png"))

# Seconds-driven dance: visible bounce, side steps, alternating feet and blink.
ANIM_POS = (82, 40)
ANIM = [f"A100_{50 + i:03d}.png" for i in range(10)]
mascot = bg.crop((82, 40, 198, 124))
frames = []
for i, (dx, dy) in enumerate(((0, 0), (-3, -3), (-4, -6), (-3, -3),
                              (0, 0), (3, 3), (4, 6), (3, 3), (0, 0), (0, -3))):
    frame = Image.new("RGBA", mascot.size, BG)
    frame.paste(mascot, (dx, dy))
    fd = ImageDraw.Draw(frame)
    for foot, x in enumerate((100, 116, 156, 172)):
        if (foot + i) % 2:
            fd.rectangle([x - 82 + dx, 106 - 40 + dy,
                          x - 82 + dx + 7, 109 - 40 + dy], fill=BG)
    if i == 8:
        for x in (116, 156):
            fd.rectangle([x - 82 + dx, 68 - 40 + dy,
                          x - 82 + dx + 7, 81 - 40 + dy], fill=ORANGE)
            fd.rectangle([x - 82 + dx, 75 - 40 + dy,
                          x - 82 + dx + 7, 77 - 40 + dy], fill=BG)
    frame.save(os.path.join(RES, ANIM[i]))
    frames.append(frame)


def digit_img(name, ch, u, w, h):
    g = F[ch]
    w = w or len(g[0]) * u - 1
    h = h or 5 * u - 1
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    glyph(ImageDraw.Draw(im), 0, 0, ch, u, WHITE)
    im.save(os.path.join(RES, name))

# Render opaque glyphs on the same black surface used by the face. This
# avoids alpha handling differences on the original Watch Fit firmware.
for i in range(10):
    # Fit the measured outline inside its cell, with two clear pixels per edge.
    font = ImageFont.truetype(FONT_PATH, 104)
    bounds = font.getbbox(str(i))
    glyph_mask = Image.new("L", (bounds[2] - bounds[0], bounds[3] - bounds[1]), 0)
    ImageDraw.Draw(glyph_mask).text((-bounds[0], -bounds[1]), str(i), font=font, fill=255)
    glyph_mask = glyph_mask.resize((39, 69), Image.Resampling.LANCZOS)
    im = Image.new("RGBA", (45, 75), BG)
    ink = Image.new("RGBA", glyph_mask.size, WHITE)
    im.paste(ink, ((45 - glyph_mask.width) // 2, (75 - glyph_mask.height) // 2), glyph_mask)
    if i == 0:
        ImageDraw.Draw(im).ellipse([18, 34, 26, 42], fill=WHITE)
    im.save(os.path.join(RES, f"A100_{10 + i:03d}.png"))
for i in range(10):
    im = Image.new("RGBA", (16, 26), BG)
    ImageDraw.Draw(im).text((8, 13), str(i), font=SMALL_FONT, fill=WHITE, anchor="mm")
    im.save(os.path.join(RES, f"A100_{20 + i:03d}.png"))
WEEKS = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]      # DATA_WEEK 52: Mon first
for i, wd in enumerate(WEEKS):
    im = Image.new("RGBA", (WEEK_W, 26), BG)
    ImageDraw.Draw(im).text((WEEK_W // 2, 13), wd, font=SMALL_FONT, fill=WHITE, anchor="mm")
    im.save(os.path.join(RES, f"A100_{30 + i:03d}.png"))
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
for i, mo in enumerate(MONTHS):
    im = Image.new("RGBA", (MONTH_W, 26), BG)
    ImageDraw.Draw(im).text((MONTH_W // 2, 13), mo, font=SMALL_FONT, fill=WHITE, anchor="mm")
    im.save(os.path.join(RES, f"A100_{37 + i:03d}.png"))

# Weather enum order comes from the bundled Stia specification (DATA_WEATHERTYPE).
WEATHER_LABELS = ["unknown", "sunny", "clear night", "overcast", "cloudy",
                  "rain", "thunder", "snow", "dust storm", "hazy", "fog"]
WEATHER = [f"A100_{60 + i:03d}.png" for i in range(11)]
UNITS = ["A100_071.png", "A100_072.png"]
for name, label in zip(WEATHER + UNITS, WEATHER_LABELS + ["°C", "°F"]):
    width = 108 if name in WEATHER else 28
    im = Image.new("RGBA", (width, 26), BG)
    ImageDraw.Draw(im).text((0, 13), label,
                           font=ImageFont.truetype(FONT_PATH, 18),
                           fill=WHITE, anchor="lm")
    im.save(os.path.join(RES, name))

# Device-photo evidence: month is 1..12, weekday is Sunday=0.
unknown_month = Image.new("RGBA", (MONTH_W, 26), BG)
ImageDraw.Draw(unknown_month).text((MONTH_W // 2, 13), "---",
                                  font=SMALL_FONT, fill=WHITE, anchor="mm")
unknown_month.save(os.path.join(RES, "A100_077.png"))

BIG = [f"A100_{10 + i:03d}.png" for i in range(10)]
SML = [f"A100_{20 + i:03d}.png" for i in range(10)]
STEP_TYPES = [69, 68, 67, 66, 65]  # FIVE..ONE left-to-right (leading zeros shown)
face = {
    "titleEn": "ClaudeFit", "titleCn": "ClaudeFit",
    "elements": [
        {"label": 0, "layers": [
            {"index": 0, "drawType": 1, "singleRes": {"resName": "A100_001.png", "pos": [0, 0]}}]},
        {"label": 1, "layers": [
            {"index": 0, "drawType": 2, "selectedRes": {"res": BIG[0:3], "pos": [D[0], TY0], "value": 59}},
            {"index": 1, "drawType": 2, "selectedRes": {"res": BIG, "pos": [D[1], TY0], "value": 60}},
            {"index": 2, "drawType": 2, "selectedRes": {"res": BIG[0:6], "pos": [D[2], TY0], "value": 61}},
            {"index": 3, "drawType": 2, "selectedRes": {"res": BIG, "pos": [D[3], TY0], "value": 62}}]},
        {"label": 2, "layers": [
            {"index": 0, "drawType": 2, "selectedRes": {"res": SML[0:4], "pos": [DAY_X, DAY_Y], "value": 70}},
            {"index": 1, "drawType": 2, "selectedRes": {"res": SML, "pos": [DAY_X + 18, DAY_Y], "value": 71}},
            {"index": 2, "drawType": 2, "selectedRes": {"res": ["A100_036.png"] + [f"A100_{30 + i:03d}.png" for i in range(6)], "pos": [WEEK_X, WEEK_Y], "value": 52}},
            {"index": 3, "drawType": 2, "selectedRes": {"res": ["A100_077.png"] + [f"A100_{37 + i:03d}.png" for i in range(12)], "pos": [MONTH_X, MONTH_Y], "value": 51}}]},
        {"label": 3, "layers": [
            {"index": i, "drawType": 0, "text": {"rect": rect,
             "color": list(WHITE), "font": 127, "align": 1, "value": value}}
            for i, (rect, value) in enumerate([
                ([34, 252, 52, 30], 2),
                ([110, 252, 88, 30], 0),
                ([218, 252, 46, 30], 1),
                ([220, 18, 36, 26], 9),
            ])]},
    ],
}
face["elements"].append({"label": 4, "layers": [
    {"index": 0, "drawType": 2, "selectedRes": {
        "res": ANIM, "pos": list(ANIM_POS), "value": 64}}
]})
face["elements"].append({"label": 3, "layers": [
    {"index": 0, "drawType": 2, "selectedRes": {
        "res": WEATHER, "pos": [32, 399], "value": 53}},
    {"index": 1, "drawType": 2, "selectedRes": {
        "res": UNITS, "pos": [222, 399], "value": 73}},
    {"index": 2, "drawType": 0, "text": {
        "rect": [148, 397, 72, 30], "color": list(WHITE),
        "font": 127, "align": 1, "value": 4}},
]})
# Native Stia jump targets: HR 11, Activity records 33, Weather 21.
# Keep the visible icon and hit region separate so the whole metric is tappable.
buttons = []
for i, (rect, art, target) in enumerate([
    ([12, 246, 76, 60], [18, 258, 32, 275], 11),
    ([88, 246, 110, 60], [94, 258, 113, 276], 33),
    ([198, 246, 70, 60], [202, 258, 216, 275], 33),
    ([20, 373, 240, 59], [21, 374, 259, 397], 21),
]):
    name = f"A100_{73 + i:03d}.png"
    bg.crop(tuple(art)).save(os.path.join(RES, name))
    buttons.append({"index": i, "rect": rect, "dataType": target,
                    "layers": [{"index": 0, "drawType": 1,
                                "singleRes": {"resName": name, "pos": art[:2]}}]})
face["elements"].append({"label": 3, "layers": [], "containers": buttons})
# Stia renders live widget data inside containers, as in the 280px template.
# Keep the already working jump rectangles and add values to those containers.
metrics = face["elements"][3]["layers"]
weather_layers = face["elements"][5]["layers"]
for button, metric in zip(buttons[:3], metrics[:3]):
    metric["index"] = 1
    button["layers"].append(metric)
for i, layer in enumerate(weather_layers, 1):
    layer["index"] = i
    buttons[3]["layers"].append(layer)
buttons.append({"index": 4, "rect": [196, 12, 72, 44], "dataType": 17,
                "layers": [dict(metrics[3], index=0)]})
# Seconds data belongs to TIME so firmware schedules updates while awake.
animation_layer = face["elements"][4]["layers"][0]
animation_layer["index"] = 4
face["elements"][1]["layers"].append(animation_layer)
face["elements"] = face["elements"][:3] + [
    {"label": 3, "layers": [], "containers": buttons}]
json.dump(face, open(os.path.join(ROOT, "face.json"), "w"), indent=1)

# mockup
mock = bg.copy(); md = ImageDraw.Draw(mock)
for x, ch in zip(D, "1009"):
    mock.alpha_composite(Image.open(os.path.join(RES, f"A100_{10 + int(ch):03d}.png")).convert("RGBA"), (x, TY0))
mock.alpha_composite(Image.open(os.path.join(RES, "A100_031.png")).convert("RGBA"), (WEEK_X, WEEK_Y))
for x, ch in zip((DAY_X, DAY_X + 18), "09"):
    mock.alpha_composite(Image.open(os.path.join(RES, f"A100_{20 + int(ch):03d}.png")).convert("RGBA"), (x, DAY_Y))
mock.alpha_composite(Image.open(os.path.join(RES, "A100_045.png")).convert("RGBA"), (MONTH_X, MONTH_Y))
# Use the same regions as the firmware text widgets in the preview.
preview_font = ImageFont.truetype(FONT_PATH, 27)
for x, text in ((60, "72"), (154, "8432"), (241, "328")):
    md.text((x, 267), text, font=ImageFont.truetype(FONT_PATH, 23), fill=WHITE, anchor="mm")
md.text((238, 31), "78", font=ImageFont.truetype(FONT_PATH, 18), fill=WHITE, anchor="mm")
mock.paste(Image.open(os.path.join(RES, WEATHER[4])), (32, 399))
mock.paste(Image.open(os.path.join(RES, UNITS[0])), (222, 399))
md.text((184, 412), "28", font=ImageFont.truetype(FONT_PATH, 23), fill=WHITE, anchor="mm")
mock.convert("RGB").save(os.path.join(ROOT, "preview_mock.png"))
gif_frames = []
for frame in frames:
    preview = mock.copy()
    preview.paste(frame, ANIM_POS)
    gif_frames.append(preview.convert("RGB"))
gif_frames[0].save(os.path.join(ROOT, "preview_animated.gif"),
                   save_all=True, append_images=gif_frames[1:],
                   duration=1000, loop=0, disposal=2)

PV = os.path.join(ROOT, "preview")
os.makedirs(PV, exist_ok=True)
mock.convert("RGB").save(os.path.join(PV, "cover.jpg"), quality=90)
Image.open(os.path.join(PV, "cover.jpg")).resize((137, 223)).save(os.path.join(PV, "icon_small.jpg"), quality=85)

names = set(os.listdir(RES))
want = ["A100_001.png"] + BIG + SML + [f"A100_{30 + i:03d}.png" for i in range(7)] + [f"A100_{37 + i:03d}.png" for i in range(12)]
assert all(n in names for n in want + ANIM + WEATHER + UNITS), "missing assets"
assert Image.open(os.path.join(RES, "A100_001.png")).size == (280, 456)
print(f"OK art: {len(names)} pngs + face.json")
