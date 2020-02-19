# -*- coding: utf-8 -*-
import argparse
import os
from urllib.parse import unquote

os.environ['PYWIKIBOT_DIR'] = os.path.dirname(os.path.realpath(__file__))
import pywikibot


os.environ['TZ'] = 'UTC'

parser = argparse.ArgumentParser()
parser.add_argument('source_lang')
parser.add_argument('source_family')
parser.add_argument('source_title')
parser.add_argument('target_lang')
parser.add_argument('target_family')
parser.add_argument('target_title')
args = parser.parse_args()

source_site = pywikibot.Site(args.source_lang, args.source_family)
source_site.login()

target_site = pywikibot.Site(args.target_lang, args.target_family)
target_site.login()

source_page = pywikibot.Page(source_site, args.source_title)
target_page = pywikibot.Page(target_site, args.target_title)

pywikibot.showDiff(target_page.text, source_page.text)

print('Copying from {} to {}'.format(source_page, target_page))
summary = 'Copied from {}'.format(unquote(source_page.full_url()))
print(summary)

if input('Save?').lower() in ['', 'y', 'yes']:
    target_page.text = source_page.text
    target_page.save(summary=summary)
