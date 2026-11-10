# -*- coding: utf-8 -*-
"""
Generate complete document.xml and updated DOCX package with ECKD frames and stamps.
"""
import zipfile
import re
import os
import shutil
import xml.sax.saxutils as saxutils
from course_sections import SECTIONS_DATA

def escape(s):
    return saxutils.escape(s)

def make_p_toc(title, pagenum, level=1):
    ident = 0 if level == 1 else 360
    b_tag = "<w:b/>" if level == 1 else ""
    return f"""<w:p>
<w:pPr>
<w:pStyle w:val="11"/>
<w:tabs>
<w:tab w:val="right" w:leader="dot" w:pos="8900"/>
</w:tabs>
<w:ind w:left="{ident}"/>
<w:spacing w:line="300" w:lineRule="auto" w:after="60"/>
<w:rPr>
<w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/>
{b_tag}
<w:sz w:val="24"/>
<w:szCs w:val="24"/>
<w:lang w:val="ru-RU"/>
</w:rPr>
</w:pPr>
<w:r>
<w:rPr>
<w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/>
{b_tag}
<w:sz w:val="24"/>
<w:szCs w:val="24"/>
<w:lang w:val="ru-RU"/>
</w:rPr>
<w:t>{escape(title)}</w:t>
</w:r>
<w:r>
<w:tab/>
</w:r>
<w:r>
<w:rPr>
<w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/>
{b_tag}
<w:sz w:val="24"/>
<w:szCs w:val="24"/>
<w:lang w:val="ru-RU"/>
</w:rPr>
<w:t>{pagenum}</w:t>
</w:r>
</w:p>"""

def make_heading_1(title):
    return f"""<w:p>
<w:pPr>
<w:pStyle w:val="1"/>
<w:spacing w:before="360" w:after="240" w:line="360" w:lineRule="auto"/>
<w:jc w:val="center"/>
<w:rPr>
<w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/>
<w:b/>
<w:sz w:val="28"/>
<w:szCs w:val="28"/>
<w:lang w:val="ru-RU"/>
</w:rPr>
</w:pPr>
<w:r>
<w:rPr>
<w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/>
<w:b/>
<w:sz w:val="28"/>
<w:szCs w:val="28"/>
<w:lang w:val="ru-RU"/>
</w:rPr>
<w:t>{escape(title)}</w:t>
</w:r>
</w:p>"""

def make_heading_2(title):
    return f"""<w:p>
<w:pPr>
<w:pStyle w:val="2"/>
<w:ind w:firstLine="709"/>
<w:spacing w:before="240" w:after="160" w:line="360" w:lineRule="auto"/>
<w:jc w:val="both"/>
<w:rPr>
<w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/>
<w:b/>
<w:sz w:val="26"/>
<w:szCs w:val="26"/>
<w:lang w:val="ru-RU"/>
</w:rPr>
</w:pPr>
<w:r>
<w:rPr>
<w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/>
<w:b/>
<w:sz w:val="26"/>
<w:szCs w:val="26"/>
<w:lang w:val="ru-RU"/>
</w:rPr>
<w:t>{escape(title)}</w:t>
</w:r>
</w:p>"""

def make_body_p(text):
    return f"""<w:p>
<w:pPr>
<w:ind w:firstLine="709"/>
<w:spacing w:line="360" w:lineRule="auto" w:after="0"/>
<w:jc w:val="both"/>
<w:rPr>
<w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/>
<w:sz w:val="24"/>
<w:szCs w:val="24"/>
<w:lang w:val="ru-RU"/>
</w:rPr>
</w:pPr>
<w:r>
<w:rPr>
<w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/>
<w:sz w:val="24"/>
<w:szCs w:val="24"/>
<w:lang w:val="ru-RU"/>
</w:rPr>
<w:t xml:space="preserve">{escape(text)}</w:t>
</w:r>
</w:p>"""

def make_code_p(text):
    lines = text.split('\n')
    runs = []
    for i, line in enumerate(lines):
        runs.append(f"""<w:p>
<w:pPr>
<w:ind w:left="360"/>
<w:spacing w:line="240" w:lineRule="auto" w:after="0"/>
<w:jc w:val="left"/>
<w:rPr>
<w:rFonts w:ascii="Consolas" w:hAnsi="Consolas"/>
<w:sz w:val="18"/>
<w:szCs w:val="18"/>
<w:lang w:val="ru-RU"/>
</w:rPr>
</w:pPr>
<w:r>
<w:rPr>
<w:rFonts w:ascii="Consolas" w:hAnsi="Consolas"/>
<w:sz w:val="18"/>
<w:szCs w:val="18"/>
<w:lang w:val="ru-RU"/>
</w:rPr>
<w:t xml:space="preserve">{escape(line)}</w:t>
</w:r>
</w:p>""")
    return '\n'.join(runs)

