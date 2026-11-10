# -*- coding: utf-8 -*-
from PIL import Image

def analyze_boxes(im):
    w, h = im.size
    # let's look at rectangular borders
    boxes = []
    # scan for horizontal line segments of length > 80
    for y in range(h):
        in_line = False
        start_x = 0
        for x in range(w):
            val = im.getpixel((x, y))
            if val < 50:
                if not in_line:
                    in_line = True
                    start_x = x
            else:
                if in_line:
                    in_line = False
                    if x - start_x > 80:
                        boxes.append((y, start_x, x))
    return boxes

print("img_30 horizontal borders:", len(analyze_boxes(Image.open('img_30.png').convert('L'))))
print("img_37 horizontal borders:", len(analyze_boxes(Image.open('img_37.png').convert('L'))))
