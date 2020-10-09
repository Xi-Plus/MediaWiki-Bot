# -*- coding: utf-8 -*-
import os
import re

os.environ['PYWIKIBOT_DIR'] = os.path.dirname(os.path.realpath(__file__))
import pywikibot

os.environ['TZ'] = 'UTC'

site = pywikibot.Site()
site.login()

cat = pywikibot.Page(site, 'Category:合併歷史候選')

cnt = 1
for targetPage in site.categorymembers(cat):
    targetTitle = targetPage.title()
    targetText = targetPage.text
    print(cnt, targetTitle)

    sourceTitle = None
    for template in targetPage.templatesWithParams():
        # print(template)
        if template[0].title() in ['Template:History merge', 'Template:Histmerge']:
            templateArgs = template[1]
            sourceTitle = templateArgs[0]
            break

    if sourceTitle is None:
        print('Cannot get source title')
        continue

    print('Merging history from {} to {}'.format(sourceTitle, targetTitle))

    sourcePage = pywikibot.Page(site, sourceTitle)

    targetText = re.sub(
        r'\{\{\s*(Histmerge|History[ _]merge)\s*(\|(?:\{\{[^{}]*\}\}|[^{}])*)?\}\}\s*', '', targetText, flags=re.I)

    sourcePage.text = targetText
    print('Editing {}'.format(sourceTitle))
    sourcePage.save(summary='準備進行合併歷史', minor=False)

    print('Deleting {}'.format(targetTitle))
    targetPage.delete(reason='[[Wiktionary:CSD|G8]]: 刪除以便移動', prompt=False)

    print('Moving {} to {}'.format(sourceTitle, targetTitle))
    sourcePage.move(targetTitle, reason='合併歷史', movetalk=True, noredirect=True)

    print('Undeleting {}'.format(targetTitle))
    targetPage.undelete(reason='合併歷史')

    cnt += 1
