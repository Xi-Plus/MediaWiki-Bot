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
print(args)

os.environ['TZ'] = 'UTC'

site = pywikibot.Site(args.lang, args.wiki)
site.login()

config_page = pywikibot.Page(site, protect_config_page_name[args.lang][args.wiki])
cfg = config_page.text
cfg = json.loads(cfg)
print(json.dumps(cfg, indent=4, ensure_ascii=False))

if not cfg['enable']:
    exit('disabled\n')

db = pymysql.connect(host=database['host'],
                     user=database['user'],
                     passwd=database['passwd'],
                     db=database['db'],
                     charset=database['charset'])
cur = db.cursor()

cur.execute("""SELECT `title`, `count`, `protectedit`, `protectmove`, `redirect` FROM `MostTranscludedPages_page` WHERE `wiki` = %s AND `redirect` != 2 ORDER BY `title` ASC""", (args.dbwiki))
rows = cur.fetchall()


def check_required_protection(title, count):
    if title.startswith('MediaWiki:'):
        return 0
    if title.startswith('User:'):
        if title.endswith('.js') or title.endswith('.css') or title.endswith('.json'):
            return 0
    if count >= cfg['template_full'] and cfg['template_full'] > 0:
        return 3
    if count >= cfg['template_temp'] and cfg['template_temp'] > 0:
        return 2
    if count >= cfg['template_semi'] and cfg['template_semi'] > 0:
        return 1
    return 0


protection2number = {
    'sysop': 3,
    'templateeditor': 2,
    'autoconfirmed': 1,
    '': 0,
}
number2protection = {
    3: 'sysop',
    2: 'templateeditor',
    1: 'autoconfirmed',
    0: '',
}

for row in rows:
    title = row[0]
    count = row[1]
    protectedit = row[2]
    protectmove = row[3]
    redirect = row[4]

    required_protection = check_required_protection(title, count)
    current_protection = protection2number[protectedit]

    if required_protection > current_protection:
        page = pywikibot.Page(site, title)

        if not page.exists():
            print('{} is not exist'.format(title))
            continue

        if 'exclude_regex' in cfg and re.search(cfg['exclude_regex'], title):
            print('Ignore {}'.format(title))
            continue

        args = {
            'reason': cfg['summary'].format(count),
            'prompt': False,
            'protections': {
                'edit': number2protection[required_protection],
                'move': number2protection[required_protection],
            },
        }
        print(title, args)
        page.protect(**args)
