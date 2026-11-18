"""Воспроизводимые диаграммы фактической архитектуры и схемы БД."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import math

ROOT = Path(__file__).resolve().parents[1]
FONT = ROOT / 'assets/fonts/DejaVuSans.ttf'
OUT = ROOT / 'docs/diagrams'


def diagram(name,size,boxes,edges):
    image=Image.new('RGB',size,'white'); draw=ImageDraw.Draw(image)
    font=ImageFont.truetype(str(FONT),28); small=ImageFont.truetype(str(FONT),24)
    for points,label in edges:
        draw.line(points,fill='#252525',width=3)
        a,b=points[-2:]; angle=math.atan2(b[1]-a[1],b[0]-a[0]); length=17
        draw.polygon([b,(b[0]-length*math.cos(angle-.5),b[1]-length*math.sin(angle-.5)),
                        (b[0]-length*math.cos(angle+.5),b[1]-length*math.sin(angle+.5))],fill='#252525')
        if label:
            if len(points)==2:
                x=(points[0][0]+points[1][0])/2
                y=(points[0][1]+points[1][1])/2
            else:
                x=(points[0][0]+points[1][0])/2
                y=(points[0][1]+points[1][1])/2
            draw.text((x,y-18),label,font=small,fill='black',anchor='mm')
    for rect,title,lines in boxes:
        draw.rounded_rectangle(rect,radius=12,fill='#fafafa',outline='black',width=3)
        x1,y1,x2,y2=rect
        draw.text(((x1+x2)/2,y1+15),title,font=font,fill='black',anchor='mt')
        if lines:
            draw.line((x1,y1+60,x2,y1+60),fill='#aaaaaa',width=2)
            for i,line in enumerate(lines): draw.text((x1+18,y1+77+i*34),line,font=small,fill='black')
    OUT.mkdir(parents=True,exist_ok=True); image.save(OUT/name)


def arrow(draw, points, label=""):
    draw.line(points, fill="#252525", width=3)
    a, b = points[-2:]
    angle = math.atan2(b[1] - a[1], b[0] - a[0])
    size = 15
    draw.polygon([b, (b[0] - size * math.cos(angle - .5), b[1] - size * math.sin(angle - .5)),
                  (b[0] - size * math.cos(angle + .5), b[1] - size * math.sin(angle + .5))],
                 fill="#252525")
    if label:
        first, second = points[:2]
        horizontal = abs(second[0] - first[0]) > abs(second[1] - first[1])
        x = (first[0] + second[0]) / 2 + (0 if horizontal else 28)
        y = (first[1] + second[1]) / 2 + (-22 if horizontal else 0)
        draw.text((x, y), label, font=ImageFont.truetype(str(FONT), 24),
                  fill="black", anchor="mm")


def flow_node(draw, bounds, text, kind="process", size=27):
    x1, y1, x2, y2 = bounds
    if kind == "decision":
        draw.polygon([((x1 + x2) / 2, y1), (x2, (y1 + y2) / 2),
                      ((x1 + x2) / 2, y2), (x1, (y1 + y2) / 2)],
                     fill="#fafafa", outline="black", width=3)
    elif kind == "terminal":
        draw.rounded_rectangle(bounds, radius=38, fill="#fafafa", outline="black", width=3)
    elif kind == "input":
        draw.polygon([(x1 + 25, y1), (x2, y1), (x2 - 25, y2), (x1, y2)],
                     fill="#fafafa", outline="black", width=3)
    else:
        draw.rectangle(bounds, fill="#fafafa", outline="black", width=3)
    font = ImageFont.truetype(str(FONT), size)
    draw.multiline_text(((x1 + x2) / 2, (y1 + y2) / 2), text,
                        font=font, fill="black", anchor="mm", align="center", spacing=8)


def use_case():
    image = Image.new("RGB", (1500, 1150), "white")
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype(str(FONT), 26)
    draw.rectangle((510, 35, 1460, 1100), outline="black", width=3)
    draw.text((985, 58), "Система учета преподавателей", font=font, anchor="mt", fill="black")
    actors = [(260, 220, "Администратор"), (260, 545, "Заведующий кафедрой"),
              (260, 900, "Методист")]
    cases = [
        ((660, 140, 1360, 270), "Пользователи, копии и настройки"),
        ((660, 400, 1360, 550), "Карточки и справочники"),
        ((660, 635, 1360, 785), "План и назначения"),
        ((660, 900, 1360, 1045), "Просмотр и экспорт отчетов"),
    ]
    for actor_index, case_indices in [(0, [0, 1, 2, 3]), (1, [1, 2, 3]), (2, [3])]:
        x, y, _ = actors[actor_index]
        for case_index in case_indices:
            bounds, _ = cases[case_index]
            draw.line((x + 70, y + 45, bounds[0], (bounds[1] + bounds[3]) / 2),
                      fill="#555555", width=2)
    for x, y, name in actors:
        draw.ellipse((x - 30, y - 75, x + 30, y - 15), outline="black", width=3)
        draw.line((x, y - 15, x, y + 70), fill="black", width=3)
        draw.line((x - 70, y + 15, x + 70, y + 15), fill="black", width=3)
        draw.line((x, y + 70, x - 55, y + 135), fill="black", width=3)
        draw.line((x, y + 70, x + 55, y + 135), fill="black", width=3)
        draw.text((x, y + 155), name, font=font, fill="black", anchor="mt")
    for bounds, text in cases:
        draw.ellipse(bounds, fill="#fafafa", outline="black", width=3)
        draw.text(((bounds[0] + bounds[2]) / 2, (bounds[1] + bounds[3]) / 2), text,
                  font=font, fill="black", anchor="mm")
    image.save(OUT / "use_case.png")


def flowcharts():
    image = Image.new("RGB", (1120, 1400), "white")
    draw = ImageDraw.Draw(image)
    flow_node(draw, (330, 25, 730, 100), "Начало", "terminal")
    flow_node(draw, (270, 145, 790, 245), "Ввод логина и пароля", "input")
    flow_node(draw, (270, 290, 790, 450), "Поля\nзаполнены", "decision")
    flow_node(draw, (270, 495, 790, 595), "Найти запись по логину")
    flow_node(draw, (270, 650, 790, 830), "Пароль\nподтвержден", "decision")
    flow_node(draw, (865, 640, 1070, 835), "Ошибка\nвхода")
    flow_node(draw, (270, 895, 790, 1015), "Обновить legacy SHA-256\nпосле успешной проверки")
    flow_node(draw, (270, 1070, 790, 1190), "Получить роль\nоткрыть главное окно")
    flow_node(draw, (330, 1250, 730, 1335), "Конец", "terminal")
    for points, label in [
        ([(530, 100), (530, 145)], ""), ([(530, 245), (530, 290)], ""),
        ([(530, 450), (530, 495)], "да"), ([(530, 595), (530, 650)], ""),
        ([(790, 370), (967, 370), (967, 640)], "нет"),
        ([(790, 740), (865, 740)], "нет"),
        ([(530, 830), (530, 895)], "да"), ([(530, 1015), (530, 1070)], ""),
        ([(530, 1190), (530, 1250)], ""),
        ([(1070, 740), (1095, 740), (1095, 195), (790, 195)], ""),
    ]:
        arrow(draw, points, label)
    image.save(OUT / "auth_flowchart.png")

    image = Image.new("RGB", (1400, 1510), "white")
    draw = ImageDraw.Draw(image)
    flow_node(draw, (180, 25, 1040, 145), "Выбрать план, преподавателя и часы", "input")
    flow_node(draw, (180, 205, 1040, 330), "Проверить формат и начать транзакцию\nзаблокировать планы в порядке ID")
    flow_node(draw, (180, 400, 1040, 565), "Рассчитать свободную теорию и практику\nбез текущего назначения")
    flow_node(draw, (180, 640, 1040, 880), "Запрос допустим\nи часов достаточно", "decision")
    flow_node(draw, (1100, 655, 1365, 850), "Откатить\nизменения\nи показать отказ", size=23)
    flow_node(draw, (180, 965, 1040, 1110), "Сохранить назначение\nзафиксировать транзакцию")
    flow_node(draw, (180, 1185, 1040, 1300), "Обновить таблицы и остатки")
    flow_node(draw, (390, 1375, 830, 1460), "Конец", "terminal")
    for points, label in [
        ([(610, 145), (610, 205)], ""), ([(610, 330), (610, 400)], ""),
        ([(610, 565), (610, 640)], ""), ([(1040, 760), (1100, 760)], "нет"),
        ([(610, 880), (610, 965)], "да"), ([(610, 1110), (610, 1185)], ""),
        ([(610, 1300), (610, 1375)], ""),
        ([(1232, 850), (1232, 1417), (830, 1417)], ""),
    ]:
        arrow(draw, points, label)
    image.save(OUT / "workload_flowchart.png")


def main():
    diagram('architecture.png',(1500,1050),[
        ((150,40,1350,175),'Пользователь',['администратор · заведующий кафедрой · методист']),
        ((150,240,1350,410),'Интерфейс PyQt6',['карточки · общий план → назначения · отчеты · справка']),
        ((150,475,1350,645),'Сервисы Python',['проверка ФИО · остаток часов · фильтры · Excel и PDF']),
        ((150,710,1350,880),'SQLAlchemy и база данных',['SQLite локально / PostgreSQL в сети · 7 таблиц'])],
        [([(750,175),(750,240)],''), ([(750,410),(750,475)],''), ([(750,645),(750,710)],'')])
    diagram('erd.png',(1600,1540),[
        ((80,50,650,230),'roles',['PK id · name UNIQUE']),
        ((900,50,1500,230),'users',['PK id · username UNIQUE','password_hash · FK role_id']),
        ((80,350,650,540),'departments',['PK id · name · head_name']),
        ((900,350,1500,650),'teachers',['PK id · FK department_id','last_name · first_name · middle_name','full_name · birth_date · phone · email','qualification · experience · status','photo_path']),
        ((80,690,650,880),'disciplines',['PK id · code · name','FK department_id']),
        ((80,1030,650,1360),'workload_pools',['PK id · FK discipline_id','academic_year · semester · group_name','hours_lecture · hours_practice · weeks','UNIQUE год + семестр + группа','+ дисциплина']),
        ((900,930,1500,1360),'teacher_workload',['PK id · FK teacher_id · FK pool_id','FK discipline_id','academic_year · semester','hours_lecture · hours_practice','total_hours','UNIQUE pool_id + teacher_id'])],
        [([(650,130),(900,130)],'1 → N'), ([(650,445),(900,445)],'1 → N'),
         ([(350,540),(350,690)],'1 → N'), ([(350,880),(350,1030)],'1 → N'),
         ([(1200,650),(1200,930)],'1 → N'), ([(650,1200),(900,1200)],'1 → N'),
         ([(650,795),(790,795),(790,1000),(900,1000)],'1 → N')])
    diagram('network.png',(1500,700),[
        ((75,40,650,225),'Место пользователя',['PyQt6 · run_client.py','формы, таблицы и выборки']),
        ((850,40,1425,225),'Прикладной сервер',['Uvicorn · FastAPI · /api/v1','сессии, роли, схемы запроса']),
        ((850,290,1425,460),'Сервисы и ORM',['проверки учета · SQLAlchemy']),
        ((850,525,1425,670),'Хранилище',['файл SQLite на стороне сервера']),
        ((75,400,650,570),'Файлы на рабочем месте',['ведомость XLSX или PDF']),
        ],[([(650,130),(850,130)],'HTTP JSON'), ([(1137,225),(1137,290)],''),
           ([(1137,460),(1137,525)],''), ([(362,225),(362,400)],'')])
    diagram('client_navigation.png',(1480,665),[
        ((490,25,990,145),'Вход',['логин и пароль']),
        ((490,210,990,330),'Главное окно',['период, кафедра, преподаватель']),
        ((35,445,480,620),'Преподаватели',['ФИО · кафедра · стаж','поиск и сортировка']),
        ((515,445,965,620),'Общий план',['план и остатки','форма строки плана']),
        ((1000,445,1445,620),'Назначения',['форма распределения','ведомость XLSX или PDF']),
        ],[([(740,145),(740,210)],''), ([(740,330),(740,445)],''),
           ([(630,330),(630,380),(255,380),(255,445)],''),
           ([(850,330),(850,380),(1223,380),(1223,445)],'')])
    use_case()
    flowcharts()

if __name__=='__main__':main()
