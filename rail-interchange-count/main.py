# -*- coding: utf-8 -*-
from collections import defaultdict
import pymysql
from config import host, password, user  # pylint: disable=E0611,W0614


query = '''
SELECT cl_sortkey_prefix, COUNT(*) AS cnt
FROM categorylinks
WHERE cl_to = '使用Rail-interchange的頁面'
GROUP BY cl_sortkey_prefix
'''

conn = pymysql.connect(
    host=host,
    user=user,
    password=password,
    charset='utf8'
)
with conn.cursor() as cursor:
    cursor.execute('use zhwiki_p')
    cursor.execute(query)
    result = cursor.fetchall()

maincnt = defaultdict(int)
subcnt = defaultdict(lambda: defaultdict(int))
for row in result:
    params = row[0].decode().split('-')
    cnt = row[1]
    maincnt[params[0]] += cnt
    subcnt[params[0]]['-'.join(params[1:])] += cnt

text = '''{| class="wikitable sortable" style="word-break: break-all;"
! param 1
! count
! param 2
! count
|-
'''

for key in sorted(maincnt.keys()):
    text += '| rowspan={} | {}\n'.format(len(subcnt[key]), key)
    text += '| rowspan={} | {}\n'.format(len(subcnt[key]), maincnt[key])
    for subkey in sorted(subcnt[key].keys()):
        text += '| {}\n'.format(subkey)
        text += '| {}\n'.format(subcnt[key][subkey])
        text += '|-\n'
text += '|}'

with open('out.txt', 'w') as f:
    f.write(text)
