# -*- coding: utf-8 -*-
import argparse
import os
import re

os.environ['PYWIKIBOT_DIR'] = os.path.dirname(os.path.realpath(__file__))
import pywikibot
from pywikibot.data.api import Request


def converttitle(title):
    r = Request(site=site, parameters={
        'action': 'query',
        'titles': title,
        'redirects': 1,
        'converttitles': 1
    })
    data = r.submit()
    try:
        return list(data['query']['pages'].values())[0]['title']
    except KeyError:
        print(title, data)
        return title


os.environ['TZ'] = 'UTC'

parser = argparse.ArgumentParser()
parser.add_argument('page')
args = parser.parse_args()

site = pywikibot.Site()
site.login()

listpage = pywikibot.Page(site, args.page)

if not listpage.exists():
    print('not exists')
    exit()

listtext = listpage.text

links = re.findall(r'\[\[([^\]|]+)(?:\]\]|\|)', listtext)
print(links)

for link in links:
    if link.startswith('#'):
        continue

    newlink = converttitle(link)
    if link != newlink:
        listtext = re.sub(r'\[\[{}(\]\]|\|)'.format(
            re.escape(link)), r'[[{}\1'.format(newlink), listtext)
        print(link, newlink)

with open('out.txt', 'w') as f:
    f.write(listtext)
