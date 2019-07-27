# -*- coding: utf-8 -*-
import argparse
import csv
import os
import re
import urllib.parse

os.environ['PYWIKIBOT_DIR'] = os.path.dirname(os.path.realpath(__file__))
import pywikibot


site = pywikibot.Site()
site.login()
datasite = site.data_repository()


def main(studio):
    data = {
        'labels': {
            'zh-tw': {
                'language': 'zh-tw',
                'value': studio
            },
        },
        'sitelinks': {
            'zhwiki': {
                'site': 'zhwiki',
                'title': studio,
                'badges': [],
            },
        },
        # https://www.mediawiki.org/wiki/Wikibase/DataModel/JSON#Snaks
        'claims': {
            'P3': [{
                'mainsnak': {
                    'snaktype': 'value',
                    'property': 'P3',
                    'datatype': 'wikibase-item',
                    'datavalue': {
                        'value': {
                            'entity-type': 'item',
                            'numeric-id': 65,
                        },
                        'type': 'wikibase-entityid',
                    },
                },
                'type': 'statement',
                'rank': 'normal',
            }],
        },
    }

    # claim = pywikibot.page.Claim(datasite, 'P25', datatype='wikibase-item')
    # item.editEntity({'claims': [claim.toJSON()]})

    print(data)
    item = datasite.editEntity({}, data, summary=u'建立新項目並連結')
    print(item['entity']['id'])


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('studio')
    args = parser.parse_args()
    main(args.studio)
