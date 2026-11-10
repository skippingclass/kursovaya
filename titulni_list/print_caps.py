import zipfile, re

with zipfile.ZipFile('Курсовая_работа_Пояснительная_записка_ИТОГ.docx', 'r') as z:
    xml = z.read('word/document.xml').decode('utf-8')
    caps = re.findall(r'Рисунок [0-9][^<]+', xml)
    for c in caps:
        print(c)
