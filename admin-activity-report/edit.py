#!/usr/bin/env python
# coding: utf-8

# %%
import argparse
import json
import os
from collections import defaultdict
from datetime import timedelta
from functools import lru_cache

import pymysql
os.environ['PYWIKIBOT_DIR'] = os.path.dirname(os.path.realpath(__file__))
import pywikibot
import pywikibot.flow
from config import (config_page_name, host,  # pylint: disable=E0611,W0614
                    password, user)

# %%
parser = argparse.ArgumentParser()
parser.add_argument('--confirm-report', action='store_true')
parser.set_defaults(
    confirm_report=False,
)
args = parser.parse_args()

os.environ['TZ'] = 'UTC'

# %%
site = pywikibot.Site('zh', 'wikipedia')
site.login()

# %%
config_page = pywikibot.Page(site, config_page_name)
cfg = config_page.text
cfg = json.loads(cfg)

if not cfg['enable']:
    exit('disabled\n')

# %%

DATE_50_RED = pywikibot.Timestamp.now() - timedelta(days=730)  # 2 years
DATE_50_YELLOW = pywikibot.Timestamp.now() - timedelta(days=365)  # 1 year
DATE_100_RED = pywikibot.Timestamp.now() - timedelta(days=1825)  # 5 years
DATE_100_YELLOW = pywikibot.Timestamp.now() - timedelta(days=730)  # 2 years
DATE_300_RED = pywikibot.Timestamp.now() - timedelta(days=1095)  # 3 years
DATE_300_YELLOW = pywikibot.Timestamp.now() - timedelta(days=730)  # 2 years
DATE_500_RED = pywikibot.Timestamp.now() - timedelta(days=3650)  # 10 years
DATE_500_YELLOW = pywikibot.Timestamp.now() - timedelta(days=1825)  # 5 years
DATE_LOG_RED = pywikibot.Timestamp.now() - timedelta(days=1825)  # 5 years
DATE_LOG_YELLOW = pywikibot.Timestamp.now() - timedelta(days=1095)  # 3 years

REPORT_START = '<!-- report start -->'
REPORT_END = '<!-- report end -->'
SIGN_START = '<!-- sign start -->'
SIGN_END = '<!-- sign end -->'

user_groups_query = """
SELECt ug_user, actor_id, user_name, GROUP_CONCAT(ug_group SEPARATOR ',') AS `groups`
FROM user_groups
LEFT JOIN user ON ug_user = user_id
LEFT JOIN actor ON user_id = actor_user
WHERE ug_group IN ('sysop', 'bot')
GROUP BY ug_user
ORDER BY user_name
"""

revision_query = """
SELECT *
FROM ((
SELECT rev_timestamp AS timestamp
FROM revision_userindex
WHERE rev_actor = %s
ORDER BY rev_id DESC
LIMIT 500
) UNION ALL (
SELECT ar_timestamp AS timestamp
FROM archive
WHERE ar_actor = %s
ORDER BY ar_timestamp DESC
LIMIT 500
)) t
ORDER BY timestamp DESC
LIMIT 500
"""

last_log_query = """
SELECT log_timestamp
FROM logging_userindex
WHERE log_actor = %s
AND log_type IN ('block', 'delete', 'protect')
ORDER BY log_id DESC
LIMIT 1
"""

# %%


def parse_query_timestamp(row):
    if row is None:
        return pywikibot.Timestamp(1970, 1, 1)
    return pywikibot.Timestamp.fromtimestampformat(row[0].decode())


@lru_cache(maxsize=None)
def get_revs_by_actor_id(actor_id):
    cur.execute(revision_query, (actor_id, actor_id))
    return cur.fetchall()


@lru_cache(maxsize=None)
def get_last_log_by_actor_id(actor_id):
    cur.execute(last_log_query, actor_id)
    return parse_query_timestamp(cur.fetchone())


def foramt_timestamp_row(timestamp, red, yellow):
    res = ''
    if timestamp < red:
        res += " style='background:#FFC7C7' |"
    elif timestamp < yellow:
        res += " style='background:#FE9' |"
    res += timestamp.strftime('%Y-%m-%d')
    return res


# %%
conn = pymysql.connect(
    host=host,
    user=user,
    password=password,
    database='zhwiki_p',
    charset='utf8'
)
cur = conn.cursor()

# %%
cur.execute(user_groups_query)
user_with_groups = cur.fetchall()

# %%
report_text = ''
for row in user_with_groups:
    user_id, actor_id, username, groups = row
    username = username.decode()
    groups = sorted(groups.decode().split(','))
    if 'bot' in groups or 'sysop' not in groups:
        continue
    if username in cfg['ignored_users']:
        continue

    revs = get_revs_by_actor_id(actor_id)
    last_log = get_last_log_by_actor_id(actor_id)

    edit1 = parse_query_timestamp(revs[0])
    edit50 = parse_query_timestamp(revs[49])
    edit100 = parse_query_timestamp(revs[99])
    edit300 = parse_query_timestamp(revs[299])
    edit500 = parse_query_timestamp(revs[499])
    report_text += '|-\n'
    report_text += '|[[Special:Contribs/{0}|{0}]]'.format(username)
    report_text += '||' + edit1.strftime('%Y-%m-%d')
    report_text += '||' + foramt_timestamp_row(edit50, DATE_50_RED, DATE_50_YELLOW)
    report_text += '||' + foramt_timestamp_row(edit100, DATE_100_RED, DATE_100_YELLOW)
    report_text += '||' + foramt_timestamp_row(edit300, DATE_300_RED, DATE_300_YELLOW)
    report_text += '||' + foramt_timestamp_row(edit500, DATE_500_RED, DATE_500_YELLOW)
    report_text += '||' + foramt_timestamp_row(last_log, DATE_LOG_RED, DATE_LOG_YELLOW)
    report_text += '\n'

# %%
report_page = pywikibot.Page(site, cfg['page'])
text = report_page.text

idx1 = text.index(SIGN_START) + len(SIGN_START)
idx2 = text.index(SIGN_END)
text = text[:idx1] + '<onlyinclude>~~~~~</onlyinclude>' + text[idx2:]

idx1 = text.index(REPORT_START) + len(REPORT_START)
idx2 = text.index(REPORT_END)
text = text[:idx1] + '\n' + report_text + text[idx2:]

# %%
if args.confirm_report:
    pywikibot.showDiff(report_page.text, text)

# %%
if not args.confirm_report or input('Save report page? ').lower() in ['y', 'yes']:
    report_page.text = text
    report_page.save(summary=cfg['summary'], minor=False)
