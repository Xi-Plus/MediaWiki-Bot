#!/usr/bin/env python
# coding: utf-8

import pywikibot
from pywikibot.data.api import Request
import pymysql

from config import host, password, user  # pylint: disable=E0611,W0614

site = pywikibot.Site('zh', 'wikipedia')
site.login()

conn = pymysql.connect(
    host=host,
    user=user,
    password=password,
    database='zhwiki_p',
    charset='utf8'
)
cur = conn.cursor()

query = """
SELECT page_title
FROM page
LEFT JOIN user ON REGEXP_REPLACE(REPLACE(page_title, '_', ' '), '/.*', '') = user_name
WHERE page_namespace = 3
AND page_content_model = 'flow-board'
AND user_id IS NULL
"""
cur.execute(query)
pages = cur.fetchall()


def test_title_exists(title):
    page = pywikibot.Page(site, title)
    return page.exists()


def get_new_title(username, subpage):
    new_title = 'User talk:' + username
    if subpage:
        new_title += '/' + subpage
    if not test_title_exists(new_title):
        return new_title
    i = 1
    while True:
        new_title = 'User talk:{}/结构式讨论 存档 {}'.format(username, i)
        if not test_title_exists(new_title):
            return new_title
        i += 1


for row in pages:
    title = row[0].decode()
    titleparts = title.split('/')
    olduser = titleparts[0]
    subpage = '/'.join(titleparts[1:])
    page = pywikibot.Page(site, 'User talk:' + title)

    r = Request(site=site, parameters={
        'action': 'query',
        'format': 'json',
        'list': 'logevents',
        'utf8': 1,
        'leprop': 'details',
        'letype': 'renameuser',
        'letitle': 'User:' + olduser
    })
    data = r.submit()
    if len(data['query']['logevents']) != 1:
        print('Failed to get new username for {}: {}'.format(olduser, data['query']['logevents']))
        continue
    newuser = data['query']['logevents'][0]['params']['newuser']

    newtitle = get_new_title(newuser, subpage)
    save = input('Move {} to {} ? '.format(page.title(), newtitle))
    if save.lower() in ['yes', 'y', '']:
        reason = '使用者已更名'
        page.move(newtitle, reason=reason, movetalk=False, noredirect=True, movesubpages=False)
