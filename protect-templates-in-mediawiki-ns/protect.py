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

mediawiki_whitelist = []
for title in cfg['mediawiki_whitelist']:
    page = pywikibot.Page(site, title)
    mediawiki_whitelist.append(str(page.pageid))

mediawiki_whitelist = ', '.join(mediawiki_whitelist)

with conn.cursor() as cur:
    cur.execute('use zhwiki_p')
    cur.execute("""
        SELECT tl_namespace, tl_title, tl_from
        FROM templatelinks
        WHERE tl_from_namespace = 8 AND tl_namespace != 8
        AND tl_from NOT IN ({})
    """.format(mediawiki_whitelist))
    res = cur.fetchall()

templates = set()
for row in res:
    ns = int(row[0])
    title = row[1].decode()
    tl_from = int(row[2])
    templates.add((ns, title))

titles = []
for (ns, title) in templates:
    page = pywikibot.Page(site, title, ns)
    fulltitle = page.title()
    if re.search(cfg['template_whiteregex'], fulltitle):
        continue

    titles.append(fulltitle)

titles.sort()

text = '\n'
for title in titles:
    # print(title)
    text += '| ' + title + '\n'

page = pywikibot.Page(site, cfg['page'])
try:
    idx1 = page.text.index('<!--listbegins-->') + len('<!--listbegins-->')
    idx2 = page.text.index('<!--listends-->', idx1)
except ValueError:
    print('Cannot locate insertion position')
    exit()

newtext = page.text[:idx1] + text + page.text[idx2:]
pywikibot.showDiff(page.text, newtext)

page.text = newtext
page.save(cfg['summary'])
