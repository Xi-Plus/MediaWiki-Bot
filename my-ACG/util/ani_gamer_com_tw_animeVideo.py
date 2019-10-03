import argparse
import re
import requests
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
        soup = BeautifulSoup(text, 'html.parser')
        data = {}

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

        return data


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('url')
    args = parser.parse_args()
    print(AniGamerComTwAnimeVideo().getData(args.url))
