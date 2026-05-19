# -*- coding: utf-8 -*-
import requests
import os
import json
from datetime import date, timedelta, datetime, timezone

TOKEN    = os.environ['BIBLE_TELEGRAM_BOT_TOKEN']
CHAT_ID  = os.environ['BIBLE_CHANNEL_ID']

# ── 성경 66권 장 수 ──────────────────────────────────────────
BOOKS = [
    ('창세기', 50), ('출애굽기', 40), ('레위기', 27), ('민수기', 36), ('신명기', 34),
    ('여호수아', 24), ('사사기', 21), ('룻기', 4), ('사무엘상', 31), ('사무엘하', 24),
    ('열왕기상', 22), ('열왕기하', 25), ('역대상', 29), ('역대하', 36), ('에스라', 10),
    ('느헤미야', 13), ('에스더', 10), ('욥기', 42), ('시편', 150), ('잠언', 31),
    ('전도서', 12), ('아가', 8), ('이사야', 66), ('예레미야', 52), ('예레미야애가', 5),
    ('에스겔', 48), ('다니엘', 12), ('호세아', 14), ('요엘', 3), ('아모스', 9),
    ('오바댜', 1), ('요나', 4), ('미가', 7), ('나훔', 3), ('하박국', 3),
    ('스바냐', 3), ('학개', 2), ('스가랴', 14), ('말라기', 4),
    ('마태복음', 28), ('마가복음', 16), ('누가복음', 24), ('요한복음', 21),
    ('사도행전', 28), ('로마서', 16), ('고린도전서', 16), ('고린도후서', 13),
    ('갈라디아서', 6), ('에베소서', 6), ('빌립보서', 4), ('골로새서', 4),
    ('데살로니가전서', 5), ('데살로니가후서', 3), ('디모데전서', 6), ('디모데후서', 4),
    ('디도서', 3), ('빌레몬서', 1), ('히브리서', 13), ('야고보서', 5),
    ('베드로전서', 5), ('베드로후서', 3), ('요한일서', 5), ('요한이서', 1),
    ('요한삼서', 1), ('유다서', 1), ('요한계시록', 22)
]

ALL_CHAPTERS = []
for book, chapters in BOOKS:
    for ch in range(1, chapters + 1):
        ALL_CHAPTERS.append((book, ch))

TOTAL_DAYS  = (len(ALL_CHAPTERS) + 2) // 3   # 397일
START_DATE  = date(2025, 1, 7)

# ── 오늘 읽을 장 계산 ────────────────────────────────────────
kst = datetime.now(timezone(timedelta(hours=9)))
today = kst.date()
day_idx  = (today - START_DATE).days          # 0-based
day_num  = day_idx + 1                        # 1-based (D1~)

start_ch = day_idx * 3
chapters_today = ALL_CHAPTERS[start_ch:start_ch + 3]

# ── 날짜 헤더 ────────────────────────────────────────────────
weekday_kr = ['월', '화', '수', '목', '금', '토', '일']
date_str = today.strftime('%-m/%-d') + '(' + weekday_kr[today.weekday()] + ')'

# ── 날씨 이모지 (open-meteo, 김포) ──────────────────────────
try:
    res = requests.get(
        'https://api.open-meteo.com/v1/forecast'
        '?latitude=37.6154&longitude=126.7224'
        '&daily=weathercode,temperature_2m_max,temperature_2m_min'
        '&timezone=Asia/Seoul&forecast_days=1'
    ).json()
    wcode    = res['daily']['weathercode'][0]
    temp_max = round(res['daily']['temperature_2m_max'][0])
    temp_min = round(res['daily']['temperature_2m_min'][0])
    weather_map = {0: '☀️', 1: '🌤️', 2: '⛅', 3: '☁️'}
    if wcode in weather_map:
        w_emoji = weather_map[wcode]
    elif wcode in [51,53,55,61,63,65,80,81,82]:
        w_emoji = '🌧️'
    elif wcode in [71,73,75,77,85,86]:
        w_emoji = '🌨️'
    elif wcode in [95,96,99]:
        w_emoji = '⛈️'
    else:
        w_emoji = '🌫️'
    weather_str = f'{w_emoji} {temp_max}°/{temp_min}°'
except Exception:
    weather_str = '🌤️'

# ── 분량 헤더 텍스트 ─────────────────────────────────────────
# 권이 바뀌는 경우 처리: 같은 권끼리 묶어서 표시
def format_range(chapters):
    result = []
    i = 0
    while i < len(chapters):
        book = chapters[i][0]
        group = [ch for b, ch in chapters if b == book]
        same = [(b, ch) for b, ch in chapters if b == book]
        chs  = [ch for b, ch in same]
        if len(chs) == 1:
            result.append(f'{book} {chs[0]}장')
        else:
            result.append(f'{book} {chs[0]}~{chs[-1]}장')
        i += len(same)
    return ', '.join(result)

range_str = format_range(chapters_today)

# ── 성경 본문 가져오기 ───────────────────────────────────────
with open('bible_nrv.json', 'r', encoding='utf-8') as f:
    bible = json.load(f)

def get_chapter_text(book, chapter):
    ch_data = bible.get(book, {}).get(str(chapter), {})
    lines = []
    for v in sorted(ch_data.keys(), key=lambda x: int(x)):
        lines.append(f'{v}. {ch_data[v]}')
    return '\n'.join(lines)

# ── 메시지 조립 ──────────────────────────────────────────────
header = f'📖 {date_str} {weather_str}\n[D{day_num}/{TOTAL_DAYS}] {range_str}\n'
header += '─' * 20

body_parts = [header]
for book, ch in chapters_today:
    chapter_text = get_chapter_text(book, ch)
    body_parts.append(f'\n\n[ {book} {ch}장 ]\n{chapter_text}')

full_msg = ''.join(body_parts)

# ── 텔레그램 발송 (4096자 초과 시 분할) ─────────────────────
def send(text):
    requests.post(
        f'https://api.telegram.org/bot{TOKEN}/sendMessage',
        json={'chat_id': CHAT_ID, 'text': text}
    )

MAX = 4096
if len(full_msg) <= MAX:
    send(full_msg)
else:
    # 헤더 먼저 발송
    send(header)
    # 각 장별로 발송
    for book, ch in chapters_today:
        chapter_text = get_chapter_text(book, ch)
        chunk = f'[ {book} {ch}장 ]\n{chapter_text}'
        # 장 하나가 4096 넘는 경우 (시편 등) 추가 분할
        while len(chunk) > MAX:
            send(chunk[:MAX])
            chunk = chunk[MAX:]
        send(chunk)

print('발송 완료')
