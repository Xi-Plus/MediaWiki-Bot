import argparse
import re
import requests
from bs4 import BeautifulSoup


class AcgGamerComTwAcgDetail:
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


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('url')
    args = parser.parse_args()
    print(AcgGamerComTwAcgDetail().getData(args.url))
