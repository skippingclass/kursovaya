"""Сборка записки и руководств по актуальным схеме и протоколу проверок."""
from pathlib import Path
from copy import deepcopy
import ast
import json
from docx import Document
from docx.shared import Cm, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT, WD_TAB_LEADER
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.enum.style import WD_STYLE_TYPE
ROOT=Path(__file__).resolve().parents[1]
TMP=ROOT/'tmp/documents';REF=ROOT/'docs/templates';DOCS=ROOT/'docs'
COURSE=DOCS/'Пояснительная_записка.docx'
GUIDE_WORD=TMP/'guides'
AUTHOR='Евполов Владислав';GROUP='П-24-67Б';COLLEGE='Высший колледж «ASTANA POLYTECHNIC»'
CODE='КП.06130100.П-24-67Б.10.11.2026.ПЗ'
TESTS=json.loads((DOCS/'test_results.json').read_text(encoding='utf-8'))
SCHEMA=json.loads((DOCS/'schema.json').read_text(encoding='utf-8'))
FIGURE=0;TABLE=0
PAGE_BREAKS=set()


def apply_page(d,p):
    if id(d) in PAGE_BREAKS:
        p.paragraph_format.page_break_before=True
        PAGE_BREAKS.remove(id(d))


def font(style,size=14,bold=False):
    style.font.name='Times New Roman';style.font.size=Pt(size);style.font.bold=bold
    style.font.color.rgb=RGBColor(0,0,0)
    fonts=OxmlElement('w:rFonts')
    for attr in ['ascii','hAnsi','eastAsia','cs']:fonts.set(qn('w:'+attr),'Times New Roman')
    style.element.get_or_add_rPr().append(fonts)


def prepare(d):
    normal=d.styles['Normal'];font(normal)
    pf=normal.paragraph_format;pf.line_spacing=1.5;pf.first_line_indent=Cm(1.25)
    pf.space_before=Pt(0);pf.space_after=Pt(0)
    for name,size,bold in [('CourseHeading',14,True),('CourseCaption',12,False),('CourseTable',11,False),('CourseTOC',12,False)]:
        if name not in d.styles:d.styles.add_style(name,WD_STYLE_TYPE.PARAGRAPH)
        st=d.styles[name];st.base_style=normal;font(st,size,bold)
        st.paragraph_format.first_line_indent=Cm(0);st.paragraph_format.line_spacing=1.15
        st.paragraph_format.space_after=Pt(6)
        num=OxmlElement('w:numPr');numid=OxmlElement('w:numId');numid.set(qn('w:val'),'0');num.append(numid)
        st.element.get_or_add_pPr().append(num)
        if name=='CourseHeading':
            st.paragraph_format.keep_with_next=True
            outline=OxmlElement('w:outlineLvl');outline.set(qn('w:val'),'0');st.element.get_or_add_pPr().append(outline)
    font(d.styles['Title'],20,True);d.styles['Title'].paragraph_format.first_line_indent=Cm(0)
    if 'CourseCode' not in d.styles:
        d.styles.add_style('CourseCode', WD_STYLE_TYPE.PARAGRAPH)
    code = d.styles['CourseCode']
    code.base_style = normal
    font(code, 10)
    code.font.name = 'Courier New'
    for fonts in code.element.get_or_add_rPr().findall(qn('w:rFonts')):
        for key in ['ascii', 'hAnsi', 'eastAsia', 'cs']:
            fonts.set(qn('w:' + key), 'Courier New')
    code.paragraph_format.first_line_indent = Cm(0)
    code.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT
    code.paragraph_format.line_spacing = 1
    code.paragraph_format.space_after = Pt(0)
    for border in list(d.styles.element.iter(qn('w:pBdr'))):border.getparent().remove(border)
    d.core_properties.author=AUTHOR;d.core_properties.last_modified_by=AUTHOR
    d.core_properties.subject='Автоматизация учета преподавателей и учебной нагрузки'
    return d


def new_course():
    d=Document(REF/'course.docx');section=deepcopy(d.sections[-1]._sectPr)
    for child in list(d._element.body):d._element.body.remove(child)
    d._element.body.append(section)
    sec=d.sections[0];sec.top_margin=Cm(2);sec.bottom_margin=Cm(2.5)
    pg=section.find(qn('w:pgNumType'))
    if pg is None:pg=OxmlElement('w:pgNumType');section.append(pg)
    pg.set(qn('w:start'),'3')
    for node in sec.header._element.iter(qn('w:t')):
        if node.text and node.text.startswith('КП.'):node.text=CODE
        elif node.text=='1':node.text=''
    # Абзацы внутри штампа не должны наследовать отступ основного текста.
    for p in sec.header._element.iter(qn('w:p')):
        pr=p.find(qn('w:pPr'))
        if pr is None:pr=OxmlElement('w:pPr');p.insert(0,pr)
        for tag in ['ind','spacing']:
            for old in pr.findall(qn('w:'+tag)):pr.remove(old)
        ind=OxmlElement('w:ind')
        for key in ['firstLine','left','right']:ind.set(qn('w:'+key),'0')
        pr.append(ind)
        spacing=OxmlElement('w:spacing')
        for key,value in [('before','0'),('after','0'),('line','240'),('lineRule','auto')]:spacing.set(qn('w:'+key),value)
        pr.append(spacing)
        for run in p.findall(qn('w:r')):
            text=''.join(node.text or '' for node in run.iter(qn('w:t')))
            rp=run.find(qn('w:rPr'))
            if rp is None:rp=OxmlElement('w:rPr');run.insert(0,rp)
            for old in rp.findall(qn('w:sz')):rp.remove(old)
            sz=OxmlElement('w:sz');sz.set(qn('w:val'),'24' if text.startswith('КП.') else '16');rp.append(sz)
    return prepare(d)


def new_guide(title):
    d=prepare(Document());s=d.sections[0]
    font(d.styles['Normal'],12)
    d.styles['Normal'].paragraph_format.line_spacing=1.3
    d.styles['Normal'].paragraph_format.space_after=Pt(6)
    s.page_width=Cm(21);s.page_height=Cm(29.7);s.left_margin=Cm(2.5);s.right_margin=Cm(2)
    s.top_margin=Cm(2);s.bottom_margin=Cm(2)
    p=d.add_paragraph(title,'Title');p.alignment=WD_ALIGN_PARAGRAPH.CENTER
    p=d.add_paragraph(f'{COLLEGE}\n{AUTHOR} · группа {GROUP}\nGitHub skippingclass · версия 2.1 · 2026')
    p.paragraph_format.first_line_indent=Cm(0);p.alignment=WD_ALIGN_PARAGRAPH.CENTER
    for r in p.runs:r.font.size=Pt(12)
    p=s.footer.paragraphs[0];p.alignment=WD_ALIGN_PARAGRAPH.RIGHT
    field=OxmlElement('w:fldSimple');field.set(qn('w:instr'),'PAGE');p._p.append(field)
    return d


def heading(d,text,new_page=True):
    p=d.add_paragraph(text,'CourseHeading');p.paragraph_format.page_break_before=new_page
    apply_page(d,p)
    p.paragraph_format.space_after=Pt(12);return p


def body(d,text):
    p=d.add_paragraph(text);p.alignment=WD_ALIGN_PARAGRAPH.JUSTIFY;apply_page(d,p);return p


def listing(d,items):
    for i,text in enumerate(items):
        p=body(d,f'{i+1}) {text.rstrip(".;")}'+('.' if i==len(items)-1 else ';'))
        p.paragraph_format.first_line_indent=Cm(0);p.paragraph_format.left_indent=Cm(1.25)


def table(d,title,headers,rows,widths=None):
    global TABLE
    TABLE+=1
    p=d.add_paragraph(f'Таблица {TABLE} - {title}','CourseCaption');p.paragraph_format.keep_with_next=True
    apply_page(d,p)
    t=d.add_table(rows=1,cols=len(headers));t.alignment=WD_TABLE_ALIGNMENT.CENTER;t.autofit=False
    widths=widths or [16.5/len(headers)]*len(headers)
    for col,width in zip(t.columns,widths):col.width=Cm(width)
    for cell,value in zip(t.rows[0].cells,headers):cell.text=str(value)
    for row in rows:
        for cell,value in zip(t.add_row().cells,row):cell.text=str(value)
    for ri,row in enumerate(t.rows):
        row._tr.get_or_add_trPr().append(OxmlElement('w:cantSplit'))
        if ri==0:row._tr.trPr.append(OxmlElement('w:tblHeader'))
        for ci,cell in enumerate(row.cells):
            cell.width=Cm(widths[ci]);cell.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER
            tcpr=cell._tc.get_or_add_tcPr();borders=OxmlElement('w:tcBorders')
            for edge in ['top','left','bottom','right']:
                e=OxmlElement('w:'+edge);e.set(qn('w:val'),'single');e.set(qn('w:sz'),'4');e.set(qn('w:color'),'D9D9D9');borders.append(e)
            tcpr.append(borders);margins=OxmlElement('w:tcMar')
            for edge in ['top','bottom','left','right']:
                e=OxmlElement('w:'+edge);e.set(qn('w:w'),'75');e.set(qn('w:type'),'dxa');margins.append(e)
            tcpr.append(margins)
            if ri==0:
                shade=OxmlElement('w:shd');shade.set(qn('w:fill'),'E9EDF2');tcpr.append(shade)
            for p in cell.paragraphs:
                p.style=d.styles['CourseTable'];p.paragraph_format.space_after=Pt(2);p.paragraph_format.space_before=Pt(2)
                p.paragraph_format.keep_with_next=False
                for r in p.runs:r.bold=ri==0
    p=d.add_paragraph();p.paragraph_format.space_after=Pt(2);p.paragraph_format.line_spacing=1
    return TABLE


