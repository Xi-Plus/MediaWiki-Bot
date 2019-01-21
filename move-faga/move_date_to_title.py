# -*- coding: utf-8 -*-
import os
import pywikibot
import json
import re


os.environ["PYWIKIBOT2_DIR"] = os.path.dirname(os.path.realpath(__file__))
os.environ["TZ"] = "UTC"

site = pywikibot.Site()
site.login()

token = site.getToken()

runpages = ""
with open("page.txt", "r") as f:
    runpages = f.read().split("\n")

for title in runpages:

    page = pywikibot.Page(site, title)

    pagetitle = page.title()
    print(title, pagetitle)

    if not page.exists():
        print("not exists")
        continue

    text = page.text
    print("-----\n"+text+"\n--------")

    m = re.search(r"'''《?\[\[(.+?)(\|.+?)?]]》?'''", text)
    if not m:
        print("cannot find title")
        continue

    target = m.group(1)

    targetpage = pywikibot.Page(site, target)
    if targetpage.isRedirectPage():
        targetpage = targetpage.getRedirectTarget()
        print("follow redirect")

    print(targetpage.title())

    print("move {} to {}".format(page.title(), "Wikipedia:优良条目/"+targetpage.title())+" ?")
    data = pywikibot.data.api.Request(site=site, parameters={
        "action": "move",
        "from": page.title(),
        "to": "Wikipedia:优良条目/"+targetpage.title(),
        "reason": "機器人：整理標題格式",
        "movetalk": "1",
        "noredirect": "1",
        "token": token
        }).submit()
    print(data)

    print("save {} as {}".format(page.title(), "Wikipedia:优良条目/"+targetpage.title())+" ?")
    page = pywikibot.Page(site, title)
    page.text = "{{Wikipedia:优良条目/"+targetpage.title()+"}}"
    page.save(summary="機器人：整理標題格式")
