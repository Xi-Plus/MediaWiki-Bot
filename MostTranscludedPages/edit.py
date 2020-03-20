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
print(args)

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

cur.execute("""SELECT `title`, `count`, `protectedit`, `protectmove`, `redirect` FROM `MostTranscludedPages_page` WHERE `wiki` = %s ORDER BY `title` ASC""", (args.dbwiki))
rows = cur.fetchall()


def check_required_protection(title, count):
    if title.startswith('模块:'):
        if count >= args.modulefull:
            return 2
        if count >= args.modulesemi:
            return 1
        return 0
    if title.startswith('MediaWiki:'):
        return 0
    if title.startswith('User:'):
        if title.endswith('.js') or title.endswith('.css') or title.endswith('.json'):
            return 0
    if count >= args.full:
        return 2
    if count >= args.semi:
        return 1
    return 0


countsysop = 0
countautoconfirmed = 0
for row in rows:
    title = row[0]
    count = row[1]
    protectedit = row[2]
    protectmove = row[3]
    redirect = row[4]
    comment = ''

    required_protection = check_required_protection(title, count)
    if required_protection == 2:
        if protectedit != 'sysop':
            comment = '[{{{{fullurl:{0}|action=protect&mwProtect-level-edit=sysop&mwProtect-level-move=sysop&mwProtect-level-create=sysop&mwProtect-reason=高風險模板：{1}引用}}}} 需要全保護]'.format(
                title, count)
            countsysop += 1
    if required_protection == 1:
        if protectedit == '':
            comment = '[{{{{fullurl:{0}|action=protect&mwProtect-level-edit=autoconfirmed&mwProtect-level-move=autoconfirmed&mwProtect-level-create=autoconfirmed&mwProtect-reason=高風險模板：{1}引用}}}} 需要半保護]'.format(
                title, count)
            countautoconfirmed += 1

    table += '\n|-\n| [[{0}]] || {1} || {2} || {3} || {4} || {5}'.format(
        title, count, protectedit, protectmove, redirect, comment
    )

table += '\n|}'

output = """* 參見[[Special:MostTranscludedPages]]
* {0}個頁面需要全保護
* {1}個頁面需要半保護
* 產生時間：<onlyinclude>~~~~~</onlyinclude>
{2}
""".format(countsysop, countautoconfirmed, table)

if len(output) / len(outputPage.text) < 0.5:
    exit('Something went wrong!\n')

outputPage.text = output
outputPage.save(summary=cfg['summary'])
