# -*- coding: utf-8 -*-
"""
Full assembler script:
1. Translates stamps in header1.xml and header2.xml to Russian.
2. Updates footer1.xml and header2.xml total page references.
3. Generates complete document.xml.
4. Adds images (img_20, img_30, img_37, img_43) to word/media/ and updates document.xml.rels.
5. Saves clean package Курсовая_работа_Пояснительная_записка_ИТОГ.docx.
"""
import zipfile
import re
import os
import shutil
import xml.etree.ElementTree as ET
from generate_doc_xml import generate_document_xml

def translate_header1(xml):
    # Textbox replacements for header1 (Large Stamp)
    subs = [
        ('>Ө<', '>И<'),
        ('>лш.<', '>зм.<'),
        ('>лш<', '>зм.<'),
        ('>Құжат<', '>№ докум.<'),
        ('>Құжат <', '>№ докум.<'),
        ('>№ <', '><'),
        ('>№<', '><'),
        ('>Қ<', '>П<'),
        ('>олы<', '>одп.<'),
        ('>Күні<', '>Дата<'),
        ('>м<', '><'),
        ('>Орындаған:<', '>Разраб.<'),
        ('>Тексерген:<', '>Провер.<'),
        ('>А.Ахмадиева<', '>Евполов В.<'),
        ('>Қ.Мажитова<', '>Атантаева А.З.<'),
        ('>Курстық жоба тақырыбы<', '>Автоматизация учета преподавателей колледжа<'),
        ('>(Түсіндірме жазба)<', '>(Пояснительная записка)<'),
        ('>Литера<', '>Лит.<'),
        ('>Беттер<', '>Листов<'),
        ('w:val="kk-KZ"', 'w:val="ru-RU"'),
    ]
    for old, new in subs:
        xml = xml.replace(old, new)
    
    # Handle 'Бет' -> 'Лист' in txbx 1 and 5
    # Let's inspect where 'Бет' appears and replace with 'Лист'
    xml = xml.replace('>Бет<', '>Лист<')
    xml = xml.replace('>Б<', '>Л<')
    xml = xml.replace('>ет<', '>ист<')
    
    # Replace code paragraph 3A402B39
    old_p_pat = r'<w:p [^>]*w14:paraId="3A402B39".*?</w:p>'
    new_p = '''<w:p w14:paraId="3A402B39" w14:textId="59B9A4C6" w:rsidR="00812E22" w:rsidRPr="00DC0900" w:rsidRDefault="00812E22" w:rsidP="0098209F">
<w:pPr><w:jc w:val="center"/></w:pPr>
<w:r><w:rPr><w:lang w:val="ru-RU"/></w:rPr><w:t>КП.06130100.П-24-67б.07.11.2026.ПЗ</w:t></w:r>
</w:p>'''
    xml = re.sub(old_p_pat, new_p, xml, flags=re.DOTALL)
    
    return xml

def translate_header2(xml):
    # Textbox replacements for header2 (Small Stamp)
    subs = [
        ('>Ө<', '>И<'),
        ('>лш.<', '>зм.<'),
        ('>лш<', '>зм.<'),
        ('>Құжат<', '>№ докум.<'),
        ('>Құжат <', '>№ докум.<'),
        ('>№ <', '><'),
        ('>№<', '><'),
        ('>Қ<', '>П<'),
        ('>олы<', '>одп.<'),
        ('>Күні<', '>Дата<'),
        ('>м<', '><'),
        ('w:val="kk-KZ"', 'w:val="ru-RU"'),
    ]
    for old, new in subs:
        xml = xml.replace(old, new)
    
    xml = xml.replace('>Бет<', '>Лист<')
    xml = xml.replace('>Б<', '>Л<')
    xml = xml.replace('>ет<', '>ист<')
    
    # Replace code paragraph 05D02254
    old_p_pat = r'<w:p [^>]*w14:paraId="05D02254".*?</w:p>'
    new_p = '''<w:p w14:paraId="05D02254" w14:textId="3099212C" w:rsidR="00812E22" w:rsidRPr="00DC0900" w:rsidRDefault="001863B3" w:rsidP="001E4619">
<w:pPr><w:jc w:val="center"/></w:pPr>
<w:r><w:rPr><w:lang w:val="ru-RU"/></w:rPr><w:t>КП.06130100.П-24-67б.07.11.2026.ПЗ</w:t></w:r>
</w:p>'''
    xml = re.sub(old_p_pat, new_p, xml, flags=re.DOTALL)
    
    return xml

