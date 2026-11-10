# -*- coding: utf-8 -*-
"""
Render ASCII art preview of top of each image.
"""
from PIL import Image

def ascii_art(img_path, w_target=80):
    im = Image.open(img_path).convert('L')
    w, h = im.size
    h_target = int(h * (w_target / w) * 0.5)
    im_small = im.resize((w_target, h_target), Image.Resampling.BILINEAR)
    chars = " .:-=+*#%@"
    lines = []
    for y in range(h_target):
        row = ""
        for x in range(w_target):
            val = im_small.getpixel((x, y))
            idx = int((255 - val) / 255 * (len(chars) - 1))
            row += chars[idx]
        lines.append(row)
    return lines

for name in ['img_20.png', 'img_30.png', 'img_37.png', 'img_43.png']:
    lines = ascii_art(name, 75)
    print(f"================ {name} ================")
    # print lines that have some ink
    for l in lines:
        if any(c in l for c in "+*#%@"):
            print(l)