def figure(d,file,caption,width=16):
    global FIGURE
    FIGURE+=1
    p=d.add_paragraph();p.paragraph_format.first_line_indent=Cm(0)
    apply_page(d,p)
    p.alignment=WD_ALIGN_PARAGRAPH.CENTER;p.paragraph_format.keep_with_next=True
    picture=p.add_run().add_picture(str(DOCS/file),width=Cm(width));picture._inline.docPr.set('descr',caption)
    p=d.add_paragraph(f'Рисунок {FIGURE} - {caption}','CourseCaption');p.alignment=WD_ALIGN_PARAGRAPH.CENTER
    return FIGURE


def page(d):PAGE_BREAKS.add(id(d))


def code_listing(d, number, title, file, functions):
    source = (ROOT / file).read_text(encoding="utf-8")
    lines = source.splitlines()
    nodes = {node.name: node for node in ast.parse(source).body
             if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}
    heading(d, f'Приложение Д Листинг {number} {title}')
    body(d, f'Файл {file}. Фрагмент соответствует исходному коду проекта.')
    for function in functions:
        node = nodes[function]
        for line in lines[node.lineno - 1:node.end_lineno]:
            paragraph = d.add_paragraph(line, 'CourseCode')
            paragraph.paragraph_format.keep_with_next = False
        d.add_paragraph('', 'CourseCode')


def front_matter(d):
    def center(text, before=0, style=None):
        paragraph = d.add_paragraph(text, style=style)
        paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        paragraph.paragraph_format.first_line_indent = Cm(0)
        paragraph.paragraph_format.space_before = Pt(before)
        return paragraph

    center('ГКП на ПХВ Высший колледж «ASTANA POLYTECHNIC»\nАкимата г. Астана')
    center('АВТОМАТИЗАЦИЯ УЧЕТА\nПРЕПОДАВАТЕЛЕЙ ВЫСШЕГО КОЛЛЕДЖА\n«ASTANA POLYTECHNIC»', 125, 'Title')
    center('КУРСОВОЙ ПРОЕКТ\nПояснительная записка', 22)
    center(CODE, 18)
    paragraph = d.add_paragraph(f'Выполнил {AUTHOR}\nГруппа {GROUP}\nРуководитель проекта Атантаева А.З.')
    paragraph.alignment = WD_ALIGN_PARAGRAPH.LEFT
    paragraph.paragraph_format.left_indent = Cm(7.2)
    paragraph.paragraph_format.first_line_indent = Cm(0)
    paragraph.paragraph_format.space_before = Pt(65)
    center('Астана 2026', 70)

    heading(d, 'ЗАДАНИЕ НА КУРСОВОЙ ПРОЕКТ')
    for text in [
        f'Обучающийся: {AUTHOR}, группа {GROUP}. Специальность 06130100 «Программное обеспечение».',
        'Тема: автоматизация учета преподавателей Высшего колледжа «ASTANA POLYTECHNIC».',
        'Объект: учет преподавателей и распределение педагогической нагрузки по учебному плану колледжа.',
        'Проблема: раздельное ведение карточек и часов затрудняет обнаружение дублей и контроль свободного объема нагрузки.',
        'Результат: приложение для карточек преподавателей, общего плана, назначений и отчетов, дополненное REST API и сетевым клиентом.',
    ]:
        body(d, text)
    listing(d, [
        'анализ предметной области, аналогов и требований',
        'проектирование архитектуры, базы, API и экранов',
        'реализация, интеграция, тестирование и локальное развертывание',
        'пояснительная записка, документация, графические материалы и презентация',
    ])
    for text in [
        'Руководитель проекта ______________________ Атантаева А.З.',
        'Задание принял __________________________ Евполов Владислав',
        'Дата выдачи __________________ Дата защиты __________________',
    ]:
        body(d, text)
    separator = d.add_paragraph()
    separator.paragraph_format.space_after = Pt(0)
    separator.paragraph_format.line_spacing = 1
    separator.add_run().font.size = Pt(1)
    section = deepcopy(d.sections[0]._sectPr)
    for child in list(section):
        if child.tag in {qn('w:headerReference'), qn('w:footerReference'), qn('w:pgNumType')}:
            section.remove(child)
    separator._p.get_or_add_pPr().append(section)
    front = d.sections[0]
    front.different_first_page_header_footer = True
    number = front.footer.paragraphs[0]
    number.paragraph_format.first_line_indent = Cm(0)
    number.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    field = OxmlElement('w:fldSimple')
    field.set(qn('w:instr'), 'PAGE')
    number._p.append(field)


REQUIREMENTS=[('ФТ01','Карточки','раздельные ФИО, маска телефона, проверка обязательных полей'),
 ('ФТ02','Повторный ввод','точные дубликаты блокируются, похожие ФИО требуют проверки'),
 ('ФТ03','Поиск и сортировка','кириллический поиск, выбор поля и направления сортировки'),
 ('ФТ04','Годовая ставка','меньше, ровно и больше 720 часов за выбранный год'),
 ('ФТ05','Общий план','год, семестр, группа, дисциплина, недели, теория и практика'),
 ('ФТ06','Назначения','выдача часов только из доступного остатка плана'),
 ('ФТ07','Изменения','возврат часов при уменьшении, переносе и отмене'),
 ('ФТ08','Отчетность','выбор года, семестра, преподавателя; Excel и PDF'),
 ('ФТ09','Сохранность','миграция старой базы и копии всех семи таблиц'),
 ('ФТ10','Доступ и справка','три роли, сведения об авторе и руководства'),
 ('ФТ11','REST API','версионированные маршруты, OpenAPI, вход и проверка роли'),
 ('ФТ12','Сетевой клиент','просмотр карточек, изменение плана и назначений, выгрузка ведомости')]
CHAPTERS=['ВВЕДЕНИЕ','1 АНАЛИТИКО-ПОСТАНОВОЧНАЯ ЧАСТЬ','1.3 Требования и постановка задачи',
 '2 ТЕОРЕТИКО-ПРОЕКТНАЯ ЧАСТЬ','2.2 Структура данных',
 '2.3 Сценарии и интерфейсы','2.4 Алгоритмы и безопасность',
 '3 ПРАКТИЧЕСКАЯ РЕАЛИЗАЦИЯ И ОЦЕНКА РЕЗУЛЬТАТОВ','3.4 Тестирование','3.5 Оценка результатов',
 'ЗАКЛЮЧЕНИЕ','СПИСОК ИСПОЛЬЗОВАННЫХ ИСТОЧНИКОВ','ПРИЛОЖЕНИЯ']
SUBHEADINGS = {
    1: ['1.1 Предметная область и текущий процесс', '1.2 Сравнение аналогов'],
    2: ['1.4 Права доступа и критерии качества'],
    3: ['2.1 Архитектура и технологии'],
    6: ['2.5 Контракт API и взаимодействие компонентов', '2.6 Порядок работы с Git'],
    7: ['3.1 Реализация приложения', '3.2 Сервер и сетевой клиент', '3.3 Развертывание'],
}
TOC = [title for index, chapter in enumerate(CHAPTERS)
       for title in [chapter, *SUBHEADINGS.get(index, [])]]


def subsection(d, chapter, index=0, *, new_page=True):
    paragraph = heading(d, SUBHEADINGS[chapter][index], new_page)
    paragraph.paragraph_format.space_after = Pt(8)
    return paragraph


