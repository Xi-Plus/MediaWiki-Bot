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

zhsite = pywikibot.Site('zh', 'wikipedia')
zhsite.login()


def importSitelinks(title):
    print(title)

    myitem = pywikibot.ItemPage(datasite, title)
    mysitelinks = myitem.get()['sitelinks']
    if 'wikidatawiki' in mysitelinks and 'zhwiki' not in mysitelinks:
        wditem = pywikibot.ItemPage(wdsite, mysitelinks['wikidatawiki'])
        wdsitelinks = wditem.get()['sitelinks']
        data = {
            'sitelinks': []
        }
        for sitelink in wdsitelinks:
            data['sitelinks'].append({
                'site': sitelink,
                'title': wdsitelinks[sitelink]
            })
        summary = '匯入網站連結，來自[[wikidata:{}]]'.format(mysitelinks['wikidatawiki'])
        print(data)
        print(summary)
        myitem.editEntity(data, summary=summary)
    if 'zhwiki' in mysitelinks and 'wikidatawiki' not in mysitelinks:
        zhpage = pywikibot.Page(zhsite, mysitelinks['zhwiki'])
        wditem = zhpage.data_item()
        wdsitelinks = wditem.get()['sitelinks']
        data = {
            'sitelinks': [
                {'site': 'wikidatawiki', 'title': wditem.title()}
            ]
        }
        for sitelink in wdsitelinks:
            data['sitelinks'].append({
                'site': sitelink,
                'title': wdsitelinks[sitelink]
            })
        summary = '匯入網站連結，來自[[wikidata:{}]]'.format(wditem.title())
        print(data)
        print(summary)
        myitem.editEntity(data, summary=summary)


def main():
    animeitem = pywikibot.ItemPage(datasite, 'Q53')

    for backlink in animeitem.backlinks():
        importSitelinks(backlink.title())


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('title', nargs='?')
    args = parser.parse_args()
    if args.title is None:
        main()
    else:
        importSitelinks(args.title)
