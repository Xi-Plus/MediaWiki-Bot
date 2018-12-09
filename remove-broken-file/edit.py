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

cat = pywikibot.Page(site, "Category:缺少文件的条目")

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
            
            checkotherwiki = {
                "en": "英文維基百科"
            }
            existother = None
            for wiki in checkotherwiki:
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
                    if "CSD F7" in deletelog['comment']:
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
                
                regex = r"(^\s*\|\s*(?:image|logo|map_image)\s*=\s*)((?:(?:File|Image):)?{0})\s*$".format(imageregex)
                if deleted:
                    replace = r"\1"
                else:
                    replace = r"\1<!-- 檔案不存在 \2  -->"

                text = re.sub(regex, replace, text, flags=re.M)

                regex = r"(\[\[(?:File|Image):{0}\s*(?:\|(?:\[\[[^[\]]*\]\]|[^[\]])*)?\]\])[ \t]*".format(imageregex)
                if deleted:
                    replace = ""
                else:
                    replace = r"<!-- 檔案不存在 \1 -->"

                text = re.sub(regex, replace, text)

            else:
                print("File:{} exist on {}".format(imagename, existother))
                
                regex = r"^(\s*\|\s*(?:image|logo|map_image)\s*=\s*)((?:(?:File|Image):)?{0}\s*)$".format(imageregex)
                if deleted:
                    replace = r"\1"
                else:
                    replace = r"\1<!-- 檔案不存在 \2 ，可從{0}取得 -->".format(checkotherwiki[existother])
                text = re.sub(regex, replace, text, flags=re.M)

                regex = r"(\[\[(?:File|Image):{0}\s*(?:\|(?:\[\[[^[\]]*\]\]|[^[\]])*)?\]\])[ \t]*".format(imageregex)
                if deleted:
                    replace = ""
                else:
                    replace = r"<!-- 檔案不存在 \1 ，可從{0}取得 -->".format(checkotherwiki[existother])
                text = re.sub(regex, replace, text)

            if deleted:
                if deletedoncommons:
                    comment = re.sub(r"\[\[([^\[\]]+?)]]", r"[[:c:\1]]", deletelog["comment"])
                    summary_remove.append("{0}，已被[[:c:Special:Contributions/{1}|{1}]][[:c:Special:Redirect/logid/{2}|刪除]]：{3}".format(imagename, deletelog["user"], deletelog["logid"], comment))
                else:
                    summary_remove.append("{0}，已被[[Special:Contributions/{1}|{1}]][[Special:Redirect/logid/{2}|刪除]]：{3}".format(imagename, deletelog["user"], deletelog["logid"], deletelog["comment"]))
            else:
                if existother:
                    summary_comment.append("{0}（[[:{1}:File:{0}|從{1}取得]]）".format(imagename, existother))
                else:
                    summary_comment.append(imagename)

    if page.text == text:
        print("nothing changed")
        skipfile.write(pagetitle + "\n")
        continue

    pywikibot.showDiff(page.text, text)

    summary = []
    if len(summary_comment):
        summary.append("注釋不存在檔案：" + "、".join(summary_comment))
    if len(summary_remove):
        summary.append("移除檔案：" + "、".join(summary_remove))
    summary = "；".join(summary)
    print("summary = {}".format(summary))

    save = input("save?")
    if save in ["Yes", "yes", "Y", "y"]:
        page.text = text
        page.save(summary=summary, minor=False)
    else:
        print("skip")
        skipfile.write(pagetitle + "\n")
