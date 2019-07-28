# -*- coding: utf-8 -*-
import argparse
import os

os.environ['PYWIKIBOT_DIR'] = os.path.dirname(os.path.realpath(__file__))
import pywikibot


site = pywikibot.Site()
site.login()
datasite = site.data_repository()

wdsite = pywikibot.Site('wikidata', 'wikidata')
wdsite.login()


def getItem(site, title):
    if title[0] == 'Q':
        return pywikibot.ItemPage(site, title)
    if title[0] == 'P':
        return pywikibot.PropertyPage(site, title)
    print('\t Not Wikibase page')
    return None


itemMap = {}

P67item = pywikibot.PropertyPage(datasite, 'P67')
for backlink in P67item.backlinks():
    localtitle = backlink.title()
    localtitle = localtitle.replace('Item:', '')
    localtitle = localtitle.replace('Property:', '')
    item = getItem(datasite, localtitle)
    targettitle = item.get()['claims']['P67'][0].getTarget()
    targettitle = targettitle.replace('https://www.wikidata.org/wiki/Property:', '')
    targettitle = targettitle.replace('https://www.wikidata.org/wiki/', '')
    # print(localtitle)
    # print('\t', targettitle)
    itemMap[targettitle] = localtitle


def importClaimsFromWikidata(localtitle, targettitle):
    print(localtitle, targettitle)

    myitem = getItem(datasite, localtitle)
    wditem = getItem(wdsite, targettitle)

    wdclaims = wditem.get()['claims']
    myclaims = myitem.get()['claims']

    for Pid in wdclaims:
        if Pid not in itemMap:
            continue

        print('\t', Pid, itemMap[Pid])
        claims = wdclaims[Pid]
        for claim in claims:
            if claim.type in ['wikibase-item', 'wikibase-property']:
                valueId = claim.getTarget().getID()
                if valueId not in itemMap:
                    continue
            new_claim = pywikibot.page.Claim(datasite, itemMap[Pid])
            if claim.type in ['wikibase-item', 'wikibase-property']:
                new_claim.setTarget(getItem(datasite, itemMap[valueId]))
                print('\t\t value', valueId, itemMap[valueId])
                print('\t\t target', claim)
                print('\t\t local', new_claim)
            else:
                new_claim.setTarget(claim.getTarget())
                print('\t\t value', claim.getTarget())
            exist = False
            if itemMap[Pid] in myclaims:
                for myclaim in myclaims[itemMap[Pid]]:
                    if new_claim.target_equals(myclaim.getTarget()):
                        exist = True
            if exist:
                print('\t\t Skip exist')
                continue
            if len(claim.qualifiers):
                print('\t\t Skip claim with qualifiers')
                continue

            myitem.addClaim(new_claim, summary='匯入陳述')


def main():
    for targettitle, localtitle in itemMap.items():
        importClaimsFromWikidata(localtitle, targettitle)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('local', nargs='?')
    parser.add_argument('target', nargs='?')
    args = parser.parse_args()
    if args.local and args.target:
        importClaimsFromWikidata(args.local, args.target)
    else:
        main()
