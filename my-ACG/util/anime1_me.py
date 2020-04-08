import argparse
import html
import logging
import re
from functools import lru_cache

import pywikibot
import requests
from bs4 import BeautifulSoup


class Anime1Me:
    def getData(self, url):
        data = {
            'episodes': 0,
            'end': False,
        }
        text = self._request(url)
        soup = BeautifulSoup(text, 'html.parser')
        titleel = soup.find('h1', {'class': 'page-title'})
        if titleel is None:
            print('cannot find title')
            return None
        title = titleel.text

        # print('title', title)
        text = self._request('https://anime1.me')
        text = html.unescape(text)
        m = re.search(r'>{}</a></td><td class=\"column-2\">(.+?)</td>'.format(re.escape(title)), text)
        if m:
            episodes = m.group(1)
            data['episodes'], data['end'] = self._parse_episodes(episodes)
        else:
            # print('Not match')
            pass

        return data

    @lru_cache(maxsize=32)
    def _request(self, url):
        return requests.get(url).text

    def _parse_episodes(self, episodes):
        if episodes == '劇場版':
            return 1, True

        m = re.match(r'^連載中\((\d+)(?:正式版|AT-X|AT-X無修)?\)$', episodes)
        if m:
            return int(m.group(1)), False

        m = re.match(r'^連載中\((\d+)\.5\)$', episodes)
        if m:
            return int(m.group(1)) + 1, False

        m = re.match(r'^連載中\((\d+)/\d+\)$', episodes)
        if m:
            return int(m.group(1)), False

        m = re.match(r'^1-(\d+)$', episodes)
        if m:
            return int(m.group(1)), True

        m = re.match(r'^1-(\d+)\+SP$', episodes)
        if m:
            return int(m.group(1)) + 1, True

        m = re.match(r'^1-(\d+)\+OVA1$', episodes)
        if m:
            return int(m.group(1)) + 1, True

        m = re.match(r'^1-(\d+)\+(\d+)(\(全集BD\))?$', episodes)
        if m:
            if int(m.group(1)) + 1 == int(m.group(2)):
                return int(m.group(2)), True

        raise Exception('Unknwon episodes format: {}'.format(episodes))

    def updateItem(self, datasite, item):
        itemlabel = item.get()['labels']['zh-tw']
        logging.info('%s %s', item.id, itemlabel)

        claims = item.get()['claims']

        if 'P38' not in claims:
            logging.error('\t No anime1 claims')
            return

        url = claims['P38'][0].getTarget()
        data = self.getData(url)

        if data is None:
            return

        # 總集數
        if 'episodes' in data:
            new_episodes = data['episodes']
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
        if 'P31' in claims:
            if data['end']:
                if claims['P31'][0].getTarget().id != 'Q58':
                    logging.info('\t Update status to end')
                    statusValue = pywikibot.ItemPage(datasite, 'Q58')  # 已完結
                    claims['P31'][0].changeTarget(statusValue, summary='更新播放狀態')
            elif claims['P31'][0].getTarget().id == 'Q57':
                logging.info('\t Update status to playing')
                statusValue = pywikibot.ItemPage(datasite, 'Q56')  # 放送中
                claims['P31'][0].changeTarget(statusValue, summary='更新播放狀態')
        else:
            itemid = 'Q56'
            if data['end']:
                itemid = 'Q58'
            new_claim = pywikibot.page.Claim(datasite, 'P31')
            new_claim.setTarget(pywikibot.ItemPage(datasite, itemid))
            logging.info('\t Add new status')
            item.addClaim(new_claim, summary='新增播放狀態')


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('url')
    args = parser.parse_args()
    logging.info(Anime1Me().getData(args.url))
