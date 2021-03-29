# -*- coding: utf-8 -*-
import csv
import os

os.environ['PYWIKIBOT_DIR'] = os.path.dirname(os.path.realpath(__file__))
import pywikibot


os.environ['TZ'] = 'UTC'

site = pywikibot.Site()
site.login()
datasite = site.data_repository()

result = {}

for backlink in pywikibot.ItemPage(datasite, 'Q53').backlinks(namespaces=[120]):  # 動畫
    item = pywikibot.ItemPage(datasite, backlink.title())
    item = item.get()

    row_res = {
        'title': item['labels']['zh-tw'],
        'wp': '',
        'gamer': '',
    }

    claims = item['claims']

    if 'P68' in claims:
        row_res['wp'] = claims['P68'][0].getTarget()
    else:
        row_res['wp'] = row_res['title']
    if 'P1' in claims:
        row_res['gamer'] = claims['P1'][0].getTarget()

    print(row_res)

    if row_res['wp'] not in result:
        result[row_res['wp']] = row_res
    else:
        for key, value in result[row_res['wp']].items():
            if not value:
                result[row_res['wp']][key] = row_res[key]


csvfile = open('titles.csv', 'w', encoding='utf8')
writer = csv.writer(csvfile)
writer.writerow(['title', 'wp', 'gamer'])
for row in result.values():
    writer.writerow([row['title'], row['wp'], row['gamer']])
csvfile.close()
