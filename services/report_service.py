"""
Сервис формирования и экспорта аналитических отчетов (ReportModule)
Поддержка выгрузки в Excel (.xlsx) и PDF (.pdf)
"""
import os
from datetime import datetime
from typing import List, Dict, Any, Tuple
import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter

from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from config import COLLEGE_NAME
from database.connection import get_session
from database.models import Teacher, Department, TeacherWorkload, Discipline


# Регистрация системного шрифта для поддержки кириллицы в PDF
def register_cyrillic_font():
    try:
        # Пробуем стандартные пути Windows шрифтов
        win_fonts = [
            "C:\\Windows\\Fonts\\arial.ttf",
            "C:\\Windows\\Fonts\\tahoma.ttf",
            "C:\\Windows\\Fonts\\calibri.ttf"
        ]
        for fpath in win_fonts:
            if os.path.exists(fpath):
                pdfmetrics.registerFont(TTFont("CyrillicFont", fpath))
                return "CyrillicFont"
    except Exception:
        pass
    return "Helvetica"


CYRILLIC_FONT = register_cyrillic_font()


def get_teachers_report_data(department_id: int = None) -> List[Dict[str, Any]]:
    """Сбор данных для отчета по преподавательскому составу"""
    from services.teacher_service import get_teachers
    teachers = get_teachers(department_id=department_id)
    result = []
    for i, t in enumerate(teachers, 1):
        result.append({
            "num": i,
            "full_name": t.full_name,
            "department": t.department.name if t.department else "",
            "qualification": t.qualification or "Без категории",
            "experience": f"{t.experience} лет",
            "phone": t.phone or "-",
            "email": t.email or "-",
            "status": t.status or "работает",
            "total_hours": t.total_hours
        })
    return result


def get_workload_report_data(academic_year: str = None, department_id: int = None) -> List[Dict[str, Any]]:
    """Сбор данных для ведомости распределения учебной нагрузки"""
    from services.workload_service import get_workloads
    workloads = get_workloads(academic_year=academic_year, department_id=department_id)
    result = []
    for i, w in enumerate(workloads, 1):
        result.append({
            "num": i,
            "academic_year": w.academic_year,
            "teacher": w.teacher.full_name if w.teacher else "",
            "department": w.teacher.department.name if w.teacher and w.teacher.department else "",
            "discipline_code": w.discipline.code if w.discipline else "",
            "discipline_name": w.discipline.name if w.discipline else "",
            "hours_lecture": w.hours_lecture,
            "hours_practice": w.hours_practice,
            "total_hours": w.total_hours
        })
    return result


