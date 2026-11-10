# -*- coding: utf-8 -*-
"""
Inspect text in img_30.png vs img_43.png vs img_20.png by character pixel matching or font rendering.
"""
from PIL import Image

im30 = Image.open('img_30.png')
print("img_30 size:", im30.size)

# Save high-contrast version of img_30.png to inspect
im30_gray = im30.convert('L')
im30_bw = im30_gray.point(lambda x: 0 if x < 200 else 255, '1')
im30_bw.save('img_30_bw.png')
print("Saved img_30_bw.png")

for name in ['img_20.png', 'img_37.png', 'img_43.png']:
    im = Image.open(name).convert('L')
    im_bw = im.point(lambda x: 0 if x < 200 else 255, '1')
    im_bw.save(name.replace('.png', '_bw.png'))
