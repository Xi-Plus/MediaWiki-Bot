# -*- coding: utf-8 -*-
import argparse
import re
import os

os.environ['PYWIKIBOT_DIR'] = os.path.dirname(os.path.realpath(__file__))
import pywikibot


site = pywikibot.Site()
site.login()
datasite = site.data_repository()


def fixUrl(title):
    print(title)

    myitem = pywikibot.ItemPage(datasite, title)
    claims = myitem.get()['claims']['P66']

    toRemove = []
    for claim in claims:
        if not re.search(r'^https?://zh.moegirl.org', claim.getTarget()):
            toRemove.append(claim)

    print('toRemove', toRemove)
    if not toRemove:
        return

    myitem.removeClaims(toRemove, summary='移除錯誤放置的連結')


def main():
    moegirlitem = pywikibot.PropertyPage(datasite, 'Property:P66')

    for backlink in moegirlitem.backlinks():
        fixUrl(backlink.title())


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('title', nargs='?')
    args = parser.parse_args()
    if args.title is None:
        main()
    else:
        fixUrl(args.title)
