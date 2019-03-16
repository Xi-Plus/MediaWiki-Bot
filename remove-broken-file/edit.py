# -*- coding: utf-8 -*-
import argparse
import json
import os
import re

os.environ["PYWIKIBOT2_DIR"] = os.path.dirname(os.path.realpath(__file__))
import pywikibot

from config import *


os.environ["TZ"] = "UTC"

parser = argparse.ArgumentParser()
parser.add_argument('--category', type=str, default=None)
parser.add_argument('--confirm', type=bool, default=False)
parser.add_argument('--limit', type=int, default=0)
parser.add_argument('--skiplimit', type=int, default=20)
args = parser.parse_args()
print(args)

site = pywikibot.Site()
site.login()
sitecommons = pywikibot.Site("commons", "commons")

config_page = pywikibot.Page(site, config_page_name)
cfg = config_page.text
cfg = json.loads(cfg)
print(json.dumps(cfg, indent=4, ensure_ascii=False))

if not cfg["enable"]:
    exit("disabled\n")

if args.category:
    cat = pywikibot.Page(site, args.category)
else:
    cat = pywikibot.Page(site, cfg["category"])

skippages = ""
skippagespath = os.path.join(os.path.dirname(
    os.path.realpath(__file__)), "skipedpage.txt")
with open(skippagespath, "r") as f:
    skippages = f.read()
skipfile = open(skippagespath, "a")


def checkImageExists(title):
    image = pywikibot.FilePage(site, title)
    if image.exists():
        return True
    try:
        if image.fileIsShared():
            return True
    except Exception:
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
            movelog["params"]["target_title_without_ns"] = pywikibot.Page(
                site, movelog["params"]["target_title"]).titleWithoutNamespace()
            logs.append(movelog)
            title = movelog["params"]["target_title"]

            if checkImageExists(title):
                return logs

            if title == first_title:
                return []
        else:
            break
    return logs


def checkReplace(oldText, newText):
    if re.search(r'<!--.*<!--.*-->.*-->', newText):
        return oldText
    return newText


