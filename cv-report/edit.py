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
    print('Nothing to report')
    exit()

text = cvpage.text

appendtext = ''
for pagetitle in notreportedpage:
    if '{{{{CopyvioEntry|1={0}|'.format(pagetitle) in text:
        continue
    appendtext += '\n\n{{{{subst:CopyvioVFDRecord|{0}}}}}'.format(pagetitle)

if appendtext:
    d = datetime.today()
    datestr = '{}月{}日'.format(d.strftime('%-m'), d.strftime('%-d'))
    if not re.search(r'===\s*{}\s*==='.format(datestr), text):
        text += '\n\n==={}==='.format(datestr)
    text += appendtext

if cvpage.text == text:
    print('Nothing changed')
    exit()

pywikibot.showDiff(cvpage.text, text)
cvpage.text = text
summary = cfg['summary']
print(summary)
cvpage.save(summary=summary, minor=False)
