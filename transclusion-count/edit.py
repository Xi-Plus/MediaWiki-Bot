# -*- coding: utf-8 -*-

# Public domain; bjweeks, MZMcBride, ahecht; 2008, 2016, 2018, 2019
# Copied from https://en.wikipedia.org/w/index.php?title=User%3AAhechtbot%2Ftransclusioncount.py&oldid=944285730

import argparse
import json
import os
import re
import time

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

config_page = pywikibot.Page(site, config_page_name)
cfg = config_page.text
cfg = json.loads(cfg)

if not cfg['enable']:
    exit('disabled\n')


report_template = '''\
return {{
{}
}}
'''

query1 = '''
/* transclusioncount.py SLOW_OK */
SELECT
  tl_title,
  COUNT(*)
FROM templatelinks
WHERE tl_namespace = 10
GROUP BY tl_title
HAVING COUNT(*) > 2000
LIMIT 10000;
'''

query2 = '''
/* transclusioncount.py SLOW_OK */
SELECT
  tl_title,
  COUNT(*)
FROM templatelinks
WHERE tl_namespace = 828
GROUP BY tl_title
HAVING COUNT(*) > 2000
LIMIT 10000;
'''

connectSuccess = False
tries = 0

while not connectSuccess:
    try:
        conn = pymysql.connect(
            host=host,
            user=user,
            password=password,
            charset='utf8'
        )
        print('\nExecuting query1 at {}...'.format(time.ctime()))
        with conn.cursor() as cursor:
            cursor.execute('use zhwiki_p')
            cursor.execute(query1)
            result1 = cursor.fetchall()
        print('\nExecuting query2 at {}...'.format(time.ctime()))
        with conn.cursor() as cursor:
            cursor.execute('use zhwiki_p')
            cursor.execute(query2)
            result2 = cursor.fetchall()
        connectSuccess = True
        print('Success at {}!'.format(time.ctime()))
    except Exception as e:
        try:
            cursor.close()
        except Exception:
            pass
        try:
            conn.close()
        except Exception:
            pass
        print('Error: ', e)
        tries += 1
        if tries > 24:
            print('Script failed after 24 tries at {}.'.format(time.ctime()))
            raise SystemExit(e)
        print('Waiting 1 hour starting at {}...'.format(time.ctime()))
        time.sleep(3600)

if args.dry_run:
    try:
        with open(os.path.join(LOGDIR, 'result1.txt'), 'w') as f:
            f.write(str(result1))
        with open(os.path.join(LOGDIR, 'result2.txt'), 'w') as f:
            f.write(str(result2))
    except Exception as e:
        print('Error writing to file: {}'.format(e))
    print('\nBuilding output...')


output = {'other': []}
for i in range(ord('A'), ord('Z') + 1):
    output[chr(i)] = []

for row in result1:
    try:
        tl_title = row[0].decode()
    except Exception:
        tl_title = str(row[0])
    index_letter = tl_title[0]
    uses = row[1]
    table_row = '''["%s"] = %i,''' % (tl_title.replace("\\", "\\\\").replace('"', '\\"'), uses)
    try:
        output[index_letter].append(table_row)
    except Exception:
        output["other"].append(table_row)

for row in result2:
    try:
        tl_title = row[0].decode()
    except Exception:
        tl_title = str(row[0])
    index_letter = tl_title[0]
    uses = row[1]
    table_row = '''["Module:{}"] = {},'''.format(tl_title.replace('\\', '\\\\').replace('"', '\\"'), uses)
    try:
        output[index_letter].append(table_row)
    except Exception:
        output['other'].append(table_row)

for section, content in sorted(output.items()):
    report = pywikibot.Page(site, cfg['data_root'] + section)
    report.text = report_template.format('\n'.join(content))
    if not args.dry_run:
        try:
            report.save(cfg['summary'])
        except Exception as e:
            print('Error at {}: {}'.format(time.ctime(), e))
    else:
        with open(os.path.join(LOGDIR, '{}.txt'.format(section)), 'w') as f:
            f.write(report.text)

print('\nDone at {}!'.format(time.ctime()))
