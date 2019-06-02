# -*- coding: utf-8 -*-
import os
import pywikibot

os.environ['PYWIKIBOT_DIR'] = os.path.dirname(os.path.realpath(__file__))
os.environ['TZ'] = 'UTC'

site = pywikibot.Site()
site.login()

with open("list-module.csv", "r") as f:
    for title in f:
        oldtitle = title.strip()

        page = pywikibot.Page(site, oldtitle)

        if not page.exists():
            continue

        if page.isRedirectPage():
            continue

        ns = page.namespace().canonical_name
        title = page.titleWithoutNamespace()
        title = title[0].upper() + title[1:]
        newtitle = ns + ":" + title

        if "return require('" + newtitle + "');" in page.text:
            continue

        print("move", oldtitle, "to", newtitle)
        page.move(newtitle, reason="[[:phab:T187783]]，移動到大寫開頭")
        page.text = "return require('" + newtitle + "');"
        page.save(summary="[[:phab:T187783]]，移動到大寫開頭，建立重定向", minor=False)

        # print("move", oldtitle, "to", newtitle, "without redirect")
        # page.move(newtitle, reason="[[:phab:T187783]]，移動到大寫開頭", noredirect=True)
