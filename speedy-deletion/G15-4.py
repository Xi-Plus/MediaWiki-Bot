# -*- coding: utf-8 -*-
import os
import sys
import json
from config import *

os.environ['PYWIKIBOT2_DIR'] = os.path.dirname(os.path.realpath(__file__))
os.environ['TZ'] = 'UTC'
import pywikibot


if len(sys.argv) < 2:
    exit("no pagename provided.\n")

site = pywikibot.Site()
site.login()

config_page = pywikibot.Page(site, config_page_name)
cfg = config_page.text
cfg = json.loads(cfg)["G15_4"]
print(json.dumps(cfg, indent=4, ensure_ascii=False))

if not cfg["enable"]:
    exit("disabled\n")

pagename = sys.argv[1]

mainpage = pywikibot.Page(site, pagename)

if mainpage.isTalkPage():
    talkpage = mainpage
    mainpage = talkpage.toggleTalkPage()
else:
    talkpage = mainpage.toggleTalkPage()

if mainpage.exists():
    exit("mainpage exist.\n");

if not talkpage.exists():
    exit("talkpage not exist.\n");

if talkpage.namespace().id in [3, 9]:
    exit("ignore namespace.\n")

if talkpage.depth > 0:
    exit("ignore subpage.\n")

for template in talkpage.templates():
    if template.title() in ["Template:Talk archive"]:
        exit("ignore talk archive.\n")
    if template.title() in ["Template:Delete"]:
        exit("marked deletion.\n")

text = cfg["prepend_text"] + talkpage.text
pywikibot.showDiff(talkpage.text, text)
talkpage.text = text
summary = cfg["summary"]
print(summary)
input("Save?")
talkpage.save(summary=summary, minor=False)
