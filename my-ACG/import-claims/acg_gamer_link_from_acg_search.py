# -*- coding: utf-8 -*-
import argparse
import logging
import os

import requests

os.environ['PYWIKIBOT_DIR'] = os.path.dirname(os.path.realpath(__file__))
import pywikibot
from bs4 import BeautifulSoup


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)-8s %(message)s',
)

site = pywikibot.Site()
site.login()
datasite = site.data_repository()


def main(title):
    pywikibot.ItemPage(datasite, title)
    item = pywikibot.ItemPage(datasite, title)
    itemlabel = item.get()['labels']['zh-tw']
    logging.info('%s %s', item.id, itemlabel)

    claims = item.get()['claims']

    if 'P1' in claims:
        logging.error('\t acg gamer link exists')
        return

    url = 'https://acg.gamer.com.tw/search.php?kw={}&s=1'.format(itemlabel)
    text = requests.get(url).text
    soup = BeautifulSoup(text, 'html.parser')
    for result in soup.findAll('p', {'class': 'search_title'}):
        if '[ 動畫 ]' in result.text:
            link = result.find('a')
            if link:
                url = link.get('href')

                if url.startswith('//'):
                    url = 'https:' + url

                if url.startswith('https://acg.gamer.com.tw/acgDetail.php?s='):
                    new_claim = pywikibot.page.Claim(datasite, 'P1')
                    new_claim.setTarget(url)
                    logging.info('\t Add acg gamer link %s', url)
                    item.addClaim(new_claim, summary='匯入連結')
                break


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('title')
    args = parser.parse_args()

    main(args.title)
