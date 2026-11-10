# -*- coding: utf-8 -*-
from PIL import Image

def find_words(img_path):
    im = Image.open(img_path).convert('L')
    w, h = im.size
    print(f"=== {img_path} ({w}x{h}) ===")
    
    # We know that PlantUML and UI text is rendered with black/dark gray letters.
    # Let's find connected components of dark pixels or bounding boxes of text lines!
    # Let's find lines with horizontal clusters of dark pixels.
    # Sample 10 lines of text and their y-coordinates, x-ranges
    dark = []
    for y in range(0, h, 2):
        row_dark = [x for x in range(w) if im.getpixel((x, y)) < 80]
        if len(row_dark) > 10:
            dark.append((y, min(row_dark), max(row_dark), len(row_dark)))
    print(f"Rows with text: {len(dark)}")
    for d in dark[:10]:
        print(f"  y={d[0]}: x=[{d[1]}..{d[2]}], count={d[3]}")

for name in ['img_20.png', 'img_30.png', 'img_37.png', 'img_43.png']:
    find_words(name)
