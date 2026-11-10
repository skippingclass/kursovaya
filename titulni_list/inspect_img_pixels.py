# -*- coding: utf-8 -*-
"""
Inspect pixel contents of the 4 images.
"""
from PIL import Image

for name in ['img_20.png', 'img_30.png', 'img_37.png', 'img_43.png']:
    im = Image.open(name)
    print(f"=== {name}: {im.size}, mode={im.mode} ===")
