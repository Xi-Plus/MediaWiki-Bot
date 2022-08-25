# -*- coding: utf-8 -*-
import argparse
import json
import os
import re
from datetime import datetime, timedelta

import mwparserfromhell

os.environ['PYWIKIBOT_DIR'] = os.path.dirname(os.path.realpath(__file__))
import pywikibot
from pywikibot.data.api import Request

from config import config_page_name  # pylint: disable=E0611,W0614

parser = argparse.ArgumentParser()
parser.add_argument('pagename', nargs='?')
parser.add_argument('--debug', action='store_true')
parser.set_defaults(debug=False)
args = parser.parse_args()
pywikibot.log(args)

site = pywikibot.Site()
site.login()

config_page = pywikibot.Page(site, config_page_name)
cfg = config_page.text
cfg = json.loads(cfg)
if args.debug:
    print(json.dumps(cfg, indent=4, ensure_ascii=False))

if not cfg['enable']:
    print('disabled')
    exit()


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
        if not page.exists():
            mode.append('vfd_on_source')
        if page.exists() and (page.content_model != 'wikitext'
                              or page.namespace().id == 8
                              or re.search(r'{{\s*([vaictumr]fd|Copyvio)', page.text, flags=re.I)):
            mode.append('vfd_on_source')
    else:
        page = pywikibot.Page(site, oldtitle)
        if page.exists() and (page.content_model != 'wikitext'
                              or page.namespace().id == 8
                              or re.search(r'{{\s*([vaictumr]fd|Copyvio)', page.text, flags=re.I)):
            mode.append('vfd_on_source')
        page = pywikibot.Page(site, title)
        if page.exists() and (page.content_model != 'wikitext'
                              or page.namespace().id == 8
                              or re.search(r'{{\s*([vaictumr]fd|Copyvio)', page.text, flags=re.I)):
            mode.append('vfd_on_target')
    if 'vfd_on_source' not in mode and 'vfd_on_target' not in mode:
        mode.append('no_vfd')
    return {'title': title, 'mode': mode}


def appendComment(text, mode):
    if 'A2093064-bot' not in text:
        append_text = []
        if 'fix' in mode:
            comment = []
            if 'redirects' in mode and isinstance(cfg['comment_fix']['redirects'], str):
                comment.append(cfg['comment_fix']['redirects'])
                if args.debug:
                    print('\tcomment_fix - redirects')
            if 'converted' in mode and isinstance(cfg['comment_fix']['converted'], str):
                comment.append(cfg['comment_fix']['converted'])
                if args.debug:
                    print('\tcomment_fix - converted')
            if 'normalized' in mode and isinstance(cfg['comment_fix']['normalized'], str):
                comment.append(cfg['comment_fix']['normalized'])
                if args.debug:
                    print('\tcomment_fix - normalized')
            if len(comment) > 0:
                append_text.append(cfg['comment_fix']['main'].format(
                    ''.join(comment)))
                if args.debug:
                    print('\tcomment_fix - redirects')
        if 'no_vfd' in mode:
            append_text.append(cfg['comment_vfd'])
            if args.debug:
                print('\tcomment_vfd')
        if len(append_text) > 0:
            text = text.strip()
            append_text = '\n'.join(append_text)
            hr = '\n----'
            if hr in text:
                temp = text.split(hr)
                text = hr.join(temp[:-1]) + '\n' + append_text + hr + temp[-1]
            else:
                text += '\n' + append_text
            text += '\n\n'
    return text


def escapeEqualSign(titlelist):
    anyEqual = any(['=' in title for title in titlelist])
    if anyEqual:
        newtitlelist = []
        for i, title in enumerate(titlelist, 1):
            newtitlelist.append('{}={}'.format(i, title))
        return newtitlelist
    return titlelist


