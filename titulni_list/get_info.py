# -*- coding: utf-8 -*-
from PIL import Image

for name in ['img_20.png', 'img_30.png', 'img_37.png', 'img_43.png']:
    im = Image.open(name)
    print(name, im.size)
