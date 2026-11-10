# -*- coding: utf-8 -*-
from PIL import Image

def analyze_slices(img_path):
    im = Image.open(img_path).convert('L')
    w, h = im.size
    print(f"================ {img_path} ({w}x{h}) ================")
    # Let's count horizontal line projections: how many non-white pixels per row
    row_counts = []
    for y in range(h):
        cnt = sum(1 for x in range(w) if im.getpixel((x, y)) < 200)
        row_counts.append(cnt)
    
    # find clusters of rows with text
    in_text = False
    bands = []
    start_y = 0
    for y, c in enumerate(row_counts):
        if c > 15 and not in_text:
            in_text = True
            start_y = y
        elif c <= 15 and in_text:
            in_text = False
            if y - start_y > 5:
                bands.append((start_y, y, max(row_counts[start_y:y])))
    if in_text:
        bands.append((start_y, h, max(row_counts[start_y:h])))
        
    print(f"Total text bands found: {len(bands)}")
    for b in bands[:15]:
        print(f"  band y=[{b[0]}, {b[1]}], max width={b[2]}")

for name in ['img_20.png', 'img_30.png', 'img_37.png', 'img_43.png']:
    analyze_slices(name)
