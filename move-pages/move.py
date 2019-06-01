# -*- coding: utf-8 -*-
import os
import pywikibot

os.environ['PYWIKIBOT_DIR'] = os.path.dirname(os.path.realpath(__file__))
os.environ['TZ'] = 'UTC'

site = pywikibot.Site()
site.login()

with open("list.csv", "r") as f:
    for title in f:
        oldtitle = title.strip()
        page = pywikibot.Page(site, oldtitle)
        ns = page.namespace().custom_name
        title = page.titleWithoutNamespace()
        title = title[0].upper() + title[1:]
        newtitle = ns + ":" + title
        print("move", oldtitle, "to", newtitle)
        page.move(newtitle, reason="[[:phab:T187783]]，移動到大寫開頭")
