# -*- coding: utf-8 -*-
import csv
import json
import os

os.environ['PYWIKIBOT_DIR'] = os.path.dirname(os.path.realpath(__file__))
import pywikibot

from config import config_page_name  # pylint: disable=E0611,W0614


os.environ['TZ'] = 'UTC'

site = pywikibot.Site()
site.login()

metasite = pywikibot.Site('meta', 'meta')
metasite.login()


config_page = pywikibot.Page(site, config_page_name)
cfg = config_page.text
cfg = json.loads(cfg)
print(json.dumps(cfg, indent=4, ensure_ascii=False))

if not cfg['enable']:
    exit('disabled\n')


cat = pywikibot.Page(site, cfg['category'])

for page in site.categorymembers(cat):
    print(page.username)
    data = pywikibot.data.api.Request(site=metasite, parameters={
        'action': 'query',
        'format': 'json',
        'list': 'logevents',
        'meta': 'globaluserinfo',
        'leaction': 'globalauth/setstatus',
        'letitle': 'User:{}@global'.format(page.username),
        'guiuser': page.username
    }).submit()
    print(data)
    locked = False
    if 'locked' in data['query']['globaluserinfo']:
        locked = True
    elif len(data['query']['logevents']) > 0 and data['query']['logevents'][0]['params']['0'] == 'locked':
        locked = True
    print(locked)

    if locked:
        args = {
            'reason': cfg['summary'],
            'prompt': False,
            'protections': {
                'edit': 'sysop',
                'move': 'sysop',
            }
        }
        print(page.title(), args)
        page.protect(**args)
        page.save(asynchronous=True)
