# -*- coding: utf-8 -*-
import json
import os
import re

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
for page in cvpage.linkedPages(namespaces=[0, 118]):
    linksoncvpage.append(page.title())

cvtem = pywikibot.Page(site, cfg['cvtemplate_name'])
notreportedpage = []
for page in cvtem.embeddedin(namespaces=[0, 118]):
    pagetitle = page.title()
    if pagetitle not in linksoncvpage:
        notreportedpage.append(pagetitle)

if len(notreportedpage) == 0:
    exit('Nothing to report')

text = cvpage.text

appendtext = ''
for pagetitle in notreportedpage:
    appendtext += '{{{{CopyvioEntry|1={0}|time={{{{subst:#time:U}}}}|sign=~~~~}}}}\n\n'.format(pagetitle)

if '=== 未知日期 ===' in text:
    text = re.sub(r'(^=== 未知日期 ===.*\n[\s\S]*?\n)(===)', r'\1{}\2'.format(appendtext), text, flags=re.M)
else:
    appendtext = '=== 未知日期 ===\n\n' + appendtext
    text = re.sub(r'(^==當前的疑似侵權條目==.*\n[\s\S]*?\n)(===)', r'\1{}\2'.format(appendtext), text, flags=re.M)

if cvpage.text == text:
    exit('Nothing changed')

pywikibot.showDiff(cvpage.text, text)
cvpage.text = text
summary = cfg['summary']
print(summary)
cvpage.save(summary=summary, minor=False)
