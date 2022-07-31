# -*- coding: utf-8 -*-
import argparse
import csv
import os

os.environ['PYWIKIBOT_DIR'] = os.path.dirname(os.path.realpath(__file__))
import pywikibot

parser = argparse.ArgumentParser()
parser.add_argument('lang', nargs='?', default='zh')
parser.add_argument('wiki', nargs='?', default='wikipedia')
parser.add_argument('dbwiki', nargs='?', default='zhwiki')
args = parser.parse_args()

os.environ['TZ'] = 'UTC'

site = pywikibot.Site(args.lang, args.wiki)
site.login()

with open('list.csv', 'r', encoding='utf8') as f:
    r = csv.reader(f)
    for row in r:
        title = row[0]
        edit = row[1]
        move = row[2]
        create = row[3]
        reason = row[4]

        page = pywikibot.Page(site, title)
        args = {
            'reason': reason,
            'prompt': False,
        }
        protections = {}
        if page.exists():
            protections['edit'] = edit
            protections['move'] = move
        else:
            protections['create'] = create
        args['protections'] = protections

        print(title, args)

        page.protect(**args)
