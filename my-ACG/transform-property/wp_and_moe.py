# -*- coding: utf-8 -*-
import argparse
import json
import os

os.environ['PYWIKIBOT_DIR'] = os.path.dirname(os.path.realpath(__file__))
import pywikibot
from pywikibot.data.api import Request
import requests
from config import API, PASSWORD, USER  # pylint: disable=E0611


site = pywikibot.Site()
site.login()
datasite = site.data_repository()
zhsite = pywikibot.Site('zh', 'wikipedia')
moesite = pywikibot.Site('moegirl', 'moegirl')


session = requests.Session()

print('fetching login token')
res = session.get(API, params={
    'action': 'query',
    'meta': 'tokens',
    'type': 'login',
    'format': 'json',
}).json()
logintoken = res['query']['tokens']['logintoken']

print('logging in')
res = session.post(API, data={
    'action': 'login',
    'lgname': USER,
    'lgpassword': PASSWORD,
    'lgtoken': logintoken,
    'format': 'json',
}).json()
if res['login']['result'] == 'Success':
    print('login success')
else:
    exit('login fail\n')

res = session.get(API, params={
    'action': 'query',
    'meta': 'tokens',
    'type': 'csrf',
    'format': 'json',
}).json()
csrftoken = res['query']['tokens']['csrftoken']
print('csrftoken', csrftoken)


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


def changeWpAndMoe(title):
    title = title.replace('Item:', '')
    title = title.replace('Property:', '')
    print(title)

    data = {
        'claims': []
    }

    if title[0] == 'Q':
        myitem = pywikibot.ItemPage(datasite, title)
    elif title[0] == 'P':
        myitem = pywikibot.PropertyPage(datasite, title)
    else:
        print('\t Not Wikibase page')
        return

    myitem.get()

    if 'P68' not in myitem.claims and 'P65' in myitem.claims:
        url = myitem.claims['P65'][0].getTarget()
        targettitle = url.replace('https://zh.wikipedia.org/wiki/', '')
        targettitle = converttitle(zhsite, targettitle)
        if targettitle:
            new_claim = pywikibot.page.Claim(datasite, 'P68')
            new_claim.setTarget(targettitle)
            print('\t Add P68', targettitle)
            data['claims'].append(new_claim.toJSON())

    if 'P70' not in myitem.claims and 'P66' in myitem.claims:
        url = myitem.claims['P66'][0].getTarget()
        targettitle = url.replace('https://zh.moegirl.org/', '')
        targettitle = converttitle(moesite, targettitle)
        if targettitle:
            new_claim = pywikibot.page.Claim(datasite, 'P70')
            new_claim.setTarget(targettitle)
            print('\t Add P70', targettitle)
            data['claims'].append(new_claim.toJSON())

    if 'P65' in myitem.claims:
        data['claims'].append({"id": myitem.claims['P65'][0].toJSON()['id'], "remove": ""})
        print('\t Del P65')
    if 'P66' in myitem.claims:
        data['claims'].append({"id": myitem.claims['P66'][0].toJSON()['id'], "remove": ""})
        print('\t Del P66')

    print('\t', data)

    session.post(API, data={
        'action': 'wbeditentity',
        'format': 'json',
        'id': title,
        'data': json.dumps(data),
        'summary': '轉換屬性',
        'token': csrftoken,
        'bot': 1,
    }).json()


def main():
    P65 = pywikibot.PropertyPage(datasite, 'P65')
    for backlink in P65.backlinks():
        changeWpAndMoe(backlink.title())

    P66 = pywikibot.PropertyPage(datasite, 'P66')
    for backlink in P66.backlinks():
        changeWpAndMoe(backlink.title())


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('title', nargs='?')
    args = parser.parse_args()
    if args.title:
        changeWpAndMoe(args.title)
    else:
        main()
