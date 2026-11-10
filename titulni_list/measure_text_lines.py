# -*- coding: utf-8 -*-
from PIL import Image

def find_text_lines(im):
    w, h = im.size
    lines = []
    # scan vertically
    for y in range(h):
        cnt = sum(1 for x in range(w) if im.getpixel((x, y)) < 50)
        lines.append(cnt)
    
    # find intervals where cnt > 0
    intervals = []
    in_interval = False
    start = 0
    for y, cnt in enumerate(lines):
        if cnt > 5 and not in_interval:
            in_interval = True
            start = y
        elif cnt <= 5 and in_interval:
            in_interval = False
            if y - start > 6:
                intervals.append((start, y))
    return intervals

for name in ['img_30.png', 'img_37.png']:
    im = Image.open(name).convert('L')
    intervals = find_text_lines(im)
    print(f"=== {name} intervals ({len(intervals)}) ===")
    for s, e in intervals:
        # get bounding box in x
        xs = [x for y in range(s, e) for x in range(im.width) if im.getpixel((x, y)) < 50]
        if xs:
            print(f"  y=[{s}, {e}], height={e-s}, x=[{min(xs)}, {max(xs)}], width={max(xs)-min(xs)}")
