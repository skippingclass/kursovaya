# -*- coding: utf-8 -*-
from PIL import Image

# Let's inspect some pixel regions or save slices of the images to analyze text
for img_name in ['img_20.png', 'img_30.png', 'img_37.png', 'img_43.png']:
    im = Image.open(img_name)
    print(f"=== {img_name} ({im.size}) ===")