def make_image_p(rId, width, height, caption):
    return f"""<w:p>
<w:pPr>
<w:spacing w:before="240" w:after="120" w:line="360" w:lineRule="auto"/>
<w:jc w:val="center"/>
<w:rPr>
<w:lang w:val="ru-RU"/>
</w:rPr>
</w:pPr>
<w:r>
<w:drawing>
<wp:inline distT="0" distB="0" distL="0" distR="0">
<wp:extent cx="{width}" cy="{height}"/>
<wp:effectExtent l="0" t="0" r="0" b="0"/>
<wp:docPr id="100" name="Picture"/>
<wp:cNvGraphicFramePr>
<a:graphicFrameLocks xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" noChangeAspect="1"/>
</wp:cNvGraphicFramePr>
<a:graphic xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">
<a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture">
<pic:pic xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture">
<pic:nvPicPr>
<pic:cNvPr id="0" name="Picture"/>
<pic:cNvPicPr/>
</pic:nvPicPr>
<pic:blipFill>
<a:blip r:embed="{rId}"/>
<a:stretch>
<a:fillRect/>
</a:stretch>
</pic:blipFill>
<pic:spPr>
<a:xfrm>
<a:off x="0" y="0"/>
<a:ext cx="{width}" cy="{height}"/>
</a:xfrm>
<a:prstGeom prst="rect">
<a:avLst/>
</a:prstGeom>
</pic:spPr>
</pic:pic>
</a:graphicData>
</a:graphic>
</wp:inline>
</w:drawing>
</w:r>
</w:p>
<w:p>
<w:pPr>
<w:spacing w:before="120" w:after="240" w:line="360" w:lineRule="auto"/>
<w:jc w:val="center"/>
<w:rPr>
<w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/>
<w:sz w:val="22"/>
<w:szCs w:val="22"/>
<w:lang w:val="ru-RU"/>
</w:rPr>
</w:pPr>
<w:r>
<w:rPr>
<w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/>
<w:sz w:val="22"/>
<w:szCs w:val="22"/>
<w:lang w:val="ru-RU"/>
</w:rPr>
<w:t>{escape(caption)}</w:t>
</w:r>
</w:p>"""

def make_table(rows):
    # standard GOST table with thin borders
    tbl_xml = ["""<w:tbl>
<w:tblPr>
<w:tblW w:w="0" w:type="auto"/>
<w:jc w:val="center"/>
<w:tblBorders>
<w:top w:val="single" w:sz="4" w:space="0" w:color="000000"/>
<w:left w:val="single" w:sz="4" w:space="0" w:color="000000"/>
<w:bottom w:val="single" w:sz="4" w:space="0" w:color="000000"/>
<w:right w:val="single" w:sz="4" w:space="0" w:color="000000"/>
<w:insideH w:val="single" w:sz="4" w:space="0" w:color="000000"/>
<w:insideV w:val="single" w:sz="4" w:space="0" w:color="000000"/>
</w:tblBorders>
</w:tblPr>"""]
    
    for r_idx, row in enumerate(rows):
        tbl_xml.append("<w:tr>")
        is_hdr = (r_idx == 0)
        for cell in row:
            b_tag = "<w:b/>" if is_hdr else ""
            jc_val = "center" if is_hdr else "left"
            tbl_xml.append(f"""<w:tc>
<w:tcPr>
<w:tcMar>
<w:top w:w="80" w:type="dxa"/>
<w:bottom w:w="80" w:type="dxa"/>
<w:left w:w="120" w:type="dxa"/>
<w:right w:w="120" w:type="dxa"/>
</w:tcMar>
</w:tcPr>
<w:p>
<w:pPr>
<w:spacing w:line="240" w:lineRule="auto" w:after="0"/>
<w:jc w:val="{jc_val}"/>
<w:rPr>
<w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/>
{b_tag}
<w:sz w:val="20"/>
<w:szCs w:val="20"/>
<w:lang w:val="ru-RU"/>
</w:rPr>
</w:pPr>
<w:r>
<w:rPr>
<w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/>
{b_tag}
<w:sz w:val="20"/>
<w:szCs w:val="20"/>
<w:lang w:val="ru-RU"/>
</w:rPr>
<w:t>{escape(cell)}</w:t>
</w:r>
</w:p>
</w:tc>""")
        tbl_xml.append("</w:tr>")
    tbl_xml.append("</w:tbl>")
    return '\n'.join(tbl_xml)

