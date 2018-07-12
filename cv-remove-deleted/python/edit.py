# -*- coding: utf-8 -*-
import os
import pywikibot
import mwparserfromhell
import json
import re
import time
import hashlib
from config import *
from pywikibot.data.api import Request

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

cvpage = pywikibot.Page(site, cfg["page_name"])
text = cvpage.text

wikicode = mwparserfromhell.parse(text)

totalcnt = 0
istimeout = False
for section in wikicode.get_sections()[2:]:
    title = str(section.get(0).title)
    print(title, end="\t")
    text = str(section)

    rndstr = hashlib.md5(str(time.time()).encode()).hexdigest()
    text = re.sub(r"^(.*{{CopyvioEntry\|.+)$", rndstr+r"\1", text, flags=re.M)

    text = text.split(rndstr)

    entrycnt = len(text[1:])
    print(entrycnt)

    newtext = text[0]
    cnt = 0
    for entry in text[1:]:
        m = re.match(r"{{CopyvioEntry\|1=([^|]+)\|time=(\d+)\|", entry)
        if m:
            pagename = m.group(1)
            entrytime = int(m.group(2))
            print("\t", pagename, entrytime, end="\t")
            if entrytime > time.time():
                istimeout = True
                print("timeout", end="\t")
            page = pywikibot.Page(site, pagename)
            remove = False
            if page.exists():
                for reversion in page.getVersionHistory():
                    if "替换为未侵权版本" in reversion.comment:
                        print(reversion.comment)
                        remove = True
                        break
            else:
                data = Request(site=site, parameters={
                    'action': 'query',
                    'letitle': pagename,
                    "list": "logevents",
                    "leprop": "comment",
                    "letype": "delete",
                    "lelimit": "1"
                    }).submit()
                print(data['query']['logevents'][0]['comment'])
                remove = True

            if remove:
                cnt += 1
            else:
                print("not remove")
                newtext += entry
        else:
            print("not match")
            newtext += entry

    if cnt == entrycnt:
        print("\t*** remove {} entry and section".format(cnt))
        wikicode.remove(section)
    elif cnt > 0:
        print("\t*** remove {} entry".format(cnt))
        wikicode.replace(section, newtext)

    totalcnt += cnt

    if istimeout:
        break

text = str(wikicode)

if cvpage.text == text:
    exit("nothing changed")

pywikibot.showDiff(cvpage.text, text)
cvpage.text = text
summary = cfg["page_summary"].format(totalcnt)
print(summary)
input("Save?")
cvpage.save(summary=summary, minor=False)
