#!/usr/bin/env python
# coding: utf-8

import json
import os
import re

import pymysql
os.environ['PYWIKIBOT_DIR'] = os.path.dirname(os.path.realpath(__file__))
import pywikibot

from config import config_page_name, host, password, user  # pylint: disable=E0611,W0614


site = pywikibot.Site('zh', 'wikipedia')
site.login()

# config_page = pywikibot.Page(site, config_page_name)
# cfg = config_page.text
# cfg = json.loads(cfg)
# print(json.dumps(cfg, indent=4, ensure_ascii=False))

# if not cfg['enable']:
#     exit('disabled\n')

conn = pymysql.connect(
    host=host,
    user=user,
    password=password,
    charset="utf8"
)

with conn.cursor() as cur:
    cur.execute('use zhwiki_p')
    cur.execute("""
        SELECT tl_namespace, tl_title, page_id, pr_level
        FROM
        (
            SELECT DISTINCT tl_namespace, tl_title
            FROM templatelinks
            WHERE tl_from_namespace = 8 AND tl_namespace != 8 AND tl_namespace % 2 = 0
            AND tl_from NOT IN (6709868, 6743456, 5545686, 5733059, 6486575, 3073030)
        ) t1
        LEFT JOIN page ON tl_namespace = page_namespace AND tl_title = page_title
        LEFT JOIN page_restrictions ON pr_page = page_id AND pr_type = 'edit'
        WHERE pr_level != 'sysop'
    """)
    res = cur.fetchall()

whitelist = [
    68860,  # TOWitem
    79357,  # TOWpercent
    71082,  # Bulletin
    1224493,  # Bulletin/maintenance
    1612163,  # Recent_changes_article_requests/list
    84599,  # 新条目推荐/候选
]

protectargs = {
    'reason': '[[Wikipedia:保護方針#永久保护|嵌入在MediaWiki命名空間的頁面]]',
    'prompt': False,
    'protections': {
        'edit': 'sysop',
        'move': 'sysop',
    }
}

for row in res:
    ns = int(row[0])
    title = row[1].decode()
    pageid = int(row[2])

    if '历史上的今天' in title:
        continue
    if pageid in whitelist:
        continue

    page = pywikibot.Page(site, title, ns)
    print(ns, title, pageid, page.title())
    page.protect(**protectargs)
