# -*- coding: utf-8 -*-
from PIL import Image

def get_char_shapes(img_path):
    im = Image.open(img_path).convert('L')
    w, h = im.size
    # let's find dark pixels
    dark = []
    for y in range(h):
        for x in range(w):
            if im.getpixel((x, y)) < 50:
                dark.append((x, y))
    print(f"{img_path}: total dark pixels = {len(dark)}")
    if dark:
        min_x = min(x for x, y in dark)
        max_x = max(x for x, y in dark)
        min_y = min(y for x, y in dark)
        max_y = max(y for x, y in dark)
        print(f"  Bounding box of content: x=[{min_x}, {max_x}], y=[{min_y}, {max_y}]")

for name in ['img_20.png', 'img_30.png', 'img_37.png', 'img_43.png']:
    get_char_shapes(name)
