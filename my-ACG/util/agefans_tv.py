import argparse
import logging
import re

import pywikibot
import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent


class AgefansTv:
    def __init__(self):
        self.ua = UserAgent()

    def getData(self, url):
        headers = {'User-Agent': self.ua.random}
        text = requests.get(url, headers=headers).text
        soup = BeautifulSoup(text, 'html.parser')
        data = {}

        movurl = soup.find('div', {'class': 'movurl', 'style': 'display:block'})
        data['episodes'] = len(movurl.findAll('li'))

        return data

    def updateItem(self, datasite, item):
        itemlabel = item.get()['labels']['zh-tw']
        logging.info('%s %s', item.id, itemlabel)

        claims = item.get()['claims']

        if 'P76' not in claims:
            logging.error('\t No age claims')
            return

        url = claims['P76'][0].getTarget()
        data = self.getData(url)

        # 總集數
        if 'episodes' in data:
            new_episodes = data['episodes']
            if 'P27' in claims:
                episodesValue = claims['P27'][0].getTarget()
                old_episodes = episodesValue.amount
                if new_episodes > old_episodes:
                    episodesValue.amount = new_episodes
                    logging.info('\t Update episodes from %s to %s', old_episodes, new_episodes)
                    claims['P27'][0].changeTarget(episodesValue, summary='更新總集數')
            else:
                new_claim = pywikibot.page.Claim(datasite, 'P27')
                new_claim.setTarget(pywikibot.WbQuantity(new_episodes, site=datasite))
                logging.info('\t Add new episodes %s', new_episodes)
                item.addClaim(new_claim, summary='新增總集數')

        # 播放狀態
        if 'P31' in claims and claims['P31'][0].getTarget().id == 'Q57':
            logging.info('\t Update status to playing')
            statusValue = pywikibot.ItemPage(datasite, 'Q56')
            claims['P31'][0].changeTarget(statusValue, summary='更新播放狀態')


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('url')
    args = parser.parse_args()
    print(AgefansTv().getData(args.url))
