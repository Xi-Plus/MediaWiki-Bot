# -*- coding: utf-8 -*-
import argparse
import datetime
import os
import re

import pymysql

from config import host, password, user  # pylint: disable=E0611,W0614

os.environ['TZ'] = 'UTC'

os.environ['PYWIKIBOT_DIR'] = os.path.dirname(os.path.realpath(__file__))
import pywikibot

parser = argparse.ArgumentParser()
parser.add_argument('outpage')
parser.add_argument('basetime')
parser.add_argument('--debug', action='store_true')
parser.set_defaults(debug=False)
args = parser.parse_args()

site = pywikibot.Site()
site.login()

BASETIME = pywikibot.Timestamp.fromtimestampformat(args.basetime)
if args.debug:
    print('base time', BASETIME)

conn = pymysql.connect(
    host=host,
    user=user,
    password=password,
    charset='utf8'
)


def run_query(query):
    with conn.cursor() as cursor:
        if args.debug:
            print('Executing query at {}'.format(datetime.datetime.now()))
        cursor.execute('use zhwiki_p')
        cursor.execute(query)
        result = cursor.fetchall()
        if args.debug:
            print('Done at {}'.format(datetime.datetime.now()))
        return result


def edit_count_filter(actor_id_list, start=None, end=None, ns=None, excludens=None):
    query = 'SELECT rev_actor, COUNT(*) AS editcount FROM revision'
    if ns or excludens:
        query += ' LEFT JOIN page ON rev_page = page_id'
    query += ' WHERE rev_actor IN ({actor})'
    params = {
        'actor': ','.join(map(str, actor_id_list)),
    }
    if start is not None:
        query += ' AND rev_timestamp > {start}'
        params['start'] = start.totimestampformat()
    if end is not None:
        query += ' AND rev_timestamp < {end}'
        params['end'] = end.totimestampformat()
    if ns is not None:
        query += ' AND page_namespace IN ({ns})'
        params['ns'] = ns
    elif excludens is not None:
        query += ' AND page_namespace NOT IN ({excludens})'
        params['excludens'] = excludens
    query += ' GROUP BY rev_actor'

    query = query.format(**params)
    result = run_query(query)

    edit_counts = {}
    for actor_id in actor_id_list:
        edit_counts[actor_id] = 0
    for row in result:
        actor_id = row[0]
        edit_count = row[1]
        edit_counts[actor_id] = edit_count

    return edit_counts


voters = {}
actor_id_user_name = {}


# Get users with edit count > 3000
result = run_query('''
SELECT user_name, actor_id
FROM user
LEFT JOIN actor ON user_id = actor_user
WHERE user_editcount >= 3000
''')
if args.debug:
    print('Found {} users with > 3000 edits'.format(len(result)))

actor_id_list = []
for row in result:
    user_name = row[0].decode()
    actor_id = row[1]
    # print(user_name, actor_id)
    actor_id_list.append(actor_id)
    actor_id_user_name[actor_id] = user_name

# Check real edit count before base time
edit_counts = edit_count_filter(actor_id_list, None, BASETIME)
cnt = 0
for actor_id, edit_count in edit_counts.items():
    # print(actor_id, edit_count)
    if edit_count >= 3000:
        voters[actor_id_user_name[actor_id]] = {
            'type': '3000',
            'editcount': edit_count,
        }
        cnt += 1
if args.debug:
    print('Found {} users with > 3000 edits before base time'.format(cnt))


# Get users with edit count > 1500
result = run_query('''
SELECT user_name, actor_id
FROM user
LEFT JOIN actor ON user_id = actor_user
WHERE user_editcount >= 1500
''')
if args.debug:
    print('Found {} users with > 1500 edits'.format(len(result)))

actor_id_list = []
for row in result:
    user_name = row[0].decode()
    if user_name in voters:
        continue
    actor_id = row[1]
    # print(user_name, actor_id)
    actor_id_list.append(actor_id)
    actor_id_user_name[actor_id] = user_name
if args.debug:
    print('Remaining {} users with 1500 <= edits < 3000'.format(len(actor_id_list)))

# Check real article edit count before base time
edit_counts = edit_count_filter(actor_id_list, None, BASETIME, '0')
cnt = 0
for actor_id, edit_count in edit_counts.items():
    if edit_count >= 1500:
        # print(actor_id, actor_id_user_name[actor_id], edit_count)
        voters[actor_id_user_name[actor_id]] = {
            'type': 'main1500',
            'maineditcount': edit_count,
        }
        cnt += 1
if args.debug:
    print('Found {} users with > 1500 article edits before base time'.format(cnt))


