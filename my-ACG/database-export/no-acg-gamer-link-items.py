# -*- coding: utf-8 -*-
import argparse
import json
import os

import pymysql
os.environ['PYWIKIBOT_DIR'] = os.path.dirname(os.path.realpath(__file__))
import pywikibot
from config import DB_HOST, DB_USER, DB_PASS, DB_NAME  # pylint: disable=E0611,W0614


os.environ['TZ'] = 'UTC'

site = pywikibot.Site()
site.login()

db = pymysql.connect(
    host=DB_HOST,
    user=DB_USER,
    passwd=DB_PASS,
    db=DB_NAME,
    charset='utf8mb4'
)
cur = db.cursor()

cur.execute("""SELECT page_title FROM ( SELECT pl_from FROM `pagelinks` WHERE pl_title = 'Q53' ) t LEFT JOIN page on pl_from = page_id LEFT JOIN pagelinks ON page_id = pagelinks.pl_from AND pl_title = 'P1' WHERE pl_title IS NULL""")
rows = cur.fetchall()

text = """{{動畫表格列標題}}
"""

for row in rows:
    qid = row[0].decode()
    text += '{{{{動畫表格列|{}}}}}\n'.format(qid)

text += '|}'

page = pywikibot.Page(site, 'Project:缺少巴哈姆特作品資料的項目')
page.text = text
page.save(summary='產生列表')
