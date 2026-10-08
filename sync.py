"""Best-effort scraper for the public FC Hegelmann schedule; fails closed."""
import hashlib
import os
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import requests
from bs4 import BeautifulSoup

BASE = 'https://fchegelmann.com/tvarkarastis/'
MONTHS = {'sausio':1,'vasario':2,'kovo':3,'balandžio':4,'gegužės':5,'birželio':6,'liepos':7,'rugpjūčio':8,'rugsėjo':9,'spalio':10,'lapkričio':11,'gruodžio':12}
TIME = re.compile(r'^([01]?\d|2[0-3]):[0-5]\d$')
MONTH_HEAD = re.compile(r'^(20\d\d)\s*-\s*([a-ząčęėįšųūž]+)\s+mėn\.?$', re.I)
TEAM = re.compile(r'(?:fc\s*hegelmann|fch\s*akademija)', re.I)
PAGE_LIMIT = 20
TZ = ZoneInfo('Europe/Vilnius')


def scrape(page, session):
    url = BASE if page == 1 else BASE + f'page/{page}/'
    response = session.get(url, timeout=25, headers={'User-Agent':'FCH-calendar-personal-sync/1.0'})
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')
    # Page body contains navigation as well; recognizable date/time headings guard extraction.
    lines = [s.strip() for s in soup.get_text('\n').splitlines() if s.strip()]
    year = None
    month = None
    day = None
    entries = []
    for i, value in enumerate(lines):
        heading = MONTH_HEAD.match(value)
        if heading:
            year, month = int(heading.group(1)), MONTHS.get(heading.group(2).lower())
            day = None
            continue
        if value.isdigit() and 1 <= int(value) <= 31 and i+1 < len(lines) and lines[i+1].lower() in MONTHS:
            day = int(value)
            month = MONTHS[lines[i+1].lower()]
            continue
        if not TIME.fullmatch(value) or day is None or year is None or month is None:
            continue
        # Most matches appear as home team, time, away team, stadium, competition.
        if i < 1 or i + 3 >= len(lines):
            continue
        home, away, stadium, competition = lines[i-1], lines[i+1], lines[i+2], lines[i+3]
        if not (TEAM.search(home) or TEAM.search(away)):
            continue
        if len(home)>100 or len(away)>100 or TIME.match(away) or len(competition)>180:
            continue
        try:
            when = datetime(year, month, day, *map(int, value.split(':')), tzinfo=TZ)
        except ValueError:
            continue
        entries.append({'home':home,'away':away,'when':when,'stadium':stadium,'competition':competition,'source':url})
    return entries


def esc(value):
    return str(value).replace('\\','\\\\').replace('\n','\\n').replace(',','\\,').replace(';','\\;')


def fold(line):
    # RFC 5545's 75-octet folding limit (UTF-8 safe).
    out = []
    part = ''
    for char in line:
        if len((part + char).encode('utf-8')) > 73:
            out.append(part)
            part = ' ' + char
        else:
            part += char
    out.append(part)
    return '\r\n'.join(out)


def build_calendar(matches):
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    lines = ['BEGIN:VCALENDAR','VERSION:2.0','PRODID:-//Personal FCH schedule//LT','CALSCALE:GREGORIAN','METHOD:PUBLISH','X-WR-CALNAME:FC Hegelmann rungtynės','X-WR-TIMEZONE:Europe/Vilnius']
    for entry in sorted(matches, key=lambda x:x['when']):
        # Competition and round identify a fixture independently of kick-off time.
        stable = '|'.join([entry['home'].lower(),entry['away'].lower(),entry['competition'].lower()])
        if 'turas' not in entry['competition'].lower():
            stable += '|' + entry['when'].strftime('%Y-%m-%d')
        uid = hashlib.sha256(stable.encode()).hexdigest()[:28] + '@fch-personal-calendar'
        start = entry['when'].astimezone(timezone.utc)
        # Site supplies kick-off, not full duration. Use 2-hour calendar placeholder.
        end = start + timedelta(hours=2)
        summary = f"{entry['home']} – {entry['away']}"
        description = f"{entry['competition']}\nPradžios laikas iš oficialios svetainės. Pabaigos laikas preliminarus (+2 val.).\nŠaltinis: {entry['source']}"
        lines += ['BEGIN:VEVENT','UID:'+uid,'DTSTAMP:'+stamp,'DTSTART:'+start.strftime('%Y%m%dT%H%M%SZ'),'DTEND:'+end.strftime('%Y%m%dT%H%M%SZ'),'SUMMARY:'+esc(summary),'LOCATION:'+esc(entry['stadium']),'DESCRIPTION:'+esc(description),'END:VEVENT']
    lines += ['END:VCALENDAR']
    return '\r\n'.join(fold(x) for x in lines) + '\r\n'


def main():
    session = requests.Session()
    all_entries = []
    repeated_pages = 0
    last_page_keys = set()
    for page in range(1, PAGE_LIMIT+1):
        entries = scrape(page,session)
        keys = {(x['home'],x['away'],x['when'].isoformat(),x['competition']) for x in entries}
        if not keys:
            if page == 1:
                raise RuntimeError('Nepavyko nuskaityti pirmojo puslapio; kalendorius neperrašytas')
            break
        if keys == last_page_keys:
            repeated_pages += 1
            if repeated_pages >= 2:
                break
        last_page_keys = keys
        all_entries += entries
        print(f'Page {page}: {len(entries)} fixtures')
    now = datetime.now(TZ)
    unique = {}
    for e in all_entries:
        if TEAM.search(e['home']) and e['when'] >= now - timedelta(hours=2):
            key=(e['home'],e['away'],e['when'].isoformat(),e['competition'])
            unique[key]=e
    # Fail closed; never wipe existing calendar on a bad fetch.
    if not unique:
        raise RuntimeError('Būsimų rungtynių nerasta; kalendorius neperrašytas')
    output = Path('calendar.ics')
    output.write_bytes(build_calendar(unique.values()).encode('utf-8'))
    print('Created', len(unique), 'upcoming events in', output)

if __name__ == '__main__':
    main()