# Get extendedconfirmed or sysop
result = run_query('''
SELECT user_name, actor_id
FROM user_groups
LEFT JOIN user ON ug_user = user_id
LEFT JOIN actor ON user_id = actor_user
WHERE ug_group IN ('extendedconfirmed', 'sysop')
''')
if args.debug:
    print('Found {} extendedconfirmed or sysop users'.format(len(result)))

actor_id_list = []
for row in result:
    user_name = row[0].decode()
    if user_name in voters:
        continue
    actor_id = row[1]
    # print(user_name, actor_id)
    actor_id_list.append(actor_id)
    actor_id_user_name[actor_id] = user_name
if args.debug:
    print('Remaining {} extendedconfirmed or sysop users to check'.format(len(actor_id_list)))

DAYS_120_AGO = BASETIME - datetime.timedelta(days=120)
DAYS_90_AGO = BASETIME - datetime.timedelta(days=90)
if args.debug:
    print('120 days ago', DAYS_120_AGO)
    print('90 days ago', DAYS_90_AGO)

# Check real extendedconfirmed edit count
edit_counts_120 = edit_count_filter(actor_id_list, None, DAYS_120_AGO)
edit_counts_90 = edit_count_filter(actor_id_list, DAYS_90_AGO, BASETIME, None, '2,3')
cnt = 0
for actor_id in actor_id_list:
    if edit_counts_120[actor_id] >= 500:
        if edit_counts_90[actor_id] >= 1:
            voters[actor_id_user_name[actor_id]] = {
                'type': '500',
                '120editcount': edit_counts_120[actor_id],
            }
            cnt += 1
        # else:
        #     print('{} ({}) have no edits in 90 days'.format(actor_id_user_name[actor_id], actor_id))
    # else:
    #     print('{} ({}) have less than 500 edits: {}'.format(actor_id_user_name[actor_id], actor_id, edit_counts_120[actor_id]))
if args.debug:
    print('Remaining {} extendedconfirmed or sysop users'.format(cnt))


# Get banned users
banned_voters = set()

# blocked users
result = run_query('''
SELECT ipb_address
FROM ipblocks
WHERE ipb_user != 0
    AND ipb_sitewide = 1
''')
if args.debug:
    print('Found {} blocked users'.format(len(result)))
for row in result:
    user_name = row[0].decode()
    banned_voters.add(user_name)

# bots
result = run_query('''
SELECT user_name
FROM user_groups
LEFT JOIN user ON ug_user = user_id
LEFT JOIN actor ON user_id = actor_user
WHERE ug_group = 'bot'
''')
if args.debug:
    print('Found {} bots'.format(len(result)))
for row in result:
    user_name = row[0].decode()
    banned_voters.add(user_name)

for user_name in list(voters.keys()):
    if user_name in banned_voters:
        del voters[user_name]
    elif re.search(r'bot\d*$', user_name, flags=re.I):
        print('Ignore {} per username'.format(user_name))
        del voters[user_name]


text = '''以下根據[[Wikipedia:人事任免投票資格]]列出投票權人名單，目前被全站封鎖的使用者及機器人已被排除，共有{}名。計算基準日為{{{{subst:#time:Y年n月j日 (D) H:i (T)|{}}}}}。
{{{{HideH|投票權人名單}}}}'''.format(
    len(voters),
    BASETIME.totimestampformat()
)
for user_name, value in sorted(voters.items(), key=lambda v: v[0]):
    text += '\n# [[User:{0}|{0}]] - '.format(user_name)
    if value['type'] == '3000':
        text += '{}編輯'.format(value['editcount'])
    elif value['type'] == 'main1500':
        text += '{}條目編輯'.format(value['maineditcount'])
    elif value['type'] == '500':
        text += '120天前{}編輯'.format(value['120editcount'])
text += '''
{{HideF}}
產生時間：~~~~'''

page = pywikibot.Page(site, args.outpage)
new_text = page.text.rstrip()

FLAG_START = '<!-- voter-start -->'
FLAG_END = '<!-- voter-end -->'
try:
    INDEX_START = new_text.index(FLAG_START)
    INDEX_END = new_text.index(FLAG_END)
    new_text = new_text[:INDEX_START] + FLAG_START + text + new_text[INDEX_END:]
except ValueError:
    new_text += '\n\n== 投票權人名單 ==\n' + FLAG_START + text + FLAG_END

if args.debug:
    pywikibot.showDiff(page.text, new_text)
if input('Save? ').lower() in ['yes', 'y']:
    page.text = new_text
    page.save(summary='產生投票權人名單', minor=False)