def generate_document_xml():
    body_parts = []
    
    # --- SECTION 1: СОДЕРЖАНИЕ ---
    body_parts.append(make_heading_1("СОДЕРЖАНИЕ"))
    
    # Table of contents items
    toc_items = [
        ("ВВЕДЕНИЕ", "5", 1),
        ("1. АНАЛИЗ ПРЕДМЕТНОЙ ОБЛАСТИ", "6", 1),
        ("1.1 Характеристика предметной области", "6", 2),
        ("1.2 Существующий процесс и проблематика", "6", 2),
        ("1.3 Причины выбора темы и целевая аудитория", "7", 2),
        ("1.4 Цель и задачи проекта", "7", 2),
        ("1.5 Ожидаемый результат", "8", 2),
        ("2. ФОРМУЛИРОВАНИЕ ТРЕБОВАНИЙ К ПРОЕКТУ", "9", 1),
        ("2.1 Функциональные требования", "9", 2),
        ("2.2 Нефункциональные требования", "9", 2),
        ("2.3 Модель пользователей и основные роли", "10", 2),
        ("2.4 Диаграмма вариантов использования (Use Case)", "11", 2),
        ("3. РАЗРАБОТКА КОНЦЕПЦИИ ПРОЕКТА", "12", 1),
        ("3.1 Архитектура системы", "12", 2),
        ("3.2 Обоснование стека используемых технологий", "12", 2),
        ("3.3 Структура программных модулей системы", "13", 2),
        ("3.4 Способ взаимодействия модулей", "14", 2),
        ("4. ПРОЕКТИРОВАНИЕ СТРУКТУРЫ ДАННЫХ", "15", 1),
        ("4.1 Информационные сущности предметной области", "15", 2),
        ("4.2 Спецификация таблиц базы данных", "15", 2),
        ("4.3 ER-диаграмма базы данных", "17", 2),
        ("5. ПРОЕКТИРОВАНИЕ ПОЛЬЗОВАТЕЛЬСКОГО ИНТЕРФЕЙСА", "18", 1),
        ("5.1 Основные формы и экраны системы", "18", 2),
        ("5.2 Сценарии навигации и переходов", "18", 2),
        ("5.3 Макет экранных форм", "19", 2),
        ("6. РАЗРАБОТКА АЛГОРИТМОВ ФУНКЦИОНИРОВАНИЯ СИСТЕМЫ", "20", 1),
        ("6.1 Алгоритм авторизации пользователя", "20", 2),
        ("6.2 Алгоритм поиска, фильтрации и расчета учебной нагрузки", "20", 2),
        ("6.3 Блок-схема алгоритма авторизации", "21", 2),
        ("ЗАКЛЮЧЕНИЕ", "22", 1),
        ("СПИСОК ИСПОЛЬЗОВАННЫХ ИСТОЧНИКОВ", "23", 1),
        ("ПРИЛОЖЕНИЯ", "24", 1),
        ("Приложение А. Листинг программных модулей авторизации и моделей БД", "24", 2),
    ]
    
    for title, pnum, lvl in toc_items:
        body_parts.append(make_p_toc(title, pnum, lvl))
    
    # End of Section 1 paragraph with Section 1 sectPr (Header 1 = Large Stamp)
    body_parts.append("""<w:p w14:paraId="73610EA1" w14:textId="77777777" w:rsidR="00827511" w:rsidRPr="00BF07A9" w:rsidRDefault="00827511" w:rsidP="00217927">
<w:pPr>
<w:tabs><w:tab w:val="left" w:pos="1005"/></w:tabs>
<w:rPr><w:noProof/><w:sz w:val="24"/><w:szCs w:val="24"/><w:lang w:val="ru-RU"/></w:rPr>
<w:sectPr w:rsidR="00827511" w:rsidRPr="00BF07A9" w:rsidSect="008907E6">
<w:headerReference w:type="default" r:id="rId8"/>
<w:footerReference w:type="default" r:id="rId9"/>
<w:footerReference w:type="first" r:id="rId10"/>
<w:pgSz w:w="11907" w:h="16839" w:code="9"/>
<w:pgMar w:top="1134" w:right="850" w:bottom="1134" w:left="1701" w:header="720" w:footer="720" w:gutter="0"/>
<w:cols w:space="720"/>
</w:sectPr>
</w:pPr>
</w:p>""")
    
    # --- SECTION 2: ОСНОВНАЯ ЧАСТЬ (Small Stamp) ---
    for sec in SECTIONS_DATA:
        body_parts.append(make_heading_1(sec["title"]))
        if "paragraphs" in sec:
            for p in sec["paragraphs"]:
                body_parts.append(make_body_p(p))
        if "subsections" in sec:
            for subsec in sec["subsections"]:
                body_parts.append(make_heading_2(subsec["title"]))
                if "paragraphs" in subsec:
                    for p in subsec["paragraphs"]:
                        if p.startswith("# Листинг"):
                            body_parts.append(make_code_p(p))
                        else:
                            body_parts.append(make_body_p(p))
                if "table_data" in subsec:
                    body_parts.append(make_table(subsec["table_data"]))
                if "image" in subsec:
                    img = subsec["image"]
                    body_parts.append(make_image_p(img["id"], img["width"], img["height"], img["caption"]))
    
    # Section 2 sectPr at body end (Header 2 = Small Stamp)
    sectPr2 = """<w:sectPr w:rsidR="00CE0AAE" w:rsidRPr="00BF07A9" w:rsidSect="004C031A">
<w:headerReference w:type="default" r:id="rId11"/>
<w:footerReference w:type="default" r:id="rId12"/>
<w:pgSz w:w="11907" w:h="16839" w:code="9"/>
<w:pgMar w:top="1134" w:right="851" w:bottom="1418" w:left="1701" w:header="0" w:footer="266" w:gutter="0"/>
<w:pgNumType w:start="5"/>
<w:cols w:space="720"/>
<w:docGrid w:linePitch="381"/>
</w:sectPr>"""
    
    full_body = '\n'.join(body_parts) + '\n' + sectPr2
    
    # Wrap in root document tag
    doc_xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:wpc="http://schemas.microsoft.com/office/word/2010/wordprocessingCanvas" xmlns:cx="http://schemas.microsoft.com/office/drawing/2014/chartex" xmlns:cx1="http://schemas.microsoft.com/office/drawing/2015/9/8/chartex" xmlns:cx2="http://schemas.microsoft.com/office/drawing/2015/10/21/chartex" xmlns:cx3="http://schemas.microsoft.com/office/drawing/2016/5/9/chartex" xmlns:cx4="http://schemas.microsoft.com/office/drawing/2016/5/10/chartex" xmlns:cx5="http://schemas.microsoft.com/office/drawing/2016/5/11/chartex" xmlns:cx6="http://schemas.microsoft.com/office/drawing/2016/5/12/chartex" xmlns:cx7="http://schemas.microsoft.com/office/drawing/2016/5/13/chartex" xmlns:cx8="http://schemas.microsoft.com/office/drawing/2016/5/14/chartex" xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006" xmlns:aink="http://schemas.microsoft.com/office/drawing/2016/ink" xmlns:am3d="http://schemas.microsoft.com/office/drawing/2017/model3d" xmlns:o="urn:schemas-microsoft-com:office:office" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math" xmlns:v="urn:schemas-microsoft-com:vml" xmlns:wp14="http://schemas.microsoft.com/office/word/2010/wordprocessingDrawing" xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing" xmlns:w10="urn:schemas-microsoft-com:office:word" xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" xmlns:w14="http://schemas.microsoft.com/office/word/2010/wordml" xmlns:w15="http://schemas.microsoft.com/office/word/2012/wordml" xmlns:w16cid="http://schemas.microsoft.com/office/word/2016/wordml/cid" xmlns:w16se="http://schemas.microsoft.com/office/word/2015/wordml/symex" xmlns:wpg="http://schemas.microsoft.com/office/word/2010/wordprocessingGroup" xmlns:wpi="http://schemas.microsoft.com/office/word/2010/wordprocessingInk" xmlns:wne="http://schemas.microsoft.com/office/word/2006/wordml" xmlns:wps="http://schemas.microsoft.com/office/word/2010/wordprocessingShape" mc:Ignorable="w14 w15 w16se w16cid wp14">
<w:body>
{full_body}
</w:body>
</w:document>"""
    return doc_xml

print("Generator script prepared.")
