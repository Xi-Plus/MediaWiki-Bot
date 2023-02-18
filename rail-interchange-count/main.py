# -*- coding: utf-8 -*-
from collections import defaultdict
import pymysql
from config import host, password, user  # pylint: disable=E0611,W0614


query = '''
SELECT pl_title, COUNT(*) AS cnt
FROM (
  SELECT LOWER(CONVERT(pl_title USING UTF8)) AS pl_title
  FROM pagelinks
  WHERE pl_namespace = 10 AND pl_title LIKE 'Rail-interchange/count/%'
) t
GROUP BY pl_title
ORDER BY cnt DESC
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
    params = row[0].replace('rail-interchange/count/', '').split('-')
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