def build_course():
    TMP.mkdir(parents=True, exist_ok=True)
    d = new_course()
    front_matter(d)
    heading(d,'СОДЕРЖАНИЕ',False)
    for title in TOC:
        p=d.add_paragraph(title+'\t','CourseTOC')
        p.paragraph_format.tab_stops.add_tab_stop(Cm(16),WD_TAB_ALIGNMENT.RIGHT,WD_TAB_LEADER.DOTS)
        p.paragraph_format.space_after = Pt(4)
        if title[1:2] == '.':
            p.paragraph_format.left_indent = Cm(0.5)
    heading(d,CHAPTERS[0])
    for text in [
      'Проект посвящен автоматизации учета преподавателей и распределения учебной нагрузки в Высшем колледже «ASTANA POLYTECHNIC». Программа объединяет карточки сотрудников, справочники, общий план и назначения. Результат включает настольное приложение, сервер REST API и сетевой клиент на PyQt6.',
      'Актуальность работы связана с риском повторного ввода преподавателей и несогласованного распределения часов в отдельных электронных таблицах. При свободном вводе нагрузки сложно установить, из какого плана получены часы и сколько осталось для других преподавателей. В разработанной системе назначение связано со строкой общего плана, поэтому остаток рассчитывается автоматически.',
      'Объект проекта — учет преподавательского состава и педагогической нагрузки колледжа. Предмет проекта — программные методы проверки кадровых данных, распределения ограниченного объема часов, формирования выборок и подготовки отчетов.',
      'Цель — разработать и проверить приложение для учета карточек и распределения часов из общего плана. Применены анализ предметной области, моделирование данных, прототипирование экранов и автоматизированное тестирование. Общий план позволяет учебной части проследить, из какого объема выданы часы и сколько доступно для новых назначений. Задачи проекта:'
    ]:body(d,text)
    listing(d,['проанализировать предметную область и пользователей','сформулировать требования к программе',
      'спроектировать архитектуру, данные и интерфейс','реализовать кадровый учет и распределение часов по семестрам',
      'реализовать REST API и сетевую работу с планом и ведомостью','проверить систему и подготовить комплект для защиты'])
    heading(d,CHAPTERS[1])
    subsection(d, 1, new_page=False)
    for text in [
      'Учебная часть хранит сведения о сотрудниках, их квалификации, стаже и принадлежности к кафедре. Для учебного года определяются дисциплины и объем занятий по группам, после чего часы закрепляются за преподавателями. Теория и практика учитываются раздельно, поскольку свободные часы одного вида не компенсируют дефицит другого.',
      'Исходный процесс допускает ввод ФИО одной строкой и независимое добавление нагрузки каждому сотруднику. Повторная регистрация с другим регистром или опечаткой создает две карточки. Назначение без связи с учебным планом приводит к ситуации, когда сумма часов по преподавателям превышает объем занятий группы.',
      'Предлагаемый процесс начинается с общего плана. Строка плана определяется учебным годом, семестром, группой и дисциплиной. В ней задаются часы теории, практики и количество учебных недель. Затем оператор выбирает строку и преподавателя, вводит назначаемые часы и получает новый остаток.',
      'Администратор управляет пользователями и копиями. Заведующий кафедрой ведет карточки, справочники и нагрузку. Методист просматривает информацию, задает фильтры и экспортирует отчеты.',
      'Удаление назначения освобождает часы. План нельзя уменьшить ниже уже распределенного объема теории или практики. Источником назначения остается конкретная строка плана.',
      'Границы проекта охватывают объем учебной нагрузки. Расписание, аудитории и расчет зарплаты остаются отдельными процессами. Проект использует ориентир в 720 часов за год. Часы в неделю являются средним показателем за семестр.'
    ]:body(d,text)
    subsection(d, 1, 1)
    body(d,'В качестве аналогов рассмотрены продукты «1С» [8] и «Галактика» [9], а также процесс с раздельными электронными таблицами. Сопоставление учитывает функции, которые требуются при распределении нагрузки колледжа.')
    table(d, 'Сопоставление подходов к учету нагрузки', ['Решение', 'Возможности', 'Применимость к проекту'], [
        ('Электронные таблицы', 'Гибкий ввод и привычные формулы', 'Связь карточки, плана и назначения нужно поддерживать вручную.'),
        ('1С:Зарплата и кадры образовательной организации', 'Тарификация и расчет окладов с учетом педагогической нагрузки [8]',
         'Подходит для задач кадров и зарплаты. В проекте достаточно учета часов и ведомости.'),
        ('Галактика ВУЗ', 'Планирование нагрузки и индивидуальных планов преподавателей [9]',
         'Покрывает вузовские процессы. Для проекта выбран учет по группе и двум видам часов.'),
        ('Разрабатываемая система', 'Карточки, план, назначения, контроль остатка, ведомость',
         'Отдельные остатки теории и практики и локальный тестовый запуск.'),
    ], [4.1, 5.6, 6.8])
    body(d,'Основные риски текущего процесса — повторная карточка, независимое изменение ведомости и превышение общего объема. Проект решает их через проверку совпадений, общую выборку для выгрузок и транзакционный расчет остатка.')
    heading(d,CHAPTERS[2])
    body(d,'Требуется реализовать кадровый учет, общий план и назначения, интегрировать сервер с клиентом, провести проверку и подготовить демонстрационный запуск. Функции и критерии приведены в таблице 2.')
    table(d,'Функциональные требования',['Код','Функция','Критерий'],REQUIREMENTS,[1.4,3.6,11.5])
    body(d,'Нефункциональные требования включают понятные сообщения об ошибках, согласованность изменений в транзакции и одинаковое поведение поиска для SQLite и PostgreSQL. Неудачное назначение должно сохранять прежние данные и остатки. Просмотр и экспорт должны оставаться доступны методисту.')
    page(d)
    body(d,'Диаграмма вариантов использования на рисунке 1 показывает функции трех ролей и соответствует вкладкам программы.')
    figure(d,'diagrams/use_case.png','Варианты использования системы',15)
    body(d,'Для запуска необходимы Python 3.10 или новее и библиотеки requirements.txt. Автономный режим работает с SQLite либо PostgreSQL. Учебный сетевой стенд использует FastAPI, Uvicorn и SQLite на стороне сервера. Для экспорта кириллицы встроен DejaVu Sans [5].')
    subsection(d, 2)
    table(d, 'Матрица прав доступа', ['Действие', 'Администратор', 'Заведующий', 'Методист'], [
        ('Просмотр карточек и плана, экспорт ведомости', 'Да', 'Да', 'Да'),
        ('Изменение карточек, плана и назначений', 'Да', 'Да', '—'),
        ('Ведение кафедр и дисциплин в автономном режиме', 'Да', 'Да', '—'),
        ('Пользователи, копии и настройки в автономном режиме', 'Да', '—', '—'),
    ], [6.6, 3.4, 3.2, 3.3])
    listing(d, [
        'НФТ01. При ошибке сохранения приложение показывает причину, а транзакция сохраняет прежние остатки',
        'НФТ02. Закрытые маршруты требуют действующую сессию. Операции записи проверяют роль на сервере',
        'НФТ03. Таблицы читаются при изменении размеров окна, широкие столбцы прокручиваются',
        'НФТ04. Испытания работают с временной базой. Повторный запуск обновления сохраняет исходные идентификаторы',
        'НФТ05. Предпросмотр и экспорт используют одинаковые фильтры, PDF сохраняет читаемую кириллицу',
    ])
    heading(d,CHAPTERS[3])
    subsection(d, 3, new_page=False)
    body(d,'Выбрана трехуровневая организация настольного приложения. Интерфейс принимает действия пользователя, сервисы проверяют предметные ограничения, SQLAlchemy выполняет чтение и запись в выбранную СУБД. Архитектура представлена на рисунке 2.')
    figure(d,'diagrams/architecture.png','Архитектура приложения',15)
    body(d,'Интерфейс расположен в ui, сервисы — в services, модели, подключение, миграция и резервное копирование — в database. Конфигурация хранится в локальном settings.json, исключенном из репозитория. Точка входа приложения — run.py.')
    page(d)
    body(d,'PyQt6 предоставляет формы, таблицы и валидаторы. SQLAlchemy использует общие модели для двух СУБД. openpyxl создает Excel, ReportLab — PDF. Назначение модулей приведено в таблице 4.')
    table(d,'Технологии и модули',['Компонент','Реализация','Назначение'],[
      ('Интерфейс','PyQt6, ui/','карточки, план, назначения, фильтры и справка'),
      ('Кадровый учет','teacher_service.py','валидация, поиск, похожие карточки и сортировка'),
      ('Нагрузка','workload_service.py','общий план, остатки, транзакции и назначения'),
      ('Отчетность','report_service.py','единые выборки для экрана, Excel и PDF'),
      ('Хранение','SQLAlchemy, SQLite / PostgreSQL','объекты, связи и транзакции'),
      ('Обновление','migrations.py, backup.py','миграция и JSON-копии версии 2'),
      ('Проверка','unittest, tests/','проверки сервисов и Qt на временных данных')],[3.2,5,8.3])
    body(d,'Взаимодействие начинается с сигнала Qt. При сохранении назначения форма передает идентификатор плана, преподавателя и часы сервису. Сервис повторно проверяет остаток внутри транзакции. После сохранения обновляются обе таблицы. При отказе выводится причина, а данные остаются прежними.')
    heading(d,CHAPTERS[4])
    body(d,'База данных содержит семь таблиц. Роли связаны с пользователями, кафедры — с преподавателями и дисциплинами. Дисциплина участвует в общем плане, назначение связывает преподавателя со строкой плана. Фактическая схема ORM показана на рисунке 3.')
    figure(d,'diagrams/erd.png','Сущности и связи базы данных',15)
    body(d,'Отдельные спецификации таблиц приведены далее. PK обозначает первичный ключ, FK — внешний. Поля года, семестра и дисциплины в назначении сохранены для совместимости и обновляются сервисом из выбранного плана.')
    descriptions={
      'id':'идентификатор записи','name':'наименование','username':'логин','password_hash':'хэш scrypt с солью',
      'role_id':'роль пользователя','head_name':'заведующий кафедрой','code':'код дисциплины',
      'department_id':'кафедра','last_name':'фамилия','first_name':'имя','middle_name':'отчество при наличии',
      'full_name':'совместимое представление ФИО','birth_date':'дата рождения','phone':'телефон','email':'почта',
      'qualification':'категория','experience':'стаж от 0 до 70 лет','status':'работает, в отпуске, уволен',
      'photo_path':'путь к фото при наличии','academic_year':'учебный год YYYY-YYYY',
      'semester':'1 или 2; 0 для архива','group_name':'учебная группа','discipline_id':'дисциплина',
      'hours_lecture':'часы теории','hours_practice':'часы практики','weeks':'учебных недель от 1 до 52',
      'pool_id':'строка общего плана','teacher_id':'преподаватель','total_hours':'сумма теории и практики'}
    titles={'roles':'Роли','users':'Учетные записи','departments':'Кафедры','disciplines':'Дисциплины',
      'teachers':'Преподаватели','workload_pools':'Общий план нагрузки','teacher_workload':'Назначения преподавателям'}
    order=['roles','users','departments','teachers','disciplines','workload_pools','teacher_workload']
    page(d)
    for entry in sorted(SCHEMA,key=lambda item:order.index(item['name'])):
        if entry['name'] in ['teachers','workload_pools','teacher_workload']:page(d)
        p=body(d,f'Структура таблицы {entry["name"]} приведена в таблице {TABLE+1}.')
        p.paragraph_format.keep_with_next=True
        rows=[]
        for c in entry['columns']:
            keys=[]
            if c['primary_key']:keys.append('PK')
            if c['foreign_key']:keys.append('FK '+c['foreign_key'])
            if c['unique']:keys.append('UNIQUE')
            if not c['nullable']:keys.append('NOT NULL')
            rows.append((c['name'],c['type'],', '.join(keys),descriptions.get(c['name'],'')))
        table(d,titles[entry['name']],['Поле','Тип','Ограничение','Описание'],rows,[3.3,3.2,4.2,5.8])
        if entry['name']=='workload_pools':
            body(d,'На уровне БД действуют составной UNIQUE (academic_year, semester, group_name, discipline_id), CHECK (hours_lecture >= 0 AND hours_practice >= 0 AND weeks > 0) и CHECK (semester IN (0, 1, 2)). Остатки вычисляются по назначениям.')
        if entry['name']=='teacher_workload':
            body(d,'Составной UNIQUE (pool_id, teacher_id) допускает одну строку для пары плана и преподавателя. Пределы входных часов и их сумма проверяются сервисом внутри транзакции. Преподаватель может вести разные группы и семестры.')
    body(d,'Значения по умолчанию задаются ORM при вставке. Для teachers это пустые части ФИО, нулевой стаж и статус «работает». Для workload_pools часы равны нулю, weeks равно 18. Для teacher_workload семестр и часы равны нулю. Полный машиночитаемый словарь с DEFAULT, UNIQUE и CHECK находится в docs/schema.json [6].')
    body(d,'Миграция добавляет раздельные ФИО и связь с планом без удаления прежних записей. Каждое старое назначение получает архивную строку с тем же объемом, неизвестными группой и семестром. Число недель получает начальное значение 18, которое необходимо уточнить. Перед обновлением старой SQLite-базы создается .before-v2.bak.')
    heading(d,CHAPTERS[5])
    body(d,'Основное окно содержит вкладки преподавателей, нагрузки, справочников, отчетов и пользователей. Последняя доступна администратору. Кадровый учет с фильтрами и порядком сортировки показан на рисунке 4.')
    figure(d,'screenshots/main_window.png','Главное окно и кадровый учет',14)
    p=body(d,'Фамилия и имя обязательны, отчество указывается при наличии. Телефон заполняется по маске QLineEdit [4], дата рождения ограничена текущей датой. Форма представлена на рисунке 5.')
    p.paragraph_format.keep_with_next=True
    figure(d,'screenshots/teacher_form.png','Раздельные ФИО и маска телефона',10)
    page(d)
    body(d,'Вкладка нагрузки разделена на общий план и назначения. Оператор добавляет объем занятий по группе и семестру, затем назначает часть преподавателю. План и форма назначения показаны на рисунках 6 и 7.')
    figure(d,'screenshots/workload_pool.png','Общий план и свободные часы',14)
    figure(d,'screenshots/workload_form.png','Назначение часов из общего плана',14)
    body(d,'Форма показывает доступную теорию и практику, сумму и часы в неделю. При редактировании в доступный остаток включаются прежние часы текущего назначения, чтобы повторное сохранение не списывало их дважды.')
    page(d)
    body(d,'Нагрузку преподавателя можно выбрать фильтрами назначений либо посмотреть в личной карточке. В ней выбираются год и семестр; итоги разделены на теорию и практику. Предпросмотр отчета показан на рисунке 8.')
    figure(d,'screenshots/workload_report.png','Ведомость по году и семестру')
    body(d,'Переключение вкладок обновляет справочники с сохранением доступных выбранных значений. В таблицах плана, назначений и отчетов числовые столбцы сортируются как числа. Сообщение о недостатке часов показывает остатки обоих видов занятий. Предупреждение о похожем ФИО позволяет проверить опечатку.')
    heading(d,CHAPTERS[6])
    body(d,'Сервис находит учетную запись по логину и проверяет пароль по хэшу scrypt с индивидуальной солью. Старый хэш SHA-256 преобразуется в scrypt после успешного входа. При неверных реквизитах выводится ошибка. Последовательность представлена на рисунке 9.')
    figure(d,'diagrams/auth_flowchart.png','Алгоритм входа в систему',11)
    page(d)
    body(d,'Распределение выполняется одной транзакцией SQLAlchemy [3]. SQLite использует BEGIN IMMEDIATE, PostgreSQL — блокировку строк FOR UPDATE. При переносе блокировки планов берутся в порядке идентификаторов. Алгоритм показан на рисунке 10.')
    figure(d,'diagrams/workload_flowchart.png','Алгоритм распределения часов',12)
    body(d,'Для каждого вида занятий остаток равен объему плана за вычетом суммы назначений. При редактировании текущее назначение исключается из суммы. Итог равен теории плюс практике, средняя недельная нагрузка — итогу, деленному на число недель. Годовой фильтр суммирует только выбранный учебный год и сравнивает результат с 720 часами.')
    body(d,'Для проверки ФИО применяется Unicode NFKC, единый регистр и нормализация пробелов. Буква ё сравнивается как е. Точный дубликат или совпадающий контакт блокирует сохранение. Сходство ФИО от 0,88 по SequenceMatcher вызывает предупреждение об опечатке.')
    subsection(d, 6)
    body(d,'HTTP-сервер построен на FastAPI. Маршруты сгруппированы по ресурсам и доступны под /api/v1. Pydantic проверяет типы входных полей и формирует схемы OpenAPI [10]. Правила учета выполняют существующие сервисы. Применение единого сервиса предотвращает расхождение между сетевым и автономным режимами.')
    figure(d,'diagrams/network.png','Физическая схема учебного стенда',16)
    body(d,'JSON используется для входа, справочников и операций учета. Ведомость передается двоичным файлом. Клиент хранит случайный токен только в памяти и отправляет его в заголовке Authorization. Сервер сверяет сессию, проверяет срок действия и обращается к текущей роли учетной записи.')
    body(d,'Структура ответа и примеры приведены в docs/API.md. Создание записи возвращает 201, отсутствие сессии — 401, запрет на изменение для методиста — 403, отказ по правилам учета — 409, некорректная структура запроса — 422.')
    page(d)
    body(d,'Навигация сетевого клиента представлена на рисунке 12. Основное окно размещает фильтры над таблицами. Кнопки работы с планом и назначениями доступны оператору и администратору. Открытая форма остается на экране при отказе сервера, чтобы пользователь мог исправить данные.')
    figure(d,'diagrams/client_navigation.png','Прототип навигации сетевого клиента',16)
    body(d,'Клиент разделен на экранные формы и транспортный модуль. NetworkWindow хранит значения выбранных фильтров, отображает строки и вызывает формы редактирования. ApiClient отправляет HTTP-запросы и преобразует JSON в данные для таблиц. Нажатие «Применить» фиксирует фильтры ведомости для просмотра и выгрузки.')
    body(d,'Фильтры размещены в два ряда, а при уменьшении ширины окна таблица использует горизонтальную прокрутку. Форма назначения показывает группу, период и доступный остаток. Наличие свободных часов повторно проверяется сервером при сохранении.')
    subsection(d, 6, 1)
    body(d,'Исходная история ветки main содержит коммит 7b410b5 с первой полной версией и 2cd21eb с общим планом, миграцией и проверками. Сервер и сетевой клиент добавлены коммитом 6297a6f в ветке feature/coursework-client-server. Код поделен на database, services, ui, server и tests. Настройки подключения и временные файлы исключены через .gitignore.')
    body(d,'Порядок командной работы предусматривает самостоятельные ветки feature/api-* и feature/client-* от main. Изменения контракта согласуются по схеме OpenAPI, примерам запросов и кодам ответов. Коммит относится к одной законченной задаче. При запросе на слияние второй участник проверяет код, контракт и протокол тестов.')
    body(d,'При пересечении изменений участник обновляет рабочую ветку, проверяет конфликтующие модели и вызовы клиента и повторно запускает тесты. История подтверждает индивидуальную работу в Git. Для подтверждения командного этапа требуются ветки участников, обсуждение контракта и записи о просмотре и слиянии изменений.')
    heading(d,CHAPTERS[7])
    subsection(d, 7, new_page=False)
    for text in [
      'Реализация соответствует семи сущностям и трем уровням архитектуры. config.py задает версию и подключение, run.py создает QApplication, применяет оформление, обновляет схему и открывает вход. Пользователь работает с локальной SQLite либо настраивает PostgreSQL в параметрах подключения.',
      'TeacherDialog содержит отдельные фамилию, имя и отчество, валидатор букв и маску +7 (999) 999-99-99. teacher_service.py повторно проверяет обязательность полей, стаж, контакты и кафедру. При изменении карточки из проверки совпадений исключается ее собственный идентификатор.',
      'WorkloadPool и PoolDialog реализуют общий план. save_pool проверяет период, группу и объем. План нельзя уменьшить ниже назначенной теории либо практики. Изменение периода плана синхронно обновляет назначения, удаление используемой строки блокируется.',
      'WorkloadDialog передает сервису строку плана, преподавателя и два вида часов. Перед фиксацией повторно читается остаток. Удаление назначения освобождает объем через удаление записи распределения, без ручного увеличения отдельного счетчика.',
      'Кадровая выборка вычисляет period_hours для выбранного учебного года. Порядок задается по ФИО, стажу, кафедре либо часам, по возрастанию или убыванию. Фильтры ставки различают значения ниже 720, ровно 720 и выше 720 часов.'
    ]:body(d,text)
    page(d)
    body(d,'Предпросмотр и экспорт используют одинаковые функции сбора данных с годом, семестром, кафедрой и преподавателем. Excel содержит числовые часы и итоги, PDF — переносимые ячейки и встроенный шрифт. Реализованные назначения приведены на рисунке 13.')
    figure(d,'screenshots/workload_assignments.png','Распределение нагрузки преподавателям')
    body(d,'JSON-копия версии 2 включает семь таблиц, раздельные ФИО и план. Файл сохраняется через временный файл и атомарную замену. Восстановление проверяет внешние ключи и остатки в транзакции. Старый формат преобразуется в архивные планы. Ошибка приводит к откату.')
    body(d,'Справка открывает три сопроводительных документа. В окне «О программе» указаны Евполов Владислав, группа П-24-67Б, Высший колледж «ASTANA POLYTECHNIC» и профиль GitHub skippingclass.')
    subsection(d, 7, 1)
    body(d,'Сервер инициализирует схему и демонстрационные данные при запуске. Для создания назначения клиент передает идентификаторы строки плана и преподавателя, часы теории и практики. Сервер определяет год, семестр и дисциплину по плану, затем повторно проверяет свободный объем внутри транзакции.')
    figure(d,'screenshots/network_client.png','Общий план в сетевом клиенте',16)
    body(d,'Сетевой клиент показывает карточки и позволяет изменять план и назначения. Ведомость XLSX или PDF формируется на стороне сервера и сохраняется по выбранному пути. Роль методиста доступна для чтения и экспорта. Сервер проверяет права даже при прямом вызове маршрута.')
    body(d,'Изменения журналируются с идентификатором пользователя, видом операции и записью. Пароли и токены не включаются в сообщения журнала. Сессия действует один час. Выход, смена логина или пароля завершают сессию. При каждом запросе проверяется текущая роль учетной записи.')
    subsection(d, 7, 2)
    body(d,'Среда разработки и проверки — Linux, Python, PyQt6, SQLAlchemy, FastAPI, Uvicorn и unittest. Исходные данные размещены в SQLite. В учебном стенде сервер и клиент запущены как два отдельных процесса на одном компьютере через loopback.')
    listing(d, [
        'создать виртуальное окружение и установить зависимости командой python -m pip install -r requirements.txt',
        'создать каталог tmp и задать COLLEGE_DB_URL=sqlite:///tmp/demo-defense.db для отдельной базы стенда',
        'запустить python -m uvicorn server.api:app --host 127.0.0.1 --port 8000',
        'в другом терминале выполнить python run_client.py и войти под демонстрационной ролью',
        'проверить /api/v1/health и /openapi.json по адресу 127.0.0.1:8000',
    ])
    body(d,'Сетевой сервер хранит сессии в памяти одного процесса. После перезапуска пользователь входит заново. Подключение с другого компьютера предусматривает HTTPS, смену учебных паролей и настройку доступа. Для приема работы достаточно локального запуска с демонстрационными данными. Подробности приведены в docs/Защита.md.')
    body(d,'Готовый архив для Windows x64 содержит Python и библиотеки. run.bat открывает автономное приложение, run-network.bat запускает сервер и сетевой клиент с отдельной демонстрационной базой.')
    heading(d,CHAPTERS[8])
    body(d,f'Проверка выполнена средствами unittest [2] на временных SQLite-базах, в том числе на отдельной модели прежней схемы. Окна Qt запускались в offscreen-режиме. Всего выполнено {TESTS["total"]} проверок. Непройденных {TESTS["failures"]}, ошибок {TESTS["errors"]}. Полный протокол находится в docs/TEST_REPORT.md и docs/test_results.json [7].')
    body(d,'Проверены корректный и ошибочный ввод, границы ставки, отмена изменений и конкурирующая запись. Представительные тест-кейсы приведены в таблицах 12 и 13. Для каждого случая создаются независимые данные.')
    table(d,'Проверка ввода и распределения',['Код','Сценарий','Данные','Ожидание и фактический результат'],[
      ('Т01','Раздельные ФИО','Евполов / Владислав / Игоревич','сохранены три поля и полное представление'),
      ('Т02','Точный дубликат','тот же ФИО с другим регистром','сохранение отклонено'),
      ('Т03','Опечатка','Евпалов вместо Евполов','без подтверждения отказ; после подтверждения разрешено'),
      ('Т04','Телефон','неполный +7 (701) 12','номер не принимается'),
      ('Т05','Сортировка','стаж 9, 10, 23','порядок 9, 10, 23 и обратный'),
      ('Т06','Ставка','720 и 721 ч.; отдельно часы другого года','порог и годовой период соблюдены'),
      ('Т07','Теория','остаток 10, запрос 11 ч.','отказ; прежний остаток сохранен'),
      ('Т08','Практика','остаток 0, запрос 1 ч.','отказ без изменения назначения')],[1.1,3.1,5.1,7.2])
    page(d)
    table(d,'Проверка изменений и сохранности',['Код','Сценарий','Данные','Ожидание и фактический результат'],[
      ('Т09','Уменьшение','50/100 → 20/30 ч.','возвращено 30/70 ч.; пройдено'),
      ('Т10','Перенос','другой план и преподаватель','старый остаток восстановлен, новый уменьшен; пройдено'),
      ('Т11','Отмена','удаление назначения','все часы освобождены; пройдено'),
      ('Т12','Сокращение плана','ниже назначенного объема','изменение отклонено; пройдено'),
      ('Т13','Конкуренция','два потока на один остаток','успешна одна операция; пройдено'),
      ('Т14','Экспорт','год 2026-2027, семестр 2, один преподаватель','в Excel и PDF только выбранные записи; пройдено'),
      ('Т15','Поврежденная копия','несуществующий teacher_id','восстановление отменено; данные сохранены; пройдено'),
      ('Т16','Повтор миграции','два запуска init_db','ID, ФИО, часы сохранены; повторных планов нет; пройдено')],[1.1,3.1,5.1,7.2])
    body(d,'Полный набор запускается командой python scripts/check_project.py. Протокол содержит дату, число проверок и результат каждого теста. Также поддерживается python -m unittest discover -s tests -v. Изменение бизнес-правил сопровождается изменением сценариев и критериев приемки.')
    page(d)
    body(d,'В процессе проверки найдены проблемы, перечисленные в таблице 14. После исправления повторно выполнены соответствующие сценарии и полный набор.')
    table(d,'Проблемы и исправления',['Проблема','Исправление','Повторная проверка'],[
      ('Неполный телефон считался допустимым','маска обязательных цифр 9 вместо необязательных 0','test_dialogs_and_phone_mask — пройден'),
      ('В PDF отсутствовала кириллица','DejaVu Sans включен в проект и встраивается в PDF','test_excel_pdf_export_matches_filters — пройден'),
      ('Числа сортировались как текст','числовой DisplayRole и числовые ключи сервиса','test_numeric_sort и test_table_numbers_sort_numerically — пройдены'),
      ('Светлая строка на темном фоне','задан темный alternate-background-color','актуальные скриншоты просмотрены')],[4.2,6.3,6])
    body(d,'Комплексная проверка запускает Uvicorn в отдельном процессе, открывает Qt-клиент, выполняет вход, читает справочники, создает строку плана через HTTP и проверяет ее в таблице после обновления. Интеграционные проверки API отдельно подтверждают права, обновление старого хэша, отказ при превышении, возврат часов и оба формата экспорта.')
    body(d,'Прогон подтверждает сценарии Linux и SQLite. Для PostgreSQL, Windows и macOS, длительной многопользовательской работы и больших объемов данных требуется отдельная приемка.')
    heading(d,CHAPTERS[9])
    body(d,'Результат сопоставлен с перечнем функций, автоматическими проверками и актуальными экранными формами. Подтверждения приведены в таблице 15.')
    table(d,'Соответствие требованиям',['Требование','Результат','Подтверждение'],[
      ('Раздельные ФИО и защита от дублей','реализовано','Т01-Т04 и форма преподавателя'),
      ('Сортировка и ставка за год','реализовано','Т05-Т06 и фильтры'),
      ('Общий план, теория и практика','реализовано','Т07-Т08 и таблица остатков'),
      ('Возврат и перенос часов','реализовано','Т09-Т13 и сервис распределения'),
      ('Семестр и преподаватель в отчете','реализовано','Т14, предпросмотр и экспорт'),
      ('Обновление и резервные копии','реализовано','Т15-Т16 и копии обоих форматов'),
      ('Справка и документация','подготовлено','руководства, презентация и материалы защиты'),
      ('Серверная проверка прав','реализовано','HTTP 401 и 403 в test_api.py'),
      ('Сетевой клиент и запуск','реализовано','test_network_client.py и демонстрационный стенд')],[5.4,2.7,8.4])
    body(d,'Практический результат — проверяемое происхождение каждого назначения. Общий план ограничивает распределяемый объем, а сохранение проверяет остатки обоих видов занятий. Это устраняет подтвержденный класс ошибок превышения плана в испытанных сценариях.')
    body(d,'Материалы для демонстрации включают графические схемы, руководства, контракт OpenAPI и презентацию. Командная работа описана как порядок дальнейшего совместного ведения Git. Доказательства фактического взаимного просмотра кода и слияния веток участников отсутствуют.')
    heading(d,CHAPTERS[10])
    for text in [
      'Разработана система учета преподавателей и учебной нагрузки для Высшего колледжа «ASTANA POLYTECHNIC». Реализованы раздельные ФИО, маски, проверки контактов, обнаружение повторных карточек, поиск и выбор порядка сортировки.',
      'Общий план формируется по годам, семестрам, группам и дисциплинам. Назначения ограничены остатками теории и практики. Уменьшение, перенос и отмена возвращают часы в соответствующий план. Годовая нагрузка сравнивается с 720 часами, недельный показатель рассчитывается по числу недель.',
      f'Сервер и клиент обмениваются данными по REST API. Excel и PDF формируются по фильтрам предпросмотра. Пройдено {TESTS["total"]} автоматических проверок. Подготовлены протокол, диаграммы, инструкции и презентация.',
      'Дальнейшее развитие предусматривает отдельную приемку PostgreSQL, сетевой стенд с HTTPS, общее хранилище сессий для нескольких процессов и расширение настроек сетевого клиента.'
    ]:body(d,text)
    heading(d,CHAPTERS[11])
    for text in [
      '1. Методические указания к курсовому проекту по дисциплине «Алгоритмизация и программирование». Высший колледж «ASTANA POLYTECHNIC». Астана, 2026. Файл docs/reference/Методические_указания.pdf.',
      '2. Python Software Foundation. unittest. https://docs.python.org/3/library/unittest.html (дата обращения 10.11.2026).',
      '3. SQLAlchemy. Transactions and Connection Management. https://docs.sqlalchemy.org/en/20/orm/session_transaction.html (дата обращения 10.11.2026).',
      '4. The Qt Company. QLineEdit inputMask. https://doc.qt.io/qt-6/qlineedit.html#inputMask-prop (дата обращения 10.11.2026).',
      '5. DejaVu Fonts. License. https://dejavu-fonts.github.io/License.html (дата обращения 10.11.2026).',
      '6. Евполов Владислав. Исходные тексты проекта, версия 2.1. Каталоги database, services, ui, server и tests. GitHub skippingclass.',
      '7. Протокол автоматической проверки. docs/TEST_REPORT.md и docs/test_results.json.',
      '8. Фирма «1С». Зарплата и кадры образовательной организации. https://solutions.1c.ru/catalog/edu-budghrm/features (дата обращения 18.11.2026).',
      '9. Корпорация «Галактика». Решения для высших учебных заведений. https://galaktika.ru/docs/Galaktika_VUZ.pdf (дата обращения 18.11.2026).',
      '10. FastAPI. Metadata and Docs URLs. https://fastapi.tiangolo.com/tutorial/metadata/ (дата обращения 18.11.2026).'
    ]:
        body(d,text).alignment = WD_ALIGN_PARAGRAPH.LEFT
    heading(d,CHAPTERS[12])
    for text in [
      'Приложение А — руководство пользователя. Файл docs/Руководство_пользователя.pdf содержит запуск, вход, карточки, общий план, назначения, возврат часов, фильтры, экспорт и примеры экранов.',
      'Приложение Б — руководство разработчика. Файл docs/Руководство_разработчика.pdf описывает окружение, модули, схему, миграцию, настройки, тестирование и изменение проекта.',
      'Приложение В — требования к ПО. Файл docs/Требования_к_ПО.pdf определяет функции, ограничения данных, окружение и критерии приемки.',
      'Приложение Г — спецификация и проверка. Контракт описан в docs/API.md и docs/openapi.json. Тесты находятся в tests, протокол — в docs/TEST_REPORT.md. Сценарий демонстрации и подтверждения требований приведены в docs/Защита.md.',
      'Автор — Евполов Владислав, группа П-24-67Б, Высший колледж «ASTANA POLYTECHNIC». GitHub https://github.com/skippingclass.'
    ]:body(d,text)
    table(d,'Календарный план подготовки проекта',['Неделя','Работы','Контрольный результат'],[
        ('1','Предметная область, аналоги, границы, роли и требования','Раздел 1, сравнение решений и матрица прав'),
        ('2','Архитектура, БД, контракт, эскизы и миграция','Раздел 2, ER-диаграмма, OpenAPI и прототип навигации'),
        ('3','Разработка сервера, форм и интеграция','Раздел 3, работающий клиент и сервер на демонстрационной базе'),
        ('4','Проверки, локальное развертывание и подготовка защиты','Протокол, инструкции, записка, презентация и сценарий демонстрации'),
    ],[2,7.2,7.3])
    body(d,'Календарный план соотнесен с этапами методических указаний [1]. Ключевые фрагменты реализации приведены в листингах 1 и 2 приложения Д.')
    code_listing(d, 1, 'Проверка пароля', 'services/passwords.py',
                 ['_derive', 'hash_password', 'verify_password'])
    code_listing(d, 2, 'Транзакция назначения часов', 'services/workload_service.py',
                 ['_save_assignment'])
    d.save(COURSE);(TMP/'chapter_titles.json').write_text(json.dumps(CHAPTERS,ensure_ascii=False),encoding='utf-8')


