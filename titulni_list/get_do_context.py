# -*- coding: utf-8 -*-
import zlib

with open('курсовая записка.pdf', 'rb') as f:
    data = f.read()

for c_id, name in [(22, 'X20'), (31, 'X30'), (38, 'X37'), (44, 'X43')]:
    idx = data.find(f'{c_id} 0 obj'.encode())
    chunk = data[idx:data.find(b'endobj', idx)]
    s = chunk[chunk.find(b'stream')+7:chunk.find(b'endstream')].strip()
    decomp = zlib.decompress(s).decode('latin1')
    do_idx = decomp.find(f'/{name} Do')
    print(f"=== {name} (Contents {c_id}) ===")
    print(decomp[max(0, do_idx-150):do_idx+30])
