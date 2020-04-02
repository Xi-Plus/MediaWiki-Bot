# -*- coding: utf-8 -*-
import json
import os
import re
import time
from datetime import datetime

import mwparserfromhell
os.environ['PYWIKIBOT_DIR'] = os.path.dirname(os.path.realpath(__file__))
import pywikibot
from config import config_page_name  # pylint: disable=E0611,W0614

os.environ['TZ'] = 'UTC'

site = pywikibot.Site()
site.login()

config_page = pywikibot.Page(site, config_page_name)
cfg = config_page.text
cfg = json.loads(cfg)
print(json.dumps(cfg, indent=4, ensure_ascii=False))

if not cfg["enable"]:
    exit("disabled\n")

ewippage = pywikibot.Page(site, cfg["main_page_name"])
text = ewippage.text

wikicode = mwparserfromhell.parse(text)

archivelist = {}
count = 0
for section in wikicode.get_sections()[1:]:
    if section == '':
        continue
    else:
        title = str(section.get(0).title)
        print(title, end="\t")

    lasttime = datetime(1, 1, 1)
    for m in re.findall(r"(\d{4})年(\d{1,2})月(\d{1,2})日 \(.\) (\d{2}):(\d{2}) \(UTC\)", str(section)):
        d = datetime(int(m[0]), int(m[1]), int(m[2]), int(m[3]), int(m[4]))
        lasttime = max(lasttime, d)
    print(lasttime, end="\t")

    processed = False
    if re.search(cfg["processed_regex"], str(section)) and not re.search(cfg["not_processed_regex"], str(section)):
        processed = True
        print("processed", end="\t")
    else:
        print("not processed", end="\t")

    if (
        (
            (processed and time.time() - lasttime.timestamp() > cfg["time_to_live_for_processed"])
            or (not processed and time.time() - lasttime.timestamp() > cfg["time_to_live_for_not_processed"])
        )
            and lasttime != datetime(1, 1, 1)):
        target = (lasttime.year, lasttime.month)
        if target not in archivelist:
            archivelist[target] = []
        archivestr = str(section).strip()
        archivestr = re.sub(
            r"{{bot-directive-archiver\|no-archive-begin}}[\s\S]+?{{bot-directive-archiver\|no-archive-end}}\n?", "", archivestr)
        archivelist[target].append(archivestr)
        count += 1
        section.remove(section)
        print("archive to " + str(target), end="\t")
    print()

text = str(wikicode)
if ewippage.text == text:
    exit("nothing changed")

pywikibot.showDiff(ewippage.text, text)
ewippage.text = text
summary = cfg["main_page_summary"].format(count)
print(summary)
ewippage.save(summary=summary, minor=False)

for target in archivelist:
    archivepage = pywikibot.Page(site, cfg["archive_page_name"].format(target[0], target[1]))
    text = archivepage.text
    print(archivepage.title())
    if not archivepage.exists():
        text = cfg["archive_page_preload"]
    text += "\n\n" + "\n\n".join(archivelist[target])

    pywikibot.showDiff(archivepage.text, text)
    archivepage.text = text
    summary = cfg["archive_page_summary"].format(len(archivelist[target]))
    print(summary)
    archivepage.save(summary=summary, minor=False)
