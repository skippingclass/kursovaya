"""Номера содержания из проверенного PDF, без ручного угадывания страниц."""
import argparse
import json
import re
from pathlib import Path
from pypdf import PdfReader
from docx import Document
ROOT=Path(__file__).resolve().parents[1]
DEFAULT=ROOT/'titulni_list/Курсовая_работа_Пояснительная_записка_ИТОГ.docx'

def normalize(value):return ' '.join(value.split())

def main():
    parser=argparse.ArgumentParser();parser.add_argument('pdf',type=Path);parser.add_argument('--docx',type=Path,default=DEFAULT)
    args=parser.parse_args()
    d=Document(args.docx)
    titles=[p.text.split('\t')[0] for p in d.paragraphs if p.style.name=='CourseTOC']
    pages={}
    reader=PdfReader(args.pdf)
    for index,page in enumerate(reader.pages):
        if index < 3:
            continue
        start=normalize(page.extract_text())[:350]
        for title in titles:
            if title in start and title not in pages:
                pages[title] = index + 1
    missing=set(titles)-pages.keys()
    if missing:raise RuntimeError('Не найдены разделы '+str(missing))
    for p in d.paragraphs:
        if p.style.name=='CourseTOC':
            title=p.text.split('\t')[0];p.text=title+'\t'+str(pages[title])
    d.save(args.docx)
    (ROOT/'tmp/documents/contents_pages.json').write_text(json.dumps(pages,ensure_ascii=False,indent=2))
    print(json.dumps(pages,ensure_ascii=False))

if __name__=='__main__':main()
