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

with open("list.csv", "r") as f:
    r = csv.reader(f)
    for row in r:
        oldtitle = row[1].strip()
        page = pywikibot.Page(site, oldtitle)
        ns = page.namespace().custom_name
        title = page.titleWithoutNamespace()
        title = title[0].upper() + title[1:]
        newtitle = ns + ":" + title
        print("move", oldtitle, "to", newtitle)
        try:
            data = Request(site=site, parameters={
                "action": "move",
                "format": "json",
                "fromid": row[0],
                "to": newtitle,
                "reason": "[[:phab:T187783]]，移動到大寫開頭",
                "noredirect": 1,
                "token": token
            }).submit()
        except Exception as e:
            traceback.print_exc()
