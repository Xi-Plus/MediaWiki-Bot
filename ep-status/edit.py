# -*- coding: utf-8 -*-
import hashlib
import json
import os
import re
import time
from datetime import datetime, timezone

os.environ['PYWIKIBOT_DIR'] = os.path.dirname(os.path.realpath(__file__))
import pywikibot

from config import *


os.environ['TZ'] = 'UTC'

site = pywikibot.Site()
site.login()

config_page = pywikibot.Page(site, config_page_name)
cfg = config_page.text
cfg = json.loads(cfg)
print(json.dumps(cfg, indent=4, ensure_ascii=False))

if not cfg['enable']:
    exit('disabled\n')

outputPage = pywikibot.Page(site, cfg['output_page_name'])
lastEditTime = list(outputPage.revisions(total=1))[0]['timestamp']
lastEditTimestamp = datetime(lastEditTime.year, lastEditTime.month, lastEditTime.day,
                             lastEditTime.hour, lastEditTime.minute, tzinfo=timezone.utc).timestamp()
if time.time() - lastEditTimestamp < cfg['interval']:
    exit('Last edit on {0}\n'.format(lastEditTime))

cat = pywikibot.Page(site, cfg['category'])

output = (
    '{| class="wikitable sortable"'
    '\n|-'
    '\n! 頁面 !! 提出日 !! 最後編輯'
)
for page in site.categorymembers(cat):
    title = page.title()
    in_whitelist = False
    for whitelist in cfg['whitelist']:
        if re.search(whitelist, title):
            in_whitelist = True
            break
    if in_whitelist:
        continue
    print(title)
    text = page.text

    rndstr = hashlib.md5(str(time.time()).encode()).hexdigest()
    text = re.sub(r'^(==[^=]+==)$', rndstr + r'\1', text, flags=re.M)
    text = text.split(rndstr)

    eps = []
    headers = {}
    for section in text:
        sechash = ''
        m = re.match(r'^==\s*([^=]+?)\s*==$', section, flags=re.M)
        if m:
            sechash = m.group(1)
            sechash = re.sub(r'\[\[:?([^\|]+?)]]', r'\1', sechash)
            sechash = sechash.strip()
            if sechash in headers:
                headers[sechash] += 1
                sechash += '_{0}'.format(headers[sechash])
            else:
                headers[sechash] = 1
            sechash = '#{{{{subst:anchorencode:{0}}}}}'.format(sechash)

        section = re.sub(r'<nowiki>[\s\S]+?</nowiki>', '', section)

        if (re.search(r'{{(Editprotected|Editprotect|Sudo|EP|请求编辑|编辑请求|請求編輯受保護的頁面|Editsemiprotected|FPER|Fper|Edit[ _]fully-protected|SPER|Edit[ _]semi-protected|Edit[ _]protected|Ep)(\||}})', section, flags=re.I)
                and not re.search(r'{{(Editprotected|Editprotect|Sudo|EP|请求编辑|编辑请求|請求編輯受保護的頁面|Editsemiprotected|FPER|Fper|Edit[ _]fully-protected|SPER|Edit[ _]semi-protected|Edit[ _]protected|Ep).*?\|(ok|no)=', section, flags=re.I)):

            firsttime = datetime(9999, 12, 31, tzinfo=timezone.utc)
            lasttime = datetime(1, 1, 1, tzinfo=timezone.utc)
            for m in re.findall(r'(\d{4})年(\d{1,2})月(\d{1,2})日 \(.\) (\d{2}):(\d{2}) \(UTC\)', str(section)):
                d = datetime(int(m[0]), int(m[1]), int(m[2]),
                             int(m[3]), int(m[4]), tzinfo=timezone.utc)
                lasttime = max(lasttime, d)
                firsttime = min(firsttime, d)
            print(firsttime, lasttime)
            if firsttime == datetime(9999, 12, 31, tzinfo=timezone.utc):
                firstvalue = 0
            else:
                firstvalue = int(firsttime.timestamp())
            if lasttime == datetime(1, 1, 1, tzinfo=timezone.utc):
                lastvalue = 0
            else:
                lastvalue = int(lasttime.timestamp())
            output += '\n{{{{/item|[[{0}{1}|{0}]]|{2}|{3}}}}}'.format(
                title, sechash, firstvalue, lastvalue)

output += '\n|}'

print(output)
outputPage.text = output
outputPage.save(summary=cfg['summary'])
