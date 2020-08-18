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
for afd_page in cfg['afd_pages']:
    for page in pywikibot.Page(site, afd_page).linkedPages():
        reported_pages.add(page.title())
# print(reported_pages)

tagged_pages = set()
templatePage = pywikibot.Page(site, cfg['afd_template'])
for page in templatePage.embeddedin():
    tagged_pages.add(page.title())
# print(tagged_pages)


text = cfg['header_text']

for title in sorted(list(tagged_pages - reported_pages)):
    if re.search(r'^Template:[ACIMRTUV]fd($|/|-)', title):
        continue
    if title in cfg['whitelist']:
        continue

    text += '# [[:{}]]\n'.format(title)

page = pywikibot.Page(site, cfg['output_page'])
pywikibot.showDiff(page.text, text)
page.text = text
page.save(summary=cfg['summary'], minor=False)
