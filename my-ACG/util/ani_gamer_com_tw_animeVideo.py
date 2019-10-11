import argparse
import logging
import re

import requests

import pywikibot
from bs4 import BeautifulSoup


class AniGamerComTwAnimeVideo:
    RATING_IMG = {
        'ALL': 0,
        '6TO12': 6,
        '12TO18': 12,
        '15TO18': 15,
        '18UP': 18,
    }

    def getData(self, url):
        text = requests.get(url).text
        data = {}

        if '目前無此動畫或動畫授權已到期！' in text:
            data['removed'] = True
            return data

        soup = BeautifulSoup(text, 'html.parser')

        season = soup.find('section', {'class': 'season'})
        if season is None:
            data['episodes'] = 1
        else:
            data['episodes'] = len(season.find('ul').findAll('li'))

        rating = soup.find('div', {'class': 'rating'})
        if rating:
            src = rating.find('img').get('src')
            m = re.search(r'TW-(.+?)\.gif', src)
            if m:
                data['rating'] = self.RATING_IMG[m.group(1)]

        data_intro = soup.find('div', {'class': 'data_intro'})
        if data_intro:
            linkdiv = data_intro.find('div', {'class': 'link'})
            if linkdiv:
                for link in linkdiv.findAll('a'):
                    if link.text == '作品資料':
                        data['acg_link'] = link.get('href')
                        if data['acg_link'].startswith('//'):
                            data['acg_link'] = 'https:' + data['acg_link']

        return data

    def updateItem(self, datasite, item):
        itemlabel = item.get()['labels']['zh-tw']
        logging.info('%s %s', item.id, itemlabel)

        claims = item.get()['claims']

        if 'P34' not in claims:
            logging.error('No anime gamer claims')
            return

        url = claims['P34'][0].getTarget()
        data = self.getData(url)

        # 從巴哈姆特動畫瘋匯入巴哈姆特作品資料
        if 'acg_link' in data and 'P1' not in claims:
            new_claim = pywikibot.page.Claim(datasite, 'P1')
            new_claim.setTarget(data['acg_link'])
            logging.info('\tAdd acg gamer link %s', data['acg_link'])
            item.addClaim(new_claim)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('url')
    args = parser.parse_args()
    print(AniGamerComTwAnimeVideo().getData(args.url))
