# -*- coding: utf-8 -*-
import argparse
import json
import os
import re
import time
from datetime import datetime

import mwparserfromhell
os.environ['PYWIKIBOT_DIR'] = os.path.dirname(os.path.realpath(__file__))
import pywikibot

from config import config_page_name  # pylint: disable=E0611,W0614

parser = argparse.ArgumentParser()
parser.add_argument('--debug', action='store_true', dest='debug')
parser.set_defaults(debug=False)
args = parser.parse_args()

os.environ['TZ'] = 'UTC'

site = pywikibot.Site()
site.login()

config_page = pywikibot.Page(site, config_page_name)
cfg = config_page.text
cfg = json.loads(cfg)
if args.debug:
    print(json.dumps(cfg, indent=4, ensure_ascii=False))

if not cfg['enable']:
    print('disabled')
    exit()

signpage = pywikibot.Page(site, cfg['main_page_name'])
text = signpage.text

wikicode = mwparserfromhell.parse(text)

archivelist = []
count = 0
MIN_TIME = datetime(1970, 1, 1)
for section in wikicode.get_sections()[2:]:
    title = str(section.get(0).title)
    if args.debug:
        print(title, end='\t')

    lasttime = MIN_TIME
    for m in re.findall(r'(\d{4})年(\d{1,2})月(\d{1,2})日 \(.\) (\d{2}):(\d{2}) \(UTC\)', str(section)):
        d = datetime(int(m[0]), int(m[1]), int(m[2]), int(m[3]), int(m[4]))
        lasttime = max(lasttime, d)
    if args.debug:
        print(lasttime, end='\t')

    if lasttime == MIN_TIME:
        if args.debug:
            print('failed to get time')
        continue

    do_archive = False

    if time.time() - lasttime.timestamp() < cfg['time_to_live']:
        if args.debug:
            print('active')
        continue

    archivestr = str(section).strip()

    if re.search(r'{{\s*(Editprotected|EP|Editprotect|请求编辑|請求編輯|编辑请求|編輯請求|請求編輯受保護的頁面|請求編輯受保護的頁面|Editsemiprotected|FPER|Edit fully\-protected|SPER|Edit semi\-protected|Edit protected)\s*}}', str(section)):
        if time.time() - lasttime.timestamp() < cfg['time_to_live_for_ep']:
            if args.debug:
                print('ep found')
            continue
        archivestr = re.sub(
            r'{{\s*(Editprotected|EP|Editprotect|请求编辑|請求編輯|编辑请求|編輯請求|請求編輯受保護的頁面|請求編輯受保護的頁面|Editsemiprotected|FPER|Edit fully\-protected|SPER|Edit semi\-protected|Edit protected)\s*}}\n*',
            '{{Editprotected|no=1|sign=，機器人自動拒絕過舊申請。--~~~~}}\n\n',
            archivestr
        )

    archivestr = re.sub(
        r'{{bot-directive-archiver\|no-archive-begin}}[\s\S]+?{{bot-directive-archiver\|no-archive-end}}\n?',
        '',
        archivestr
    )
    archivelist.append(archivestr)
    count += 1
    section.remove(section)
    if args.debug:
        print('archive')

text = str(wikicode)
if signpage.text == text:
    if args.debug:
        print('nothing changed')
    exit()

if args.debug:
    pywikibot.showDiff(signpage.text, text)
signpage.text = text
summary = cfg['main_page_summary'].format(count)
if args.debug:
    print(summary)
    save = input('Save? ').lower()
else:
    save = 'yes'
if save in ['yes', 'y', '']:
    signpage.save(summary=summary, minor=True)

archivepagename = cfg['archive_page_name'].format(datetime.now().year)
archivepage = pywikibot.Page(site, archivepagename)
text = archivepage.text
text += '\n\n' + '\n\n'.join(archivelist)

if args.debug:
    pywikibot.showDiff(archivepage.text, text)
archivepage.text = text
summary = cfg['archive_page_summary'].format(count)
if args.debug:
    print(summary)
    save = input('Save? ').lower()
else:
    save = 'yes'
if save in ['yes', 'y', '']:
    archivepage.save(summary=summary, minor=True)
