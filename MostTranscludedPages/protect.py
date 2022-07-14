# -*- coding: utf-8 -*-
import argparse
import json
import os
import re

os.environ['PYWIKIBOT_DIR'] = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'protect-config')
import pymysql
import pywikibot

from config import (database,  # pylint: disable=E0611,W0614
                    protect_config_page_name)


parser = argparse.ArgumentParser()
parser.add_argument('lang', nargs='?', default='zh')
parser.add_argument('wiki', nargs='?', default='wikipedia')
parser.add_argument('dbwiki', nargs='?', default='zhwiki')
args = parser.parse_args()

os.environ['TZ'] = 'UTC'

site = pywikibot.Site(args.lang, args.wiki)
site.login()

config_page = pywikibot.Page(site, protect_config_page_name[args.lang][args.wiki])
cfg = config_page.text
cfg = json.loads(cfg)
print(json.dumps(cfg, indent=4, ensure_ascii=False))

if not cfg['enable']:
    print('disabled')
    exit()

database['host'] = '{}.analytics.db.svc.eqiad.wmflabs'.format(args.dbwiki)
conn = pymysql.connect(
    host=database['host'],
    user=database['user'],
    passwd=database['passwd'],
    charset=database['charset']
)


def check_required_protection(page, count):
    if page.namespace().id == 8:
        return 0
    if page.namespace().id == 2:
        if page.title().endswith('.js') or page.title().endswith('.css') or page.title().endswith('.json'):
            return 0
    if count >= cfg['template_full'] and cfg['template_full'] > 0:
        return 4
    if count >= cfg['template_temp'] and cfg['template_temp'] > 0:
        return 3
    if count >= cfg['template_semi'] and cfg['template_semi'] > 0:
        return 1
    return 0


protection2number = {
    'sysop': 4,
    'templateeditor': 3,
    'extendedconfirmed': 2,
    'autoconfirmed': 1,
    '': 0,
}
number2protection = {
    4: 'sysop',
    3: 'templateeditor',
    2: 'extendedconfirmed',
    1: 'autoconfirmed',
    0: '',
}

with conn.cursor() as cursor:
    cursor.execute('use zhwiki_p')
    cursor.execute('''
    SELECT
        tl_namespace,
        tl_title,
        links,
        pr_level,
        pr_expiry
    FROm (
        SELECT
        tl_namespace,
        tl_title,
        COUNT(*) AS links
        FROM templatelinks
        GROUP BY tl_namespace, tl_title
        HAVING links >= 500
    ) templatelinks
    LEFT JOIN page ON tl_namespace = page_namespace AND tl_title = page_title
    LEFT JOIN page_restrictions ON page_id = pr_page AND pr_type = 'edit'
    ''')
    rows = cursor.fetchall()

for row in rows:
    page_namespace = row[0]
    page_title = row[1].decode()
    count = row[2]
    if row[3] is None:
        pr_level = ''
        pr_expiry = ''
    else:
        pr_level = row[3].decode()
        pr_expiry = row[4].decode()

    page = pywikibot.Page(site, page_title, page_namespace)
    required_protection = check_required_protection(page, count)
    current_protection = protection2number[pr_level]

    if required_protection > current_protection:
        if not page.exists():
            print('{} is not exist'.format(page.title()))
            continue

        if 'exclude_regex' in cfg and cfg['exclude_regex'] != '' and re.search(cfg['exclude_regex'], page.title()):
            print('Ignore {}'.format(page.title()))
            continue

        args = {
            'reason': cfg['summary'].format(count),
            'prompt': False,
            'protections': {
                'edit': number2protection[required_protection],
                'move': number2protection[required_protection],
            },
        }
        print(page.title(), args)
        page.protect(**args)
