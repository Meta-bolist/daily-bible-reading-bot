import requests, os, json
from datetime import date, timedelta, datetime, timezone

TOKEN   = os.environ['BIBLE_TELEGRAM_BOT_TOKEN']
CHAT_ID = os.environ['BIBLE_CHANNEL_ID']

BOOKS = [
    ('창세기',50),('출애굽기',40),('레위기',27),('민수기',36),('신명기',34),
    ('여호수아',24),('사사기',21),('룻기',4),('사무엘상',31),('사무엘하',24),
    ('열왕기상',22),('열왕기하',25),('역대상',29),('역대하',36),('에스라',10),
    ('느헤미야',13),('에스더',10),('욥기',42),('시편',150),('잠언',31),
    ('전도서',12),('아가',8),('이사야',66),('예레미야',52),('예레미야애가',5),
    ('에스겔',48),('다니엘',12),('호세아',14),('요엘',3),('아모스',9),
    ('오바댜',1),('요나',4),('미가',7),('나훔',3),('하박국',3),
    ('스바냐',3),('학개',2),('스가랴',14),('말라기',4),
    ('마태복음',28),('마가복음',16),('누가복음',24),('요한복음',21),
    ('사도행전',28),('로마서',16),('고린도전서',16),('고린도후서',13),
    ('갈라디아서',6),('에베소서',6),('빌립보서',4),('골로새서',4),
    ('데살로니가전서',5),('데살로니가후서',3),('디모데전서',6),('디모데후서',4),
    ('디도서',3),('빌레몬서',1),('히브리서',13),('야고보서',5),
    ('베드로전서',5),('베드로후서',3),('요한일서',5),('요한이서',1),
    ('요한삼서',1),('유다서',1),('요한계시록',22)
]

ALL_CHAPTERS = []
for book, chapters in BOOKS:
    for ch in range(1, chapters+1):
        ALL_CHAPTERS.append((book, ch))

TOTAL_DAYS = (len(ALL_CHAPTERS) + 2) // 3
START_DATE = date(2026, 1, 7)

kst = datetime.now(timezone(timedelta(hours=9)))
today = kst.date()
day_idx = (today - START_DATE).days
day_num = day_idx + 1
chapters_today = ALL_CHAPTERS[day_idx*3 : day_idx*3+3]

weekday_kr = ['월','화','수','목','금','토','일']
date_str = f"{today.month}/{today.day}({weekday_kr[today.weekday()]})"

try:
    res = requests.get(
        'https://api.open-meteo.com/v1/forecast'
        '?latitude=37.6154&longitude=126.7224'
        '&daily=weathercode,temperature_2m_max,temperature_2m_min'
        '&timezone=Asia/Seoul&forecast_days=2'
    ).json()
    wcode    = res['daily']['weathercode'][1]
    temp_max = round(res['daily']['temperature_2m_max'][1])
    temp_min = round(res['daily']['temperature_2m_min'][1])
    wmap = {0:'☀️',1:'🌤️',2:'⛅',3:'☁️'}
    w_emoji = wmap.get(wcode,
        '🌧️' if wcode in [51,53,55,61,63,65,80,81,82] else
        '🌨️' if wcode in [71,73,75,77,85,86] else
        '⛈️' if wcode in [95,96,99] else '🌫️')
    weather_str = f'{w_emoji} {temp_max}°/{temp_min}°'
except Exception:
    weather_str = '🌤️'

def format_range(chs):
    result = []
    i = 0
    while i < len(chs):
        bk = chs[i][0]
        same = [c for b,c in chs if b==bk]
        result.append(f'{bk} {same[0]}장' if len(same)==1 else f'{bk} {same[0]}~{same[-1]}장')
        i += len(same)
    return ', '.join(result)

range_str = format_range(chapters_today)

with open('bible_sum.json', 'r', encoding='utf-8') as f:
    summary = json.load(f)

multi_book = len(set(b for b,c in chapters_today)) > 1

summary_lines = []
for book, ch in chapters_today:
    key = f'{ch}편' if book == '시편' else f'{ch}장'
    s = summary.get(book, {}).get(key, '')
    label = f'{book} {ch}장' if multi_book else f'{ch}장'
    summary_lines.append(f'{label}: {s}')

body = '\n'.join(summary_lines)
msg = f'📖 {date_str}  {range_str}\n{weather_str}  [D{day_num}/{TOTAL_DAYS}]\n{"─"*18}\n\n{body}'

requests.post(
    f'https://api.telegram.org/bot{TOKEN}/sendMessage',
    json={'chat_id': CHAT_ID, 'text': msg}
)
print('발송 완료')
