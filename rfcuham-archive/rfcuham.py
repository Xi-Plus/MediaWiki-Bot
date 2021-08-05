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

# Load {{Status}} parameter data
status_config_text = pywikibot.Page(site, 'Module:Status/data.json').text
status_config = json.loads(status_config_text)
status_to_archive = []
for status in ['done', 'nd', 'wd', 'ad', 'rd']:
    status_to_archive.extend(status_config[status]['status'])

cupage = pywikibot.Page(site, cfg["main_page_name"])
text = cupage.text

wikicode = mwparserfromhell.parse(text)

archivelist = {}
count = 0
for section in wikicode.get_sections()[2:]:
    title = str(section.get(0).title)
    print(title, end="\t")
    status = '(empty)'
    for template in section.filter_templates():
        template_name = template.name.lower().strip()
        if template_name == 'status':
            if template.has(1):
                status = template.get(1)
            break
    print('status', status, end='\t')
    if status in status_to_archive:
        lasttime = datetime(1, 1, 1)
        for m in re.findall(r'(\d{4})年(\d{1,2})月(\d{1,2})日 \(.\) (\d{2}):(\d{2}) \(UTC\)', str(section)):
            d = datetime(int(m[0]), int(m[1]), int(m[2]), int(m[3]), int(m[4]))
            lasttime = max(lasttime, d)
        print(lasttime, end='\t')
        if time.time() - lasttime.timestamp() > cfg['time_to_live'] and lasttime != datetime(1, 1, 1):
            target = (lasttime.year, lasttime.month)
            if target not in archivelist:
                archivelist[target] = []
            archivestr = str(section).strip()
            archivestr = re.sub(
                r'{{bot-directive-archiver\|no-archive-begin}}[\s\S]+?{{bot-directive-archiver\|no-archive-end}}\n?', '', archivestr)
            archivelist[target].append(archivestr)
            count += 1
            section.remove(section)
            print('archive', end='\t')
    print()

text = str(wikicode)
if cupage.text == text:
    exit("nothing changed")

cupage.text = text
cupage.save(summary=cfg["main_page_summary"].format(count), minor=True)

for target in archivelist:
    targetpage = pywikibot.Page(site, cfg["archive_page_name"].format(target[0], target[1]))
    oldtext = targetpage.text
    print(targetpage.title())
    appendtext = ''
    if not targetpage.exists():
        appendtext += cfg['archive_page_preload']
    appendtext += '\n\n'.join(archivelist[target])

    targetpage.text = oldtext + '\n\n' + appendtext
    try:
        targetpage.save(summary=cfg['archive_page_summary'].format(len(archivelist[target])), minor=True)
    except pywikibot.exceptions.PageSaveRelatedError as e:
        appendtext = re.sub(r'\[https?://(.+?)\]', r'\1', appendtext)
        appendtext = re.sub(r'https?://', '', appendtext)
        targetpage.text = oldtext + '\n\n' + appendtext
        try:
            targetpage.save(summary=cfg['archive_page_summary'].format(len(archivelist[target])), minor=True)
        except pywikibot.exceptions.PageSaveRelatedError as e:
            pywikibot.error(e)
