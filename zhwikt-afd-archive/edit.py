# -*- coding: utf-8 -*-
import hashlib
import json
import os
import re
import time
from datetime import datetime

import mwparserfromhell
os.environ['PYWIKIBOT_DIR'] = os.path.dirname(os.path.realpath(__file__))
import pywikibot

from config import *


os.environ['TZ'] = 'UTC'

site = pywikibot.Site()
site.login()

config_page = pywikibot.Page(site, config_page_name)
cfg = config_page.text
cfg = json.loads(cfg)
print(json.dumps(cfg, indent=4, ensure_ascii=False))

if not cfg["enable"]:
    exit("disabled\n")

mainPage = pywikibot.Page(site, cfg["main_page_name"])
text = mainPage.text

rndstr = hashlib.md5(str(time.time()).encode()).hexdigest()
text = re.sub(r'^(===[^=]+===)$', rndstr + r'\1', text, flags=re.M)
text = text.split(rndstr)

mainPageText = text[0].strip()
text = text[1:]

archivelist = {}
count = 0
for section in text:
    section = section.strip()
    title = section.split('\n')[0]
    print(title, end="\t")
    if not re.search(r'{{delh', section, flags=re.I):
        mainPageText += '\n\n' + section
        print('not closed, skiped.')
        continue

    firsttime = datetime(9999, 1, 1)
    lasttime = datetime(1, 1, 1)
    for m in re.findall(r"(\d{4})年(\d{1,2})月(\d{1,2})日 \(.\) (\d{2}):(\d{2}) \(UTC\)", str(section)):
        d = datetime(int(m[0]), int(m[1]), int(
            m[2]), int(m[3]), int(m[4]))
        firsttime = min(firsttime, d)
        lasttime = max(lasttime, d)

    if time.time() - lasttime.timestamp() > cfg["time_to_live"] and lasttime != datetime(1, 1, 1):
        if firsttime.month <= 6:
            month = cfg['archive_page_name_first_half_year']
        else:
            month = cfg['archive_page_name_second_half_year']
        target = cfg['archive_page_name'].format(firsttime.year, month)

        if target not in archivelist:
            archivelist[target] = []
        archivelist[target].append(section)
        count += 1

        print("archive", end="\t")
    else:
        mainPageText += '\n\n' + section
        print("not archive", end="\t")
    print()

if count == 0:
    exit("nothing changed")

pywikibot.showDiff(mainPage.text, mainPageText)
mainPage.text = mainPageText
summary = cfg["main_page_summary"].format(count)
print(summary)
mainPage.save(summary=summary, minor=False)

for target in archivelist:
    archivePage = pywikibot.Page(site, target)
    text = archivePage.text
    print(archivePage.title())

    if not archivePage.exists():
        text = cfg["archive_page_preload"]

    text = text.strip()
    text += "\n\n" + "\n\n".join(archivelist[target])

    pywikibot.showDiff(archivePage.text, text)
    archivePage.text = text
    summary = cfg["archive_page_summary"].format(len(archivelist[target]))
    print(summary)
    archivePage.save(summary=summary, minor=False)