def export_teachers_to_excel(filepath: str, department_id: int = None) -> Tuple[bool, str]:
    """Экспорт кадрового состава в Excel (.xlsx)"""
    try:
        data = get_teachers_report_data(department_id)
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Преподаватели"

        # Стили
        header_fill = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
        header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
        title_font = Font(name="Calibri", size=14, bold=True, color="1F4E79")
        subtitle_font = Font(name="Calibri", size=11, italic=True)
        thin_border = Border(
            left=Side(style='thin', color='D9D9D9'),
            right=Side(style='thin', color='D9D9D9'),
            top=Side(style='thin', color='D9D9D9'),
            bottom=Side(style='thin', color='D9D9D9')
        )

        # Заголовок
        ws.merge_cells("A1:I1")
        ws["A1"] = COLLEGE_NAME
        ws["A1"].font = title_font
        ws["A1"].alignment = Alignment(horizontal="center", vertical="center")

        ws.merge_cells("A2:I2")
        ws["A2"] = f"Отчет по кадровому составу преподавателей на {datetime.now().strftime('%d.%m.%Y')}"
        ws["A2"].font = subtitle_font
        ws["A2"].alignment = Alignment(horizontal="center", vertical="center")

        ws.row_dimensions[1].height = 25
        ws.row_dimensions[2].height = 20
        ws.row_dimensions[4].height = 28

        headers = ["№", "ФИО преподавателя", "Кафедра / Отделение", "Квалификация", "Стаж", "Телефон", "E-mail", "Статус", "Всего часов"]
        for col_idx, h in enumerate(headers, 1):
            cell = ws.cell(row=4, column=col_idx, value=h)
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

        for row_idx, item in enumerate(data, 5):
            ws.cell(row=row_idx, column=1, value=item["num"]).alignment = Alignment(horizontal="center")
            ws.cell(row=row_idx, column=2, value=item["full_name"])
            ws.cell(row=row_idx, column=3, value=item["department"])
            ws.cell(row=row_idx, column=4, value=item["qualification"])
            ws.cell(row=row_idx, column=5, value=item["experience"]).alignment = Alignment(horizontal="center")
            ws.cell(row=row_idx, column=6, value=item["phone"]).alignment = Alignment(horizontal="center")
            ws.cell(row=row_idx, column=7, value=item["email"])
            ws.cell(row=row_idx, column=8, value=item["status"]).alignment = Alignment(horizontal="center")
            ws.cell(row=row_idx, column=9, value=item["total_hours"]).alignment = Alignment(horizontal="center")

            for c in range(1, 10):
                ws.cell(row=row_idx, column=c).border = thin_border

        # Итоги
        last_row = len(data) + 5
        ws.cell(row=last_row, column=2, value="ИТОГО преподавателей:").font = Font(bold=True)
        ws.cell(row=last_row, column=3, value=len(data)).font = Font(bold=True)
        ws.cell(row=last_row, column=8, value="ИТОГО часов:").font = Font(bold=True)
        total_h = sum(d["total_hours"] for d in data)
        ws.cell(row=last_row, column=9, value=total_h).font = Font(bold=True)

        # Авто-ширина колонок
        for col in ws.columns:
            max_len = 0
            col_letter = get_column_letter(col[0].column)
            for cell in col:
                if cell.row > 2 and cell.value:
                    max_len = max(max_len, len(str(cell.value)))
            ws.column_dimensions[col_letter].width = max(max_len + 3, 10)

        wb.save(filepath)
        return True, f"Отчет успешно сохранен в Excel:\n{filepath}"
    except Exception as e:
        return False, f"Ошибка экспорта в Excel: {e}"


def export_workload_to_excel(filepath: str, academic_year: str = None, department_id: int = None) -> Tuple[bool, str]:
    """Экспорт ведомости нагрузки в Excel (.xlsx)"""
    try:
        data = get_workload_report_data(academic_year, department_id)
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Учебная нагрузка"

        header_fill = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
        header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
        title_font = Font(name="Calibri", size=14, bold=True, color="1F4E79")
        subtitle_font = Font(name="Calibri", size=11, italic=True)
        thin_border = Border(
            left=Side(style='thin', color='D9D9D9'),
            right=Side(style='thin', color='D9D9D9'),
            top=Side(style='thin', color='D9D9D9'),
            bottom=Side(style='thin', color='D9D9D9')
        )

        ws.merge_cells("A1:I1")
        ws["A1"] = COLLEGE_NAME
        ws["A1"].font = title_font
        ws["A1"].alignment = Alignment(horizontal="center", vertical="center")

        year_str = f" за {academic_year} уч. год" if academic_year else ""
        ws.merge_cells("A2:I2")
        ws["A2"] = f"Ведомость распределения учебной нагрузки{year_str}"
        ws["A2"].font = subtitle_font
        ws["A2"].alignment = Alignment(horizontal="center", vertical="center")

        ws.row_dimensions[1].height = 25
        ws.row_dimensions[2].height = 20
        ws.row_dimensions[4].height = 28

        headers = ["№", "Учебный год", "Преподаватель", "Кафедра", "Код", "Дисциплина", "Лекции (ч)", "Практики (ч)", "Всего (ч)"]
        for col_idx, h in enumerate(headers, 1):
            cell = ws.cell(row=4, column=col_idx, value=h)
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

        for row_idx, item in enumerate(data, 5):
            ws.cell(row=row_idx, column=1, value=item["num"]).alignment = Alignment(horizontal="center")
            ws.cell(row=row_idx, column=2, value=item["academic_year"]).alignment = Alignment(horizontal="center")
            ws.cell(row=row_idx, column=3, value=item["teacher"])
            ws.cell(row=row_idx, column=4, value=item["department"])
            ws.cell(row=row_idx, column=5, value=item["discipline_code"]).alignment = Alignment(horizontal="center")
            ws.cell(row=row_idx, column=6, value=item["discipline_name"])
            ws.cell(row=row_idx, column=7, value=item["hours_lecture"]).alignment = Alignment(horizontal="center")
            ws.cell(row=row_idx, column=8, value=item["hours_practice"]).alignment = Alignment(horizontal="center")
            ws.cell(row=row_idx, column=9, value=item["total_hours"]).alignment = Alignment(horizontal="center")

            for c in range(1, 10):
                ws.cell(row=row_idx, column=c).border = thin_border

        # Итоги
        last_row = len(data) + 5
        tot_lec = sum(d["hours_lecture"] for d in data)
        tot_prac = sum(d["hours_practice"] for d in data)
        tot_all = sum(d["total_hours"] for d in data)

        ws.cell(row=last_row, column=6, value="ИТОГО ПО ВЕДОМОСТИ:").font = Font(bold=True)
        ws.cell(row=last_row, column=7, value=tot_lec).font = Font(bold=True)
        ws.cell(row=last_row, column=8, value=tot_prac).font = Font(bold=True)
        ws.cell(row=last_row, column=9, value=tot_all).font = Font(bold=True)

        for col in ws.columns:
            max_len = 0
            col_letter = get_column_letter(col[0].column)
            for cell in col:
                if cell.row > 2 and cell.value:
                    max_len = max(max_len, len(str(cell.value)))
            ws.column_dimensions[col_letter].width = max(max_len + 3, 10)

        wb.save(filepath)
        return True, f"Ведомость нагрузки успешно сохранена в Excel:\n{filepath}"
    except Exception as e:
        return False, f"Ошибка экспорта нагрузки в Excel: {e}"


