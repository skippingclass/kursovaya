# -*- coding: utf-8 -*-
from PIL import Image

for name in ['img_20.png', 'img_30.png', 'img_37.png', 'img_43.png']:
    im = Image.open(name)
    # let's crop top 100 pixels and bottom 100 pixels
    w, h = im.size
    print(f"=== {name} {w}x{h} ===")
