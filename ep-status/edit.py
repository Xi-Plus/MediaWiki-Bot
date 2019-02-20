# -*- coding: utf-8 -*-
import hashlib
import json
import os
import re
import time
from datetime import datetime

os.environ['PYWIKIBOT2_DIR'] = os.path.dirname(os.path.realpath(__file__))
import pywikibot

os.environ['TZ'] = 'UTC'

site = pywikibot.Site()
site.login()

token = site.getToken()

cat = pywikibot.Page(site, 'Category:維基百科編輯被保護頁面請求')

whitelist = [
    'Category:已處理的維基百科編輯被保護頁面請求',
    'Category:待回應的維基百科編輯被保護頁面請求',
    'Category:維基百科編輯全保護頁面請求',
    'Category:維基百科編輯半保護頁面請求',
    'Category:維基百科編輯無保護頁面請求'
]

output = (
    '{| class="wikitable sortable"'
    '\n|-'
    '\n! 模板 !! 提出日 !! 最後編輯'
)
for page in site.categorymembers(cat):
    title = page.title()
    if title in whitelist:
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

        if (re.search(r'{{(Editprotected|Editprotect|Sudo|EP|请求编辑|编辑请求|請求編輯受保護的頁面|Editsemiprotected|FPER|Fper|Edit[ _]fully-protected|SPER|Edit[ _]semi-protected|Edit[ _]protected|Ep)(\||}})', section, flags=re.I)
                and not re.search(r'{{(Editprotected|Editprotect|Sudo|EP|请求编辑|编辑请求|請求編輯受保護的頁面|Editsemiprotected|FPER|Fper|Edit[ _]fully-protected|SPER|Edit[ _]semi-protected|Edit[ _]protected|Ep).*?\|(ok|no)=1', section, flags=re.I)):

            firsttime = datetime(9999, 12, 31)
            lasttime = datetime(1, 1, 1)
            for m in re.findall(r'(\d{4})年(\d{1,2})月(\d{1,2})日 \(.\) (\d{2}):(\d{2}) \(UTC\)', str(section)):
                d = datetime(int(m[0]), int(m[1]), int(
                    m[2]), int(m[3]), int(m[4]))
                lasttime = max(lasttime, d)
                firsttime = min(firsttime, d)
            print(firsttime, lasttime)
            if firsttime == datetime(9999, 12, 31):
                firstvalue = 0
                firsttimetext = '無法抓取時間'
            else:
                firstvalue = int(firsttime.timestamp())
                firsttimetext = '{{{{subst:#time:Y年n月j日 (D) H:i|{0}}}}} (UTC)'.format(
                    str(firsttime))
            if lasttime == datetime(1, 1, 1):
                lastvalue = 0
                lasttimetext = '無法抓取時間'
            else:
                lastvalue = int(lasttime.timestamp())
                lasttimetext = '{{{{subst:#time:Y年n月j日 (D) H:i|{0}}}}} (UTC)'.format(
                    str(lasttime))
            output += (
                '\n|-'
                '\n| [[{0}{1}|{0}]]'
                '\n|data-sort-value={2}| {3}'
                '\n|data-sort-value={4}| {5}'
            ).format(title, sechash, firstvalue, firsttimetext, lastvalue, lasttimetext)

output += '\n|}'

print(output)
outputPage = pywikibot.Page(site, 'User:Xiplus/EP')
outputPage.text = output
outputPage.save(summary='產生EP列表', minor=False)
