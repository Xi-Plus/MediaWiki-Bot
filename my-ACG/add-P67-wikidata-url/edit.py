# -*- coding: utf-8 -*-
import argparse
import csv
import os

os.environ['PYWIKIBOT_DIR'] = os.path.dirname(os.path.realpath(__file__))
import pywikibot


site = pywikibot.Site()
site.login()
datasite = site.data_repository()


def addWikidataUrl(title, targettitle):
    print(title)

    if title[0] == 'Q':
        myitem = pywikibot.ItemPage(datasite, title)
        url = 'https://www.wikidata.org/wiki/{}'.format(targettitle)
    elif title[0] == 'P':
        url = 'https://www.wikidata.org/wiki/Property:{}'.format(targettitle)
        myitem = pywikibot.PropertyPage(datasite, title)
    else:
        print('\t Not Wikibase page')
        return

    new_claim = pywikibot.page.Claim(datasite, 'P67')
    new_claim.setTarget(url)
    print('\t', new_claim)
    myitem.addClaim(new_claim, summary='設定維基數據網址')


def main(filename):
    with open(filename) as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            addWikidataUrl(row[0], row[1])


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('filename')
    args = parser.parse_args()
    main(args.filename)
