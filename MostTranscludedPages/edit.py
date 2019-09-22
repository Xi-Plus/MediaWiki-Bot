# -*- coding: utf-8 -*-
import argparse
import json
import os

import pymysql
os.environ['PYWIKIBOT_DIR'] = os.path.dirname(os.path.realpath(__file__))
import pywikibot
from config import config_page_name, database  # pylint: disable=E0611,W0614


parser = argparse.ArgumentParser()
parser.add_argument('lang', nargs='?', default='zh')
parser.add_argument('wiki', nargs='?', default='wikipedia')
parser.add_argument('dbwiki', nargs='?', default='zhwiki')
parser.add_argument('--full', type=int, default=5000)
parser.add_argument('--semi', type=int, default=500)
parser.add_argument('--modulefull', type=int, default=5000)
parser.add_argument('--modulesemi', type=int, default=5000)
args = parser.parse_args()

os.environ['TZ'] = 'UTC'

site = pywikibot.Site(args.lang, args.wiki)
site.login()

config_page = pywikibot.Page(site, config_page_name[args.lang][args.wiki])
cfg = config_page.text
cfg = json.loads(cfg)
print(json.dumps(cfg, indent=4, ensure_ascii=False))

if not cfg['enable']:
    exit('disabled\n')

outputPage = pywikibot.Page(site, cfg['output_page_name'])

table = (
    '{| class="wikitable sortable"'
    '\n|-'
    '\n! 頁面 !! 引用數 !! 編輯保護 !! 移動保護 !! 重定向 !! 備註'
)


db = pymysql.connect(host=database['host'],
                     user=database['user'],
                     passwd=database['passwd'],
                     db=database['db'],
                     charset=database['charset'])
cur = db.cursor()

cur.execute("""SELECT `title`, `count`, `protectedit`, `protectmove`, `redirect` FROM `MostTranscludedPages_page` WHERE `wiki` = %s ORDER BY `count` DESC""", (args.dbwiki))
rows = cur.fetchall()

countsysop = 0
countautoconfirmed = 0
for row in rows:
    title = row[0]
    count = row[1]
    protectedit = row[2]
    protectmove = row[3]
    redirect = row[4]
    comment = ''

    if (not title.startswith('模块:') and count >= args.full) or (title.startswith('模块:') and count >= args.modulefull):
        if protectedit != 'sysop':
            comment = '[{{{{fullurl:{0}|action=protect&mwProtect-level-edit=sysop&mwProtect-level-move=sysop&mwProtect-reason=高風險模板：{1}引用}}}} 需要全保護]'.format(
                title, count)
            countsysop += 1
    elif (not title.startswith('模块:') and count >= args.semi) or (title.startswith('模块:') and count >= args.modulesemi):
        if protectedit == '':
            comment = '[{{{{fullurl:{0}|action=protect&mwProtect-level-edit=autoconfirmed&mwProtect-level-move=autoconfirmed&mwProtect-reason=高風險模板：{1}引用}}}} 需要半保護]'.format(
                title, count)
            countautoconfirmed += 1

    table += '\n|-\n| [[{0}]] || {1} || {2} || {3} || {4} || {5}'.format(
        title, count, protectedit, protectmove, redirect, comment
    )

table += '\n|}'

output = """* {0}個頁面需要全保護
* {1}個頁面需要半保護
{2}
""".format(countsysop, countautoconfirmed, table)

outputPage.text = output
outputPage.save(summary=cfg['summary'])
