# -*- coding: utf-8 -*-
import argparse
import importlib
import os
import sys

os.environ['PYWIKIBOT_DIR'] = os.path.dirname(os.path.realpath(__file__))
import pywikibot


sys.path.append('..')
animeSite = (importlib.import_module('util.ani_gamer_com_tw_animeVideo', 'AniGamerComTwAnimeVideo')
             .AniGamerComTwAnimeVideo())

site = pywikibot.Site()
site.login()
datasite = site.data_repository()


def importAcgGamerLink(title):
    myitem = pywikibot.ItemPage(datasite, title)

    print(title, myitem.get()['labels']['zh-tw'])

    claims = myitem.get()['claims']
    if 'P34' in claims:
        if 'P1' not in claims:
            claim = claims['P34'][0]
            url = claim.getTarget()
            data = animeSite.getData(url)

            print('\t url', url)

            if 'acg_link' in data:
                new_claim = pywikibot.page.Claim(datasite, 'P1')
                new_claim.setTarget(data['acg_link'])
                print('\t Add acg gamer link {}'.format(data['acg_link']))
                myitem.addClaim(new_claim)
    else:
        print('\t Not gamer')


def main():
    for backlink in pywikibot.PropertyPage(datasite, 'P34').backlinks(namespaces=[120]):  # 巴哈姆特動畫瘋
        myitem = pywikibot.ItemPage(datasite, backlink.title())
        claims = myitem.get()['claims']
        if 'P1' not in claims:
            importAcgGamerLink(backlink.title())


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('title', nargs='?')
    args = parser.parse_args()
    if args.title is None:
        main()
    else:
        importAcgGamerLink(args.title)
