import json
import os

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

text = cfg['header_text']

reported_pages = set()
for page in pywikibot.Page(site, cfg['np_page']).linkedPages(namespaces=[0]):
    reported_pages.add(page.title())
# print(reported_pages)

afd_pages = set()
for page in pywikibot.Category(site, cfg['afd_category']).members(namespaces=[0]):
    afd_pages.add(page.title())
# print(afd_pages)

othertext = ''
for cate in pywikibot.Category(site, cfg['np_category']).members():
    if cate.namespace().id != 14:
        othertext += '# [[:{}]]\n'.format(cate.title())
        continue
    text += '=== [[:{}]] ===\n'.format(cate.title())
    for page in cate.members():
        title = page.title()
        if title not in reported_pages and title not in afd_pages:
            text += '# [[:{}]]\n'.format(title)
    text += '\n'

if othertext != '':
    text += '=== 未知日期 ===\n' + othertext

print(text)

page = pywikibot.Page(site, cfg['output_page'])
page.text = text
page.save(summary=cfg['summary'], minor=False)
