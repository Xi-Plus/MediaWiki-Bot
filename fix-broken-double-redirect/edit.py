# -*- coding: utf-8 -*-
import argparse
import json
import os
import re

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


def fixPage(sourcePage):
    print(sourcePage.title())
    text = sourcePage.text

    if not re.search(r'{{\s*(Delete|Db-reason|D|Deletebecause|Db|速删|速刪|Speedy|SD|快删|快刪|CSD|QD).*\|g15(\||}})', text, flags=re.I) and not args.force:
        print('\tnot g15')
        return

    if re.search(r'没有对应母页面的子页面|不存在注册用户的用户页及用户页子页面', text, flags=re.I):
        print('\tblacklist')
        return

    m = re.search(r'#(?:重定向|REDIRECT) ?\[\[(.+?)]]', text, flags=re.I)
    if m:
        targetPage = pywikibot.Page(site, m.group(1))
        foundTitles = [sourcePage.title(), targetPage.title()]
        while True:
            logs = list(site.logevents(page=targetPage, total=1, logtype='move'))
            if len(logs) == 0:
                print('\tno logs')
                return
            log = logs[0]
            if log.type() != 'move':
                print('\trecent log not move')
                return
            targetPage = log.target_page
            if targetPage.title() in foundTitles:
                foundTitles.append(targetPage.title())
                print('\tget into loop:', foundTitles)
                return
            foundTitles.append(targetPage.title())
            if targetPage.exists():
                break
        if targetPage is None:
            print('\tcannot found target')
            return
        print('\ttarget', foundTitles)
        text = re.sub(r'(<noinclude>)?{{\s*(Delete|Db-reason|D|Deletebecause|Db|速删|速刪|Speedy|SD|快删|快刪|CSD|QD)\s*\|(.*)?g15.*}}\n?(<\/noinclude>)?\s*', '', text, flags=re.I)
        if text == sourcePage.text:
            print('Nothing changed')
            return
        text = re.sub(r'(#(?:重定向|REDIRECT) ?\[\[).+?(]])', r'\g<1>{}\g<2>'.format(targetPage.title()), text, flags=re.I)
        if text == sourcePage.text:
            print('Nothing changed')
            return
        pywikibot.showDiff(sourcePage.text, text)
        summary = cfg['summary'].format(log.logid())
        print(summary)
        if args.check and input('Save?').lower() not in ['', 'y', 'yes']:
            return
        sourcePage.text = text
        sourcePage.save(summary=summary, minor=False, asynchronous=True)
    else:
        print('\tcannot get redirect target')


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('page', nargs='?')
    parser.add_argument('-c', '--check', action='store_true', dest='check')
    parser.add_argument('-f', '--force', action='store_true', dest='force')
    parser.set_defaults(check=False, force=False)
    args = parser.parse_args()

    if args.page:
        page = pywikibot.Page(site, args.page)
        fixPage(page)
    else:
        cat = pywikibot.Page(site, cfg['csd_category'])

        for sourcePage in site.categorymembers(cat):
            fixPage(sourcePage)
