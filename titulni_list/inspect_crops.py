# -*- coding: utf-8 -*-
from PIL import Image

# Let's inspect small crops of each image:
# In img_20: crop top-left, center, bottom-right
# Save as small images or analyze text
im20 = Image.open('img_20.png')
im30 = Image.open('img_30.png')
im37 = Image.open('img_37.png')
im43 = Image.open('img_43.png')

print("im20 size:", im20.size)
print("im30 size:", im30.size)
print("im37 size:", im37.size)
print("im43 size:", im43.size)
