# -*- coding: utf-8 -*-
import os

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
    if 'P28' in claims:
        seen = claims['P28'][0].getTarget().amount
        if seen == 0:
            text += '{{{{動畫表格列|{}}}}}\n'.format(backlink.title().replace('Item:', ''))
    else:
        text += '{{{{動畫表格列|{}}}}}\n'.format(backlink.title().replace('Item:', ''))

text += '|}'

page = pywikibot.Page(site, 'Project:尚未開始看的動畫')
page.text = text
page.save(summary='產生列表')
