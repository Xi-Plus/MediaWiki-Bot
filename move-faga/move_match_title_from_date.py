# -*- coding: utf-8 -*-
import os
import re

os.environ["PYWIKIBOT_DIR"] = os.path.dirname(os.path.realpath(__file__))
import pywikibot

os.environ["TZ"] = "UTC"

site = pywikibot.Site()
site.login()

token = site.getToken()

runpages = ""
with open("page.txt", "r") as f:
    runpages = f.read().split("\n")

for datetitle in runpages:

    datepage = pywikibot.Page(site, datetitle)

    print("date = ", datetitle)

    if not datepage.exists():
        print("not exists")
        continue

    datetext = datepage.text
    print("-----\n" + datetext + "\n--------")

    m = re.search(r"\{\{Wikipedia:优良条目/(?:s|摘要)\|(.+?)\}\}", datetext)
    if not m:
        m = re.search(r"\{\{(.+?)\}\}", datetext)
        if not m:
            print("cannot find ga page")
            continue
        else:
            gapagetitle = m.group(1)
    else:
        gapagetitle = "Wikipedia:优良条目/" + m.group(1)

    print("ga = ", gapagetitle)

    gapage = pywikibot.Page(site, gapagetitle)

    if gapage.isRedirectPage():
        gapage = gapage.getRedirectTarget()
        print("follow redirect")

    print("-----\n" + gapage.text + "\n--------")

    m = re.search(r"'''《?\[\[(.+?)(\|.+?)?]]》?'''", gapage.text)
    if not m:
        print("cannot find title")
        continue

    articletitle = m.group(1)
    print("article = ", articletitle)

    articlepage = pywikibot.Page(site, articletitle)
    if articlepage.isRedirectPage():
        articlepage = articlepage.getRedirectTarget()
        print("follow redirect")

    print(articlepage.title())

    print("move {} to {}".format(gapage.title(), "Wikipedia:优良条目/" + articlepage.title()) + " ?")
    data = pywikibot.data.api.Request(site=site, parameters={
        "action": "move",
        "from": gapage.title(),
        "to": "Wikipedia:优良条目/" + articlepage.title(),
        "reason": "機器人：整理標題格式",
        "movetalk": "1",
        "noredirect": "1",
        "token": token
    }).submit()
    print(data)

    print("save {} as {}".format(datepage.title(), "Wikipedia:优良条目/" + articlepage.title()) + " ?")
    datepage = pywikibot.Page(site, datetitle)
    datepage.text = "{{Wikipedia:优良条目/" + articlepage.title() + "}}"
    datepage.save(summary="機器人：整理標題格式")
    # input()
