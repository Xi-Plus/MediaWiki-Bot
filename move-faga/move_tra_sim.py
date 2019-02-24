# -*- coding: utf-8 -*-
import argparse
import os
import re

os.environ['PYWIKIBOT2_DIR'] = os.path.dirname(os.path.realpath(__file__))
import pywikibot

from config import purge


os.environ['TZ'] = 'UTC'

parser = argparse.ArgumentParser()
parser.add_argument('--limit', type=int, default=0)
parser.add_argument('--limit2', type=int, default=0)
args = parser.parse_args()
print(args)

site = pywikibot.Site()
site.login()

summary = '機器人：[[Special:PermaLink/53078964#優良條目和典范条目子頁面繁簡皆有的問題|統一子頁面繁簡]]'

with open('list.csv', 'r') as f:
    cnt = 1
    cnt2 = 1
    for title in f:
        oldtitle = title.strip()
        page = pywikibot.Page(site, oldtitle)
        if not page.exists():
            print('{} not found'.format(oldtitle))
            continue

        if page.isRedirectPage():
            print('{} is redirect'.format(oldtitle))
            continue

        newtitle = oldtitle.replace('Wikipedia:優良條目', 'Wikipedia:优良条目')
        print('{} {} Moving from {} to {}'.format(
            cnt, cnt2, oldtitle, newtitle))

        try:
            page.move(newtitle, reason=summary, movetalk=True, noredirect=True)
        except pywikibot.exceptions.ArticleExistsConflict as e:
            print('{} target exist'.format(oldtitle))
            continue
        cnt += 1
        cnt2 += 1

        for backlink in (list(page.embeddedin()) + list(page.backlinks(filter_redirects=True))):
            print('backlink: {}'.format(backlink.title()))
            if re.search(r'^Wikipedia:优良条目/\d+年\d+月\d+日$|^Portal:', backlink.title()):
                print('{} Editing {}'.format(cnt2, backlink.title()))
                text = backlink.text
                if re.search(r'Wikipedia:(優良條目|优良条目)/s', text):
                    purge(backlink.title())
                    print('skip')
                    continue
                text = re.sub(r'^#(?:REDIRECT|重定向) \[\[Wikipedia:(?:优良条目|優良條目)/(.+?)]][\s\S]*$',
                              r'{{Wikipedia:优良条目/\1}}', text, flags=re.I)
                text = re.sub(r'{{(Wikipedia|维基百科|維基百科):優良條目/',
                              '{{Wikipedia:优良条目/', text)

                if backlink.text == text:
                    purge(backlink.title())
                    print('Nothing changed.')
                    continue

                pywikibot.showDiff(backlink.text, text)

                backlink.text = text
                print(summary)
                backlink.save(summary=summary, minor=True)
                cnt2 += 1
            else:
                purge(backlink.title())

        if args.limit > 0 and cnt > args.limit:
            print('Reach the limit. Quitting.')
            break

        if args.limit2 > 0 and cnt2 > args.limit2:
            print('Reach the limit2. Quitting.')
            break
