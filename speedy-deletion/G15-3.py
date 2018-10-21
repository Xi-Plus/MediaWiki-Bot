# -*- coding: utf-8 -*-
import os
import sys
import pywikibot
import json
from config import *

os.environ['PYWIKIBOT2_DIR'] = os.path.dirname(os.path.realpath(__file__))
os.environ['TZ'] = 'UTC'

if len(sys.argv) < 2:
    exit("no pagename provided.\n")

site = pywikibot.Site()
site.login()

config_page = pywikibot.Page(site, config_page_name)
cfg = config_page.text
cfg = json.loads(cfg)["G15_3"]
print(json.dumps(cfg, indent=4, ensure_ascii=False))

if not cfg["enable"]:
    exit("disabled\n")

pagename = sys.argv[1]

mainpage = pywikibot.Page(site, pagename)

if mainpage.exists():
    exit("mainpage exist.\n");

if mainpage.namespace().id in [3]:
    exit("ignore namespace.\n")

for backlink in mainpage.backlinks(filter_redirects=True):
    print(backlink.title())
    if backlink.namespace().id in [3]:
        print("ignore namespace.\n")
        continue

    marked = False
    for template in backlink.templates():
        if template.title() in ["Template:Delete"]:
            marked = True
            print("marked deletion.\n")
            continue

    if marked:
        continue

    text = cfg["prepend_text"] + backlink.text
    pywikibot.showDiff(backlink.text, text)
    backlink.text = text
    summary = cfg["summary"]
    print(summary)
    input("Save?")
    backlink.save(summary=summary, minor=False)
