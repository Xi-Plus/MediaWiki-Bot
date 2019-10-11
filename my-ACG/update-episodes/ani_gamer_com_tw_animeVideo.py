# -*- coding: utf-8 -*-
import argparse
import importlib
import os
import sys

os.environ['PYWIKIBOT_DIR'] = os.path.dirname(os.path.realpath(__file__))
import pywikibot


sys.path.append('..')
animeSite = (importlib.import_module('util.ani_gamer_com_tw_animeVideo', 'AniGamerComTwAnimeVideo')
             .AniGamerComTwAnimeVideo())

site = pywikibot.Site()
site.login()
datasite = site.data_repository()


def updateEpisodes(title):
    myitem = pywikibot.ItemPage(datasite, title)

    print(title, myitem.get()['labels']['zh-tw'])

    claims = myitem.get()['claims']
    if 'P34' in claims:
        claim = claims['P34'][0]
        url = claim.getTarget()
        data = animeSite.getData(url)

        new_episodes = data['episodes']

        print('\t url', url)
        print('\t new_episodes', new_episodes)
        if 'P27' in claims:
            episodesValue = claims['P27'][0].getTarget()
            old_episodes = episodesValue.amount
            print('\t old_episodes', old_episodes)
            if new_episodes > old_episodes:
                episodesValue.amount = new_episodes
                print('\t Update episodes from {} to {}'.format(old_episodes, new_episodes))
                claims['P27'][0].changeTarget(episodesValue, summary='更新總集數')
            else:
                print('\t Not update')

            # 播放狀態
            if 'P31' in claims and claims['P31'][0].getTarget().id == 'Q57':
                print('\t Update status to playing')
                statusValue = pywikibot.ItemPage(datasite, 'Q56')
                claims['P31'][0].changeTarget(statusValue, summary='更新播放狀態')
        else:
            new_claim = pywikibot.page.Claim(datasite, 'P27')
            new_claim.setTarget(pywikibot.WbQuantity(new_episodes, site=datasite))
            print('\t Add new episodes {}'.format(new_episodes))
            myitem.addClaim(new_claim, summary='新增總集數')
    else:
        print('\t Not gamer')


def main():
    for backlink in pywikibot.ItemPage(datasite, 'Q56').backlinks(namespaces=[120]):  # 放送中
        updateEpisodes(backlink.title())
    for backlink in pywikibot.ItemPage(datasite, 'Q57').backlinks(namespaces=[120]):  # 尚未放送
        updateEpisodes(backlink.title())


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('title', nargs='?')
    args = parser.parse_args()
    if args.title is None:
        main()
    else:
        updateEpisodes(args.title)
