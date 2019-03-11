# -*- coding: utf-8 -*-
import json
import os
import re
import sys
from datetime import datetime, timedelta

import mwparserfromhell
os.environ['PYWIKIBOT2_DIR'] = os.path.dirname(os.path.realpath(__file__))
import pywikibot
from pywikibot.data.api import Request

from config import *


site = pywikibot.Site()
site.login()

config_page = pywikibot.Page(site, config_page_name)
cfg = config_page.text
cfg = json.loads(cfg)
print(json.dumps(cfg, indent=4, ensure_ascii=False))

if not cfg['enable']:
    exit('disabled\n')


def converttitle(title):
    oldtitle = title
    r = Request(site=site, parameters={
        'action': 'query',
        'titles': title,
        'redirects': 1,
        'converttitles': 1
    })
    data = r.submit()
    title = list(data['query']['pages'].values())[0]['title']
    mode = []
    if 'redirects' in data['query']:  # 重定向
        mode.append('redirects')
    if 'converted' in data['query']:  # 繁簡轉換
        mode.append('converted')
    if 'normalized' in data['query']:  # 命名空間
        mode.append('normalized')
    if 'redirects' not in mode:
        page = pywikibot.Page(site, title)
        if page.exists() and (page.content_model != 'wikitext' or re.search(r'{{\s*[vaictumr]fd', page.text, flags=re.I)):
            mode.append('vfd_on_source')
    else:
        page = pywikibot.Page(site, oldtitle)
        if page.exists() and (page.content_model != 'wikitext' or re.search(r'{{\s*[vaictumr]fd', page.text, flags=re.I)):
            mode.append('vfd_on_source')
        page = pywikibot.Page(site, title)
        if page.exists() and (page.content_model != 'wikitext' or re.search(r'{{\s*[vaictumr]fd', page.text, flags=re.I)):
            mode.append('vfd_on_target')
    if not 'vfd_on_source' in mode and not 'vfd_on_target' in mode:
        mode.append('no_vfd')
    return {'title': title, 'mode': mode}


def appendComment(text, mode):
    text = text.strip()
    if 'A2093064-bot' not in text:
        if 'fix' in mode:
            comment = []
            if 'redirects' in mode and isinstance(cfg['comment_fix']['redirects'], str):
                comment.append(cfg['comment_fix']['redirects'])
                print('\tcomment_fix - redirects')
            if 'converted' in mode and isinstance(cfg['comment_fix']['converted'], str):
                comment.append(cfg['comment_fix']['converted'])
                print('\tcomment_fix - converted')
            if 'normalized' in mode and isinstance(cfg['comment_fix']['normalized'], str):
                comment.append(cfg['comment_fix']['normalized'])
                print('\tcomment_fix - normalized')
            if len(comment) > 0:
                text += '\n' + \
                    cfg['comment_fix']['main'].format(''.join(comment))
                print('\tcomment_fix - redirects')
        if 'no_vfd' in mode:
            text += '\n' + cfg['comment_vfd']
            print('\tcomment_vfd')
    text += '\n\n'
    return text


def fix(pagename):
    if re.search(r'\d{4}/\d{2}/\d{2}', pagename):
        pagename = 'Wikipedia:頁面存廢討論/記錄/' + pagename

    print('-' * 50)
    print('running for ' + pagename)

    afdpage = pywikibot.Page(site, pagename)
    text = afdpage.text

    wikicode = mwparserfromhell.parse(text)

    changes = []
    for secid, section in enumerate(list(wikicode.get_sections())):
        if secid == 0:
            continue
        title = str(section.get(0).title)
        print(secid, title)
        if re.search(r'{{\s*(delh|TalkendH)\s*\|', str(section), re.IGNORECASE) != None:
            print('  closed, skip')
            continue

        m = re.search(r'^\[\[([^\]]+)\]\]$', title, re.IGNORECASE)
        if m != None:
            title = m.group(1)
            start = ''
            if title[0] == ':':
                start = ':'
                title = title[1:]

            mode = []

            convert = converttitle(title)
            if (('redirects' in convert['mode'] and 'vfd_on_target' in convert['mode'])
                    or (not 'redirects' in convert['mode'])):
                title = convert['title']
                mode.append('fix')
            mode += convert['mode']
            print('    ', mode)

            title = '[[' + start + title + ']]'

            if str(section.get(0).title) != title:
                if str(section.get(0).title).replace('_', ' ') != title:
                    section.insert(
                        1, '\n{{formerly|' + str(section.get(0).title) + '}}')
                    pass
                print('  set new title = ' + title)
                section.get(0).title = title
            newtext = appendComment(str(section), mode)
            changes.append([secid, newtext])
            continue

        m = re.search(
            r'^(\[\[[^\]]+\]\][、，])+\[\[[^\]]+\]\]$', title, re.IGNORECASE)
        if m != None:
            titlelist = m.group(0).replace(']]，[[', ']]、[[').split('、')
            newtitlelist = []
            mode = []
            for title in titlelist:
                if title.startswith('[[') and title.endswith(']]'):
                    title = title[2:-2]

                    if title[0] == ':':
                        title = title[1:]

                    convert = converttitle(title)
                    if (('redirects' in convert['mode'] and 'vfd_on_target' in convert['mode'])
                            or (not 'redirects' in convert['mode'])):
                        title = convert['title']
                        mode.append('fix')
                    mode += convert['mode']

                    newtitlelist.append(title)
                else:
                    print('  wrong title: ' + title)
                    return
            title = '{{al|' + '|'.join(newtitlelist) + '}}'
            if str(section.get(0).title) != title:
                print('  set new title = ' + title)
                section.get(0).title = title
            newtext = appendComment(str(section), mode)
            changes.append([secid, newtext])
            continue

        m = re.search(r'^{{al\|([^\]]+\|)+[^\]]+}}$', title, re.IGNORECASE)
        if m != None:
            titlelist = m.group(0)[5:-2].split('|')
            newtitlelist = []
            mode = []
            for title in titlelist:
                if title[0] == ':':
                    title = title[1:]

                convert = converttitle(title)
                if (('redirects' in convert['mode'] and 'vfd_on_target' in convert['mode'])
                        or (not 'redirects' in convert['mode'])):
                    title = convert['title']
                    mode.append('fix')
                mode += convert['mode']

                newtitlelist.append(title)
            title = '{{al|' + '|'.join(newtitlelist) + '}}'
            if str(section.get(0).title) != title:
                print('  set new title = ' + title)
                section.get(0).title = title
            newtext = appendComment(str(section), mode)
            changes.append([secid, newtext])
            continue

        print('  unknown format, skip')

    for change in changes:
        wikicode = mwparserfromhell.parse(text)
        sections = list(wikicode.get_sections())
        secid, newtext = change
        wikicode.replace(sections[secid], newtext)
        text = str(wikicode)

    if re.sub(r'\s+', '', afdpage.text) == re.sub(r'\s+', '', text):
        print('  nothing changed')
        return

    pywikibot.showDiff(afdpage.text, text)
    summary = cfg['summary']
    print(summary)
    afdpage.text = text
    afdpage.save(summary=summary, minor=False)


if len(sys.argv) >= 2:
    pagename = sys.argv[1]
    fix(pagename)
else:
    print('run past {} days'.format(cfg['run_past_days']))
    for delta in range(cfg['run_past_days']):
        rundate = datetime.now() - timedelta(days=delta)
        pagename = rundate.strftime('%Y/%m/%d')
        fix(pagename)
