# -*- coding: utf-8 -*-
import json
import os
import re
import sys
from datetime import datetime, timedelta

import mwparserfromhell
os.environ['PYWIKIBOT_DIR'] = os.path.dirname(os.path.realpath(__file__))
import pywikibot
from pywikibot.data.api import Request


site = pywikibot.Site()
site.login()

r = Request(site=site, parameters={
    "action": "query",
    "format": "json",
    "list": "logevents",
    "leaction": "rights/rights",
    "lelimit": "max"
})
data = r.submit()

text = '''{| class="wikitable sortable"
|+
! 時間
! 管理員
! 授權天數
! 對象
! 理由
'''

for log in data['query']['logevents']:
    oldexpirys = {}
    newexpirys = {}
    for meta in log['params']['oldmetadata']:
        oldexpirys[meta['group']] = meta['expiry']
    for meta in log['params']['newmetadata']:
        newexpirys[meta['group']] = meta['expiry']

    if 'confirmed' not in newexpirys:
        continue

    if (set(log['params']['newgroups']) - set(log['params']['oldgroups']) == set(['confirmed']) and 'confirmed' not in oldexpirys) or (set(log['params']['newgroups']) == set(log['params']['oldgroups']) and 'confirmed' in oldexpirys):
        # new
        print(log['timestamp'], log['user'], log['title'], log['comment'], newexpirys['confirmed'])
        text += '|-\n'
        text += '| [[Special:redirect/logid/{}|{}]]\n'.format(log['logid'], log['timestamp'])
        text += '| {}\n'.format(log['user'])
        if newexpirys['confirmed'] == 'infinity':
            text += '| infinity\n'
        else:
            text += '| {{{{subst:#expr: floor(({{{{subst:#time:U|{} }}}}-{{{{subst:#time:U|{} }}}}) / 86400) }}}}\n'.format(newexpirys['confirmed'], log['timestamp'])
        text += '| [[User:{0}|{0}]]\n'.format(log['title'].replace('User:', ''))
        text += '| {}\n'.format(log['comment'])

text += '|}'

with open('out.txt', 'w', encoding='utf8') as f:
    f.write(text)
