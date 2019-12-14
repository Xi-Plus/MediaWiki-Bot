import json
import os

os.environ['PYWIKIBOT_DIR'] = os.path.dirname(os.path.realpath(__file__))
import pywikibot
from pywikibot.data.api import Request

from config import config_page_name  # pylint: disable=E0611,W0614


site = pywikibot.Site()
site.login()

config_page = pywikibot.Page(site, config_page_name)
cfg = config_page.text
cfg = json.loads(cfg)
print(json.dumps(cfg, indent=4, ensure_ascii=False))

if not cfg['enable']:
    exit('disabled\n')


skip_pages = set()

for page in pywikibot.Page(site, "Template:Merge from").getReferences(only_template_inclusion=True):
    print(page.title())
    skip_pages.add(page.title())

for page in pywikibot.Page(site, "Template:Merge to").getReferences(only_template_inclusion=True):
    print(page.title())
    skip_pages.add(page.title())

for page in pywikibot.Page(site, "Template:Merge").getReferences(only_template_inclusion=True):
    print(page.title())
    skip_pages.add(page.title())

# print(len(skip_pages), skip_pages)

parameters = {
    "action": "query",
    "format": "json",
    "list": "querypage",
    "qppage": "UnconnectedPages",
    "qplimit": "max"
}
allpages = []
while True:
    print(parameters)
    r = Request(site=site, parameters=parameters)
    data = r.submit()
    for row in data['query']['querypage']['results']:
        #         if row['ns'] != 0:
        #             continue
        allpages.append(row)
#         print(row)
    del data['query']
    print(data)
    if 'query-continue' not in data:
        break
    for key in data['query-continue']['querypage']:
        parameters[key] = data['query-continue']['querypage'][key]
print('allpages', len(allpages))


text_temp = {
    0: '',
    4: '',
    10: '',
    14: '',
    100: '',
    828: '',
}
for row in allpages:
    title = row['title']
    if title in skip_pages:
        continue
    if re.search(r'^(Template|模块):.*\/doc', title):
        continue
    if re.search(r'模块:(沙盒|CGroup)\/', title):
        continue
    if re.search(r'\.css$', title):
        continue
    if re.search(r'^Wikipedia:(頁面|檔案)存廢討論', title):
        continue
    if re.search(r'^Wikipedia:(資料庫報告|中国大陆维基人用户组|条目请求|投票|《新手》|机器人\/申请|香港維基人佈告板|臺灣教育專案|聚會|持续出没的破坏者|邊緣人小組|坏笑话和删除的胡话|中文维基政治编辑战|维基奖励|管理員解任投票|修订版本删除请求|元維基用戶查核請求|特色圖片評選|申请成为管理员|維基獎勵|存廢覆核請求|特色列表|動員令|《求闻》|管理员通告板|新闻动态候选|《育知》|新手會|互助客栈|优良条目|典范条目|每日图片|已删除内容查询|新条目推荐|聚会|維基學生會)\/', title):
        continue
    if re.search(r'^Wikipedia:.+\/header$', title):
        continue
    if re.search(r'^Wikipedia:.+(存档|存檔|沙盒)', title):
        continue
    if re.search(r'^Wikipedia:.+(專題|专题)\/', title):
        continue
    if re.search(r'^Category:自\d+年', title):
        continue
#     if re.search(r'^Wikipedia:', title):
    print(title)
    text_temp[row['ns']] += '# [[:{}]]\n'.format(title)


text = cfg['header_text']

ns_text = {
    0: '條目',
    4: '維基百科',
    10: '模板',
    14: '分類',
    100: '主題',
    828: '模組',
}
for ns in text_temp:
    text += '== {} ==\n'.format(ns_text[ns])
    text += text_temp[ns]


page = pywikibot.Page(site, cfg['output_page'])
page.text = text
page.save(summary=cfg['summary'], minor=False)
