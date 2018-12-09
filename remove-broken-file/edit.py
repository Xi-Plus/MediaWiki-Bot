# -*- coding: utf-8 -*-
import os
import pywikibot
import json
import re
from config import *


os.environ['PYWIKIBOT2_DIR'] = os.path.dirname(os.path.realpath(__file__))
os.environ['TZ'] = 'UTC'

site = pywikibot.Site()
site.login()
sitecommons = pywikibot.Site("commons", "commons")

config_page = pywikibot.Page(site, config_page_name)
cfg = config_page.text
cfg = json.loads(cfg)
print(json.dumps(cfg, indent=4, ensure_ascii=False))

if not cfg["enable"]:
    exit("disabled\n")

cat = pywikibot.Page(site, cfg["category"])

skippages = ""
with open("skipedpage.txt", "r") as f:
    skippages = f.read()
skipfile = open("skipedpage.txt", "a")

for page in site.categorymembers(cat):
    pagetitle = page.title()
    print(pagetitle)
    if pagetitle in skippages:
        print("skip")
        continue
    text = page.text
    summary_comment = []
    summary_remove = []
    for image in page.imagelinks():
        if not image.exists():
            try:
                if image.fileIsShared():
                    continue
            except Exception as e:
                pass
            
            imagename = image.title(with_ns=False)

            imageregex = "[" + imagename[0].upper() + imagename[0].lower() + "]" + re.escape(imagename[1:])
            imageregex = imageregex.replace("\\ ", "[ _]")

            existother = None
            for wiki in cfg["check_other_wiki"]:
                if pywikibot.Page(site, "{}:File:{}".format(wiki, imagename)).exists():
                    existother = wiki
                    break

            deleted = False
            
            if existother is None:
                print("File:{} not exist".format(imagename))

                data = pywikibot.data.api.Request(site=site, parameters={
                    'action': 'query',
                    'letitle': image.title(),
                    "list": "logevents",
                    "letype": "delete",
                    "lelimit": "1"
                    }).submit()
                if len(data['query']['logevents']) > 0:
                    deleted = True
                    deletelog = data['query']['logevents'][0]
                    if re.search(cfg["csd_f7_comment"], deletelog['comment']):
                        deleted = False
                deletedoncommons = False
                if not deleted:
                    data = pywikibot.data.api.Request(site=sitecommons, parameters={
                        'action': 'query',
                        'letitle': image.title(),
                        "list": "logevents",
                        "letype": "delete",
                        "lelimit": "1"
                        }).submit()
                    if len(data['query']['logevents']) > 0:
                        deleted = True
                        deletedoncommons = True
                        deletelog = data['query']['logevents'][0]
                        print(deletelog)
                
                regex = cfg["regex"]["not_exist_other"]["infobox"]["pattern"].format(imageregex)
                if deleted:
                    replace = cfg["regex"]["not_exist_other"]["infobox"]["replace"]["deleted"]
                else:
                    replace = cfg["regex"]["not_exist_other"]["infobox"]["replace"]["not_deleted"]

                text = re.sub(regex, replace, text, flags=re.M)

                regex = cfg["regex"]["not_exist_other"]["normal"]["pattern"].format(imageregex)
                if deleted:
                    replace = cfg["regex"]["not_exist_other"]["normal"]["replace"]["deleted"]
                else:
                    replace = cfg["regex"]["not_exist_other"]["normal"]["replace"]["not_deleted"]

                text = re.sub(regex, replace, text)

            else:
                print("File:{} exist on {}".format(imagename, existother))
                
                regex = cfg["regex"]["exist_other"]["infobox"]["pattern"].format(imageregex)
                if deleted:
                    replace = cfg["regex"]["exist_other"]["infobox"]["replace"]["deleted"]
                else:
                    replace = cfg["regex"]["exist_other"]["infobox"]["replace"]["not_deleted"].format(cfg["check_other_wiki"][existother])

                text = re.sub(regex, replace, text, flags=re.M)

                regex = cfg["regex"]["exist_other"]["normal"]["pattern"].format(imageregex)
                if deleted:
                    replace = cfg["regex"]["exist_other"]["normal"]["replace"]["deleted"]
                else:
                    replace = cfg["regex"]["exist_other"]["normal"]["replace"]["not_deleted"].format(cfg["check_other_wiki"][existother])

                text = re.sub(regex, replace, text)

            if deleted:
                if deletedoncommons:
                    comment = re.sub(r"\[\[([^\[\]]+?)]]", r"[[:c:\1]]", deletelog["comment"])
                    summary_remove.append(cfg["summary"]["deleted"]["commons"].format(imagename, deletelog["user"], deletelog["logid"], comment))
                else:
                    summary_remove.append(cfg["summary"]["deleted"]["local"].format(imagename, deletelog["user"], deletelog["logid"], deletelog["comment"]))
            else:
                if existother:
                    summary_comment.append(cfg["summary"]["not_deleted"]["exist_other"].format(imagename, existother))
                else:
                    summary_comment.append(cfg["summary"]["not_deleted"]["not_exist_other"].format(imagename))

    if page.text == text:
        print("nothing changed")
        skipfile.write(pagetitle + "\n")
        continue

    pywikibot.showDiff(page.text, text)

    summary = []
    if len(summary_comment):
        summary.append(cfg["summary"]["prepend"]["comment"] + "、".join(summary_comment))
    if len(summary_remove):
        summary.append(cfg["summary"]["prepend"]["remove"] + "、".join(summary_remove))
    summary = "；".join(summary)
    print("summary = {}".format(summary))

    save = input("save?")
    if save in ["Yes", "yes", "Y", "y"]:
        page.text = text
        page.save(summary=summary, minor=False)
    else:
        print("skip")
        skipfile.write(pagetitle + "\n")