limit = 1
skiplimit = 0
for page in site.categorymembers(cat):
    if args.limit > 0 and limit > args.limit:
        print('Reach the limit. Quitting.')
        break
    if args.skiplimit > 0 and skiplimit >= args.skiplimit:
        print('Reach the skiplimit. Quitting.')
        break

    pagetitle = page.title()
    print(limit, pagetitle)
    is_skip = False
    for skip_regex in cfg['skip_title']:
        if re.search(skip_regex, pagetitle):
            print('skip ({0})'.format(skip_regex))
            is_skip = True
            break
    if is_skip:
        continue
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

            imageregex = "[" + imagename[0].upper() + \
                imagename[0].lower() + "]" + re.escape(imagename[1:])
            imageregex = imageregex.replace("\\ ", "[ _]")

            # comment_other start
            existother = None
            for wiki in cfg["check_other_wiki"]:
                if pywikibot.Page(site, "{}:File:{}".format(wiki, imagename)).exists():
                    existother = wiki
                    break

            if existother is not None:
                print("{} exist on {}".format(image_fullname, existother))

                for regex_type in cfg["regex"]:
                    regex = cfg["regex"][regex_type]["pattern"].format(
                        imageregex)
                    replace = cfg["regex"][regex_type]["replace"]["comment_other"].format(
                        cfg["check_other_wiki"][existother])

                    newtext, count = re.subn(
                        regex, replace, text, flags=re.M | re.I)
                    text = checkReplace(text, newtext)

                    if count > 0:
                        break

                summary_comment.append(
                    cfg["summary"]["comment_other"].format(imagename, existother))

                continue
            # coment_other end

            # moved start
            movelog = followMove(image_fullname)
            if len(movelog) > 0:
                if checkImageExists(imagename):
                    print("File:{} moved".format(imagename))

                    for regex_type in cfg["regex"]:
                        regex = cfg["regex"][regex_type]["pattern"].format(
                            imageregex)
                        replace = cfg["regex"][regex_type]["replace"]["moved"].format(
                            movelog[-1]["params"]["target_title_without_ns"])

                        newtext, count = re.subn(
                            regex, replace, text, flags=re.M | re.I)
                        text = checkReplace(text, newtext)

                        if count > 0:
                            break

                    summary_temp = image_fullname
                    for log in movelog:
                        summary_temp = cfg["summary"]["moved"].format(
                            summary_temp, log["params"]["target_title_without_ns"], log["user"], log["logid"], log["comment"])
                    summary_moved.append(summary_temp)

                    continue
                else:
                    image_fullname = movelog[-1]["params"]["target_title"]
                    print("Info: File moved to {}".format(image_fullname))

            # moved end

            # deleted start
            deleted = False
            deleted_commons = False
            deleted_comment = False

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
                    if re.search(cfg["drv_csd_comment"], deletelog["comment"]):
                        deleted_comment = True
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

            if deleted_comment or deleted:
                summary_prefix = imagename
                for log in movelog:
                    summary_prefix = cfg["summary"]["moved_deleted"].format(
                        summary_prefix, log["params"]["target_title_without_ns"], log["logid"])

            if deleted_comment:
                print("{} deleted by F6".format(image_fullname))

                for regex_type in cfg["regex"]:
                    regex = cfg["regex"][regex_type]["pattern"].format(
                        imageregex)
                    replace = cfg["regex"][regex_type]["replace"]["deleted_comment"]

                    newtext, count = re.subn(
                        regex, replace, text, flags=re.M | re.I)
                    text = checkReplace(text, newtext)

                    if count > 0:
                        break

                summary_comment.append(cfg["summary"]["deleted"]["local"].format(
                    summary_prefix, deletelog["user"], deletelog["logid"], deletelog["comment"]))

                drv_page = pywikibot.Page(site, cfg["drv_page"])
                drv_page_text = drv_page.text
                if image_fullname not in drv_page_text:
                    drv_page_text += cfg["drv_append_text"].format(
                        image_fullname, pagetitle, deletelog["user"], deletelog["comment"], deletelog["logid"])
                    pywikibot.showDiff(drv_page.text, drv_page_text)
                    summary = cfg["drv_summary"]
                    print("summary = {}".format(summary))

                    if args.confirm:
                        save = input("save?")
                    else:
                        save = "Yes"
                    if save in ["Yes", "yes", "Y", "y", ""]:
                        drv_page.text = drv_page_text
                        drv_page.save(summary=summary,
                                      minor=False, botflag=False)
                else:
                    print('Already reported to DRV.')

                continue

            if deleted:
                if deleted_commons:
                    print("{} deleted on commons".format(image_fullname))
                else:
                    print("{} deleted".format(image_fullname))

                for regex_type in cfg["regex"]:
                    regex = cfg["regex"][regex_type]["pattern"].format(
                        imageregex)
                    replace = cfg["regex"][regex_type]["replace"]["deleted"]

                    newtext, count = re.subn(
                        regex, replace, text, flags=re.M | re.I)
                    text = checkReplace(text, newtext)

                    if count > 0:
                        break

                if deleted_commons:
                    comment = re.sub(r"\[\[([^\[\]]+?)]]",
                                     r"[[:c:\1]]", deletelog["comment"])
                    summary_deleted.append(cfg["summary"]["deleted"]["commons"].format(
                        imagename, deletelog["user"], deletelog["logid"], comment))
                else:
                    summary_deleted.append(cfg["summary"]["deleted"]["local"].format(
                        summary_prefix, deletelog["user"], deletelog["logid"], deletelog["comment"]))

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

                for regex_type in cfg["regex"]:
                    regex = cfg["regex"][regex_type]["pattern"].format(
                        imageregex)
                    replace = cfg["regex"][regex_type]["replace"]["comment"]

                    newtext, count = re.subn(
                        regex, replace, text, flags=re.M | re.I)
                    text = checkReplace(text, newtext)

                    if count > 0:
                        break

                summary_comment.append(
                    cfg["summary"]["comment"].format(imagename))

                continue

            # comment end

            # unknown start
            print("{} missed for unknown reason".format(image_fullname))
            # unknown end

    if page.text == text:
        print("nothing changed")
        if args.confirm:
            input()
        skipfile.write(pagetitle + "\n")
        skiplimit += 1
        if args.skiplimit > 0 and skiplimit >= args.skiplimit:
            print('Reach the skiplimit. Quitting.')
            break
        continue

    # General fixes start
    text = re.sub(r'(\|align=center\|)<br ?/?>', r'\1', text)
    text = re.sub(r'(^<!--.+-->$\n)\n+', r'\1', text, flags=re.M)
    text = re.sub(r'\n<gallery>\s+</gallery>\n', '\n', text)
    text = re.sub(r'<gallery>\s+</gallery>', '', text)
    text = re.sub(r'^\n+', '', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    # General fixes end

    pywikibot.showDiff(page.text, text)

    summary = []
    if len(summary_comment):
        summary.append(cfg["summary"]["prepend"]
                       ["comment"] + "、".join(summary_comment))
    if len(summary_moved):
        summary.append(cfg["summary"]["prepend"]
                       ["moved"] + "、".join(summary_moved))
    if len(summary_deleted):
        summary.append(cfg["summary"]["prepend"]
                       ["deleted"] + "、".join(summary_deleted))
    summary = cfg["summary"]["prepend"]["all"] + "；".join(summary)
    print("summary = {}".format(summary))

    if args.confirm:
        save = input("save?")
    else:
        save = "Yes"
    if save in ["Yes", "yes", "Y", "y", ""]:
        page.text = text
        try:
            page.save(summary=summary, minor=False)
        except pywikibot.exceptions.SpamfilterError as e:
            print(e)
            if args.confirm:
                input()
            skipfile.write(pagetitle + "\n")
            skiplimit += 1
            limit += 1
    else:
        print("skip")
        skipfile.write(pagetitle + "\n")
