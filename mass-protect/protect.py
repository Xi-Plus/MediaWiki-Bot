# -*- coding: utf-8 -*-
import csv
import os

os.environ['PYWIKIBOT_DIR'] = os.path.dirname(os.path.realpath(__file__))
import pywikibot


os.environ['TZ'] = 'UTC'

site = pywikibot.Site()
site.login()

with open('list.csv', 'r') as f:
    r = csv.reader(f)
    for row in r:
        title = row[0]
        edit = row[1]
        move = row[2]
        create = row[3]
        reason = row[4]

        print(title, edit, move, create, reason)

        page = pywikibot.Page(site, title)
        args = {
            'reason': reason,
            'prompt': False,
        }
        if page.exists():
            args['edit'] = edit
            args['move'] = move
        else:
            args['create'] = create

        page.protect(**args)
