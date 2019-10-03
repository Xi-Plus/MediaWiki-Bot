import re

import requests
from bs4 import BeautifulSoup


class Anime1Me:
    def getData(self, url):
        data = {
            'episodes': 0,
            'end': False,
        }
        text = requests.get(url).text
        soup = BeautifulSoup(text, 'html.parser')
        title = soup.find('h1', {'class': 'page-title'}).text

        # print('title', title)
        text = requests.get('https://anime1.me').text
        m = re.search(r'>{}</a></td><td class=\"column-2\">(.+?)</td>'.format(re.escape(title)), text)
        if m:
            episodes = m.group(1)
            data['episodes'], data['end'] = self._parse_episodes(episodes)
        else:
            # print('Not match')
            pass

        return data

    def _parse_episodes(self, episodes):
        if episodes == '劇場版':
            return 1, True

        m = re.match(r'^連載中\((\d+)\)$', episodes)
        if m:
            return int(m.group(1)), False

        m = re.match(r'^1-(\d+)$', episodes)
        if m:
            return int(m.group(1)), True

        m = re.match(r'^1-(\d+)\+(\d+)$', episodes)
        if m:
            if int(m.group(1)) + 1 == int(m.group(2)):
                return int(m.group(2)), True

        raise Exception('Unknwon episodes format: {}'.format(episodes))