def export_teachers_to_pdf(filepath: str, department_id: int = None) -> Tuple[bool, str]:
    """Экспорт списка преподавателей в PDF формат"""
    try:
        data = get_teachers_report_data(department_id)
        doc = SimpleDocTemplate(filepath, pagesize=landscape(A4), leftMargin=20, rightMargin=20, topMargin=20, bottomMargin=20)
        elements = []

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'TitleStyle',
            parent=styles['Heading1'],
            fontName=CYRILLIC_FONT,
            fontSize=14,
            leading=18,
            alignment=1, # Center
            textColor=colors.HexColor("#1F4E79")
        )
        subtitle_style = ParagraphStyle(
            'SubTitleStyle',
            parent=styles['Normal'],
            fontName=CYRILLIC_FONT,
            fontSize=10,
            leading=14,
            alignment=1,
            textColor=colors.HexColor("#555555")
        )
        cell_style = ParagraphStyle(
            'CellText',
            parent=styles['Normal'],
            fontName=CYRILLIC_FONT,
            fontSize=8,
            leading=10
        )
        header_cell_style = ParagraphStyle(
            'HeaderCellText',
            parent=styles['Normal'],
            fontName=CYRILLIC_FONT,
            fontSize=8,
            leading=10,
            textColor=colors.white,
            fontStyle='bold',
            alignment=1
        )

        elements.append(Paragraph(COLLEGE_NAME, title_style))
        elements.append(Paragraph(f"Отчет по кадровому составу преподавателей ({datetime.now().strftime('%d.%m.%Y')})", subtitle_style))
        elements.append(Spacer(1, 15))

        table_data = [
            [
                Paragraph("<b>№</b>", header_cell_style),
                Paragraph("<b>ФИО преподавателя</b>", header_cell_style),
                Paragraph("<b>Кафедра / Отделение</b>", header_cell_style),
                Paragraph("<b>Квалификация</b>", header_cell_style),
                Paragraph("<b>Стаж</b>", header_cell_style),
                Paragraph("<b>Телефон</b>", header_cell_style),
                Paragraph("<b>E-mail</b>", header_cell_style),
                Paragraph("<b>Статус</b>", header_cell_style),
                Paragraph("<b>Часы</b>", header_cell_style),
            ]
        ]

        for item in data:
            table_data.append([
                Paragraph(str(item["num"]), cell_style),
                Paragraph(item["full_name"], cell_style),
                Paragraph(item["department"], cell_style),
                Paragraph(item["qualification"], cell_style),
                Paragraph(str(item["experience"]), cell_style),
                Paragraph(item["phone"], cell_style),
                Paragraph(item["email"], cell_style),
                Paragraph(item["status"], cell_style),
                Paragraph(str(item["total_hours"]), cell_style),
            ])

        col_widths = [25, 140, 160, 110, 45, 85, 110, 60, 45]
        t = Table(table_data, colWidths=col_widths, repeatRows=1)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1F4E79")),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#D9D9D9")),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#F9FBFD")]),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        elements.append(t)
        doc.build(elements)
        return True, f"Отчет успешно сохранен в PDF:\n{filepath}"
    except Exception as e:
        return False, f"Ошибка экспорта в PDF: {e}"


