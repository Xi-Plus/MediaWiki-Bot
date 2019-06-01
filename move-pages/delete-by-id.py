# -*- coding: utf-8 -*-
import os
import pywikibot
import csv
import traceback
from pywikibot.data.api import Request

os.environ['PYWIKIBOT_DIR'] = os.path.dirname(os.path.realpath(__file__))
os.environ['TZ'] = 'UTC'

site = pywikibot.Site()
site.login()

token = site.getToken()

with open("list-delete.csv", "r") as f:
    r = csv.reader(f)
    for row in r:
        pageid = row[2]
        oldtitle = row[1].strip()
        print("delete", oldtitle, pageid)
        try:
            data = Request(site=site, parameters={
                "action": "delete",
                "format": "json",
                "pageid": pageid,
                "reason": "[[:phab:T187783]]，刪除小寫重定向",
                "token": token
            }).submit()
        except Exception as e:
            traceback.print_exc()
