# -*- coding: utf-8 -*-
import os
import re

import pywikibot


os.environ['PYWIKIBOT2_DIR'] = os.path.dirname(os.path.realpath(__file__))
os.environ['TZ'] = 'UTC'

site = pywikibot.Site()
site.login()

summary = '機器人：[[Special:PermaLink/53078964#優良條目和典范条目子頁面繁簡皆有的問題|統一子頁面繁簡]]'

with open('list.csv', 'r') as f:
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
        print('move', oldtitle, 'to', newtitle)

        try:
            page.move(newtitle, reason=summary, movetalk=True, noredirect=True)
        except pywikibot.exceptions.ArticleExistsConflict as e:
            print('{} target exist'.format(oldtitle))

        for backlink in page.embeddedin():
            if re.search(r'^Wikipedia:优良条目/\d+年\d+月\d+日$', backlink.title()):
                print(backlink.title())
                text = backlink.text
                if re.search(r'Wikipedia:優良條目/s', text):
                    print('skip')
                    continue
                text = re.sub(r'{{(Wikipedia|维基百科):優良條目/',
                              '{{Wikipedia:优良条目/', text)

                pywikibot.showDiff(backlink.text, text)

                backlink.text = text
                print(summary)
                backlink.save(summary=summary, minor=True)
