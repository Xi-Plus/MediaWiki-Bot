# -*- coding: utf-8 -*-
import json
import os
import re
from datetime import datetime

os.environ['PYWIKIBOT_DIR'] = os.path.dirname(os.path.realpath(__file__))
import pywikibot
from config import config_page_name  # pylint: disable=E0611,W0614


os.environ['TZ'] = 'UTC'

site = pywikibot.Site()
site.login()

config_page = pywikibot.Page(site, config_page_name)
cfg = config_page.text
cfg = json.loads(cfg)
print(json.dumps(cfg, indent=4, ensure_ascii=False))

if not cfg["enable"]:
    exit("disabled\n")

cvpage = pywikibot.Page(site, cfg['cvpage_name'])

linksoncvpage = []
for page in cvpage.linkedPages():
    linksoncvpage.append(page.title())

linksoncvpage += cfg['whitelist']

cvtem = pywikibot.Category(site, cfg['cvcategory_name'])
notreportedpage = []
for page in cvtem.members():
    pagetitle = page.title()
    if pagetitle not in linksoncvpage:
        notreportedpage.append(pagetitle)

if len(notreportedpage) == 0:
    exit('Nothing to report')

text = cvpage.text

appendtext = ''
for pagetitle in notreportedpage:
    appendtext += '\n\n{{{{CopyvioEntry|1={0}|time={{{{subst:#time:U|+7 days}}}}|sign=~~~~}}}}'.format(pagetitle)

if appendtext:
    d = datetime.today()
    datestr = d.strftime('%-m月%-d日')
    if not re.search(r'===\s*{}\s*==='.format(datestr), text):
        text += '\n\n==={}==='.format(datestr)
    text += appendtext

if cvpage.text == text:
    exit('Nothing changed')

pywikibot.showDiff(cvpage.text, text)
cvpage.text = text
summary = cfg['summary']
print(summary)
cvpage.save(summary=summary, minor=False)
