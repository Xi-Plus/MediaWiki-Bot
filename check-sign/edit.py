#!/usr/bin/env python
# coding: utf-8

import bisect
import json
import os
import re
from datetime import datetime, timedelta

import pymysql
os.environ['PYWIKIBOT_DIR'] = os.path.dirname(os.path.realpath(__file__))
import pywikibot
import requests

from config import config_page_name, host, password, user  # pylint: disable=E0611,W0614


site = pywikibot.Site('zh', 'wikipedia')
site.login()

config_page = pywikibot.Page(site, config_page_name)
cfg = config_page.text
cfg = json.loads(cfg)
print(json.dumps(cfg, indent=4, ensure_ascii=False))

if not cfg['enable']:
    exit('disabled\n')

conn = pymysql.connect(
    host=host,
    user=user,
    password=password,
    charset="utf8"
)

with conn.cursor() as cur:
    datelimit = datetime.now() - timedelta(days=7)
    timestamp = datelimit.strftime('%Y%m%d%H%M%S')

    cur.execute('use zhwiki_p')
    cur.execute("""
        SELECT rc_actor, actor_name, actor_user,
            up_value AS `nickname`
        FROM (
            SELECT rc_actor, actor_name, actor_user,
                up_value AS `fancysig`
            FROM (
                SELECT rc_actor, actor_name, actor_user
                FROM (
                    SELECT DISTINCT rc_actor
                    FROM recentchanges
                    WHERE (rc_namespace = 4 OR rc_namespace % 2 = 1)
                        AND rc_timestamp > {}
                    ORDER BY rc_timestamp DESC
                ) temp1
                LEFT JOIN actor ON rc_actor = actor_id
                WHERE actor_user IS NOT NULL
            ) temp2
            LEFT JOIN user_properties  ON actor_user = up_user AND up_property = 'fancysig'
            WHERE up_value IS NOT NULL
        ) temp3
        LEFT JOIN user_properties ON actor_user = up_user AND up_property = 'nickname'
        WHERE up_value IS NOT NULL AND up_value != ''
    """.format(timestamp))
    res = cur.fetchall()

usernames = []
raw_sign = {}
text = ''
for row in res:
    username = row[1].decode()
    sign = row[3].decode()
    raw_sign[username] = sign
    usernames.append(username)
    text += '<!-- {0} start -->{1}<!-- {0} end -->\n'.format(username, sign)

print('Process {} users'.format(len(usernames)))

API = 'https://zh.wikipedia.org/w/api.php'
data = requests.post(API, data={
    "action": "parse",
    "format": "json",
    "text": text,
    "onlypst": 1,
    "contentmodel": "wikitext",
    "utf8": 1
}).json()

parsed_text = data['parse']['text']['*']

text2 = ''
text2index = []
expanded_sign = {}
sign_errors = {}
hide_sign = {}
for username in usernames:
    flag = '<!-- {} start -->'.format(username)
    idx1 = parsed_text.index(flag)
    idx2 = parsed_text.index('<!-- {} end -->'.format(username))
    sign = parsed_text[idx1 + len(flag):idx2]
    clearsign = re.sub(r'[^\x00-\x7F]', 'C', sign)

    expanded_sign[username] = sign
    sign_errors[username] = set()
    hide_sign[username] = False
    text2 += '<div id="sign-{}">{}</div>\n'.format(username, clearsign)
    text2index.append(len(text2))
    if '[[File:' in sign:
        sign_errors[username].add('檔案')
    if '<div' in sign:
        sign_errors[username].add('div')
        hide_sign[username] = True
    if len(re.findall(r'{{', sign)) > len(re.findall(r'{{!}}', sign)):
        sign_errors[username].add('模板')
    if '<templatestyles' in sign:
        sign_errors[username].add('模板樣式')
    if re.search(r'\[(https?)?://', sign):
        sign_errors[username].add('外部連結')
    signlen = len(sign.encode())
    if signlen >= 280:
        sign_errors[username].add('簽名過長-{{{{red|{}}}}}'.format(signlen))
    elif signlen >= 270:
        sign_errors[username].add('簽名過長-{{{{orange|{}}}}}'.format(signlen))
    elif signlen > 255:
        sign_errors[username].add('簽名過長-{}'.format(signlen))

data = requests.post('https://zh.wikipedia.org/api/rest_v1/transform/wikitext/to/lint', data=json.dumps({
    "wikitext": text2,
}).encode(), headers={
    'Content-Type': 'application/json',
    'Accept': "application/json",
}).json()

for row in data:
    idx = bisect.bisect_left(text2index, row['dsr'][0])
    username = usernames[idx]
    linttype = row['type']
    linttag = row['params']['name']
    if linttype == 'obsolete-tag':
        linttype = '過時的標籤'
    sign_errors[username].add('{}-{}'.format(linttype, linttag))

text3 = '''{| class="wikitable sortable"
!使用者
!檢查
!簽名
!問題
'''
for username in sorted(usernames):
    error = sign_errors[username]
    if len(error) > 0:
        checklink = '[https://signatures.toolforge.org/check/zh.wikipedia.org/{} check]'.format(username.replace(' ', '%20'))
        sign = ''
        if not hide_sign[username]:
            sign = expanded_sign[username]
        error = '、'.join(sorted(list(error)))
        text3 += '''|-
| [[Special:Contributions/{0}|{0}]]
| {1}
| {2}
| {3}
'''.format(username, checklink, sign, error)

text3 += '|}'

page = pywikibot.Page(site, cfg['output_page'])

print('Diff:')
pywikibot.showDiff(page.text, text3)
print('-' * 50)

page.text = text3
page.save(summary=cfg['summary'], minor=False)
