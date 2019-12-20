import json
import os
import re

os.environ['PYWIKIBOT_DIR'] = os.path.dirname(os.path.realpath(__file__))
import pywikibot

from config import config_page_name  # pylint: disable=E0611,W0614


site = pywikibot.Site()
site.login()

config_page = pywikibot.Page(site, config_page_name)
cfg = config_page.text
cfg = json.loads(cfg)
print(json.dumps(cfg, indent=4, ensure_ascii=False))

if not cfg['enable']:
    exit('disabled\n')

reported_pages = set()
for page in pywikibot.Page(site, cfg['np_page']).linkedPages(namespaces=[0]):
    reported_pages.add(page.title())
# print(reported_pages)

afd_pages = set()
for page in pywikibot.Category(site, cfg['afd_category']).members(namespaces=[0]):
    afd_pages.add(page.title())
# print(afd_pages)

othertext = ''
text_dict = {}
for cate in pywikibot.Category(site, cfg['np_category']).members():
    if cate.namespace().id != 14:
        othertext += '# [[:{}]]\n'.format(cate.title())
        continue
    m = re.search(r'^Category:自(\d+)年(\d+)月主題關注度不足的條目$', cate.title())
    key = None
    if m:
        key = int(m.group(1)) * 100 + int(m.group(2))
        text_dict[key] = '=== [[:{}]] ===\n'.format(cate.title())
    for page in cate.members():
        title = page.title()
        if title not in reported_pages and title not in afd_pages:
            if key:
                text_dict[key] += '# [[:{}]]\n'.format(title)
            else:
                othertext += '# [[:{}]]\n'.format(title)

text = cfg['header_text']

if othertext != '':
    text += '=== 未知日期 ===\n' + othertext

text_dict = sorted(text_dict.items())
for _, temp_text in text_dict:
    if re.search(r'^===.+===\n$', temp_text):
        continue
    text += temp_text + '\n'

page = pywikibot.Page(site, cfg['output_page'])
pywikibot.showDiff(page.text, text)
page.text = text
page.save(summary=cfg['summary'], minor=False)
