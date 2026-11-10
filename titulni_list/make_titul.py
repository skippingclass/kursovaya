# -*- coding: utf-8 -*-
import zipfile
import re
import os
import shutil

def update_title_page():
    print("Updating Title Page...")
    with zipfile.ZipFile('Титульный лист_пример.docx', 'r') as z:
        file_map = {name: z.read(name) for name in z.namelist()}
    
    doc_xml = file_map['word/document.xml'].decode('utf-8')
    
    # 1. Update Title paragraph P10
    # Search for P10 paragraph with «Тема»
    doc_xml = re.sub(
        r'(<w:p [^>]*w14:paraId="550EE687".*?</w:p>)',
        r'''<w:p w14:paraId="550EE687" w14:textId="2C4322F2" w:rsidR="000510D1" w:rsidRDefault="00457BB8" w:rsidP="00457BB8">
<w:pPr>
<w:spacing w:line="360" w:lineRule="auto"/>
<w:jc w:val="center"/>
<w:rPr>
<w:b/>
<w:color w:val="000000"/>
<w:sz w:val="28"/>
<w:szCs w:val="28"/>
<w:lang w:val="ru-RU"/>
</w:rPr>
</w:pPr>
<w:r>
<w:rPr>
<w:b/>
<w:color w:val="000000"/>
<w:sz w:val="28"/>
<w:szCs w:val="28"/>
<w:lang w:val="ru-RU"/>
</w:rPr>
<w:t>«АВТОМАТИЗАЦИЯ УЧЕТА ПРЕПОДАВАТЕЛЕЙ ВЫСШЕГО КОЛЛЕДЖА «ASTANA POLYTECHNIC»</w:t>
</w:r>
</w:p>''',
        doc_xml,
        flags=re.DOTALL
    )
    
    # 2. Update Code paragraph P14
    doc_xml = re.sub(
        r'(<w:p [^>]*w14:paraId="5E303B02".*?</w:p>)',
        r'''<w:p w14:paraId="5E303B02" w14:textId="2A1162EE" w:rsidR="00F84673" w:rsidRPr="00FC020A" w:rsidRDefault="00F84673" w:rsidP="00F84673">
<w:pPr>
<w:spacing w:line="360" w:lineRule="auto"/>
<w:jc w:val="center"/>
<w:rPr>
<w:b/>
<w:lang w:val="ru-RU"/>
</w:rPr>
</w:pPr>
<w:r>
<w:rPr>
<w:b/>
<w:lang w:val="ru-RU"/>
</w:rPr>
<w:t>КП.06130100.П-24-67б.07.11.2026.ПЗ</w:t>
</w:r>
</w:p>''',
        doc_xml,
        flags=re.DOTALL
    )
    
    # 3. Update Student paragraph P17
    doc_xml = re.sub(
        r'(<w:p [^>]*w14:paraId="365234D5".*?</w:p>)',
        r'''<w:p w14:paraId="365234D5" w14:textId="00473CD9" w:rsidR="00F84673" w:rsidRPr="00457BB8" w:rsidRDefault="00FC020A" w:rsidP="00F84673">
<w:pPr>
<w:tabs><w:tab w:val="left" w:pos="6804"/></w:tabs>
<w:spacing w:line="360" w:lineRule="auto"/>
<w:jc w:val="left"/>
<w:rPr><w:lang w:val="ru-RU"/></w:rPr>
</w:pPr>
<w:r><w:rPr><w:lang w:val="ru-RU"/></w:rPr><w:t>Выполнил:</w:t></w:r>
<w:r><w:tab/><w:rPr><w:lang w:val="ru-RU"/></w:rPr><w:t>Евполов В.</w:t></w:r>
</w:p>''',
        doc_xml,
        flags=re.DOTALL
    )
    
    # 4. Clean up any Kazakh lang tags
    doc_xml = doc_xml.replace('w:val="kk-KZ"', 'w:val="ru-RU"')
    # Remove yellow highlights if any
    doc_xml = re.sub(r'<w:highlight w:val="yellow"/>', '', doc_xml)
    
    file_map['word/document.xml'] = doc_xml.encode('utf-8')
    
    out_name = 'Титульный_лист_ИТОГ.docx'
    with zipfile.ZipFile(out_name, 'w', compression=zipfile.ZIP_DEFLATED) as z_out:
        for fname, data in file_map.items():
            z_out.writestr(fname, data)
    print(f"Created {out_name} successfully.")

if __name__ == '__main__':
    update_title_page()
