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

from config import (CONFIG_PAGE_NAME,  # pylint: disable=E0611,W0614
                    REPLICA_CONFIG_PATH)

site = pywikibot.Site('zh', 'wikipedia')
site.login()

config_page = pywikibot.Page(site, CONFIG_PAGE_NAME)
cfg = config_page.text
cfg = json.loads(cfg)
print(json.dumps(cfg, indent=4, ensure_ascii=False))

if not cfg['enable']:
    print('disabled')
    exit()

conn = pymysql.connect(read_default_file=REPLICA_CONFIG_PATH)

QUERY_USER_WITH_SIGN = '''
SELECT rc_actor, actor_name, actor_user, up2.up_value AS `nickname`
FROM recentchanges
LEFT JOIN actor ON rc_actor = actor_id
LEFT JOIN user_properties AS up1 ON actor_user = up1.up_user AND up1.up_property = 'fancysig'
LEFT JOIN user_properties AS up2 ON actor_user = up2.up_user AND up2.up_property = 'nickname'
WHERE (rc_namespace = 4 OR rc_namespace % 2 = 1)
    AND rc_timestamp > DATE_FORMAT(DATE_SUB(NOW(), INTERVAL 7 DAY), '%Y%m%d%H%i%s')
    AND actor_user IS NOT NULL
    AND up1.up_value IS NOT NULL
    AND up2.up_value IS NOT NULL
GROUP BY actor_user
ORDER BY rc_timestamp DESC
'''

with conn.cursor() as cur:
    datelimit = datetime.now() - timedelta(days=7)
    timestamp = datelimit.strftime('%Y%m%d%H%M%S')

    cur.execute(QUERY_USER_WITH_SIGN)
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
    'action': 'parse',
    'format': 'json',
    'text': text,
    'onlypst': 1,
    'contentmodel': 'wikitext',
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
    'wikitext': text2,
}).encode(), headers={
    'Content-Type': 'application/json',
    'Accept': 'application/json',
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
