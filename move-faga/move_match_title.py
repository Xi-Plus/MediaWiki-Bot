# -*- coding: utf-8 -*-
import argparse
import os
import re

os.environ['PYWIKIBOT_DIR'] = os.path.dirname(os.path.realpath(__file__))
import pywikibot
from pywikibot.data.api import Request

from config import purge  # pylint: disable=E0611,W0614


def converttitle(title):
    r = Request(site=site, parameters={
        'action': 'query',
        'titles': title,
        'redirects': 1,
        'converttitles': 1
    })
    data = r.submit()
    return list(data['query']['pages'].values())[0]['title']


os.environ['TZ'] = 'UTC'

parser = argparse.ArgumentParser()
parser.add_argument('--limit', type=int, default=0)
parser.add_argument('--limit2', type=int, default=0)
args = parser.parse_args()

site = pywikibot.Site()
site.login()

summary = '[[Special:PermaLink/53078964#優良條目和典范条目子頁面繁簡皆有的問題|統一子頁面繁簡]]、配合條目繁簡'

runpages = ''
with open('list.txt', 'r') as f:
    runpages = f.read().split('\n')

cnt = 1
cnt2 = 1
for gatitle in runpages:

    gapage = pywikibot.Page(site, gatitle)

    print('ga =', gapage)

    if not gapage.exists():
        print('not exists')
        continue

    gatext = gapage.text

    m = re.search(r"'''《?\[\[(.+?)(\|.+?)?]]》?'''", gapage.text)
    if not m:
        print('cannot find title')
        continue

    articletitle = m.group(1)
    articletitle = converttitle(articletitle)
    print('article =', articletitle)

    realgatitle = 'Wikipedia:典范条目/{0}'.format(articletitle)

    if gatitle == realgatitle:
        print('no need to move')
        continue

    targetPage = pywikibot.Page(site, realgatitle)
    if targetPage.exists():
        print('{} {} Deleting {}'.format(cnt, cnt2, realgatitle))
        print('-' * 50)
        print(targetPage.text)
        print('-' * 50)
        if not targetPage.isRedirectPage():
            input('delete?')
        targetPage.delete(reason='[[Wiktionary:CSD|G8]]: 刪除以便移動', prompt=False)
        cnt2 += 1

    print('{} {} Moving {} to {} ({})'.format(
        cnt, cnt2, gapage.title(), realgatitle, summary))
    try:
        gapage.move(realgatitle, reason=summary,
                    movetalk=True, noredirect=True)
    except pywikibot.exceptions.ArticleExistsConflict as e:
        print('{} target exist'.format(realgatitle))
        continue

    cnt2 += 1

    toPurgePages = []
    allbacklinks = list(set(
        list(gapage.embeddedin())
        + list(gapage.backlinks(follow_redirects=True, filter_redirects=True))
    ))
    print('embeddedin', list(gapage.embeddedin()))
    print('backlinks', list(gapage.backlinks(
        follow_redirects=True, filter_redirects=True)))
    for backlink in allbacklinks:
        print('backlink: {}'.format(backlink.title()))
        if re.search(r'^Wikipedia:典范条目/\d+年\d+月\d+日$|^Portal:', backlink.title()):
            print('{} {} Editing {}'.format(cnt, cnt2, backlink.title()))
            text = backlink.text
            if re.search(r'Wikipedia:(典範條目|典范条目|特色條目|特色条目)/(s|摘要)', text):
                toPurgePages.append(backlink.title())
                print('skip')
                continue
            text = re.sub(r'^#(?:REDIRECT|重定向) \[\[Wikipedia:(?:典範條目|典范条目|特色條目|特色条目)/(.+?)]][\s\S]*$',
                          r'{{Wikipedia:典范条目/\1}}', text, flags=re.I)
            text = re.sub(r'{{(Wikipedia|维基百科|維基百科):(?:典範條目|典范条目|特色條目|特色条目)/[^}]*?}}',
                          r'{{Wikipedia:典范条目/' + articletitle + r'}}', text, flags=re.I)

            if backlink.text == text:
                toPurgePages.append(backlink.title())
                print('Nothing changed.')
                continue

            pywikibot.showDiff(backlink.text, text)

            backlink.text = text
            print(summary)
            backlink.save(summary=summary, minor=True)
            cnt2 += 1
        else:
            toPurgePages.append(backlink.title())

    for toPurgePage in toPurgePages:
        purge(toPurgePage)

    cnt += 1
    print('=' * 50)

    if args.limit > 0 and cnt > args.limit:
        print('Reach the limit. Quitting.')
        break

    if args.limit2 > 0 and cnt2 > args.limit2:
        print('Reach the limit2. Quitting.')
        break
