# -*- coding: utf-8 -*-
import csv
import os
import traceback

os.environ['PYWIKIBOT_DIR'] = os.path.dirname(os.path.realpath(__file__))
import pywikibot
from pywikibot.data.api import Request
from config import interwikisource, summary  # pylint: disable=E0611,W0614

os.environ['TZ'] = 'UTC'

site = pywikibot.Site()
site.login()

token = site.tokens['csrf']

with open('list.csv', 'r') as f:
    r = csv.reader(f)
    for row in r:
        title = row[0].strip()
        print('import', title)
        try:
            data = Request(site=site, parameters={
                'action': 'import',
                'format': 'json',
                'interwikisource': interwikisource,
                'interwikipage': title,
                'summary': summary,
                'token': token
            }).submit()
            print(data)
        except Exception as e:
            traceback.print_exc()
