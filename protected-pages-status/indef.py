import json
import os

import pymysql

os.environ['PYWIKIBOT_DIR'] = os.path.dirname(os.path.realpath(__file__))
import pywikibot

from config import (config_page_name, host,  # pylint: disable=E0611,W0614
                    password, user)

site = pywikibot.Site()
site.login()

config_page = pywikibot.Page(site, config_page_name)
cfg = config_page.text
cfg = json.loads(cfg)
print(json.dumps(cfg, indent=4, ensure_ascii=False))

if not cfg['longtime_enable']:
    print('disabled')
    exit()

conn = pymysql.connect(
    host=host,
    user=user,
    password=password,
    charset="utf8"
)


with conn.cursor() as cur:
    cur.execute('use zhwiki_p')
    cur.execute("""
        SELECT pr_page, page_namespace, page_title
        FROM page_restrictions
        LEFT JOIN page ON pr_page = page_id
        WHERE pr_type = "edit"
            AND pr_level = "autoconfirmed"
            AND pr_expiry = "infinity"
            AND page_namespace = 0
        ORDER BY page_title ASC
    """)
    res = cur.fetchall()


text = cfg['indef_header_text']
text += """{| class="wikitable sortable"
!頁面!!保護日誌"""

for row in res:
    pid = str(row[0])
    ns = str(row[1])
    title = row[2].decode()
    text += "\n|-\n"
    text += "|[[Special:Redirect/page/" + pid + "|{{subst:#ifeq:" + ns + "|0||{{subst:ns:" + ns + "}}:}}" + title + "]]"
    text += "||[{{fullurl:Special:日志/protect|page={{subst:#ifeq:" + ns + "|0||{{subst:ns:" + ns + "}}:}}" + title + "}} 保護日誌]"
text += "\n|}"


page = pywikibot.Page(site, cfg['indef_output_page'])
page.text = text
page.save(summary=cfg['indef_summary'], minor=False)
