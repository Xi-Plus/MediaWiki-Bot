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

if not cfg['enable']:
    print('disabled')
    exit()

signpage = pywikibot.Page(site, cfg['main_page_name'])
text = signpage.text

wikicode = mwparserfromhell.parse(text)

archivelist = []
count = 0
for section in wikicode.get_sections()[1:]:
    title = str(section.get(0).title)
    print(title, end='\t')

    lasttime = datetime(1, 1, 1)
    for m in re.findall(r'(\d{4})年(\d{1,2})月(\d{1,2})日 \(.\) (\d{2}):(\d{2}) \(UTC\)', str(section)):
        d = datetime(int(m[0]), int(m[1]), int(m[2]), int(m[3]), int(m[4]))
        lasttime = max(lasttime, d)
    print(lasttime, end='\t')

    if re.search(cfg['not_processed_regex'], str(section)):
        print('not processed', end='\n')
        continue

    if (time.time() - lasttime.timestamp() > cfg['time_to_live']
            and lasttime != datetime(1, 1, 1)):
        archivestr = str(section).strip()
        archivestr = re.sub(
            r'{{bot-directive-archiver\|no-archive-begin}}[\s\S]+?{{bot-directive-archiver\|no-archive-end}}\n?', '', archivestr)
        archivelist.append(archivestr)
        count += 1
        section.remove(section)
        print('archive', end='\t')
    print()

text = str(wikicode)
if signpage.text == text:
    print('nothing changed')
    exit()

pywikibot.showDiff(signpage.text, text)
signpage.text = text
summary = cfg['main_page_summary'].format(count)
print(summary)
signpage.save(summary=summary, minor=True)

archivepagename = cfg['archive_page_name'].format(datetime.now().year)
archivepage = pywikibot.Page(site, archivepagename)
text = archivepage.text
text += '\n\n' + '\n\n'.join(archivelist)

pywikibot.showDiff(archivepage.text, text)
archivepage.text = text
summary = cfg['archive_page_summary'].format(count)
print(summary)
archivepage.save(summary=summary, minor=True)
