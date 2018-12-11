# -*- coding: utf-8 -*-
import os
import pywikibot
import json
import re
from config import *


os.environ["PYWIKIBOT2_DIR"] = os.path.dirname(os.path.realpath(__file__))
os.environ["TZ"] = "UTC"

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

def checkImageExists(title):
    image = pywikibot.Page(site, title)
    if image.exists():
        return True
    try:
        if image.fileIsShared():
            return True
    except Exception as e:
        pass
    return False

def followMove(title, commons=False):
    if commons:
        runsite = sitecommons
    else:
        runsite = site
    logs = []
    first_title = title
    while True:
        data = pywikibot.data.api.Request(site=runsite, parameters={
            "action": "query",
            "letitle": title,
            "list": "logevents",
            "letype": "move",
            "lelimit": "1"
            }).submit()
        if len(data["query"]["logevents"]) > 0:
            movelog = data["query"]["logevents"][0]
            movelog["params"]["target_title_without_ns"] = pywikibot.Page(site, movelog["params"]["target_title"]).titleWithoutNamespace()
            logs.append(movelog)
            title = movelog["params"]["target_title"]

            if checkImageExists(title):
                return logs

            if title == first_title:
                return []
        else:
            break
    return logs

cnt = 1
for page in site.categorymembers(cat):
    pagetitle = page.title()
    print(cnt, pagetitle)
    if pagetitle in skippages:
        print("skip")
        continue
    text = page.text
    summary_comment = []
    summary_moved = []
    summary_deleted = []
    for image in page.imagelinks():
        if not image.exists():
            try:
                if image.fileIsShared():
                    continue
            except Exception as e:
                pass

            image_fullname = image.title()
            imagename = image.title(with_ns=False)

            imageregex = "[" + imagename[0].upper() + imagename[0].lower() + "]" + re.escape(imagename[1:])
            imageregex = imageregex.replace("\\ ", "[ _]")

            # comment_other start
            existother = None
            for wiki in cfg["check_other_wiki"]:
                if pywikibot.Page(site, "{}:File:{}".format(wiki, imagename)).exists():
                    existother = wiki
                    break

            if existother is not None:
                print("{} exist on {}".format(image_fullname, existother))

                regex = cfg["regex"]["infobox"]["pattern"].format(imageregex)
                replace = cfg["regex"]["infobox"]["replace"]["comment_other"].format(cfg["check_other_wiki"][existother])

                text = re.sub(regex, replace, text, flags=re.M)

                regex = cfg["regex"]["normal"]["pattern"].format(imageregex)
                replace = cfg["regex"]["normal"]["replace"]["comment_other"].format(cfg["check_other_wiki"][existother])

                text = re.sub(regex, replace, text)

                summary_comment.append(cfg["summary"]["comment_other"].format(imagename, existother))

                continue
            # coment_other end

            # moved start
            movelog = followMove(image_fullname)
            if len(movelog) > 0:
                print("Info: File moved")
                image_fullname = movelog[-1]["params"]["target_title"]
                old_image_fullname = image_fullname

                if checkImageExists(imagename):
                    print("File:{} moved".format(imagename))

                    regex = cfg["regex"]["infobox"]["pattern"].format(imageregex)
                    replace = cfg["regex"]["infobox"]["replace"]["moved"].format(movelog[-1]["params"]["target_title_without_ns"])

                    text = re.sub(regex, replace, text, flags=re.M)

                    regex = cfg["regex"]["normal"]["pattern"].format(imageregex)
                    replace = cfg["regex"]["normal"]["replace"]["moved"].format(movelog[-1]["params"]["target_title_without_ns"])

                    text = re.sub(regex, replace, text)

                    summary_temp = old_image_fullname
                    for log in movelog:
                        summary_temp = cfg["summary"]["moved"].format(summary_temp, movelog["params"]["target_title_without_ns"], movelog["user"], movelog["logid"], movelog["comment"])
                    summary_moved.append(summary_temp)

                continue
            # moved end

            # deleted start
            deleted = False
            deleted_commons = False

            data = pywikibot.data.api.Request(site=site, parameters={
                "action": "query",
                "letitle": image_fullname,
                "list": "logevents",
                "leaction": "delete/delete",
                "lelimit": "1"
                }).submit()
            if len(data["query"]["logevents"]) > 0:
                deletelog = data["query"]["logevents"][0]
                if re.search(cfg["ignored_csd_comment"], deletelog["comment"]):
                    deleted = False
                else:
                    deleted = True
            if not deleted:
                data = pywikibot.data.api.Request(site=sitecommons, parameters={
                    "action": "query",
                    "letitle": image_fullname,
                    "list": "logevents",
                    "leaction": "delete/delete",
                    "lelimit": "1"
                    }).submit()
                if len(data["query"]["logevents"]) > 0:
                    deleted = True
                    deleted_commons = True
                    deletelog = data["query"]["logevents"][0]
                    print("deleted on commons")

            if deleted:
                if deleted_commons:
                    print("{} deleted on commons".format(image_fullname))
                else:
                    print("{} deleted".format(image_fullname))

                regex = cfg["regex"]["infobox"]["pattern"].format(imageregex)
                replace = cfg["regex"]["infobox"]["replace"]["deleted"]

                text = re.sub(regex, replace, text, flags=re.M)

                regex = cfg["regex"]["normal"]["pattern"].format(imageregex)
                replace = cfg["regex"]["normal"]["replace"]["deleted"]

                text = re.sub(regex, replace, text)

                if deleted_commons:
                    comment = re.sub(r"\[\[([^\[\]]+?)]]", r"[[:c:\1]]", deletelog["comment"])
                    summary_deleted.append(cfg["summary"]["deleted"]["commons"].format(imagename, deletelog["user"], deletelog["logid"], comment))
                else:
                    summary_deleted.append(cfg["summary"]["deleted"]["local"].format(imagename, deletelog["user"], deletelog["logid"], deletelog["comment"]))

                continue

            # deleted end

            # comment start
            uploaded = False

            data = pywikibot.data.api.Request(site=site, parameters={
                "action": "query",
                "letitle": image_fullname,
                "list": "logevents",
                "letype": "upload",
                "lelimit": "1"
                }).submit()
            if len(data["query"]["logevents"]) > 0:
                uploaded = True
            if not uploaded:
                data = pywikibot.data.api.Request(site=sitecommons, parameters={
                    "action": "query",
                    "letitle": image_fullname,
                    "list": "logevents",
                    "letype": "upload",
                    "lelimit": "1"
                    }).submit()
                if len(data["query"]["logevents"]) > 0:
                    uploaded = True

            if not uploaded:
                print("{} never uploaded".format(image_fullname))

                regex = cfg["regex"]["infobox"]["pattern"].format(imageregex)
                replace = cfg["regex"]["infobox"]["replace"]["comment"]

                text = re.sub(regex, replace, text, flags=re.M)

                regex = cfg["regex"]["normal"]["pattern"].format(imageregex)
                replace = cfg["regex"]["normal"]["replace"]["comment"]

                text = re.sub(regex, replace, text)

                summary_comment.append(cfg["summary"]["comment"].format(imagename))

                continue

            # comment end

            # unknown start
            print("{} missed for unknown reason".format(image_fullname))
            # unknown end

    if page.text == text:
        print("nothing changed")
        skipfile.write(pagetitle + "\n")
        continue

    pywikibot.showDiff(page.text, text)

    summary = []
    if len(summary_comment):
        summary.append(cfg["summary"]["prepend"]["comment"] + "、".join(summary_comment))
    if len(summary_moved):
        summary.append(cfg["summary"]["prepend"]["moved"] + "、".join(summary_moved))
    if len(summary_deleted):
        summary.append(cfg["summary"]["prepend"]["deleted"] + "、".join(summary_deleted))
    summary = cfg["summary"]["prepend"]["all"] + "；".join(summary)
    print("summary = {}".format(summary))

    save = input("save?")
    if save in ["Yes", "yes", "Y", "y"]:
        page.text = text
        page.save(summary=summary, minor=False, botflag=False)
        cnt += 1
    else:
        print("skip")
        skipfile.write(pagetitle + "\n")
