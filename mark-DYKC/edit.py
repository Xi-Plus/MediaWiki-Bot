# -*- coding: utf-8 -*-
import argparse
import json
import os
import re

os.environ['PYWIKIBOT_DIR'] = os.path.dirname(os.path.realpath(__file__))
import pywikibot
from config import config_page_name  # pylint: disable=E0611,W0614

parser = argparse.ArgumentParser()
parser.add_argument('--confirm', action='store_true')
parser.set_defaults(confirm=False)
args = parser.parse_args()
print(args)

os.environ['TZ'] = 'UTC'

site = pywikibot.Site()
site.login()

config_page = pywikibot.Page(site, config_page_name)
cfg = config_page.text
cfg = json.loads(cfg)
print(json.dumps(cfg, indent=4, ensure_ascii=False))

if not cfg['enable']:
    exit('disabled\n')

dykcpage = pywikibot.Page(site, cfg['dykc_page'])
text = dykcpage.text

matches = re.findall(r'\|\s*article\s*=\s*([^|]+?)\s*(?:\||}})', text)
print(matches)

DYKCPages = []
for article in matches:
    article = article.strip()
    if article == '':
        continue

    articlePage = pywikibot.Page(site, article)
    if not articlePage.exists():
        continue
    talkPage = articlePage.toggleTalkPage()
    print(talkPage.title())
    DYKCPages.append(talkPage.title())

    talkText = talkPage.text
    sections = pywikibot.textlib.extract_sections(talkText)
    if not re.search(r'{{\s*(DYK[ _]Invite|DYKInvite|DYKC|DYKN)\s*(?:\||}})', sections[0], flags=re.I):
        talkText = '{{DYK Invite}}\n' + talkText
        pywikibot.showDiff(talkPage.text, talkText)
        talkPage.text = talkText
        summary = cfg['add_summary']
        print(summary)

        if args.confirm:
            save = input('Save?').lower()
        else:
            save = 'yes'
        if save in ['yes', 'y', '']:
            talkPage.save(summary=summary, minor=True)

# 開始移除模板
templatePage = pywikibot.Page(site, 'Template:DYK Invite')
for talkPage in templatePage.embeddedin(namespaces=1):
    if talkPage.title() not in DYKCPages:
        print(talkPage.title())
        sections = pywikibot.textlib.extract_sections(talkPage.text)
        header = sections[0]
        header = re.sub(r'{{\s*(DYK[ _]Invite|DYKInvite|DYKC|DYKN)\s*(\|.*)*}} *\n?', '', header)

        newText = header
        for body in sections[1]:
            newText += body[0] + body[1]
        newText += sections[2]

        pywikibot.showDiff(talkPage.text, newText)
        talkPage.text = newText
        summary = cfg['remove_summary']
        print(summary)

        if args.confirm:
            save = input('Save?').lower()
        else:
            save = 'yes'
        if save in ['yes', 'y', '']:
            talkPage.save(summary=summary, minor=True)
