# -*- coding: utf-8 -*-
import os
import re
import sys
from datetime import datetime, timedelta

import mwparserfromhell
os.environ['PYWIKIBOT_DIR'] = os.path.dirname(os.path.realpath(__file__))
import pywikibot

from config import cfg  # pylint: disable=E0611,W0614


site = pywikibot.Site()
site.login()


output = (
    '{| class="wikitable sortable"'
    '\n|-'
    '\n! 日期 !! 條目 !! 關閉代碼 !! 留言 !! 關閉者'
)


def fix(pagename):
    global output  # pylint: disable=W0603
    if re.search(r'\d{4}/\d{2}/\d{2}', pagename):
        pagename = 'Wikipedia:頁面存廢討論/記錄/' + pagename

    print('-' * 50)
    print('running for ' + pagename)

    afdpage = pywikibot.Page(site, pagename)
    text = afdpage.text

    wikicode = mwparserfromhell.parse(text)

    for secid, section in enumerate(list(wikicode.get_sections())):
        if secid == 0:
            continue

        sectext = str(section)
        title = str(section.get(0).title)

        if re.search(r'{{\s*(delh|TalkendH)\s*\|', sectext, re.IGNORECASE) is None:
            continue
        if re.search(r'===(.+?)===\n', re.sub(r'^.+\n', '', sectext)):
            # print(secid, title, 'contains sub title')
            continue
        if 'class="NAC"' not in sectext:
            continue

        code = 'no code'
        m = re.search(r'{{delh\|(.+?)}}', sectext)
        if m:
            code = m.group(1)

        comment = 'no comment'
        m = re.search(r'\n(.+<span class="NAC">.+)\n', sectext)
        if m:
            comment = m.group(1)

        comment_pre = re.sub(r'<span class="NAC">.+$', '', comment)
        comment_pre = re.sub(r'^[:*]* *', '', comment_pre)

        comment_suf = re.sub(r'^.+<span class="NAC">', '', comment)

        user = 'no user'
        m = re.search(
            r'\[\[(?:(?:User(?:[ _]talk)?|U|UT):|Special:(?:(?:Contributions|Contribs)|(?:用户|用戶|使用者)?(?:贡献|貢獻))/)([^|\]]+)', comment_suf)
        if m:
            user = m.group(1)

        print(secid, title, code, comment_pre, user)
        link = ''
        if '{{al|' in title:
            link = '[[{0}|<nowiki>{1}</nowiki>]]'.format(pagename, title)
        else:
            link = '[[{0}#{{{{subst:anchorencode:{1}}}}}|{{{{subst:anchorencode:{1}}}}}]]'.format(
                pagename, title)
        output += (
            '\n|-'
            '\n| {0}'
            '\n| {1}'
            '\n| {2}'
            '\n| {3}'
            '\n| {{{{User|{4}}}}}'
        ).format(
            pagename[-10:],
            link,
            code,
            comment_pre,
            user,
        )


if len(sys.argv) >= 2:
    pagename = sys.argv[1]
    fix(pagename)
else:
    print('run past {} days'.format(cfg['run_past_days']))
    for delta in range(cfg['run_past_days']):
        rundate = datetime.now() - timedelta(days=delta)
        pagename = rundate.strftime('%Y/%m/%d')
        fix(pagename)

output += '\n|}'

print(output)
with open('out.txt', 'w') as f:
    f.write(output)
