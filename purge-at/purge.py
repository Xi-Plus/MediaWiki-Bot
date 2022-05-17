# -*- coding: utf-8 -*-
import datetime
import json
import os

from config import config_page_name  # pylint: disable=E0611,W0614

os.environ['TZ'] = 'UTC'

os.environ['PYWIKIBOT_DIR'] = os.path.dirname(os.path.realpath(__file__))
import pywikibot

site = pywikibot.Site()
site.login()

config_page = pywikibot.Page(site, config_page_name)
cfg = config_page.text
cfg = json.loads(cfg)

if not cfg['enable']:
    print('disabled')
    exit()

now = datetime.datetime.now()
pywikibot.log('Current time: {}'.format(now))

categorymembers = []
cmcontinue = ''
while True:
    data = pywikibot.data.api.Request(site=site, parameters={
        'action': 'query',
        'format': 'json',
        'list': 'categorymembers',
        'continue': '-||',
        'cmtitle': cfg['category'],
        'cmprop': 'title|sortkeyprefix',
        'cmlimit': 'max',
        'cmcontinue': cmcontinue,
    }).submit()
    categorymembers.extend(data['query']['categorymembers'])
    if 'continue' in data:
        cmcontinue = data['continue']['cmcontinue']
    else:
        break

for row in categorymembers:
    purge_at = datetime.datetime.strptime(row['sortkeyprefix'], '%Y%m%d%H%M%S')
    cat = pywikibot.Page(site, row['title'])
    if now >= purge_at:
        pywikibot.log('Purge {} {}'.format(cat, purge_at))
        cat.purge()