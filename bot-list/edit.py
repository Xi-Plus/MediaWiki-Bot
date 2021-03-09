# -*- coding: utf-8 -*-
import json
import os
import re
from collections import defaultdict
from datetime import datetime
from functools import cmp_to_key

os.environ['PYWIKIBOT_DIR'] = os.path.dirname(os.path.realpath(__file__))
import pywikibot
from pywikibot.data.api import Request

from config import config_page_name  # pylint: disable=E0611,W0614

os.environ['TZ'] = 'UTC'

site = pywikibot.Site()
site.login()

# config_page = pywikibot.Page(site, config_page_name)
# cfg = config_page.text
# cfg = json.loads(cfg)
# print(json.dumps(cfg, indent=4, ensure_ascii=False))

# if not cfg['enable']:
#     exit('disabled\n')

cfg = {
    'category': 'Category:已批准機械人作業申請',
    'flag1': '<!-- bot:start -->',
    'flag2': '<!-- bot:end -->',
    'page': 'User:Xiplus/沙盒',
    'summary': '機器人：產生機器人列表',
}


cat = pywikibot.Category(site, cfg['category'])
data = []
cntbot = defaultdict(int)
cntoperator = defaultdict(int)
for page in cat.members():
    text = page.text

    botname = None
    m = re.search(r'==(.+?)==', text)
    if m:
        m2 = re.search(r'\[\[:?(?:(?:User(?:[ _]talk)?|U|UT|用户|用戶|使用者|用戶對話|用戶討論|用户对话|用户讨论|使用者討論):|(?:Special|特殊):(?:(?:Contributions|Contribs)|(?:用户|用戶|使用者)?(?:贡献|貢獻))/)([^\]/|]+)', m.group(1), flags=re.I)
        if m2:
            botname = pywikibot.tools.normalize_username(m2.group(1))
        else:
            print('Fail to get botname')

    operator = None
    m = re.search(r"(?:'''操作者：'''|Operator:|'''Operator''':)(.+?)\n", text)
    if m:
        m2 = re.search(
            r'\[\[(?::?[a-z]{2})?:?(?:(?:User(?:[ _]talk)?|U|UT|用户|用戶|使用者|用戶對話|用戶討論|用户对话|用户讨论|使用者討論):|(?:Special|特殊):(?:(?:Contributions|Contribs)|(?:用户|用戶|使用者)?(?:贡献|貢獻))/)([^\]/|]+)', m.group(1), flags=re.I)
        if m2:
            operator = pywikibot.tools.normalize_username(m2.group(1))
        else:
            print('Fail to get username')
    else:
        print('Fail to find operator line')

    task = None
    m = re.search(r"(?:'''用途：'''|Tasks:|'''Function''':|'''Function:''')(.+?)\n", text)
    if m:
        task = m.group(1)
    else:
        print('Fail to get task')

    idx = 1
    m = re.search(r'Wikipedia:机器人/申请/[^/]+/(\d+)', page.title())
    if m:
        idx = int(m.group(1))

    cntbot[botname] += 1
    cntoperator[(botname, operator)] += 1
    data.append({
        'page': page.title(),
        'idx': idx,
        'bot': botname,
        'operator': operator,
        'task': task,
    })

groups = {}
for botname in cntbot:
    groups[botname] = []

    user = pywikibot.User(site, botname)

    if len(user.groups()) == 0:
        print(botname, 'is missing')
        continue

    if 'bot' in user.groups():
        groups[botname].append('有')
    else:
        res = Request(site=site, parameters={
            "action": "query",
            "format": "json",
            "meta": "globaluserinfo",
            "guiuser": botname,
            "guiprop": "groups"
        }
        ).submit()
        if 'global-bot' in res['query']['globaluserinfo']['groups']:
            groups[botname].append('全域')

    if 'sysop' in user.groups():
        groups[botname].append('管理')


def cmp(a, b):
    if a['bot'] == b['bot']:
        if a['operator'] == b['operator']:
            return -1 if a['idx'] < b['idx'] else 1
        return -1 if a['operator'] < b['operator'] else 1
    return -1 if a['bot'] < b['bot'] else 1


data.sort(key=cmp_to_key(cmp))
text = '''\
{| class="wikitable sortable" style="word-break: break-all;"
! width="15%"|用戶名
! width="15%"|操作者
! width="58%"|已批准操作
! width="7%"|申請頁
! width="5%"|機械人權限
'''
cnt2 = defaultdict(bool)
for row in data:
    botname = row['bot']
    operator = row['operator']

    text += '|-\n'

    if botname not in cnt2:
        text += '| '
        if cntbot[botname] > 1:
            text += 'rowspan={} | '.format(cntbot[botname])
        text += '[[User:{0}|{0}]] \n'.format(botname)

    if (botname, operator) not in cnt2:
        text += '| '
        if cntoperator[(botname, operator)] > 1:
            text += 'rowspan={} |'.format(cntoperator[(botname, operator)])
        text += '[[User:{0}|{0}]] \n'.format(operator)

    text += '| {} \n'.format(row['task'])
    text += '| [[{0}|存檔{1}]] \n'.format(row['page'], row['idx'])
    text += '| {} \n'.format('<br>'.join(groups[botname]))

    cnt2[botname] = True
    cnt2[(botname, operator)] = True
text += '|}'
# print(text)

page = pywikibot.Page(site, cfg['page'])

try:
    idx1 = page.text.index(cfg['flag1']) + len(cfg['flag1'])
    idx2 = page.text.index(cfg['flag2'])
except Exception:
    print('Cannot find position to insert table')
    exit()

newtext = page.text[:idx1] + text + page.text[idx2:]

pywikibot.showDiff(page.text, newtext)
page.text = newtext
summary = cfg['summary']
page.save(summary=summary, minor=False)
