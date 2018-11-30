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

config_page = pywikibot.Page(site, config_page_name)
cfg = config_page.text
cfg = json.loads(cfg)
print(json.dumps(cfg, indent=4, ensure_ascii=False))

if not cfg["enable"]:
    exit("disabled\n")

cat = pywikibot.Page(site, "Category:缺少文件的条目")

for page in site.categorymembers(cat):
    print(page.title())
    text = page.text
    summary = []
    for image in page.imagelinks():
        if not image.exists():
            try:
                if image.fileIsShared():
                    continue
            except Exception as e:
                pass
            
            imagename = image.title(with_ns=False)
            
            imageregex = "[" + imagename[0].upper() + imagename[0].lower() + "]" + re.escape(imagename[1:])
            imageregex = imageregex.replace("\ ", "[ _]")
            imageregex = imageregex
            
            existonen = pywikibot.Page(site, "en:File:{}".format(imagename)).exists()
            
            if not existonen:
                print("File:{} not exist".format(imagename))
            
                regex = r"^(\s*\|\s*(?:image|logo|map_image)\s*=\s*(?:(File|Image):)?)"+imageregex+"\s*$"
                text = re.sub(regex, r"\1", text, flags=re.M)

                regex = r"\[\[(File|Image):" + imageregex + r"\s*\|[^\]]+\]\](?:\n(?!\s*\|))?"
                text = re.sub(regex, r"", text)
                
                summary.append("移除不存在檔案 File:{}".format(imagename))
            else:
                print("File:{} exist on en".format(imagename))
                
                regex = r"^(\s*\|\s*(?:image|logo|map_image)\s*=\s*)((?:File:)?"+imageregex+"\s*)$"
                text = re.sub(regex, r"\1<!-- \2 ，可於英文維基百科取得 -->", text, flags=re.M)

                regex = r"(\[\[File:" + imageregex + r"\s*\|[^\]]+\]\])"
                text = re.sub(regex, r"<!-- \1 ，可於英文維基百科取得 -->", text)
                
                summary.append("注釋掉檔案 File:{0} ，不存在於本地，可於[[en:File:{0}|英文維基百科]]取得".format(imagename))
    if page.text == text:
        print("nothing changed")
        continue
    pywikibot.showDiff(page.text, text)
    summary = "；".join(summary)
    print("summary = {}".format(summary))
    save = input("save?")
    if save in ["Yes", "yes", "Y", "y"]:
        page.text = text
        page.save(summary=summary, minor=False)
