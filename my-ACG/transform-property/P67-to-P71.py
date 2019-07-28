# -*- coding: utf-8 -*-
import argparse
import os

os.environ['PYWIKIBOT_DIR'] = os.path.dirname(os.path.realpath(__file__))
import pywikibot


site = pywikibot.Site()
site.login()
datasite = site.data_repository()


def changeP67toP71(title):
    title = title.replace('Item:', '')
    title = title.replace('Property:', '')
    print(title)

    if title[0] == 'Q':
        myitem = pywikibot.ItemPage(datasite, title)
    elif title[0] == 'P':
        myitem = pywikibot.PropertyPage(datasite, title)
    else:
        print('\t Not Wikibase page')
        return

    myitem.get()

    if 'P71' not in myitem.claims:
        new_claim = pywikibot.page.Claim(datasite, 'P71')
        url = myitem.claims['P67'][0].getTarget()
        targettitle = url.replace('https://www.wikidata.org/wiki/', '')
        print('\t', targettitle)
        new_claim.setTarget(targettitle)
        print('\t', new_claim)
        myitem.addClaim(new_claim, summary='轉換屬性')

    myitem.removeClaims(myitem.claims['P67'], summary='移除舊屬性')


def main():
    P67 = pywikibot.PropertyPage(datasite, 'P67')

    for backlink in P67.backlinks():
        changeP67toP71(backlink.title())


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('title', nargs='?')
    args = parser.parse_args()
    if args.title:
        changeP67toP71(args.title)
    else:
        main()
