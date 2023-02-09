# -*- coding: utf-8 -*-

import argparse
import ipaddress
import json
import os
import re
import datetime
import time
from math import floor, log10

import pymysql
os.environ['PYWIKIBOT_DIR'] = os.path.dirname(os.path.realpath(__file__))
import pywikibot

from config import (config_page_name, host,  # pylint: disable=E0611,W0614
                    password, user)

ROOTDIR = os.path.dirname(os.path.realpath(__file__))
LOGDIR = os.path.join(ROOTDIR, 'log')
os.makedirs(LOGDIR, exist_ok=True)

parser = argparse.ArgumentParser()
parser.add_argument('--dry-run', action='store_true')
parser.set_defaults(dry_run=False)
args = parser.parse_args()
if args.dry_run:
    print('dry_run is on')

os.environ['TZ'] = 'UTC'

site = pywikibot.Site()
site.login()

# config_page = pywikibot.Page(site, config_page_name)
# cfg = config_page.text
# cfg = json.loads(cfg)

# if not cfg['enable']:
#     print('disabled')
#     exit()

print('Start at {}'.format(datetime.datetime.now()))


query1 = '''
SELECT ipb_address, ipb_expiry, ipb_anon_only, ipb_create_account, ipb_block_email, ipb_allow_usertalk, comment_text
FROM ipblocks
LEFT JOIN comment ON ipb_reason_id = comment_id
WHERE ipb_user = 0
    AND ipb_auto = 0
    AND ipb_expiry > DATE_FORMAT(DATE_ADD(NOW(), INTERVAL 30 DAY), '%Y%m%d%H%i%s')
    AND ipb_expiry != 'infinity'
    AND comment_text NOT LIKE '%blocked proxy%'
    AND comment_text NOT LIKE '%nonblock%'
    AND comment_text NOT LIKE '%ange block%'
    AND comment_text NOT LIKE '%angeblock%'
    AND comment_text NOT LIKE '%chool block%'
    AND comment_text NOT LIKE '%choolblock%'
    AND comment_text NOT LIKE '%heckUser block%'
    AND ipb_range_start != ipb_range_end
'''

query2 = '''
SELECT ipb_address, ipb_expiry, ipb_anon_only, ipb_create_account, ipb_block_email, ipb_allow_usertalk, comment_text
FROM ipblocks
LEFT JOIN comment ON ipb_reason_id = comment_id
WHERE ipb_user = 0
    AND ipb_auto = 0
    AND ipb_anon_only = 0
    AND ipb_expiry > DATE_FORMAT(DATE_ADD(NOW(), INTERVAL 30 DAY), '%Y%m%d%H%i%s')
    AND (comment_text LIKE '%anonblock%'
        OR comment_text LIKE '%nonblock%'
        OR comment_text LIKE '%ange block%'
        OR comment_text LIKE '%chool block%'
        OR comment_text LIKE '%choolblock%')
    AND ipb_range_start != ipb_range_end
'''

conn = pymysql.connect(
    host=host,
    user=user,
    password=password,
    charset='utf8'
)

with conn.cursor() as cursor:
    cursor.execute('use zhwiki_p')
    cursor.execute(query1)
    result1 = cursor.fetchall()

for row in result1:
    ipb_address, ipb_expiry, ipb_anon_only, ipb_create_account, ipb_block_email, ipb_allow_usertalk, comment_text = row
    ipb_address = ipb_address.decode()
    ipb_expiry = ipb_expiry.decode()
    comment_text = comment_text.decode()

    if '調整封鎖原因' in comment_text:
        continue

    network = ipaddress.ip_network(ipb_address)
    if isinstance(network, ipaddress.IPv6Network) and network.prefixlen >= 64:
        # print('Ignore {}'.format(network))
        continue

    user = pywikibot.User(site, ipb_address)

    new_summary = ''
    if ipb_anon_only == 1:
        new_summary += '<!-- 請登入您的帳號，若無帳號，請閱讀 https://w.wiki/Jyi -->{{range block}}'
    else:
        new_summary += '<!-- 請閱讀 https://w.wiki/Jyi -->{{CheckUser block}}'
    new_summary += '<!-- ' + comment_text + '，調整封鎖原因 -->'

    input('Block {}\n\twith reason {}? '.format(user.username, new_summary))

    try:
        result = site.blockuser(
            user=user,
            expiry=ipb_expiry,
            reason=new_summary,
            anononly=ipb_anon_only == 1,
            nocreate=ipb_create_account == 1,
            noemail=ipb_block_email == 1,
            allowusertalk=ipb_allow_usertalk == 1,
            reblock=True,
        )
        print('block {} result: {}'.format(ipb_address, result))
    except Exception as e:
        print('error when block {}: {}'.format(ipb_address, e))


with conn.cursor() as cursor:
    cursor.execute('use zhwiki_p')
    cursor.execute(query2)
    result2 = cursor.fetchall()

for row in result2:
    ipb_address, ipb_expiry, ipb_anon_only, ipb_create_account, ipb_block_email, ipb_allow_usertalk, comment_text = row
    ipb_address = ipb_address.decode()
    ipb_expiry = ipb_expiry.decode()
    comment_text = comment_text.decode()

    network = ipaddress.ip_network(ipb_address)

    user = pywikibot.User(site, ipb_address)

    # input('Block {}? '.format(user.username))

    try:
        result = site.blockuser(
            user=user,
            expiry=ipb_expiry,
            reason=comment_text,
            anononly=True,
            nocreate=ipb_create_account == 1,
            noemail=ipb_block_email == 1,
            allowusertalk=ipb_allow_usertalk == 1,
            reblock=True,
        )
        print('block {} result: {}'.format(ipb_address, result))
    except Exception as e:
        print('error when block {}: {}'.format(ipb_address, e))


conn.close()
print('Done at {}'.format(datetime.datetime.now()))
