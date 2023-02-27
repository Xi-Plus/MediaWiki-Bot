# -*- coding: utf-8 -*-
import argparse
import json
import os
import re

import pymysql

os.environ['PYWIKIBOT_DIR'] = os.path.dirname(os.path.realpath(__file__))
import pywikibot

from config import database, config_page_name  # pylint: disable=E0611,W0614

parser = argparse.ArgumentParser()
parser.add_argument('lang')
parser.add_argument('wiki')
parser.add_argument('dbwiki')
parser.add_argument('--dry-run', action='store_true', dest='dry_run')
parser.set_defaults(dry_run=False)
args = parser.parse_args()

os.environ['TZ'] = 'UTC'

site = pywikibot.Site(args.lang, args.wiki)
site.login()

config_page = pywikibot.Page(site, config_page_name[args.lang][args.wiki])
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
    charset=database['charset'],
    database='{}_p'.format(args.dbwiki),
)


def check_required_protection(page, count):
    if page.namespace().id == 8:  # MediaWiki
        return 0
    if page.namespace().id == 2:  # User
        if re.search(r'\.(js|css|json)$', page.title()):
            return 0
    if page.site.dbName() == 'zhwiki':
        if re.search(r'^(Template|Module):CGroup/', page.title()) and not re.search(r'^Module:CGroup/core$', page.title()) and count >= cfg['template_temp']:
            return 2
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
    cursor.execute('''
    SELECT
        lt_namespace,
        lt_title,
        links,
        page_id,
        pr1.pr_level AS edit_level,
        pr1.pr_expiry AS edit_expiry,
        pr2.pr_level AS move_level,
        pr2.pr_expiry AS move_expiry,
        pt_create_perm,
        pt_expiry
    FROM (
        SELECT
        tl_target_id,
        COUNT(*) AS links
        FROM templatelinks
        GROUP BY tl_target_id
        HAVING links >= 500
    ) templatelinks
    LEFT JOIN linktarget ON tl_target_id = lt_id
    LEFT JOIN page ON lt_namespace = page_namespace AND lt_title = page_title
    LEFT JOIN page_restrictions AS pr1 ON page_id = pr1.pr_page AND pr1.pr_type = 'edit'
    LEFT JOIN page_restrictions AS pr2 ON page_id = pr2.pr_page AND pr2.pr_type = 'move'
    LEFT JOIN protected_titles ON page_id IS NULL AND lt_namespace = pt_namespace AND lt_title = pt_title
    ''')
    rows = cursor.fetchall()


def get_protection(cur_level, cur_expiry, req_level):
    if req_level > cur_level:
        return number2protection[req_level], 'infinity', True
    if req_level == cur_level:
        return number2protection[req_level], 'infinity', req_level > 0 and cur_expiry != 'infinity'
    return number2protection[cur_level], cur_expiry, False


for row in rows:
    page_namespace = row[0]
    page_title = row[1].decode()
    count = row[2]
    page_id = row[3]
    edit_level = protection2number[row[4].decode()] if row[4] else 0
    edit_expiry = row[5].decode() if row[5] else ''
    move_level = protection2number[row[6].decode()] if row[6] else 0
    move_expiry = row[7].decode() if row[7] else ''
    create_level = protection2number[row[8].decode()] if row[8] else 0
    create_expiry = row[9].decode() if row[9] else ''

    # https://phabricator.wikimedia.org/T315055
    if page_namespace == 0 and page_title == '':
        continue

    page = pywikibot.Page(site, '{}:{}'.format(site.namespace(page_namespace), page_title))
    required_protection = check_required_protection(page, count)

    needs_protect = False

    params = {
        'reason': cfg['summary'].format(count),
        'prompt': False,
        'protections': {},
    }
    if page_id:
        params['protections']['edit'], new_exp_edit, changed = get_protection(edit_level, edit_expiry, required_protection)
        needs_protect |= changed
        params['protections']['move'], new_exp_move, changed = get_protection(move_level, move_expiry, required_protection)
        if required_protection >= 2:
            needs_protect |= changed
        params['expiry'] = new_exp_edit + '|' + new_exp_move
    else:
        params['protections']['create'], params['expiry'], needs_protect = get_protection(create_level, create_expiry, required_protection)

    if needs_protect:
        if 'exclude_regex' in cfg and cfg['exclude_regex'] != '' and re.search(cfg['exclude_regex'], page.title()):
            print('Ignore {}'.format(page.title()))
            continue

        print(page.title(), params)
        if not args.dry_run:
            page.protect(**params)
