# -*- coding: utf-8 -*-
import argparse
import os

os.environ['PYWIKIBOT_DIR'] = os.path.dirname(os.path.realpath(__file__))
import pywikibot


site = pywikibot.Site()
site.login()
datasite = site.data_repository()


def removeProperty(property_id, title):
    print(title)

    myitem = pywikibot.ItemPage(datasite, title)
    claims = myitem.get()['claims'][property_id]

    print(claims)

    myitem.removeClaims(claims)


def main(property_id):
    moegirlitem = pywikibot.PropertyPage(datasite, 'Property:{}'.format(property_id))

    for backlink in moegirlitem.backlinks():
        removeProperty(property_id, backlink.title())


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('property')
    parser.add_argument('title', nargs='?')
    args = parser.parse_args()
    if args.title is None:
        main(args.property)
    else:
        removeProperty(args.property, args.title)