def update_relationships(rels_xml):
    # Parse rels_xml
    root = ET.fromstring(rels_xml)
    
    # Check existing target IDs
    existing_ids = {c.attrib['Id'] for c in root}
    image_rels = [
        ("rId20", "media/image1.png"),
        ("rId30", "media/image2.png"),
        ("rId37", "media/image3.png"),
        ("rId43", "media/image4.png"),
    ]
    
    image_type = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/image"
    for r_id, target in image_rels:
        if r_id not in existing_ids:
            elem = ET.SubElement(root, "{http://schemas.openxmlformats.org/package/2006/relationships}Relationship")
            elem.attrib["Id"] = r_id
            elem.attrib["Type"] = image_type
            elem.attrib["Target"] = target
            
    return ET.tostring(root, encoding="utf-8", xml_declaration=True).decode("utf-8")

def assemble():
    print("Reading template...")
    with zipfile.ZipFile('Түсіндірме жазба_пример.docx', 'r') as z:
        file_map = {name: z.read(name) for name in z.namelist()}
    
    print("Translating header1.xml...")
    h1_xml = file_map['word/header1.xml'].decode('utf-8')
    file_map['word/header1.xml'] = translate_header1(h1_xml).encode('utf-8')
    
    print("Translating header2.xml...")
    h2_xml = file_map['word/header2.xml'].decode('utf-8')
    file_map['word/header2.xml'] = translate_header2(h2_xml).encode('utf-8')
    
    print("Updating footer1.xml (replacing language)...")
    f1_xml = file_map['word/footer1.xml'].decode('utf-8').replace('kk-KZ', 'ru-RU')
    file_map['word/footer1.xml'] = f1_xml.encode('utf-8')
    
    print("Updating document relationships...")
    rels_xml = file_map['word/_rels/document.xml.rels'].decode('utf-8')
    file_map['word/_rels/document.xml.rels'] = update_relationships(rels_xml).encode('utf-8')
    
    print("Adding media images...")
    img_files = {
        'word/media/image1.png': 'img_20.png',
        'word/media/image2.png': 'img_30.png',
        'word/media/image3.png': 'img_37.png',
        'word/media/image4.png': 'img_43.png',
    }
    for target_path, src_file in img_files.items():
        with open(src_file, 'rb') as f_img:
            file_map[target_path] = f_img.read()
    
    # Also update [Content_Types].xml if png extension is missing
    ct_xml = file_map['[Content_Types].xml'].decode('utf-8')
    if 'Extension="png"' not in ct_xml:
        ct_xml = ct_xml.replace('</Types>', '<Default Extension="png" ContentType="image/png"/></Types>')
        file_map['[Content_Types].xml'] = ct_xml.encode('utf-8')
        
    print("Generating full document.xml...")
    doc_xml = generate_document_xml()
    file_map['word/document.xml'] = doc_xml.encode('utf-8')
    
    out_docx = 'Курсовая_работа_Пояснительная_записка_ИТОГ.docx'
    print(f"Writing {out_docx}...")
    with zipfile.ZipFile(out_docx, 'w', compression=zipfile.ZIP_DEFLATED) as z_out:
        for fname, data in file_map.items():
            z_out.writestr(fname, data)
            
    print(f"Document {out_docx} successfully created!")

if __name__ == '__main__':
    assemble()
