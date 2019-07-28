# -*- coding: utf-8 -*-
import argparse
import os

os.environ['PYWIKIBOT_DIR'] = os.path.dirname(os.path.realpath(__file__))
import pywikibot
from pywikibot.data.api import Request


site = pywikibot.Site()
site.login()
datasite = site.data_repository()

zhsite = pywikibot.Site('zh', 'wikipedia')


def converttitle(site, title):
    r = Request(site=site, parameters={
        'action': 'query',
        'titles': title,
        'redirects': 1,
        'converttitles': 1
    })
    data = r.submit()
    page = list(data['query']['pages'].values())[0]
    if 'missing' in page:
        return None
    return page['title']


def changeWpAndMoe(title):
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

    if 'P68' not in myitem.claims and 'P65' in myitem.claims:
        url = myitem.claims['P65'][0].getTarget()
        targettitle = url.replace('https://zh.wikipedia.org/wiki/', '')
        targettitle = converttitle(zhsite, targettitle)
        if targettitle:
            new_claim = pywikibot.page.Claim(datasite, 'P68')
            new_claim.setTarget(targettitle)
            print('\t', targettitle)
            myitem.addClaim(new_claim, summary='轉換屬性')

    if 'P70' not in myitem.claims and 'P66' in myitem.claims:
        url = myitem.claims['P66'][0].getTarget()
        targettitle = url.replace('https://zh.moegirl.org/', '')
        targettitle = converttitle(zhsite, targettitle)
        if targettitle:
            new_claim = pywikibot.page.Claim(datasite, 'P70')
            new_claim.setTarget(targettitle)
            print('\t', targettitle)
            myitem.addClaim(new_claim, summary='轉換屬性')

    toRemove = []
    if 'P65' in myitem.claims:
        toRemove.extend(myitem.claims['P65'])
    if 'P66' in myitem.claims:
        toRemove.extend(myitem.claims['P66'])
    if toRemove:
        myitem.removeClaims(toRemove, summary='移除舊屬性')


def main():
    P65 = pywikibot.PropertyPage(datasite, 'P65')
    for backlink in P65.backlinks():
        changeWpAndMoe(backlink.title())

    P66 = pywikibot.PropertyPage(datasite, 'P66')
    for backlink in P66.backlinks():
        changeWpAndMoe(backlink.title())


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('title', nargs='?')
    args = parser.parse_args()
    if args.title:
        changeWpAndMoe(args.title)
    else:
        main()
