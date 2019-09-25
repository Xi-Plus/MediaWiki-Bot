# -*- coding: utf-8 -*-
import argparse
import json
import os

os.environ['PYWIKIBOT_DIR'] = os.path.dirname(os.path.realpath(__file__))
import pywikibot
from pywikibot.data.api import Request


site = pywikibot.Site()
site.login()
datasite = site.data_repository()
zhsite = pywikibot.Site('zh', 'wikipedia')
moesite = pywikibot.Site('moegirl', 'moegirl')


def converttitle(site, title):
    r = Request(site=site, parameters={
        'action': 'query',
        'titles': title,
        'redirects': 1,
        'converttitles': 1
    })
    data = r.submit()
    page = list(data['query']['pages'].values())[0]
    if 'missing' in page:
        return None
    return page['title'].replace(' ', '_')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('title')
    parser.add_argument('--year')
    parser.add_argument('--episodes', type=int, default=12)
    parser.add_argument('--wp')
    parser.add_argument('--moe')
    args = parser.parse_args()

    title = args.title
    year = args.year
    episodes = args.episodes

    zhtitle = converttitle(zhsite, args.wp or title)
    moetitle = converttitle(moesite, args.moe or title)

    print('title', title)
    print('year', year)
    print('episodes', episodes)
    print('zhtitle', zhtitle)
    print('moetitle', moetitle)

    new_item = pywikibot.ItemPage(datasite)
    print(new_item)

    data = {
        'labels': {},
        'claims': [],
    }

    data['labels']['zh-tw'] = {
        'language': 'zh-tw',
        'value': title
    }

    # 性質
    new_claim = pywikibot.page.Claim(datasite, 'P3')
    new_claim.setTarget(pywikibot.ItemPage(datasite, 'Q53'))  # 動畫
    data['claims'].append(new_claim.toJSON())

    # 已看集數
    new_claim = pywikibot.page.Claim(datasite, 'P28')
    new_claim.setTarget(pywikibot.WbQuantity(0, site=datasite))
    data['claims'].append(new_claim.toJSON())

    # 總集數
    new_claim = pywikibot.page.Claim(datasite, 'P27')
    new_claim.setTarget(pywikibot.WbQuantity(episodes, site=datasite))
    data['claims'].append(new_claim.toJSON())

    # 播放狀態
    new_claim = pywikibot.page.Claim(datasite, 'P31')
    new_claim.setTarget(pywikibot.ItemPage(datasite, 'Q58'))  # 已完結
    data['claims'].append(new_claim.toJSON())

    # 年份
    if year:
        if len(year) == 4:
            wbtime = pywikibot.WbTime(year=int(year), calendarmodel='http://www.wikidata.org/entity/Q1985727')
        elif len(year) == 6:
            wbtime = pywikibot.WbTime(year=int(year[0:4]), month=int(year[4:6]), calendarmodel='http://www.wikidata.org/entity/Q1985727')
        elif len(year) == 8:
            wbtime = pywikibot.WbTime(year=int(year[0:4]), month=int(year[4:6]), day=int(year[6:8]), calendarmodel='http://www.wikidata.org/entity/Q1985727')
        else:
            raise Exception('unknown year {}'.format(year))

        new_claim = pywikibot.page.Claim(datasite, 'P29')
        new_claim.setTarget(wbtime)
        data['claims'].append(new_claim.toJSON())

    # 中文維基百科
    if zhtitle:
        new_claim = pywikibot.page.Claim(datasite, 'P68')
        new_claim.setTarget(zhtitle)
        data['claims'].append(new_claim.toJSON())

    # 萌娘百科
    if moetitle:
        new_claim = pywikibot.page.Claim(datasite, 'P70')
        new_claim.setTarget(moetitle)
        data['claims'].append(new_claim.toJSON())

    print(json.dumps(data['labels'], indent=4, ensure_ascii=False))
    for claim in data['claims']:
        print(claim['mainsnak']['property'],
              claim['mainsnak']['datatype'],
              claim['mainsnak']['datavalue'])

    input('Create?')

    item = datasite.editEntity({}, data, summary=u'建立新動畫')
    print(item['entity']['id'])


if __name__ == "__main__":
    main()