def export_workload_to_pdf(filepath: str, academic_year: str = None, department_id: int = None) -> Tuple[bool, str]:
    """Экспорт ведомости учебной нагрузки в PDF формат"""
    try:
        data = get_workload_report_data(academic_year=academic_year, department_id=department_id)
        doc = SimpleDocTemplate(filepath, pagesize=landscape(A4), leftMargin=20, rightMargin=20, topMargin=20, bottomMargin=20)
        elements = []

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'TitleStyleWorkload',
            parent=styles['Heading1'],
            fontName=CYRILLIC_FONT,
            fontSize=14,
            leading=18,
            alignment=1,
            textColor=colors.HexColor("#1F4E79")
        )
        subtitle_style = ParagraphStyle(
            'SubTitleStyleWorkload',
            parent=styles['Normal'],
            fontName=CYRILLIC_FONT,
            fontSize=10,
            leading=14,
            alignment=1,
            textColor=colors.HexColor("#555555")
        )
        cell_style = ParagraphStyle(
            'CellTextWorkload',
            parent=styles['Normal'],
            fontName=CYRILLIC_FONT,
            fontSize=8,
            leading=10
        )
        header_cell_style = ParagraphStyle(
            'HeaderCellTextWorkload',
            parent=styles['Normal'],
            fontName=CYRILLIC_FONT,
            fontSize=8,
            leading=10,
            textColor=colors.white,
            fontStyle='bold',
            alignment=1
        )

        year_str = f" за {academic_year} уч. год" if academic_year else ""
        elements.append(Paragraph(COLLEGE_NAME, title_style))
        elements.append(Paragraph(f"Ведомость распределения учебной нагрузки преподавателей{year_str} ({datetime.now().strftime('%d.%m.%Y')})", subtitle_style))
        elements.append(Spacer(1, 15))

        table_data = [
            [
                Paragraph("<b>№</b>", header_cell_style),
                Paragraph("<b>Учебный год</b>", header_cell_style),
                Paragraph("<b>Преподаватель</b>", header_cell_style),
                Paragraph("<b>Кафедра</b>", header_cell_style),
                Paragraph("<b>Шифр</b>", header_cell_style),
                Paragraph("<b>Дисциплина</b>", header_cell_style),
                Paragraph("<b>Лекции</b>", header_cell_style),
                Paragraph("<b>Практика</b>", header_cell_style),
                Paragraph("<b>Всего</b>", header_cell_style),
            ]
        ]

        for item in data:
            table_data.append([
                Paragraph(str(item["num"]), cell_style),
                Paragraph(item["academic_year"], cell_style),
                Paragraph(item["teacher"], cell_style),
                Paragraph(item["department"], cell_style),
                Paragraph(item["discipline_code"], cell_style),
                Paragraph(item["discipline_name"], cell_style),
                Paragraph(str(item["hours_lecture"]), cell_style),
                Paragraph(str(item["hours_practice"]), cell_style),
                Paragraph(str(item["total_hours"]), cell_style),
            ])

        col_widths = [25, 75, 140, 140, 55, 175, 55, 55, 55]
        t = Table(table_data, colWidths=col_widths, repeatRows=1)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1F4E79")),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#D9D9D9")),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#F9FBFD")]),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        elements.append(t)
        doc.build(elements)
        return True, f"Ведомость нагрузки успешно сохранена в PDF:\n{filepath}"
    except Exception as e:
        return False, f"Ошибка экспорта нагрузки в PDF: {e}"
