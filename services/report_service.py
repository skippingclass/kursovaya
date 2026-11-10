"""Отчеты и экспорт с едиными данными для предпросмотра, Excel и PDF."""
import os
from datetime import datetime
from xml.sax.saxutils import escape
from pathlib import Path
import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from config import COLLEGE_NAME
from services.workload_service import get_workloads, semester_label
from services.teacher_service import get_teachers
from services.department_service import get_departments


def register_cyrillic_font():
    candidates = [Path(__file__).resolve().parents[1] / "assets/fonts/DejaVuSans.ttf",
        Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts/arial.ttf",
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
        Path("/usr/share/fonts/TTF/DejaVuSans.ttf"), Path("/usr/share/fonts/noto/NotoSans-Regular.ttf"),
        Path("/System/Library/Fonts/Supplemental/Arial.ttf")]
    try:
        import reportlab
        candidates.append(Path(reportlab.__file__).parent / "fonts/Vera.ttf")
    except ImportError:
        pass
    for path in candidates:
        if path.exists():
            pdfmetrics.registerFont(TTFont("CyrillicFont", str(path)))
            return "CyrillicFont"
    raise RuntimeError("Не найден шрифт для PDF. Установите DejaVu Sans или Arial.")


CYRILLIC_FONT = register_cyrillic_font()
STAFF_HEADERS = ["№", "ФИО преподавателя", "Кафедра", "Категория", "Стаж", "Телефон", "E-mail", "Статус", "Часы"]
STAFF_KEYS = ["num", "full_name", "department", "qualification", "experience", "phone", "email", "status", "total_hours"]
WORKLOAD_HEADERS = ["№", "Учебный год", "Семестр", "Группа", "Преподаватель", "Кафедра", "Код", "Дисциплина", "Теория, ч.", "Практика, ч.", "Всего, ч.", "Часов в неделю"]
WORKLOAD_KEYS = ["num", "academic_year", "semester", "group_name", "teacher", "department", "discipline_code", "discipline_name", "hours_lecture", "hours_practice", "total_hours", "hours_per_week"]
STATS_HEADERS = ["Кафедра", "Преподавателей", "Исследователи", "Эксперты", "Модераторы", "Высшая", "Первая / вторая", "Специалисты", "Часы"]


def get_teachers_report_data(department_id=None, **filters):
    return [dict(num=i, full_name=t.full_name, department=t.department.name if t.department else "",
        qualification=t.qualification or "Без категории", experience=t.experience or 0,
        phone=t.phone or "", email=t.email or "", status=t.status or "работает", total_hours=t.period_hours)
        for i, t in enumerate(get_teachers(department_id=department_id, **filters), 1)]


def get_workload_report_data(academic_year=None, department_id=None, semester=None, teacher_id=None):
    return [dict(num=i, academic_year=w.academic_year, semester=semester_label(w.semester),
        group_name=w.pool.group_name if w.pool else "Не указана", teacher=w.teacher.full_name,
        department=w.teacher.department.name, discipline_code=w.discipline.code, discipline_name=w.discipline.name,
        hours_lecture=w.hours_lecture, hours_practice=w.hours_practice, total_hours=w.total_hours,
        hours_per_week=w.hours_per_week)
        for i, w in enumerate(get_workloads(academic_year, teacher_id, department_id, semester), 1)]


def get_stats_report_data(department_id=None, academic_year=None):
    teachers = get_teachers(department_id=department_id, academic_year=academic_year)
    rows = []
    for dept in get_departments():
        if department_id and dept.id != department_id:
            continue
        group = [t for t in teachers if t.department_id == dept.id]
        rows.append([dept.name, len(group), *[sum(t.qualification in qualifications for t in group) for qualifications in
            [("Педагог-исследователь",), ("Педагог-эксперт",), ("Педагог-модератор",),
             ("Высшая категория",), ("Первая категория", "Вторая категория"), ("Специалист",)]],
            sum(t.period_hours for t in group)])
    rows.append(["Итого", *[sum(row[i] for row in rows) for i in range(1, 9)]])
    return rows


def _period(year=None, semester=None):
    return f"Учебный год: {year or 'все'}; семестр: {semester_label(semester) if semester is not None else 'все'}"


def _excel(filepath, title, subtitle, headers, rows, totals=None):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Отчет"
    count = len(headers)
    for r, text in enumerate((COLLEGE_NAME, title, subtitle), 1):
        ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=count)
        cell = ws.cell(r, 1, text)
        cell.font = Font(name="Calibri", size=14 if r == 1 else 11, bold=r < 3)
        cell.alignment = Alignment(horizontal="center", wrap_text=True)
        ws.row_dimensions[r].height = 30
    border = Border(**{s: Side(style="thin", color="D9D9D9") for s in ("left", "right", "top", "bottom")})
    for r, row in enumerate([headers, *rows], 5):
        for c, value in enumerate(row, 1):
            cell = ws.cell(r, c, value)
            if isinstance(value, str):
                cell.data_type = "s"
            cell.alignment = Alignment(vertical="center", wrap_text=True)
            cell.border = border
            if r == 5:
                cell.fill = PatternFill("solid", fgColor="1F4E79")
                cell.font = Font(bold=True, color="FFFFFF")
            elif r % 2 == 0:
                cell.fill = PatternFill("solid", fgColor="F2F5F8")
        ws.row_dimensions[r].height = 32 if r == 5 else 42
    if totals:
        r = 6 + len(rows)
        ws.cell(r, 1, "Итого")
        for index, value in totals.items():
            ws.cell(r, index + 1, value).font = Font(bold=True)
    for c in range(1, count + 1):
        values = [str(row[c-1]) for row in [headers, *rows]]
        ws.column_dimensions[get_column_letter(c)].width = min(44, max(12, max(map(len, values), default=10) + 2))
    ws.freeze_panes = "A6"
    ws.auto_filter.ref = f"A5:{get_column_letter(count)}{max(5, 5+len(rows))}"
    ws.print_title_rows = "1:5"
    ws.page_setup.orientation = "landscape"
    ws.page_setup.paperSize = ws.PAPERSIZE_A4
    ws.page_setup.fitToWidth = 1
    ws.sheet_properties.pageSetUpPr.fitToPage = True
    wb.save(filepath)


