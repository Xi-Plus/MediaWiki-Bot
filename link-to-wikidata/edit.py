# -*- coding: utf-8 -*-
import csv
import os
import re

os.environ['PYWIKIBOT_DIR'] = os.path.dirname(os.path.realpath(__file__))
import pywikibot
from config import blacklists, targetSite  # pylint: disable=E0611,W0614


site = pywikibot.Site()
site.login()

with open('list.csv') as csvfile:
    reader = csv.reader(csvfile)
    for row in reader:
        fromTitle = row[0]
        if len(row) < 2:
            toTitle = fromTitle
        else:
            toTitle = row[1]
        print('Add {2} link {1} into item {0}'.format(fromTitle, toTitle, targetSite))

        inBlack = False
        for blacklist in blacklists:
            if re.search(blacklist, toTitle):
                inBlack = True
                break
        if inBlack:
            print('Skip')
            continue

        try:
            page = pywikibot.Page(site, fromTitle)
            item = pywikibot.ItemPage.fromPage(page)

            item.setSitelink(sitelink={'site': targetSite, 'title': toTitle}, summary='Add {}'.format(targetSite))
        except Exception as e:
            print(e)
