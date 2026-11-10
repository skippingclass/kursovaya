# -*- coding: utf-8 -*-
from PIL import Image

# Let's inspect some bounding boxes and shapes in img_30 vs img_37 vs img_43 vs img_20
def find_boxes(im, name):
    w, h = im.size
    print(f"*** {name} ({w}x{h}) ***")
    # let's look at horizontal line segments (rectangles)
    # in an ER diagram or GUI mockup there are horizontal and vertical borders
    h_lines = 0
    for y in range(h):
        consec = 0
        max_consec = 0
        for x in range(w):
            if im.getpixel((x, y)) < 50:
                consec += 1
                if consec > max_consec: max_consec = consec
            else:
                consec = 0
        if max_consec > 100:
            h_lines += 1
    print(f"  Rows with black line > 100px: {h_lines}")

for name in ['img_20.png', 'img_30.png', 'img_37.png', 'img_43.png']:
    find_boxes(Image.open(name).convert('L'), name)
