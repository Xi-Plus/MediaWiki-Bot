# -*- coding: utf-8 -*-
import argparse
import datetime
import os
import re
import sys

import pymysql

from config import host, password, user  # pylint: disable=E0611,W0614

os.environ['TZ'] = 'UTC'

os.environ['PYWIKIBOT_DIR'] = os.path.dirname(os.path.realpath(__file__))
import pywikibot
from pywikibot.data.api import Request

parser = argparse.ArgumentParser()
parser.add_argument('outpage')
parser.add_argument('basetime')
parser.add_argument('basetimeblock')
parser.add_argument('--candidate')
parser.add_argument('--exclude', action='append')
parser.add_argument('--debug', action='store_true')
parser.set_defaults(
    exclude=[],
    debug=False,
)
args = parser.parse_args()

site = pywikibot.Site()
site.login()

BASETIME = pywikibot.Timestamp.fromtimestampformat(args.basetime)
BASETIMEBLOCK = pywikibot.Timestamp.fromtimestampformat(args.basetimeblock)
CANDIDATE = args.candidate.capitalize() if args.candidate else None
EXCLUDED_USERS = {user.capitalize() for user in args.exclude}
if CANDIDATE:
    EXCLUDED_USERS.add(CANDIDATE)
if args.debug:
    print('base time', BASETIME)
    print('base time block', BASETIMEBLOCK)
    print('excluded users', EXCLUDED_USERS)

conn = pymysql.connect(
    host=host,
    user=user,
    password=password,
    charset='utf8'
)
authconn = pymysql.connect(
    host='centralauth.analytics.db.svc.wikimedia.cloud',
    user=user,
    password=password,
    charset='utf8'
)


def run_query(query, query_args=tuple(), db='zhwiki_p', cluster=conn):
    with cluster.cursor() as cursor:
        if args.debug:
            print('\tExecuting query at {}'.format(datetime.datetime.now()))
        cursor.execute('use ' + db)
        cursor.execute(query, query_args)
        result = cursor.fetchall()
        if args.debug:
            print('\tDone at {}'.format(datetime.datetime.now()))
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


class UserData:
    users = {}
    actor_id_to_user_id = {}
    user_name_to_user_id = {}
    ELIGIBLE_3000 = 3000
    ELIGIBLE_MAIN_1500 = 1500
    ELIGIBLE_120_500 = 500

    def add_user(self, user_id, actor_id, user_name):
        if user_id not in self.users:
            self.users[user_id] = {
                'eligible': False,
                'banned': False,
                'type': 0,
            }
            if re.search(r'^(Former|Renamed|Vanished|Deleted) (user|account) ', user_name, flags=re.I):
                self.users[user_id]['banned'] = True
            if user_name in EXCLUDED_USERS:
                self.users[user_id]['banned'] = True
        self.users[user_id]['user_id'] = user_id
        self.users[user_id]['actor_id'] = actor_id
        self.users[user_id]['user_name'] = user_name
        self.actor_id_to_user_id[actor_id] = user_id
        self.user_name_to_user_id[user_name] = user_id

    def is_eligible(self, actor_id=None, user_id=None):
        if actor_id:
            user_id = self.actor_id_to_user_id[actor_id]
        if user_id not in self.users:
            return False
        return self.users[user_id]['eligible']

    def get_user(self, user_id=None, actor_id=None):
        if actor_id:
            user_id = self.actor_id_to_user_id[actor_id]
        return self.users[user_id]

    def set_user(self, key, value, user_id=None, actor_id=None):
        if actor_id:
            user_id = self.actor_id_to_user_id[actor_id]
        self.users[user_id][key] = value

    def set_eligible(self, actor_id, el_type, edit_count):
        self.set_user('type', el_type, actor_id=actor_id)
        self.set_user('eligible', True, actor_id=actor_id)
        if el_type == self.ELIGIBLE_3000:
            self.set_user('edit_count', edit_count, actor_id=actor_id)
        elif el_type == self.ELIGIBLE_MAIN_1500:
            self.set_user('edit_count_main', edit_count, actor_id=actor_id)
        elif el_type == self.ELIGIBLE_120_500:
            self.set_user('edit_count_120', edit_count, actor_id=actor_id)

    def ban(self, user_id=None, user_name=None):
        if user_name and user_name in self.user_name_to_user_id:
            user_id = self.user_name_to_user_id[user_name]
        if user_id in self.users:
            self.set_user('banned', True, user_id)

    def user_id_list(self):
        return list(self.users.keys())

    def count_eligible(self):
        cnt = 0
        for user in self.users.values():
            if user['eligible'] and not user['banned']:
                cnt += 1
        return cnt

    def eligible_usernames(self):
        result = []
        for user in self.users.values():
            if user['eligible'] and not user['banned']:
                result.append(user['user_name'])
        return result


user_data = UserData()