def fix(pagename):
    if re.search(r'\d{4}/\d{2}/\d{2}', pagename):
        pagename = 'Wikipedia:頁面存廢討論/記錄/' + pagename

    if args.debug:
        print('-' * 50)
        print('running for ' + pagename)

    afdpage = pywikibot.Page(site, pagename)
    text = afdpage.text

    wikicode = mwparserfromhell.parse(text)

    changes = []
    for secid, section in enumerate(list(wikicode.get_sections())):
        if secid == 0:
            continue
        title = str(section.get(0).title).strip()
        if args.debug:
            print(secid, title)
        if re.search(r'{{\s*(delh|TalkendH)\s*(\||}})', str(section), re.IGNORECASE) is not None:
            if args.debug:
                print('  closed, skip')
            continue

        m = re.search(r'^\[\[([^\]]+)\]\]$', title, re.IGNORECASE)
        if m is not None:
            title = m.group(1)
            start = ''
            if title[0] == ':':
                start = ':'
                title = title[1:]

            mode = []

            convert = converttitle(title)
            if (('redirects' in convert['mode'] and 'vfd_on_target' in convert['mode'])
                    or ('redirects' not in convert['mode'])):
                title = convert['title']
                mode.append('fix')
            mode += convert['mode']
            if args.debug:
                print('    ', mode)

            title = '[[' + start + title + ']]'

            oldtitle = str(section.get(0).title).strip()
            if oldtitle != title:
                if oldtitle.replace('_', ' ').replace('&#39;', "'") != title:
                    section.insert(1, '\n{{formerly|' + oldtitle + '}}')
                if args.debug:
                    print('  set new title = ' + title)
                section.get(0).title = title
            newtext = appendComment(str(section), mode)
            changes.append([secid, newtext])
            continue

        m = re.search(
            r'^(\[\[[^\]]+\]\][、， ])+\[\[[^\]]+\]\]$', title, re.IGNORECASE)
        if m is not None:
            titlelist = re.sub(r'\]\][， ]\[\[', ']]、[[', m.group(0)).split('、')
            newtitlelist = []
            mode = []
            for title in titlelist:
                if title.startswith('[[') and title.endswith(']]'):
                    title = title[2:-2]

                    if title[0] == ':':
                        title = title[1:]

                    convert = converttitle(title)
                    if (('redirects' in convert['mode'] and 'vfd_on_target' in convert['mode'])
                            or ('redirects' not in convert['mode'])):
                        title = convert['title']
                        mode.append('fix')
                    mode += convert['mode']

                    newtitlelist.append(title)
                else:
                    if args.debug:
                        print('  wrong title: ' + title)
                    return
            newtitlelist = escapeEqualSign(newtitlelist)
            title = '{{al|' + '|'.join(newtitlelist) + '}}'
            if str(section.get(0).title) != title:
                if args.debug:
                    print('  set new title = ' + title)
                section.get(0).title = title
            newtext = appendComment(str(section), mode)
            changes.append([secid, newtext])
            continue

        m = re.search(r'^{{al\|([^\]]+\|)+[^\]]+}}$', title, re.IGNORECASE)
        if m is not None:
            titlelist = m.group(0)[5:-2].split('|')
            newtitlelist = []
            mode = []
            for title in titlelist:
                m = re.search(r'^\s*\d+\s*=\s*(.+)$', title)
                if m:
                    title = m.group(1)

                if title[0] == ':':
                    title = title[1:]

                convert = converttitle(title)
                if (('redirects' in convert['mode'] and 'vfd_on_target' in convert['mode'])
                        or ('redirects'not in convert['mode'])):
                    title = convert['title']
                    mode.append('fix')
                mode += convert['mode']

                newtitlelist.append(title)
            newtitlelist = escapeEqualSign(newtitlelist)
            title = '{{al|' + '|'.join(newtitlelist) + '}}'
            if str(section.get(0).title) != title:
                if args.debug:
                    print('  set new title = ' + title)
                section.get(0).title = title
            newtext = appendComment(str(section), mode)
            changes.append([secid, newtext])
            continue

        if args.debug:
            print('  unknown format, skip')

    for change in changes:
        wikicode = mwparserfromhell.parse(text)
        sections = list(wikicode.get_sections())
        secid, newtext = change
        wikicode.replace(sections[secid], newtext)
        text = str(wikicode)

    if re.sub(r'\s+', '', afdpage.text) == re.sub(r'\s+', '', text):
        if args.debug:
            print('  nothing changed')
        return

    if args.debug:
        pywikibot.showDiff(afdpage.text, text)
    summary = cfg['summary']
    if args.debug:
        print(summary)
    afdpage.text = text
    afdpage.save(summary=summary, minor=False)


if args.pagename:
    fix(args.pagename)
else:
    if args.debug:
        print('run past {} days'.format(cfg['run_past_days']))
    for delta in range(cfg['run_past_days']):
        rundate = datetime.now() - timedelta(days=delta)
        pagename = rundate.strftime('%Y/%m/%d')
        fix(pagename)
