# -*- coding: utf-8 -*-
import argparse
import csv
import os

os.environ['PYWIKIBOT_DIR'] = os.path.dirname(os.path.realpath(__file__))
import pywikibot


site = pywikibot.Site()
site.login()
datasite = site.data_repository()


def addSitelinks(title, site, targettitle):
    print(title)

    if title[0] == 'Q':
        myitem = pywikibot.ItemPage(datasite, title)
    else:
        print('\t Not Item page')
        return

    data = {
        'site': site,
        'title': targettitle
    }
    print('\t', data)
    myitem.setSitelink(data, summary='自動設定wikidata連結')


def main(filename):
    with open(filename) as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            addSitelinks(row[0], 'wikidatawiki', row[1])


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('filename')
    args = parser.parse_args()
    main(args.filename)
