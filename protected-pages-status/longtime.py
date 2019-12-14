import json
import os
from datetime import datetime, timedelta

os.environ['PYWIKIBOT_DIR'] = os.path.dirname(os.path.realpath(__file__))
import pywikibot

import toolforge
from config import config_page_name  # pylint: disable=E0611,W0614


site = pywikibot.Site()
site.login()

config_page = pywikibot.Page(site, config_page_name)
cfg = config_page.text
cfg = json.loads(cfg)
print(json.dumps(cfg, indent=4, ensure_ascii=False))

if not cfg['longtime_enable']:
    exit('disabled\n')

conn = toolforge.connect('zhwiki')

d = datetime.today() + timedelta(days=30)


with conn.cursor() as cur:
    cur.execute("""
        SELECT pr_page, page_namespace, page_title, pr_expiry
        FROM page_restrictions
        LEFT JOIN page ON pr_page = page_id
        WHERE pr_type = "edit"
            AND pr_level = "autoconfirmed"
            AND pr_expiry != "infinity"
            AND pr_expiry >= {}
            AND page_namespace IN (0, 4)
        ORDER BY pr_expiry DESC, page_title ASC

    """.format(d.strftime('%Y%m%d000000')))
    res = cur.fetchall()


text = cfg['longtime_header_text'].format(d.strftime('%-m月%-d日'))

text += """{{| class="wikitable sortable"
!頁面!!保護日誌!!期限"""

for row in res:
    pid = str(row[0])
    ns = str(row[1])
    title = row[2].decode()
    expiry = str(row[3].decode())
    text += "\n|-\n"
    text += "|[[Special:Redirect/page/" + pid + "|{{subst:#ifeq:" + ns + "|0||{{subst:ns:" + ns + "}}:}}" + title + "]]"
    text += "||[{{fullurl:Special:日志/protect|page={{subst:#ifeq:" + ns + "|0||{{subst:ns:" + ns + "}}:}}" + title + "}} 保護日誌]"
    text += "||" + expiry
text += "\n|}"


page = pywikibot.Page(site, cfg['longtime_output_page'])
page.text = text
page.save(summary=cfg['longtime_summary'], minor=False)
