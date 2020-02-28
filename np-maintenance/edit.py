# -*- coding: utf-8 -*-
import argparse
import os
import re
import urllib.parse

os.environ['PYWIKIBOT_DIR'] = os.path.dirname(os.path.realpath(__file__))
import pywikibot
import requests
from bs4 import BeautifulSoup


parser = argparse.ArgumentParser()
parser.add_argument('-c', '--check', action='store_true', dest='check')
parser.set_defaults(check=False)
args = parser.parse_args()
print(args)

site = pywikibot.Site()
site.login()

url = 'https://zh.wikipedia.org/wiki/Wikipedia:关注度/提报?action=render'
try:
    req = requests.get(url)
except Exception as e:
    print(e)
    exit()
page_html = req.text
soup = BeautifulSoup(page_html, 'html.parser')
root = soup.find('div', {'class': 'mw-parser-output'})
cnt = 0
npPage = pywikibot.Page(site, 'Wikipedia:关注度/提报')
text = npPage.text
for ul in root.find_all('ul', recursive=False):
    for li in ul.find_all('li', recursive=False):
        link = li.find('a')
        classlist = link.get('class')
        if link and classlist and 'mw-redirect' in classlist:
            title = re.sub(r'^//zh.wikipedia.org/wiki/(.+)$', r'\1', link.get('href'))
            title = urllib.parse.unquote_plus(title)
            print(title)

            log = list(site.logevents(page=pywikibot.Page(site, title), total=1))[0]
            if log.type() != 'move':
                print('\tnot move')
                continue
            newtitle1 = log.target_page.title()

            titleregex = re.sub(r'_', '[ _]', re.escape(title))
            page = pywikibot.Page(site, title)
            newtitle2 = page.getRedirectTarget().title()
            if newtitle1 != newtitle2:
                print('\ttitle not match:', newtitle1, newtitle2)
                continue
            text = re.sub(
                r'\[\[{0}]]，{{{{Findsources\|{0}}}}}'.format(titleregex),
                '[[{0}]]，{{{{Findsources|{0}}}}}'.format(newtitle2),
                text
            )
            cnt += 1

print(cnt)
pywikibot.showDiff(npPage.text, text)
summary = '修正{}個因移動產生的重定向'.format(cnt)
print(summary)
if args.check and input('Save?').lower() not in ['', 'y', 'yes']:
    exit()
npPage.text = text
npPage.save(summary=summary, minor=False)
