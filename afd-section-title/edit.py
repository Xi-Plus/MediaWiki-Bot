# -*- coding: utf-8 -*-
import json
import os
import re
import sys
from datetime import datetime, timedelta

import mwparserfromhell
import pywikibot
from pywikibot.data.api import Request

from config import *


os.environ['PYWIKIBOT2_DIR'] = os.path.dirname(os.path.realpath(__file__))

site = pywikibot.Site()
site.login()

config_page = pywikibot.Page(site, config_page_name)
cfg = config_page.text
cfg = json.loads(cfg)
print(json.dumps(cfg, indent=4, ensure_ascii=False))

if not cfg["enable"]:
    exit("disabled\n")


def converttitle(title):
    r = Request(site=site, parameters={
        'action': 'query',
        'titles': title,
        "redirects": 1,
        "converttitles": 1
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
    return {'title': title, 'mode': mode}


def appendComment(text, mode):
    text = text.strip()
    comment = []
    if 'redirects' in mode and isinstance(cfg['comment_redirects'], str):
        comment.append(cfg['comment_redirects'])
    if 'converted' in mode and isinstance(cfg['comment_converted'], str):
        comment.append(cfg['comment_converted'])
    if 'normalized' in mode and isinstance(cfg['comment_normalized'], str):
        comment.append(cfg['comment_normalized'])
    if len(comment) > 0:
        text += '\n' + cfg['comment'].format(''.join(comment)) + '\n\n'
    return text


def fix(pagename):
    if re.search(r'\d{4}/\d{2}/\d{2}', pagename):
        pagename = "Wikipedia:頁面存廢討論/記錄/" + pagename

    print("-"*50)
    print("running for "+pagename)

    afdpage = pywikibot.Page(site, pagename)
    text = afdpage.text

    wikicode = mwparserfromhell.parse(text)

    for section in wikicode.get_sections()[1:]:
        title = str(section.get(0).title)
        print(title)
        if re.search(r"{{\s*(delh|TalkendH)\s*\|", str(section), re.IGNORECASE) != None:
            print("  closed, skip")
            continue

        m = re.search(r"^\[\[([^\]]+)\]\]$", title, re.IGNORECASE)
        if m != None:
            title = m.group(1)
            start = ""
            if title[0] == ":":
                start = ":"
                title = title[1:]

            mode = []

            convert = converttitle(title)
            title = convert['title']
            mode += convert['mode']

            title = "[["+start+title+"]]"

            if str(section.get(0).title) != title:
                if str(section.get(0).title).replace("_", " ") != title:
                    section.insert(
                        1, "\n{{formerly|"+str(section.get(0).title)+"}}")
                print("  set new title = "+title)
                section.get(0).title = title
                newtext = appendComment(str(section), mode)
                section.replace(section, newtext)
            continue

        m = re.search(
            r"^(\[\[[^\]]+\]\][、，])+\[\[[^\]]+\]\]$", title, re.IGNORECASE)
        if m != None:
            titlelist = m.group(0).replace("]]，[[", "]]、[[").split("、")
            newtitlelist = []
            mode = []
            for title in titlelist:
                if title.startswith("[[") and title.endswith("]]"):
                    title = title[2:-2]

                    if title[0] == ":":
                        title = title[1:]

                    convert = converttitle(title)
                    title = convert['title']
                    mode += convert['mode']

                    newtitlelist.append(title)
                else:
                    print("  wrong title: "+title)
                    return
            title = "{{al|"+"|".join(newtitlelist)+"}}"
            if str(section.get(0).title) != title:
                print("  set new title = "+title)
                section.get(0).title = title
                newtext = appendComment(str(section), mode)
                section.replace(section, newtext)
            continue

        m = re.search(r"^{{al\|([^\]]+\|)+[^\]]+}}$", title, re.IGNORECASE)
        if m != None:
            titlelist = m.group(0)[5:-2].split("|")
            newtitlelist = []
            mode = []
            for title in titlelist:
                if title[0] == ":":
                    title = title[1:]

                convert = converttitle(title)
                title = convert['title']
                mode += convert['mode']

                newtitlelist.append(title)
            title = "{{al|"+"|".join(newtitlelist)+"}}"
            if str(section.get(0).title) != title:
                print("  set new title = "+title)
                section.get(0).title = title
                newtext = appendComment(str(section), mode)
                section.replace(section, newtext)
            continue

        print("  unknown format, skip")

    text = str(wikicode)

    if afdpage.text == text:
        print("  nothing changed")
        return

    pywikibot.showDiff(afdpage.text, text)
    summary = cfg["summary"]
    print(summary)
    afdpage.text = text
    afdpage.save(summary=summary, minor=False)


if len(sys.argv) >= 2:
    pagename = sys.argv[1]
    fix(pagename)
else:
    print("run past {} days".format(cfg["run_past_days"]))
    for delta in range(cfg["run_past_days"]):
        rundate = datetime.now() - timedelta(days=delta)
        pagename = rundate.strftime('%Y/%m/%d')
        fix(pagename)
