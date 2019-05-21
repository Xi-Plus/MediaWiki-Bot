# -*- coding: utf-8 -*-
import csv
import os

os.environ['PYWIKIBOT_DIR'] = os.path.dirname(os.path.realpath(__file__))
import pywikibot


site = pywikibot.Site()
site.login()

with open('list.csv') as csvfile:
    reader = csv.reader(csvfile)
    for row in reader:
        title = row[0]
        content = '#REDIRECT [[{}]]'.format(row[1])
        summary = '機器人：重定向到[[{}]]'.format(row[1])
        print('Create {} Content: {} Summary: {}'.format(title, content, summary))

        newPage = pywikibot.Page(site, title)
        newPage.text = content
        # input()
        newPage.save(summary=summary, minor=False)
