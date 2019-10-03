# -*- coding: utf-8 -*-
import argparse
import importlib
import os
import sys

os.environ['PYWIKIBOT_DIR'] = os.path.dirname(os.path.realpath(__file__))
import pywikibot


sys.path.append('..')
animeSite = importlib.import_module('util.anime1_me', 'Anime1Me').Anime1Me()

site = pywikibot.Site()
site.login()
datasite = site.data_repository()


def updateEpisodes(title):
    myitem = pywikibot.ItemPage(datasite, title)

    print(title, myitem.get()['labels']['zh-tw'])

    claims = myitem.get()['claims']
    if 'P38' in claims:
        claim = claims['P38'][0]
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

            if 'P31' in claims and claims['P31'][0].getTarget().id == 'Q57':
                print('\t Update status to playing')
                statusValue = pywikibot.ItemPage(datasite, 'Q56')
                claims['P31'][0].changeTarget(statusValue, summary='更新播放狀態')
        else:
            new_claim = pywikibot.page.Claim(datasite, 'P27')
            new_claim.setTarget(pywikibot.WbQuantity(new_episodes, site=datasite))
            print('\t Add new episodes {}'.format(new_episodes))
            myitem.addClaim(new_claim, summary='新增總集數')

        if 'P31' in claims:
            if data['end']:
                print('\t Update status to end')
                statusValue = pywikibot.ItemPage(datasite, 'Q58')
                claims['P31'][0].changeTarget(statusValue, summary='更新播放狀態')
    else:
        print('\t Not anime1')


def main():
    moegirlitem = pywikibot.ItemPage(datasite, 'Q56')

    for backlink in moegirlitem.backlinks(namespaces=[120]):
        updateEpisodes(backlink.title())


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('title', nargs='?')
    args = parser.parse_args()
    if args.title is None:
        main()
    else:
        updateEpisodes(args.title)
