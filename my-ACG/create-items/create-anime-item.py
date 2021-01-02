# -*- coding: utf-8 -*-
import argparse
import importlib
import json
import os
import sys

os.environ['PYWIKIBOT_DIR'] = os.path.dirname(os.path.realpath(__file__))
import pywikibot
from pywikibot.data.api import Request


sys.path.append('..')
animeSite = (importlib.import_module('util.acg_gamer_com_tw_acgDetail', 'AcgGamerComTwAcgDetail')
             .AcgGamerComTwAcgDetail())

site = pywikibot.Site()
site.login()
datasite = site.data_repository()
zhsite = pywikibot.Site('zh', 'wikipedia')
moesite = pywikibot.Site('zh', 'moegirl')

STATUS_QID = ['Q57', 'Q56', 'Q58']


def converttitle(site, title):
    r = Request(site=site, parameters={
        'action': 'query',
        'titles': title,
        'redirects': 1,
        'converttitles': 1
    })
    data = r.submit()
    if 'pages' not in data['query']:
        return None
    page = list(data['query']['pages'].values())[0]
    if 'missing' in page:
        return None
    return page['title'].replace(' ', '_')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('title')
    parser.add_argument('--year')
    parser.add_argument('--seen', type=int, default=1)
    parser.add_argument('--episodes', type=int, default=1)
    parser.add_argument('--status', type=int, choices=[0, 1, 2], default=1)
    parser.add_argument('--length', type=float, default=24)
    parser.add_argument('--wp')
    parser.add_argument('--moe')
    parser.add_argument('--gamer')
    args = parser.parse_args()

    title = args.title
    year = args.year
    seen = args.seen
    episodes = args.episodes
    status = args.status
    length = args.length
    if length == int(length):
        length = int(length)
    gamer = args.gamer

    zhtitle = converttitle(zhsite, args.wp or title)
    moetitle = converttitle(moesite, args.moe or args.wp or title)

    print('title', title)
    print('year', year)
    print('episodes', seen, episodes)
    print('status', status)
    print('length', length)
    print('zhtitle', zhtitle)
    print('moetitle', moetitle)
    print('gamer', gamer)

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
    new_claim.setTarget(pywikibot.WbQuantity(seen, site=datasite))
    data['claims'].append(new_claim.toJSON())

    # 總集數
    new_claim = pywikibot.page.Claim(datasite, 'P27')
    new_claim.setTarget(pywikibot.WbQuantity(episodes, site=datasite))
    data['claims'].append(new_claim.toJSON())

    # 播放狀態
    new_claim = pywikibot.page.Claim(datasite, 'P31')
    new_claim.setTarget(pywikibot.ItemPage(datasite, STATUS_QID[status]))  # 已完結
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

    # 長度
    if length > 0:
        new_claim = pywikibot.page.Claim(datasite, 'P25')
        new_claim.setTarget(pywikibot.WbQuantity(length, site=datasite, unit='https://xiplus.ddns.net/entity/Q54'))
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

    # 巴哈姆特作品資料
    if gamer:
        new_claim = pywikibot.page.Claim(datasite, 'P1')
        new_claim.setTarget(gamer)
        data['claims'].append(new_claim.toJSON())

    print(json.dumps(data['labels'], indent=4, ensure_ascii=False))
    for claim in data['claims']:
        print(claim['mainsnak']['property'],
              claim['mainsnak']['datatype'],
              claim['mainsnak']['datavalue'])

    input('Create?')

    item = datasite.editEntity({}, data, summary=u'建立新動畫')
    print(item['entity']['id'])

    # 巴哈姆特作品資料
    if gamer:
        myitem = pywikibot.ItemPage(datasite, item['entity']['id'])
        animeSite.updateItem(datasite, myitem)


if __name__ == "__main__":
    main()
