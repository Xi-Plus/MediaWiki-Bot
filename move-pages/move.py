# -*- coding: utf-8 -*-
import argparse
import csv
import os
import re

os.environ['PYWIKIBOT_DIR'] = os.path.dirname(os.path.realpath(__file__))
import pywikibot

parser = argparse.ArgumentParser()
parser.add_argument('source')
parser.add_argument('--no-redirect', action='store_true')
parser.add_argument('--fix-redirect', action='store_true')
parser.add_argument('--dry-run', action='store_true')
args = parser.parse_args()
print(args)

site = pywikibot.Site()
site.login()

with open(args.source, 'r', encoding='utf8') as f:
    reader = csv.reader(f)
    for row in reader:
        if len(row) < 3:
            continue
        oldtitle = row[0].strip()
        newtitle = row[1].strip()
        reason = row[2]
        page = pywikibot.Page(site, oldtitle)
        if args.fix_redirect:
            redirects = [redirect.title() for redirect in page.redirects()]
        print('move {} to {} reason {}'.format(oldtitle, newtitle, reason))
        if not args.dry_run:
            page.move(newtitle, reason=reason, noredirect=args.no_redirect)

        if args.fix_redirect:
            for redirect in redirects:
                rdpage = pywikibot.Page(site, redirect)
                if not rdpage.exists() or rdpage.title() == newtitle:
                    continue
                print('fix redirect {} to {}'.format(rdpage.title(), newtitle))
                if not args.dry_run:
                    rdpage.text = re.sub(r'#(?:REDIRECT|重定向)\s*\[\[.+?\]\]', '#REDIRECT [[' + newtitle + ']]', rdpage.text, flags=re.I)
                    rdpage.save(reason, minor=True)
