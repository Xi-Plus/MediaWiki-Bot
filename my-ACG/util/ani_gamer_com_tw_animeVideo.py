import requests
from bs4 import BeautifulSoup


class AniGamerComTwAnimeVideo:
    def getData(self, url):
        text = requests.get(url).text
        soup = BeautifulSoup(text, 'html.parser')
        data = {}

        season = soup.find('section', {'class': 'season'})
        if season is None:
            data['episodes'] = 1
        else:
            data['episodes'] = len(season.find('ul').findAll('li'))

        return data
