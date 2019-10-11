# -*- coding: utf-8 -*-
import argparse
import importlib
import os
import sys

os.environ['PYWIKIBOT_DIR'] = os.path.dirname(os.path.realpath(__file__))
import pywikibot


sys.path.append('..')
animeSite = (importlib.import_module('util.acg_gamer_com_tw_acgDetail', 'AcgGamerComTwAcgDetail')
             .AcgGamerComTwAcgDetail())

site = pywikibot.Site()
site.login()
datasite = site.data_repository()

RATING_ITEM = {
    0: 'Q46',
    6: 'Q47',
    12: 'Q48',
    15: 'Q49',
    18: 'Q50',
}


def updateEpisodes(title):
    myitem = pywikibot.ItemPage(datasite, title)

    print(title, myitem.get()['labels']['zh-tw'])

    claims = myitem.get()['claims']
    if 'P1' in claims:
        claim = claims['P1'][0]
        url = claim.getTarget()
        data = animeSite.getData(url)

        print('\t url', url)
        # 台灣分級
        if 'rating' in data:
            if 'P23' in claims:
                if claims['P23'][0].getTarget().id != RATING_ITEM[data['rating']]:
                    print('\t Update rating to {}'.format(data['rating']))
                    ratingValue = pywikibot.ItemPage(datasite, RATING_ITEM[data['rating']])
                    claims['P23'][0].changeTarget(ratingValue, summary='更新台灣分級')
            else:
                new_claim = pywikibot.page.Claim(datasite, 'P23')
                new_claim.setTarget(pywikibot.ItemPage(datasite, RATING_ITEM[data['rating']]))
                print('\t Add new rating {}'.format(data['rating']))
                myitem.addClaim(new_claim, summary='新增台灣分級')
    else:
        print('\t Not gamer')


def main():
    for backlink in pywikibot.PropertyPage(datasite, 'P1').backlinks(namespaces=[120]):  # 巴哈作品資料
        myitem = pywikibot.ItemPage(datasite, backlink.title())
        claims = myitem.get()['claims']
        if 'P23' not in claims:
            updateEpisodes(backlink.title())


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('title', nargs='?')
    args = parser.parse_args()
    if args.title is None:
        main()
    else:
        updateEpisodes(args.title)
