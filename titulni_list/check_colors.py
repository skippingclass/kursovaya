# -*- coding: utf-8 -*-
from PIL import Image

for name in ['img_20.png', 'img_30.png', 'img_37.png', 'img_43.png']:
    im = Image.open(name)
    w, h = im.size
    print(f"=== {name}: {w}x{h} ===")
    # sample some pixels across horizontal and vertical lines
    # or let's count colors
    colors = im.getcolors(maxcolors=1000000)
    print(f"Number of unique colors: {len(colors)}")
    # get 5 most common colors
    sorted_colors = sorted(colors, key=lambda x: x[0], reverse=True)[:5]
    print(f"Top 5 colors: {sorted_colors}")
