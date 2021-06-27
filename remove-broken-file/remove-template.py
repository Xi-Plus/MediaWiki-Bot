# -*- coding: utf-8 -*-
import argparse
import json
import os
import re
import time
from datetime import datetime, timezone

import pymysql
os.environ["PYWIKIBOT_DIR"] = os.path.dirname(os.path.realpath(__file__))
import pywikibot

from config import config_page_name, database, skip_time, skip_title  # pylint: disable=E0611,W0614


os.environ["TZ"] = "UTC"

parser = argparse.ArgumentParser()
parser.add_argument('--category', type=str, default=None)
parser.add_argument('--page', type=str, default=None)
parser.add_argument('--confirm', action='store_true')
args = parser.parse_args()
pywikibot.log(args)

site = pywikibot.Site()
site.login()
sitecommons = pywikibot.Site("commons", "commons")

config_page = pywikibot.Page(site, config_page_name)
cfg = config_page.text
cfg = json.loads(cfg)
pywikibot.log(json.dumps(cfg, indent=4, ensure_ascii=False))

if not cfg["enable"]:
    exit("disabled\n")


def checkImageExists(title):
    image = pywikibot.FilePage(site, title)
    if image.exists():
        return True
    try:
        if image.file_is_shared():
            return True
    except Exception:
        pass
    return False


if args.page:
    pages = [pywikibot.Page(site, args.page)]
else:
    pages = list(pywikibot.Page(site, cfg['marker_template']).embeddedin())

for page in pages:
    pagetitle = page.title()
    pywikibot.log('{}'.format(pagetitle))

    if page.namespace().id in [8]:
        pywikibot.log('Skip page in specify namespace.')
        continue

    text = page.text

    m = re.findall(r'{{Show if file exists\|.*?file=([^|]+?)(?:\||}})', text)
    for title in m:
        if checkImageExists(title):
            text = re.sub(
                r'{{{{(Show if file exists\|.*file={0})(\||}}}})'.format(re.escape(title)),
                r'{{subst:\1\2',
                text
            )

    if page.text == text:
        pywikibot.log('nothing changed')
        if args.confirm:
            input()
        continue

    pywikibot.showDiff(page.text, text)

    if args.confirm:
        save = input('save?')
    else:
        save = 'Yes'
    if save in ['Yes', 'yes', 'Y', 'y', '']:
        page.text = text
        page.save(summary=cfg['marker_summary'], minor=False)
    else:
        pywikibot.log('skip')
