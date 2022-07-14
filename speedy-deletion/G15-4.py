# -*- coding: utf-8 -*-
import os
import sys
import json
from config import config_page_name  # pylint: disable=E0611,W0614

os.environ['PYWIKIBOT_DIR'] = os.path.dirname(os.path.realpath(__file__))
os.environ['TZ'] = 'UTC'
import pywikibot


if len(sys.argv) < 2:
    print('no pagename provided.')
    exit()

site = pywikibot.Site()
site.login()

config_page = pywikibot.Page(site, config_page_name)
cfg = config_page.text
cfg = json.loads(cfg)["G15_4"]
print(json.dumps(cfg, indent=4, ensure_ascii=False))

if not cfg["enable"]:
    print('disabled')
    exit()

pagename = sys.argv[1]

mainpage = pywikibot.Page(site, pagename)

if mainpage.isTalkPage():
    talkpage = mainpage
    mainpage = talkpage.toggleTalkPage()
else:
    talkpage = mainpage.toggleTalkPage()

if mainpage.exists():
    print('mainpage exist.')
    exit()

if mainpage.namespace().id == 6:
    image = pywikibot.FilePage(site, mainpage.title())
    try:
        if image.file_is_shared():
            print('mainpage exist (shared file).')
            exit()
    except Exception as e:
        pass

if not talkpage.exists():
    print('talkpage not exist.')
    exit()

if talkpage.namespace().id in [3, 9]:
    print('ignore namespace.')
    exit()

if talkpage.depth > 0:
    print('ignore subpage.')
    exit()

for template in talkpage.templates():
    if template.title() in ["Template:Talk archive"]:
        print('ignore talk archive.')
        exit()
    if template.title() in ["Template:Delete"]:
        print('marked deletion.')
        exit()

if len(list(talkpage.embeddedin(total=1))) > 0:
    text = cfg["prepend_text_with_noinclude"] + talkpage.text
else:
    text = cfg["prepend_text"] + talkpage.text
pywikibot.showDiff(talkpage.text, text)
talkpage.text = text
summary = cfg["summary"]
print(summary)
talkpage.save(summary=summary, minor=False)
