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
animeSite = (importlib.import_module('util.agefans_tv', 'AgefansTv')
             .AgefansTv())

site = pywikibot.Site()
site.login()
datasite = site.data_repository()


def updateEpisodes(title):
    myitem = pywikibot.ItemPage(datasite, title)

    animeSite.updateItem(datasite, myitem)


def main():
    for backlink in pywikibot.ItemPage(datasite, 'Q56').backlinks(namespaces=[120]):  # 放送中
        updateEpisodes(backlink.title())
    for backlink in pywikibot.ItemPage(datasite, 'Q57').backlinks(namespaces=[120]):  # 尚未放送
        updateEpisodes(backlink.title())


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('title', nargs='?')
    args = parser.parse_args()
    if args.title is None:
        main()
    else:
        updateEpisodes(args.title)
