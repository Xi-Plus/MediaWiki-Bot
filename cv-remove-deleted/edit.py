# -*- coding: utf-8 -*-
import argparse
import hashlib
import json
import os
import re
import time

os.environ['PYWIKIBOT_DIR'] = os.path.dirname(os.path.realpath(__file__))
import pywikibot
from pywikibot.data.api import Request
from config import config_page_name  # pylint: disable=E0611,W0614

parser = argparse.ArgumentParser()
parser.add_argument('--confirm', action='store_true')
parser.set_defaults(confirm=False)
args = parser.parse_args()
print(args)

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

rndstr = hashlib.md5(str(time.time()).encode()).hexdigest()
text = re.sub(r'^(===.*=== *)$', rndstr + r'\1', text, flags=re.M)
sections = text.split(rndstr)

removedcnt = 0
remaincnt = 0
istimeout = False
for secid, section in enumerate(sections[1:], 1):
    title = section[:section.index('\n')]
    print(title, end="\t")
    text = section[section.index('\n') + 1:]

    rndstr = hashlib.md5(str(time.time()).encode()).hexdigest()
    text = re.sub(r"^(.*{{CopyvioEntry\|.+)$", rndstr + r"\1", text, flags=re.M)

    text = text.split(rndstr)

    entrycnt = len(text[1:])
    print(entrycnt)

    newtext = title + '\n' + text[0]
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
                for reversion in page.revisions():
                    if reversion.timestamp.timestamp() < entrytime - 86400 * 7:
                        break
                    if re.search(r"替换为未侵权版本|清理\[\[Category:已完成侵權驗證的頁面]]", reversion.comment):
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
                if len(data['query']['logevents']) > 0:
                    print(data['query']['logevents'][0]['comment'])
                    remove = True

            if remove:
                cnt += 1
            else:
                if not istimeout:
                    remaincnt += 1
                print("not remove")
                newtext += entry
        else:
            print("not match")
            newtext += entry

    if cnt == entrycnt:
        print("\t*** remove {} entry and section".format(cnt))
        sections[secid] = ''
    elif cnt > 0:
        print("\t*** remove {} entry".format(cnt))
        sections[secid] = newtext

    removedcnt += cnt

    if istimeout:
        break

text = ''.join(sections)

if cvpage.text == text:
    exit("nothing changed")

pywikibot.showDiff(cvpage.text, text)
cvpage.text = text
summary = cfg["page_summary"].format(removedcnt, remaincnt)
print(summary)
if args.confirm:
    save = input('Save?').lower()
else:
    save = 'yes'
if save in ['yes', 'y', '']:
    cvpage.save(summary=summary, minor=False)
