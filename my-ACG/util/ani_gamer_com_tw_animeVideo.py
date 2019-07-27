import requests
from bs4 import BeautifulSoup


class AniGamerComTwAnimeVideo:
    def getData(self, url):
        text = requests.get(url).text
        soup = BeautifulSoup(text, 'html.parser')
        data = {}

        data['episodes'] = len(soup.find('section', {'class': 'season'}).find('ul').findAll('li'))

        return data