def guide(filename,title,sections):
    global FIGURE,TABLE
    FIGURE=TABLE=0;doc=new_guide(title)
    for index,(name,paragraphs,pictures,items) in enumerate(sections):
        heading(doc,name,index>0)
        for text in paragraphs:
            body(doc,text)
        if items:
            listing(doc,items)
        for file,caption,width in pictures:
            figure(doc,file,caption,width)
    GUIDE_WORD.mkdir(parents=True, exist_ok=True)
    doc.save(GUIDE_WORD/(filename+'.docx'))


def build_guides():
    guide('Руководство_пользователя','Руководство пользователя',[
      ('1 Назначение и запуск',[
       'Программа учитывает преподавателей и распределяет теоретические и практические часы из общего плана. Сначала заполняются справочники и карточки, затем создается план и назначаются часы преподавателям.',
       'В Windows распакуйте готовый архив и дважды щелкните run.bat. Python входит в архив. При запуске исходников из репозитория установите Python 3.14 и откройте тот же файл. Локальная база SQLite создается автоматически.',
       'При первом запуске создаются демонстрационные записи. Администратор входит как admin / admin123, заведующий кафедрой — operator / operator123, методист — methodist / methodist123. Перед использованием реальных данных администратор должен сменить демонстрационные пароли.',
       'Администратор управляет пользователями и копиями. Заведующий кафедрой изменяет карточки, справочники и нагрузку. Методист просматривает данные и экспортирует отчеты.',
       'Файл run-network.bat открывает сетевой клиент вместе с локальным сервером. В этом режиме можно просматривать карточки, редактировать план и назначения и выгружать ведомости из отдельной демонстрационной базы.'
      ],[('screenshots/login_window.png','Окно входа',6)],[]),
      ('2 Преподаватели',[
       'На вкладке «Преподаватели» нажмите «Добавить преподавателя». Заполните фамилию и имя раздельно, отчество при наличии. Выберите кафедру, категорию, стаж и статус. Контакты и дата рождения необязательны, но заполненные значения должны быть корректными.',
       'Телефон вводится по маске +7 (999) 999-99-99. Введите все десять цифр после +7 либо очистите поле. Почта имеет формат name@example.kz. Стаж допускается от 0 до 70 лет.',
       'Тот же ФИО, телефон или e-mail блокирует повторное сохранение. При похожем ФИО проверьте опечатку. Ответ «Да» допускается, если это другой человек; ответ «Нет» возвращает к исправлению формы.',
       'Для изменения выберите строку и нажмите «Редактировать». «Карточка» открывает нагрузку по году и семестру. Поиск не учитывает регистр кириллицы. Выберите сортировку по ФИО, стажу, кафедре или часам и ее направление. Фильтр ставки считает 720 часов за выбранный учебный год.'
      ],[('screenshots/teacher_form.png','Форма преподавателя',12)],[]),
      ('3 Общий план',[
       'Откройте «Учебная нагрузка» и «Общий план часов», нажмите «Добавить в общий план». Укажите год в формате 2026-2027, семестр 1 либо 2, группу, дисциплину и число учебных недель. Введите общий объем теории и практики для группы за семестр.',
       'Учебный пример для П-24-67Б по программированию — первый семестр 2026-2027 года, 360 часов теории и 540 практики, 18 недель. Общий объем составляет 900 часов. Замените эти значения фактическим планом колледжа.',
       'Таблица показывает плановые и свободные часы. Повторное сочетание года, семестра, группы и дисциплины не допускается. Для изменения выберите строку и нажмите «Редактировать». Нельзя уменьшить план ниже назначенного объема или удалить его с действующими назначениями. Перед сменой дисциплины отмените назначения.'
      ],[('screenshots/workload_pool.png','Общий план и остатки',16)],[]),
      ('4 Назначение и возврат часов',[
       'Выберите строку плана и нажмите «Назначить преподавателю». Проверьте год, семестр и план, выберите преподавателя и часы теории и практики. Доступный остаток отображается над полями.',
       'Если из плана 360/540 назначить первому преподавателю 180/180, останется 180/360. После назначения второму 90/180 свободно 90/180. Среднее число часов в неделю для первого назначения равно 360 / 18 = 20. Это средний показатель, а не расписание.',
       'Для возврата части часов на странице «Назначения преподавателям» выберите запись и уменьшите ее объем. Для возврата всех часов используйте «Удалить / вернуть часы». Чтобы передать объем другому преподавателю, измените преподавателя в форме.',
       'Для переноса в другой план измените год, семестр и строку плана. Успешное сохранение освобождает старый план и уменьшает новый. Если нового остатка недостаточно, прежнее назначение сохраняется.',
       'При нехватке часов уменьшите соответствующий вид занятий либо уточните общий план. Свободная практика не заменяет теорию. Если назначение из выбранного плана у преподавателя уже есть, отредактируйте существующее.'
      ],[('screenshots/workload_form.png','Назначение и часы в неделю',15)],[]),
      ('5 Выборки и экспорт',[
       'На вкладке нагрузки выберите год, семестр, кафедру и преподавателя. Последний фильтр изменяет назначения; общий план продолжает показывать строки всей выбранной кафедры за период. В личной карточке также доступны год и семестр.',
       'На вкладке «Отчеты и экспорт» выберите кадровый отчет, ведомость нагрузки либо статистику. Для ведомости задайте год, семестр и преподавателя, сформируйте таблицу и сохраните Excel либо PDF.',
       'Экспорт учитывает параметры предпросмотра. Ведомость содержит год, семестр, группу, преподавателя, дисциплину, теорию, практику, итог и часы в неделю. Excel на вкладке нагрузки также учитывает выбранного преподавателя.',
       'Фильтр «Не указан (архив)» показывает прежние назначения с неизвестным семестром. Уточните семестр, группу и число недель архивного плана перед подготовкой итоговых документов.'
      ],[('screenshots/workload_report.png','Ведомость и фильтры периода',16)],[]),
      ('6 Копии и сообщения',[
       'Администратор создает JSON-копию через меню «База данных». Она включает семь таблиц. Для восстановления выберите копию и подтвердите замену данных. Ошибочные связи или превышение плана отменяют восстановление с сохранением прежнего состояния.',
       'При первом открытии старой SQLite-базы создается .before-v2.bak. Старые назначения сохраняются в архиве. До уточнения число недель равно 18, поэтому недельные показатели архива требуют проверки.',
       'Похожая карточка требует проверки ФИО. Дубликат плана означает, что строка уже существует. Отказ сократить план требует сначала уменьшить назначения. При ошибке подключения проверьте тип базы, сервер и реквизиты.',
       'Руководства открываются из меню «Справка». В окне «О программе» указаны Евполов Владислав, П-24-67Б, Высший колледж «ASTANA POLYTECHNIC» и GitHub skippingclass.'
      ],[],[])
    ])
    guide('Руководство_разработчика','Руководство разработчика',[
      ('1 Назначение и установка',[
       'Проект — настольная система кадрового учета и распределения нагрузки. Уровни программы расположены в ui, services и database. Запуск требует Python 3.10 или новее и requirements.txt. Для Word-документов и проверки экспорта установите также requirements-dev.txt.',
       'Создайте окружение python -m venv .venv, активируйте его, выполните python -m pip install -r requirements-dev.txt и python run.py. Для локальной работы используется SQLite. Параметры находятся в settings.json, локальные данные — в data/college_teachers.db.',
       'PostgreSQL выбирается в диалоге подключения. Сервер, база и права на создание таблиц подготавливаются отдельно. Встроенный локальный снимок старой базы относится только к SQLite.'
      ],[],[]),
      ('2 Модули и архитектура',[
       'config.py содержит константы и чтение настроек, run.py — запуск Qt и базы. models.py определяет семь моделей, connection.py — движок и инициализацию, migrations.py — совместимость старой схемы, backup.py — JSON-копии.',
       'teacher_service.py выполняет нормализацию, проверку карточек, поиск, сравнение похожих записей и сортировку. workload_service.py управляет планом и транзакциями распределения. report_service.py предоставляет единые наборы данных для предпросмотра и форматов выгрузки.',
       'TeacherDialog содержит раздельные ФИО. PoolDialog и WorkloadDialog — общий план и назначения. WorkloadTab показывает две таблицы, ReportsTab передает одинаковые фильтры предпросмотру и экспорту. MainWindow объединяет вкладки и открывает руководства из docs.',
       'Сервисы возвращают статус и сообщение. Формы не должны записывать ORM-объекты напрямую, поскольку проверки остатков, дубликатов и синхронизация периода находятся в сервисах.'
      ],[('diagrams/architecture.png','Архитектура программы',15)],[]),
      ('3 Данные и транзакции',[
       'Модели — Role, User, Department, Teacher, Discipline, WorkloadPool и TeacherWorkload. Команда python scripts/export_schema.py сохраняет фактические поля в docs/schema.json. Строка плана определяется дисциплиной, группой, годом и семестром.',
       'Остаток каждого вида часов вычисляется как план минус сумма назначений. Отдельный счетчик остатка не хранится. Поэтому отмена назначения освобождает часы через удаление записи распределения.',
       'Уникальны год + семестр + группа + дисциплина и pool_id + teacher_id. Год, семестр и дисциплина назначения копируются из плана и синхронизируются при изменении периода. Проверка остатка выполняется внутри транзакции.',
       'SQLite использует BEGIN IMMEDIATE, PostgreSQL — FOR UPDATE. Перенос блокирует оба плана в порядке ID. Нельзя заменять проверку внутри транзакции проверкой только в форме.',
       'Модуль server/api.py проверяет роли, валидирует запросы и передает их в сервисы. Вход выдает сессию на один час. Пароли хранятся в формате scrypt с солью. Записи SHA-256 обновляются после успешного входа. Контракт публикуется по /openapi.json и описан в docs/API.md.'
      ],[('diagrams/erd.png','Семь сущностей базы',12)],[]),
      ('4 Миграция и копии',[
       'init_db создает отсутствующие таблицы, добавляет новые столбцы старой схемы, заполняет начальные данные и преобразует записи. ФИО разделяется по первым двум пробелам; составные имена после миграции необходимо проверить.',
       'Перед обновлением старой SQLite создается .before-v2.bak через sqlite3.backup. Каждое прежнее назначение получает архивный план, семестр 0 и начальное число недель 18. Повторная инициализация не создает дубликаты.',
       'JSON версии 2 хранит семь таблиц. Создание копии использует временный файл и атомарную замену. Старые копии преобразуются при восстановлении. Проверка внешних ключей, баланса, удаление и вставка выполняются одной транзакцией. Промежуточный commit нарушит атомарность.',
       'Для отката закройте приложение, сохраните текущую SQLite отдельно и верните .before-v2.bak вместе с совместимой версией программы. Для PostgreSQL используйте штатную серверную копию до обновления.'
      ],[],[]),
      ('5 Проверки и документы',[
       f'Команда python scripts/check_project.py выполняет {TESTS["total"]} проверок и обновляет docs/TEST_REPORT.md и docs/test_results.json. Используются временные SQLite-базы, отдельная модель старой схемы, HTTP API и Qt offscreen. PostgreSQL и другие ОС требуют отдельного прогона.',
       'Проверяются ФИО, контакты, сортировка, кириллица, порог 720, независимые остатки, редактирование, перенос, конкурирующая запись, копии обоих форматов, откат ошибки восстановления, миграция и экспорт.',
       'Диаграммы создает scripts/build_diagrams.py, снимки на одноразовой базе — scripts/capture_screenshots.py. До сборки Word обновите схему и протокол. Скрипт scripts/build_documents.py использует шаблон docs/templates/course.docx. Промежуточные Word-файлы руководств создаются в tmp/documents/guides.',
       'После сборки преобразуйте DOCX в PDF через LibreOffice. Для записки обновите страницы содержания скриптом scripts/update_contents.py по первому PDF и преобразуйте документ повторно. Итоговые материалы помещаются в docs.',
       'Для упаковки Windows x64 выполните python scripts/package_windows.py. Архив проверяет контрольную сумму Python для встраивания и включает библиотеки и материалы для защиты. ZIP сохраняется в dist.',
       'assets/fonts/DejaVuSans.ttf обеспечивает кириллицу PDF. Лицензия находится в assets/fonts/LICENSE.txt. Сохраняйте оба файла при упаковке приложения.'
      ],[],[]),
      ('6 Изменение программы',[
       'Новое поле требует согласованного обновления ORM, миграции, JSON-копий, форм и отчетов. Правило, влияющее на часы, сопровождается проверкой успеха, границы и отказа без изменения прежних данных.',
       'Изменение сравнения ФИО проверяется на кириллице, пробелах, составных фамилиях и подтверждении похожих записей. Изменение ориентира ставки согласуется с сервисами, подписями и приемочными тестами.',
       'После изменения выполните проверки и обновите изображения и документы. Не заявляйте сетевые гарантии или показатели производительности только по локальной SQLite. Автор — Евполов Владислав, П-24-67Б, GitHub skippingclass.'
      ],[],[])
    ])
    guide('Требования_к_ПО','Требования к программному обеспечению',[
      ('1 Назначение и границы',[
       'Система предназначена для учета преподавателей Высшего колледжа «ASTANA POLYTECHNIC» и распределения часов из общего плана по группам, годам и семестрам. Пользователи — администратор, заведующий кафедрой и методист. Требования соответствуют версии 2.1.',
       'В область проекта входят карточки, справочники, общий план, назначения, выборки, отчеты и резервные копии. Расписание по дням, зарплата и аудитории не входят. Ориентир ставки задан в проекте и равен 720 часам за учебный год.'
      ],[],[]),
      ('2 Функциональные требования',[
       'Требования проверяются через действия пользователя и сервисные сценарии. Отрицательная операция завершается понятным сообщением и сохраняет прежние данные.'
      ],[],[f'{code} {name.lower()} — {criterion}' for code,name,criterion in REQUIREMENTS]),
      ('3 Ограничения данных',[
       'Фамилия и имя обязательны, отчество допускается пустым. Разрешены буквы, пробелы, дефис и апостроф. Каждая часть не длиннее 100 символов, полное ФИО не длиннее 200. Стаж от 0 до 70 лет, дата рождения не позже текущей даты. Заполненный телефон содержит 11 цифр с кодом 7 либо 8; e-mail имеет допустимую структуру.',
       'Год задается двумя последовательными годами YYYY-YYYY. Новый план имеет семестр 1 либо 2, значение 0 используется для старого архива. Группа обязательна, не длиннее 100 символов. Учебных недель от 1 до 52.',
       'Часы теории и практики — целые неотрицательные значения с положительной суммой. План уникален по году, семестру, группе и дисциплине. Назначение уникально по плану и преподавателю. Остатки каждого вида часов не могут быть отрицательными.',
       'Уменьшение освобождает разницу, отмена или удаление карточки — весь назначенный объем. Период назначений синхронизируется с планом. Нельзя удалить используемый план или уменьшить его ниже распределенного объема.',
       'Недельный показатель равен итогу назначения, деленному на число недель, и отображается с двумя знаками после запятой. Фильтр ставки суммирует только выбранный учебный год; значения меньше, ровно и больше 720 различаются без часов других лет.'
      ],[],[]),
      ('4 Окружение и качество',[
       'Версии зависимостей приведены в requirements.txt. Автономный режим использует SQLite или PostgreSQL. Сетевой стенд использует FastAPI, Uvicorn и SQLite на стороне сервера. При малой ширине окна доступна горизонтальная прокрутка таблиц.',
       'Операции должны сохранять согласованность транзакцией и показывать причину отказа. Повторная миграция не должна менять ID исходных записей или создавать повторный план. При конкурирующих назначениях нельзя превышать доступный объем.',
       'Предпросмотр и выгрузка используют одинаковые фильтры. PDF содержит читаемую кириллицу и таблицы в пределах страницы. В Excel часы остаются числами, заголовки и итоги соответствуют выбранным строкам.',
       'Резервная копия включает семь таблиц и поддерживает старый формат. Ошибка восстановления откатывается. Методист может просматривать и экспортировать данные. Сервер отклоняет запросы записи с ролью методиста.'
      ],[],[]),
      ('5 Приемка и комплект поставки',[
       f'Локальная приемка запускается python scripts/check_project.py. Протокол содержит {TESTS["total"]} проверок. Непройденных {TESTS["failures"]}, ошибок {TESTS["errors"]}. Для PostgreSQL и целевых рабочих мест предусмотрена отдельная приемка.',
       'Для карточек проверяются отдельные поля, точный дубликат и опечатка. Для нагрузки — два независимых остатка, порог 720, уменьшение, отмена и перенос. Для отчетов — совпадение года, семестра и преподавателя на экране и в выгрузке. Для сохранности — повтор миграции и откат ошибочной копии.',
       'Поставка включает код, зависимости, инструкции запуска, протокол, записку, руководства пользователя и разработчика и требования к ПО. Рисунки отражают фактический интерфейс и схему семи таблиц. Автор — Евполов Владислав, группа П-24-67Б, GitHub skippingclass.'
      ],[],[])
    ])


if __name__=='__main__':
    assert TESTS['failures']==0 and TESTS['errors']==0,'Сначала исправьте проверки'
    build_course()
    build_guides()
    print('Сохранены записка с титулом и три сопроводительных документа')
