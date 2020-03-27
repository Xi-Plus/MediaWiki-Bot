# -*- coding: utf-8 -*-
import argparse
import os
import re

os.environ['PYWIKIBOT_DIR'] = os.path.dirname(os.path.realpath(__file__))
import pywikibot


parser = argparse.ArgumentParser()
parser.add_argument('-c', '--check', action='store_true', dest='check')
parser.set_defaults(check=False)
args = parser.parse_args()
print(args)

os.environ['TZ'] = 'UTC'

site = pywikibot.Site()
site.login()

cat = pywikibot.Page(site, 'Category:快速删除候选')

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
        summary = '-delete並修復損壞的雙重重定向，[[Special:Redirect/logid/{}|目標頁已被不留重定向移動]]，若認為重定向不合適請提交存廢討論'.format(log.logid())
        print(summary)
        if args.check and input('Save?').lower() not in ['', 'y', 'yes']:
            continue
        sourcePage.text = text
        sourcePage.save(summary=summary, minor=False, asynchronous=True)
    else:
        print('\tcannot get redirect target')
