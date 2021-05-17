# -*- coding: utf-8 -*-
import html
import json
import os
import re
import time

import requests

os.environ['PYWIKIBOT_DIR'] = os.path.dirname(os.path.realpath(__file__))
import pywikibot

from util import headers, noteTA  # pylint: disable=E0611


def translateText(strings, tolang, noteTA, headers):
    def escapeWikitextMatch(text):
        return '&#{};'.format(ord(text[0]))

    def escapeWikitext(text):
        text = re.sub(r"[\[\]{}<>|\\:*'_#&\s]", escapeWikitextMatch, text)
        return text

    text = noteTA
    for idx, string in enumerate(strings):
        text += '<div id="text{}">{}</div>'.format(idx, escapeWikitext(string))

    data = {
        'action': 'parse',
        'format': 'json',
        'text': text,
        'prop': 'text',
        'contentmodel': 'wikitext',
        'utf8': 1,
        'uselang': tolang
    }
    r = requests.post('https://zh.wikipedia.org/w/api.php', data=data, headers=headers)
    try:
        result = r.json()
    except Exception as e:
        print(e)
        print(r.text)
        raise e

    newstrings = [''] * len(strings)

    result = result['parse']['text']['*']
    matches = re.findall(r'<div id="text(\d+)">(.+?)</div>', result)
    for match in matches:
        idx = int(match[0])
        newtext = html.unescape(match[1]).replace('\\n', '\\\\n')
        newstrings[idx] = newtext

    return newstrings


site = pywikibot.Site()
site.login()

with open('list.txt', 'r', encoding='utf8') as f:
    for key in f:
        key = key.strip()

        namehant = '{}/zh-hant'.format(key)
        namehans = '{}/zh-hans'.format(key)

        pagehant = pywikibot.Page(site, namehant)

        if not pagehant.exists():
            print('{} is not exists'.format(namehant))
            continue

        newtext = translateText([pagehant.text], 'zh-cn', noteTA, headers)[0]

        pagehans = pywikibot.Page(site, namehans)
        summary = '自動從[[{}]]轉換'.format(namehant)
        print('Editing {} with summary {}'.format(namehans, summary))
        print(pagehant.text)
        print('-' * 50)
        pywikibot.showDiff(pagehans.text, newtext)
        input('Save?')
        pagehans.text = newtext

        pagehans.save(summary=summary, asynchronous=True)
