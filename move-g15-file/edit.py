# -*- coding: utf-8 -*-
import os
import pywikibot
import json
import re
from config import *


os.environ["PYWIKIBOT_DIR"] = os.path.dirname(os.path.realpath(__file__))
os.environ["TZ"] = "UTC"

site = pywikibot.Site()
site.login()
sitecommons = pywikibot.Site("commons", "commons")

token = site.getToken()

# config_page = pywikibot.Page(site, config_page_name)
# cfg = config_page.text
# cfg = json.loads(cfg)
# print(json.dumps(cfg, indent=4, ensure_ascii=False))

# if not cfg["enable"]:
#     exit("disabled\n")

cat = pywikibot.Page(site, "Category:快速删除候选")

skippages = ""
with open("skipedpage.txt", "r") as f:
    skippages = f.read()
skipfile = open("skipedpage.txt", "a")

cnt = 1
for page in site.categorymembers(cat, namespaces="6"):
    pagetitle = page.title()
    print(cnt, pagetitle)
    # if pagetitle in skippages:
    #     print("skip")
    #     continue
    text = page.text
    if not "Jimmy-bot|g15" in page.text:
        print("no g15 skip")
        continue

    pagecommons = pywikibot.Page(sitecommons, page.title())
    if not pagecommons.isRedirectPage():
        print("not redirect skip")
        continue

    target = pagecommons.getRedirectTarget()
    print("target=", target.title())

    summary = "配合commons重命名"
    print("summary = {}".format(summary))

    save = input("move?")
    if save in ["Yes", "yes", "Y", "y"]:
        # page.move(target.title(), reason=summary, noredirect=True, sysop=True)

        data = pywikibot.data.api.Request(site=site, parameters={
            "action": "move",
            "from": page.title(),
            "to": target.title(),
            "reason": summary,
            "movetalk": "1",
            "noredirect": "1",
            "ignorewarnings": "1",
            "token": token
            }).submit()
        print(data)

        cnt += 1
        skipfile.write(pagetitle + "\n")
    else:
        print("skip")
        skipfile.write(pagetitle + "\n")
