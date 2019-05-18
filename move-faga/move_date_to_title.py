# -*- coding: utf-8 -*-
import argparse
import os
import re

os.environ['PYWIKIBOT_DIR'] = os.path.dirname(os.path.realpath(__file__))
import pywikibot

os.environ['TZ'] = 'UTC'

site = pywikibot.Site()
site.login()

token = site.tokens['csrf']


def move_date_to_title(title, confirm=False, dry_run=False):
    page = pywikibot.Page(site, title)

    pagetitle = page.title()
    print(pagetitle)

    if not page.exists():
        print('not exists')
        return

    text = page.text
    print('-----\n' + text + '\n--------')

    m = re.search(r"'''《?\[\[(.+?)(\|.+?)?]]》?'''", text)
    if not m:
        print('cannot find title')
        return

    target = m.group(1)

    targetpage = pywikibot.Page(site, target)
    if targetpage.isRedirectPage():
        targetpage = targetpage.getRedirectTarget()
        print('follow redirect')

    print(targetpage.title())

    movefrom = page.title()
    moveto = 'Wikipedia:优良条目/' + targetpage.title()
    print('move {} to {} ?'.format(movefrom, moveto))
    if not dry_run:
        if confirm:
            input()
        data = pywikibot.data.api.Request(site=site, parameters={
            'action': 'move',
            'from': page.title(),
            'to': 'Wikipedia:优良条目/' + targetpage.title(),
            'reason': '整理標題格式',
            'noredirect': '1',
            'token': token
        }).submit()
        print(data)

    print('save {} as {} ?'.format(movefrom, moveto))
    if not dry_run:
        if confirm:
            input()
        page = pywikibot.Page(site, movefrom)
        page.text = '{{' + moveto + '}}'
        page.save(summary='整理標題格式')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('page')
    parser.add_argument('--confirm', type=bool, default=False)
    parser.add_argument('--dry_run', type=bool, default=False)
    args = parser.parse_args()

    print(args)

    move_date_to_title(args.page, confirm=args.confirm, dry_run=args.dry_run)
