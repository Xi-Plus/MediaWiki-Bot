# -*- coding: utf-8 -*-
import json
import os

import pymysql
os.environ["PYWIKIBOT_DIR"] = os.path.dirname(os.path.realpath(__file__))
import pywikibot

from config import config_page_name, database  # pylint: disable=E0611,W0614


os.environ["TZ"] = "UTC"

site = pywikibot.Site()
site.login()

config_page = pywikibot.Page(site, config_page_name)
cfg = config_page.text
cfg = json.loads(cfg)
print(json.dumps(cfg, indent=4, ensure_ascii=False))

if not cfg["enable"]:
    exit("disabled\n")

db = pymysql.connect(host=database['host'],
                     user=database['user'],
                     passwd=database['passwd'],
                     db=database['db'],
                     charset=database['charset'])
cur = db.cursor()

cur.execute(
    """SELECT `page`, `file` FROM `remove_broken_file_files` ORDER BY `page` ASC, `file` ASC""")
rows = cur.fetchall()

text = """* 本頁列出缺少檔案的條目，請檢查檔案的日誌並從條目中更換或移除檔案
* 產生時間：<onlyinclude>~~~~~</onlyinclude>
{| class="wikitable sortable"
|-
! 頁面 !! 檔案 !! 備註"""

for row in rows:
    text += '\n{{{{/row|1={0}|2={1}}}}}'.format(
        row[0], row[1])
text += """
|}"""

out_page = pywikibot.Page(site, cfg['output_page'])
out_page.text = text
out_page.save(summary=cfg['output_summary'], minor=False)
