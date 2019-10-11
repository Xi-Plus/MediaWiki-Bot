# -*- coding: utf-8 -*-
import argparse
import importlib
import logging
import os
import sys

os.environ['PYWIKIBOT_DIR'] = os.path.dirname(os.path.realpath(__file__))
import pywikibot


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)-8s %(message)s',
)

sys.path.append('..')
animeSite = (importlib.import_module('util.ani_gamer_com_tw_animeVideo', 'AniGamerComTwAnimeVideo')
             .AniGamerComTwAnimeVideo())

site = pywikibot.Site()
site.login()
datasite = site.data_repository()


def importAcgGamerLink(title):
    myitem = pywikibot.ItemPage(datasite, title)

    animeSite.updateItem(datasite, myitem)


def main():
    for backlink in pywikibot.PropertyPage(datasite, 'P34').backlinks(namespaces=[120]):  # 巴哈姆特動畫瘋
        myitem = pywikibot.ItemPage(datasite, backlink.title())
        claims = myitem.get()['claims']
        if 'P23' not in claims:
            importAcgGamerLink(backlink.title())


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('title', nargs='?')
    args = parser.parse_args()
    if args.title is None:
        main()
    else:
        importAcgGamerLink(args.title)
