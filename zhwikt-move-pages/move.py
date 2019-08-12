# -*- coding: utf-8 -*-
import csv
import os
import traceback

os.environ['PYWIKIBOT_DIR'] = os.path.dirname(os.path.realpath(__file__))
import pywikibot
from pywikibot.data.api import Request

os.environ['TZ'] = 'UTC'

site = pywikibot.Site()
site.login()

token = site.tokens['csrf']

with open("list.csv", "r") as f:
    r = csv.reader(f)
    for row in r:
        oldtitle = row[0].strip()
        newtitle = row[1].strip()

        print("move", oldtitle, "to", newtitle)
        try:
            data = Request(site=site, parameters={
                "action": "move",
                "format": "json",
                "from": oldtitle,
                "to": newtitle,
                "reason": "轉為全站小工具",
                "noredirect": 1,
                "token": token
            }).submit()
        except Exception as e:
            traceback.print_exc()
