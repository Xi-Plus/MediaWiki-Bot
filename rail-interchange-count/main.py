# -*- coding: utf-8 -*-
from collections import defaultdict
import pymysql
from config import host, password, user  # pylint: disable=E0611,W0614


query = '''
SELECT pl_from, pl_title
FROM pagelinks
WHERE pl_namespace = 10 AND pl_title LIKE 'Rail-interchange/count/%'
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

maincnt = defaultdict(set)
subcnt = defaultdict(lambda: defaultdict(set))
for row in result:
    pl_from = row[0]
    pl_title = row[1].decode()
    params = pl_title.replace('Rail-interchange/count/', '').lower().split('-')
    maincnt[params[0]].add(pl_from)
    subcnt[params[0]]['-'.join(params[1:])].add(pl_from)

text = '''{| class="wikitable sortable" style="word-break: break-all;"
! param 1
! count
! param 2
! count
|-
'''

EXCLUDES = {
    'cn',
    'tw',
    'taipei',
    'london',
    'gb',
    'tokyo',
    'kaohsiung',
    'my',
}
allcnt = 0

for key in sorted(maincnt.keys()):
    text += '| rowspan={} | {}\n'.format(len(subcnt[key]), key)
    text += '| rowspan={} | {}\n'.format(len(subcnt[key]), len(maincnt[key]))
    for subkey in sorted(subcnt[key].keys()):
        text += '| {}\n'.format(subkey)
        text += '| {}\n'.format(len(subcnt[key][subkey]))
        text += '|-\n'
    if key not in EXCLUDES:
        allcnt += len(maincnt[key])
text += '|}'

print('allcnt', allcnt)

with open('out.txt', 'w') as f:
    f.write(text)
