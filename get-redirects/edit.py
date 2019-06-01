# -*- coding: utf-8 -*-
import os

import pywikibot

os.environ['PYWIKIBOT_DIR'] = os.path.dirname(os.path.realpath(__file__))
os.environ['TZ'] = 'UTC'

site = pywikibot.Site()
site.login()

print('input:')
pages = []
try:
    while True:
        page = input()
        pages.append(page)
except EOFError:
    print('end')

for title in pages:
    if title.strip() == '':
        continue
    page = pywikibot.Page(site, title)
    print(page.title())
    for backlink in page.backlinks(filter_redirects=True):
        print('\t' + backlink.title())
