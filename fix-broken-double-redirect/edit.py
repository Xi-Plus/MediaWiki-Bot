# -*- coding: utf-8 -*-
import argparse
import json
import os
import re

os.environ['PYWIKIBOT_DIR'] = os.path.dirname(os.path.realpath(__file__))
import pywikibot
from config import config_page_name  # pylint: disable=E0611,W0614


parser = argparse.ArgumentParser()
parser.add_argument('-c', '--check', action='store_true', dest='check')
parser.set_defaults(check=False)
args = parser.parse_args()
print(args)

os.environ['TZ'] = 'UTC'

site = pywikibot.Site()
site.login()

config_page = pywikibot.Page(site, config_page_name)
cfg = config_page.text
cfg = json.loads(cfg)
print(json.dumps(cfg, indent=4, ensure_ascii=False))

if not cfg['enable']:
    exit('disabled\n')

cat = pywikibot.Page(site, cfg['csd_category'])

for sourcePage in site.categorymembers(cat):
    print(sourcePage.title())
    text = sourcePage.text
    if '{{d|bot=Jimmy-bot|g15|' not in text:
        print('\tnot g15')
        continue

    m = re.search(r'#(?:重定向|REDIRECT) ?\[\[(.+?)]]', text, flags=re.I)
    if m:
        middlePage = pywikibot.Page(site, m.group(1))
        logs = list(site.logevents(page=middlePage, total=1))
        if len(logs) == 0:
            print('\tno logs')
            continue
        log = logs[0]
        if log.type() != 'move':
            print('\trecent log not move')
            continue
        targetPage = log.target_page
        print('\ttarget', targetPage.title())
        text = re.sub(r'^{{d\|bot=Jimmy-bot\|g15\|.+\n', '', text)
        text = re.sub(r'(#(?:重定向|REDIRECT) ?\[\[).+?(]])', r'\g<1>{}\g<2>'.format(targetPage.title()), text)
        pywikibot.showDiff(sourcePage.text, text)
        summary = cfg['summary'].format(log.logid())
        print(summary)
        if args.check and input('Save?').lower() not in ['', 'y', 'yes']:
            continue
        sourcePage.text = text
        sourcePage.save(summary=summary, minor=False, asynchronous=True)
    else:
        print('\tcannot get redirect target')