def _pdf(filepath, title, subtitle, headers, rows, weights):
    doc = SimpleDocTemplate(str(filepath), pagesize=landscape(A4), leftMargin=24, rightMargin=24,
                            topMargin=24, bottomMargin=28)
    normal = ParagraphStyle("cell", fontName=CYRILLIC_FONT, fontSize=7, leading=9)
    heading = ParagraphStyle("heading", parent=normal, textColor=colors.white, alignment=1)
    title_style = ParagraphStyle("title", parent=normal, fontSize=13, leading=17, alignment=1, spaceAfter=8)
    subtitle_style = ParagraphStyle("subtitle", parent=normal, fontSize=9, leading=12, alignment=1)
    elements = [Paragraph(escape(COLLEGE_NAME), title_style), Paragraph(escape(title), subtitle_style),
                Paragraph(escape(subtitle), subtitle_style), Spacer(1, 14)]
    content = [[Paragraph(escape(str(value)), heading if index == 0 else normal) for value in row]
               for index, row in enumerate([headers, *rows])]
    widths = [doc.width * weight / sum(weights) for weight in weights]
    table = Table(content, colWidths=widths, repeatRows=1, hAlign="LEFT")
    table.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F4E79")),
        ("GRID", (0, 0), (-1, -1), .4, colors.HexColor("#D9D9D9")), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F2F5F8")]),
        ("LEFTPADDING", (0, 0), (-1, -1), 5), ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6)]))
    elements.append(table)
    def footer(canvas, document):
        canvas.setFont(CYRILLIC_FONT, 8)
        canvas.drawRightString(document.pagesize[0] - 24, 14, f"{document.page}")
    doc.build(elements, onFirstPage=footer, onLaterPages=footer)


def _export(action, filepath):
    try:
        action()
        return True, f"Отчет сохранен: {filepath}"
    except Exception as exc:
        return False, f"Ошибка экспорта: {exc}"


def export_teachers_to_excel(filepath, department_id=None, **filters):
    def write():
        data = get_teachers_report_data(department_id, **filters)
        _excel(filepath, "Кадровый состав преподавателей", _period(filters.get("academic_year")), STAFF_HEADERS,
               [[d[k] for k in STAFF_KEYS] for d in data], {8: sum(d["total_hours"] for d in data)})
    return _export(write, filepath)


def export_teachers_to_pdf(filepath, department_id=None, **filters):
    return _export(lambda: _pdf(filepath, "Кадровый состав преподавателей", _period(filters.get("academic_year")),
        STAFF_HEADERS, [[d[k] for k in STAFF_KEYS] for d in get_teachers_report_data(department_id, **filters)],
        [3, 16, 17, 13, 5, 13, 15, 9, 5]), filepath)


def export_workload_to_excel(filepath, academic_year=None, department_id=None, semester=None, teacher_id=None):
    def write():
        data = get_workload_report_data(academic_year, department_id, semester, teacher_id)
        _excel(filepath, "Ведомость распределения учебной нагрузки", _period(academic_year, semester), WORKLOAD_HEADERS,
               [[d[k] for k in WORKLOAD_KEYS] for d in data],
               {8: sum(d["hours_lecture"] for d in data), 9: sum(d["hours_practice"] for d in data),
                10: sum(d["total_hours"] for d in data)})
    return _export(write, filepath)


def export_workload_to_pdf(filepath, academic_year=None, department_id=None, semester=None, teacher_id=None):
    return _export(lambda: _pdf(filepath, "Ведомость распределения учебной нагрузки", _period(academic_year, semester),
        WORKLOAD_HEADERS, [[d[k] for k in WORKLOAD_KEYS] for d in get_workload_report_data(academic_year, department_id, semester, teacher_id)],
        [3, 9, 6, 9, 16, 13, 7, 17, 6, 6, 6, 7]), filepath)


def export_stats(filepath, department_id=None, academic_year=None, pdf=False):
    def write():
        rows = get_stats_report_data(department_id, academic_year)
        if pdf:
            _pdf(filepath, "Статистика по категориям", _period(academic_year), STATS_HEADERS, rows, [25, 8, 10, 9, 10, 8, 10, 10, 8])
        else:
            _excel(filepath, "Статистика по категориям", _period(academic_year), STATS_HEADERS, rows)
    return _export(write, filepath)
