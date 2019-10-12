# -*- coding: utf-8 -*-
import os

import pymysql
os.environ['PYWIKIBOT_DIR'] = os.path.dirname(os.path.realpath(__file__))
import pywikibot


os.environ['TZ'] = 'UTC'

site = pywikibot.Site()
site.login()
datasite = site.data_repository()

text = """{{動畫表格列標題}}
"""

for backlink in pywikibot.ItemPage(datasite, 'Q58').backlinks(namespaces=[120]):  # 已完結
    item = pywikibot.ItemPage(datasite, backlink.title())
    claims = item.get()['claims']
    if 'P28' in claims and 'P27' in claims:
        seen = claims['P28'][0].getTarget()
        episodes = claims['P27'][0].getTarget()
        if seen > 0 and seen != episodes:
            text += '{{{{動畫表格列|{}}}}}\n'.format(backlink.title().replace('Item:', ''))

text += '|}'

page = pywikibot.Page(site, 'Project:尚未看完的動畫')
page.text = text
page.save(summary='產生列表')
