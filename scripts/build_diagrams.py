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
            draw.text((x+8,y-32),label,font=small,fill='black')
    for rect,title,lines in boxes:
        draw.rounded_rectangle(rect,radius=12,fill='#fafafa',outline='black',width=3)
        x1,y1,x2,y2=rect
        draw.text(((x1+x2)/2,y1+15),title,font=font,fill='black',anchor='mt')
        if lines:
            draw.line((x1,y1+60,x2,y1+60),fill='#aaaaaa',width=2)
            for i,line in enumerate(lines): draw.text((x1+18,y1+77+i*34),line,font=small,fill='black')
    OUT.mkdir(parents=True,exist_ok=True); image.save(OUT/name)


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
    diagram('use_case.png',(1500,1170),[
        ((50,60,450,230),'Администратор',['все операции оператора']),
        ((50,420,450,590),'Заведующий кафедрой',['ввод и изменение данных']),
        ((50,790,450,960),'Методист',['просмотр и экспорт']),
        ((800,60,1450,230),'Администрирование',['пользователи · копии · настройки']),
        ((800,420,1450,590),'Учет и распределение',['преподаватели · план · назначения']),
        ((800,790,1450,960),'Просмотр и отчетность',['поиск · фильтры · Excel · PDF'])],
        [([(450,145),(800,145)],''), ([(450,145),(650,145),(650,470),(800,470)],''),
         ([(450,505),(800,505)],''), ([(450,505),(600,505),(600,840),(800,840)],''),
         ([(450,875),(800,875)],'')])
    diagram('auth_flowchart.png',(1100,1290),[
        ((250,35,850,170),'Ввод логина и пароля',[]),
        ((250,260,850,395),'Поля заполнены',[]),
        ((250,490,850,625),'SHA-256 и запрос users',[]),
        ((250,720,850,855),'Учетная запись найдена',[]),
        ((250,970,850,1130),'Получить роль',['открыть главное окно'])],
        [([(550,170),(550,260)],''), ([(550,395),(550,490)],'да'), ([(550,625),(550,720)],''),
         ([(550,855),(550,970)],'да'), ([(850,320),(1010,320),(1010,105),(850,105)],'нет'),
         ([(850,790),(1050,790),(1050,105),(850,105)],'нет')])
    diagram('workload_flowchart.png',(1400,1430),[
        ((180,40,1220,190),'Выбрать строку плана и преподавателя',[]),
        ((180,280,1220,430),'Начать транзакцию и заблокировать план',[]),
        ((180,520,1220,720),'Рассчитать остаток теории и практики',['при изменении исключить текущее назначение']),
        ((180,810,1220,970),'Проверить часы и отсутствие дубликата',[]),
        ((180,1100,1220,1300),'Сохранить назначение и завершить транзакцию',['при ошибке отменить изменения и показать причину'])],
        [([(700,190),(700,280)],''), ([(700,430),(700,520)],''), ([(700,720),(700,810)],''),
         ([(700,970),(700,1100)],'')])

if __name__=='__main__':main()
