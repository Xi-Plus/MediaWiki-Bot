# -*- coding: utf-8 -*-
import argparse
import hashlib
import json
import os
import re
import time
from datetime import datetime, timezone

os.environ['PYWIKIBOT_DIR'] = os.path.dirname(os.path.realpath(__file__))
import pywikibot
from config import config_page_name  # pylint: disable=E0611,W0614


os.environ['TZ'] = 'UTC'

parser = argparse.ArgumentParser()
parser.add_argument('-f', '--force', dest='force', action='store_true')
parser.set_defaults(force=False)
args = parser.parse_args()

site = pywikibot.Site()
site.login()

config_page = pywikibot.Page(site, config_page_name)
cfg = config_page.text
cfg = json.loads(cfg)

if not cfg['enable']:
    print('disabled')
    exit()

outputPage = pywikibot.Page(site, cfg['output_page_name'])
lastEditTime = list(outputPage.revisions(total=1))[0]['timestamp']
lastEditTimestamp = datetime(lastEditTime.year, lastEditTime.month, lastEditTime.day,
                             lastEditTime.hour, lastEditTime.minute, tzinfo=timezone.utc).timestamp()
if time.time() - lastEditTimestamp < cfg['interval'] and not args.force:
    print('Last edit on {0}'.format(lastEditTime))
    exit()

cat = pywikibot.Page(site, cfg['category'])

output = '{{/header}}'
for page in site.categorymembers(cat):
    title = page.title()
    in_whitelist = False
    for whitelist in cfg['whitelist']:
        if re.search(whitelist, title):
            in_whitelist = True
            break
    if in_whitelist:
        continue
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
            firstuser = ''
            lasttime = datetime(1, 1, 1, tzinfo=timezone.utc)
            lastuser = ''
            for m in re.findall(r'(.+)(\d{4})年(\d{1,2})月(\d{1,2})日 \(.\) (\d{2}):(\d{2}) \(UTC\)', str(section)):
                d = datetime(int(m[1]), int(m[2]), int(m[3]),
                             int(m[4]), int(m[5]), tzinfo=timezone.utc)

                username = ''
                m2 = re.search(r'.*\[\[(?:(?:User|User[ _]talk|U|UT|用户|用戶|使用者|用戶對話|用戶討論|用户对话|用户讨论|使用者討論):|(?:Special|特殊):(?:(?:Contributions|Contribs)|(?:用户|用戶|使用者)?(?:贡献|貢獻))/)([^|\]/#]+)', m[0], flags=re.I)
                if m2:
                    username = m2.group(1)

                if d < firsttime:
                    firsttime = d
                    firstuser = username
                if d > lasttime:
                    lasttime = d
                    lastuser = username
            if firsttime == datetime(9999, 12, 31, tzinfo=timezone.utc):
                firstvalue = 0
            else:
                firstvalue = int(firsttime.timestamp())
            if lasttime == datetime(1, 1, 1, tzinfo=timezone.utc):
                lastvalue = 0
            else:
                lastvalue = int(lasttime.timestamp())

            requester = ''

            output += '\n{{{{/item|link={0}{1}|title={0}|firstuser={2}|firsttime={3}|lastuser={4}|lasttime={5}}}}}'.format(
                title, sechash, firstuser, firstvalue, lastuser, lastvalue)

output += '\n{{/footer}}'

outputPage.text = output
outputPage.save(summary=cfg['summary'])
