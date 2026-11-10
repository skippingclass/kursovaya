# -*- coding: utf-8 -*-
from PIL import Image

def ascii_art2(img_path, w_target=80):
    im = Image.open(img_path).convert('L')
    w, h = im.size
    h_target = int(h * (w_target / w) * 0.5)
    im_small = im.resize((w_target, h_target), Image.Resampling.BOX)
    # Most pixels are 255 (white) or 241 (light gray background)
    # Dark pixels are < 100
    lines = []
    for y in range(h_target):
        row = ""
        for x in range(w_target):
            val = im_small.getpixel((x, y))
            if val < 100:
                row += "#"
            elif val < 180:
                row += "+"
            elif val < 230:
                row += "."
            else:
                row += " "
        lines.append(row)
    return lines

for name in ['img_20.png', 'img_30.png', 'img_37.png', 'img_43.png']:
    lines = ascii_art2(name, 70)
    print(f"================ {name} ================")
    for l in lines:
        if "#" in l or "+" in l:
            print(l)
