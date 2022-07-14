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
cfg = json.loads(cfg)["G15_3"]
print(json.dumps(cfg, indent=4, ensure_ascii=False))

if not cfg["enable"]:
    print('disabled')
    exit()

pagename = sys.argv[1]

mainpage = pywikibot.Page(site, pagename)

if mainpage.exists():
    print('mainpage exist.')
    exit()

if mainpage.namespace().id in [2, 3]:
    print('ignore namespace.')
    exit()

for backlink in mainpage.backlinks(filter_redirects=True):
    print(backlink.title())
    if backlink.namespace().id in [2, 3]:
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

    if len(list(backlink.embeddedin(total=1))) > 0:
        text = cfg["prepend_text_with_noinclude"] + backlink.text
    else:
        text = cfg["prepend_text"] + backlink.text
    pywikibot.showDiff(backlink.text, text)
    backlink.text = text
    summary = cfg["summary"]
    print(summary)
    backlink.save(summary=summary, minor=False)
