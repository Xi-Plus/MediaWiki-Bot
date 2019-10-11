import argparse
import logging
import re

import requests

import pywikibot
from bs4 import BeautifulSoup


class AcgGamerComTwAcgDetail:
    RATING_IMG = {
        'ALL': 0,
        '6TO12': 6,
        '12TO18': 12,
        '15TO18': 15,
        '18UP': 18,
    }
    RATING_ITEM = {
        0: 'Q46',
        6: 'Q47',
        12: 'Q48',
        15: 'Q49',
        18: 'Q50',
    }

    def getData(self, url):
        text = requests.get(url).text
        soup = BeautifulSoup(text, 'html.parser')
        data = {}

        box1listA = soup.find('ul', {'class': 'ACG-box1listA'})
        episodes = re.search(r'播出集數：(\d+)', box1listA.text)
        if episodes:
            data['episodes'] = int(episodes.group(1))

        box1mark = soup.find('p', {'id': 'ACG-box1mark'})

        for img in box1mark.findAll('img'):
            m = re.search(r'TW-(.+?)\.gif', img.get('src'))
            if m:
                data['rating'] = self.RATING_IMG[m.group(1)]
                break

        return data

    def updateItem(self, datasite, item):
        itemlabel = item.get()['labels']['zh-tw']
        logging.info('%s %s', item.id, itemlabel)

        claims = item.get()['claims']

        if 'P1' not in claims:
            logging.error('No acg gamer claims')
            return

        url = claims['P1'][0].getTarget()
        data = self.getData(url)

        # 台灣分級
        if 'rating' in data:
            if 'P23' in claims:
                if claims['P23'][0].getTarget().id != self.RATING_ITEM[data['rating']]:
                    logging.info('\t Update rating to %s', data['rating'])
                    ratingValue = pywikibot.ItemPage(datasite, self.RATING_ITEM[data['rating']])
                    claims['P23'][0].changeTarget(ratingValue, summary='更新台灣分級')
            else:
                new_claim = pywikibot.page.Claim(datasite, 'P23')
                new_claim.setTarget(pywikibot.ItemPage(datasite, self.RATING_ITEM[data['rating']]))
                logging.info('\t Add new rating %s', data['rating'])
                item.addClaim(new_claim, summary='新增台灣分級')


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('url')
    args = parser.parse_args()
    print(AcgGamerComTwAcgDetail().getData(args.url))
