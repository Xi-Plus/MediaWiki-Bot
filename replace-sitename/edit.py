# -*- coding: utf-8 -*-
import argparse
import json
import os
import re

os.environ['PYWIKIBOT2_DIR'] = os.path.dirname(os.path.realpath(__file__))
import pywikibot


os.environ['TZ'] = 'UTC'

parser = argparse.ArgumentParser()
parser.add_argument('title', type=str)
parser.add_argument('--confirm', type=bool, default=False)
parser.add_argument('--lang', type=str, default='zh')
parser.add_argument('--family', type=str, default='wikipedia')
args = parser.parse_args()
print(args)

site = pywikibot.Site(args.lang, args.family)
site.login()

title = args.title
title = re.sub(r'^MediaWiki:', '', title, flags=re.I)
title = re.sub(r'^([^/]+)/.+$', r'\1', title)
print(title)

langs = [
    '',
    'zh-hans',
    'zh-cn',
    'zh-my',
    'zh-sg',
    'zh-hant',
    'zh-hk',
    'zh-mo',
    'zh-tw',
]


for lang in langs:
    if lang == '':
        realtitle = 'MediaWiki:{}'.format(title)
        reallang = 'zh'
        replacetext = '{{subst:MediaWiki:Sitetitle}}'
    else:
        realtitle = 'MediaWiki:{}/{}'.format(title, lang)
        reallang = lang
        replacetext = '{{{{subst:MediaWiki:Sitetitle/{0}}}}}'.format(lang)

    print('Running on {}'.format(realtitle))

    data = pywikibot.data.api.Request(site=site, parameters={
        "action": "query",
        "format": "json",
        "meta": "allmessages",
        "ammessages": title,
        "amlang": reallang,
    }).submit()

    oldtext = text = data['query']['allmessages'][0]['*']

    text = text.replace(' {{SITENAME}}', '{{SITENAME}}')
    text = text.replace('{{SITENAME}}', replacetext)

    if oldtext == text:
        print('Nothing changed')
        continue

    page = pywikibot.Page(site, realtitle)

    print('Editing {}'.format(page.title()))

    pywikibot.showDiff(oldtext, text)

    page.text = text
    summary = '替換{{SITENAME}}'
    print('Summary=', summary)

    if args.confirm:
        save = input('Save?')
    else:
        save = "Yes"
    if save.lower() in ['yes', 'y', '']:
        page.save(summary=summary, minor=False)
