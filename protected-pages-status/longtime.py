import json
from datetime import datetime, timedelta

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


text = """* 本頁列出被長期半保護的頁面，參見[https://paws-public.wmflabs.org/paws-public/User:Xiplus/long%20time%20protected%20ariticle.ipynb 程式碼]
* 長期為終止期限超過{}，目前僅包括條目及維基百科命名空間
* 產生時間：<onlyinclude>~~~~~</onlyinclude>

{{| class="wikitable sortable"
!頁面!!保護日誌!!期限""".format(d.strftime('%-m月%-d日'))


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


page = pywikibot.Page(site, "Wikipedia:資料庫報告/被長期半保護的頁面")
page.text = text
page.save(summary="產生列表", minor=False)