# Get users with edit count > 3000
result = run_query('''
SELECT user_name, actor_id, user_id
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
    user_id = row[2]
    # print(user_name, actor_id)
    actor_id_list.append(actor_id)
    user_data.add_user(user_id, actor_id, user_name)

# Check real edit count before base time
edit_counts = edit_count_filter(actor_id_list, None, BASETIME)
cnt = 0
for actor_id, edit_count in edit_counts.items():
    # print(actor_id, edit_count)
    if edit_count >= 3000:
        user_data.set_eligible(actor_id, UserData.ELIGIBLE_3000, edit_count)
        cnt += 1
if args.debug:
    print('Found {} users with > 3000 edits before base time'.format(cnt))


# Get users with edit count > 1500
result = run_query('''
SELECT user_name, actor_id, user_id
FROM user
LEFT JOIN actor ON user_id = actor_user
WHERE user_editcount >= 1500
''')
if args.debug:
    print('Found {} users with > 1500 edits'.format(len(result)))

actor_id_list = []
for row in result:
    user_name = row[0].decode()
    actor_id = row[1]
    user_id = row[2]
    if user_data.is_eligible(user_id=user_id):
        continue
    # print(user_name, actor_id)
    actor_id_list.append(actor_id)
    user_data.add_user(user_id, actor_id, user_name)
if args.debug:
    print('Remaining {} users with 1500 <= edits < 3000'.format(len(actor_id_list)))

# Check real article edit count before base time
edit_counts = edit_count_filter(actor_id_list, None, BASETIME, '0')
cnt = 0
for actor_id, edit_count in edit_counts.items():
    if edit_count >= 1500:
        # print(actor_id, actor_id_user_name[actor_id], edit_count)
        user_data.set_eligible(actor_id, UserData.ELIGIBLE_MAIN_1500, edit_count)
        cnt += 1
if args.debug:
    print('Found {} users with > 1500 article edits before base time'.format(cnt))


# Get extendedconfirmed or sysop
result = run_query('''
SELECT user_name, actor_id, user_id
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
    actor_id = row[1]
    user_id = row[2]
    if user_data.is_eligible(user_id=user_id):
        continue
    # print(user_name, actor_id)
    actor_id_list.append(actor_id)
    user_data.add_user(user_id, actor_id, user_name)
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
            user_data.set_eligible(actor_id, UserData.ELIGIBLE_120_500, edit_counts_120[actor_id])
            cnt += 1
        # else:
        #     print('{} ({}) have no edits in 90 days'.format(actor_id_user_name[actor_id], actor_id))
    # else:
    #     print('{} ({}) have less than 500 edits: {}'.format(actor_id_user_name[actor_id], actor_id, edit_counts_120[actor_id]))
if args.debug:
    print('Remaining {} extendedconfirmed or sysop users'.format(cnt))


# blocked users
result = run_query('''
SELECT ipb_user
FROM ipblocks
WHERE ipb_user IN ({})
    AND ipb_sitewide = 1
    AND ipb_expiry = 'infinity'
'''.format(
    ','.join(map(str, user_data.user_id_list()))
))
if args.debug:
    print('Found {} blocked users'.format(len(result)))
for row in result:
    user_id = row[0]
    user_data.ban(user_id=user_id)


# in bot user group
result = run_query('''
SELECT ug_user
FROM user_groups
WHERE ug_group = 'bot'
''')
if args.debug:
    print('Found {} users in bot group'.format(len(result)))
for row in result:
    user_id = row[0]
    user_data.ban(user_id=user_id)


# in bot category
result = run_query('''
SELECT page_title
FROM categorylinks
LEFT JOIN page ON cl_from = page_id
WHERE cl_to = '所有維基百科機器人'
    AND page_title NOT LIKE '%%/%%'
''')
if args.debug:
    print('Found {} users in bot category'.format(len(result)))
for row in result:
    user_name = row[0].decode().replace('_', ' ')
    user_data.ban(user_name=user_name)


# locked users
eligible_usernames = user_data.eligible_usernames()
result = run_query('''
SELECT gu_name
FROM globaluser
WHERE gu_locked = 1
    AND gu_name IN ({})
'''.format(
    ','.join(['%s'] * len(eligible_usernames))
), eligible_usernames, db='centralauth_p', cluster=authconn)
if args.debug:
    print('Found {} locked users'.format(len(result)))
for row in result:
    user_name = row[0].decode()
    # print(user_name)
    user_data.ban(user_name=user_name)


# users have block log
DAYS_400_AGO = BASETIME - datetime.timedelta(days=400)
DAYS_AFTER = BASETIME + datetime.timedelta(days=1)
if args.debug:
    print('400 days ago', DAYS_400_AGO)
eligible_usernames = list(map(lambda v: v.replace(' ', '_'), user_data.eligible_usernames()))
result = run_query('''
SELECT log_title, COUNT(*) AS log_count
FROM logging
WHERE log_type = 'block'
    AND log_timestamp < {}
    AND log_timestamp > {}
    AND log_title IN ({})
GROUP BY log_title
'''.format(
    BASETIME.totimestampformat(),
    DAYS_400_AGO.totimestampformat(),
    ','.join(['%s'] * len(eligible_usernames))
), eligible_usernames)
if args.debug:
    print('Found {} users with block log'.format(len(result)))
for row in result:
    user_name = row[0].decode().replace('_', ' ')
    r = Request(site=site, parameters={
        'action': 'query',
        'format': 'json',
        'list': 'logevents',
        'letype': 'block',
        'lestart': BASETIME.isoformat(),
        'leend': DAYS_400_AGO.isoformat(),
        'letitle': 'User:' + user_name,
        'lelimit': 'max'
    })
    data = r.submit()
    unblocktime = None
    # print(user_name)
    for logevent in data['query']['logevents']:
        if logevent['action'] == 'unblock':
            unblocktime = pywikibot.Timestamp.fromISOformat(logevent['timestamp'])
        else:
            if 'expiry' in logevent['params']:
                expiry = pywikibot.Timestamp.fromISOformat(logevent['params']['expiry'])
            else:
                expiry = DAYS_AFTER
            if unblocktime and unblocktime < expiry:
                expiry = unblocktime
            start = pywikibot.Timestamp.fromISOformat(logevent['timestamp'])
            # print('\t', start, expiry, logevent['params'])
            if start <= BASETIMEBLOCK <= expiry:
                if ('sitewide' in logevent['params']
                        or ('restrictions' in logevent['params'] and 'namespace' in logevent['params'] and 4 in logevent['params']['restrictions']['namespaces'])):
                    user_data.ban(user_name=user_name)
                    # print('\t*** BAN ***')
            unblocktime = start


voter_note = ''
voter_plain = ''
for user in sorted(user_data.users.values(), key=lambda v: v['user_name']):
    if not user['eligible'] or user['banned']:
        continue
    voter_note += '# {0},'.format(user['user_name'])
    if user['type'] == UserData.ELIGIBLE_3000:
        voter_note += 'b,{}'.format(user['edit_count'])
    elif user['type'] == UserData.ELIGIBLE_MAIN_1500:
        voter_note += 'c,{}'.format(user['edit_count_main'])
    elif user['type'] == UserData.ELIGIBLE_120_500:
        voter_note += 'a,{}'.format(user['edit_count_120'])
    voter_note += '\n'
    voter_plain += '{}@zhwiki\n'.format(user['user_name'])


text = '''
<!-- command: python3 {command} -->
* 以下根據[[Wikipedia:人事任免投票資格|人事任免投票資格]]列出投票權人名單，共有{count}名。
* 計算基準時間為{{{{subst:#time:Y年n月j日 (D) H:i (T)|{basetime}}}}}。
* 下列使用者已被排除：
** 被全站無限期封鎖、全域鎖定；[[Special:PermaLink/73532512#安全投票暫行規定|提名通過之時]]（基準時間：{{{{subst:#time:Y年n月j日 (D) H:i (T)|{basetimeblock}}}}}）被封鎖、禁制維基百科命名空間。
** 擁有機器人群組、使用者頁面標記為機器人。
** 使用者名稱判斷為隱退使用者。
'''.format(
    command=' '.join(sys.argv),
    count=user_data.count_eligible(),
    basetime=BASETIME.totimestampformat(),
    basetimeblock=BASETIMEBLOCK.totimestampformat(),
)
if args.candidate:
    text += '** 候選人（{}）。\n'.format(CANDIDATE)
text += '''* 該名單可能包含您的合法多重帳號，您僅可使用一個帳號投票，否則會觸犯[[Wikipedia:傀儡#被視為濫用多重帳號的行為|傀儡方針]]。
* 該名單基於固定規則產生，不保證最後會認定為有效票，具體執行仍以人事任免投票資格、申請成為管理人員等方針指引為準。如有疑義請在下方留言，對名單的直接修改將在下次更新被撤銷。

{{{{HideH|投票權人名單}}}}
代號範例：
* a,X - 120天前X編輯（人事任免投票資格第一項）
* b,X - X編輯（人事任免投票資格第二項第一款）
* c,X - X條目編輯（人事任免投票資格第二項第二款）
列表：
{votersnote}
{{{{HideF}}}}
{{{{HideH|Voter list (plain text for SecurePoll)}}}}
<pre>
{votersplain}
</pre>
{{{{HideF}}}}
產生時間：~~~~
'''.format(
    votersnote=voter_note.strip(),
    votersplain=voter_plain.strip(),
)

if args.debug:
    with open('out.txt', 'w', encoding='utf8') as f:
        f.write(text)


page = pywikibot.Page(site, args.outpage)
new_text = page.text.rstrip()
if len(new_text) > 0:
    new_text += '\n\n'

FLAG_START = '<!-- voter-start -->'
FLAG_END = '<!-- voter-end -->'
try:
    INDEX_START = new_text.index(FLAG_START)
    INDEX_END = new_text.index(FLAG_END)
    new_text = new_text[:INDEX_START] + FLAG_START + text + new_text[INDEX_END:]
except ValueError:
    new_text += '== 投票權人名單 ==\n' + FLAG_START + text + FLAG_END

pywikibot.showDiff(page.text, new_text)
if input('Save? ').lower() in ['yes', 'y']:
    page.text = new_text
    page.save(summary='產生投票權人名單', minor=False)
