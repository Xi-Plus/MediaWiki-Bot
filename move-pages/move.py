# -*- coding: utf-8 -*-
import csv
import os

os.environ['PYWIKIBOT_DIR'] = os.path.dirname(os.path.realpath(__file__))
import pywikibot

site = pywikibot.Site()
site.login()

with open('list.csv', 'r') as f:
    reader = csv.reader(f)
    for row in reader:
        if len(row) < 3:
            continue
        oldtitle = row[0].strip()
        newtitle = row[1].strip()
        reason = row[2]
        page = pywikibot.Page(site, oldtitle)
        print('move', oldtitle, 'to', newtitle, 'reason', reason)
        page.move(newtitle, reason=row[2], noredirect=True)
