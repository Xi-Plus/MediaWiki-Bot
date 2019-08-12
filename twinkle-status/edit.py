# -*- coding: utf-8 -*-
import os
import re

os.environ['PYWIKIBOT_DIR'] = os.path.dirname(os.path.realpath(__file__))
import pywikibot


os.environ['TZ'] = 'UTC'

site = pywikibot.Site()
site.login()

with open('list.txt', 'r') as f:
    for user in f:
        user = user.strip()
        page = pywikibot.Page(site, 'User:{}/common.js'.format(user))
        if not page.exists():
            print('{}\t{}'.format(user, 'gadget'))
            continue
        text = page.text
        if 'Xiplus/Twinkle.js' in text:
            print('{}\t{}'.format(user, 'Xiplus'))
            continue
        m = re.search(r'User:(.+?)/Twinkle.js', text)
        if m:
            print('{}\t{}'.format(user, m.group(1)))
            continue
        print('{}\t{}'.format(user, 'gadget'))
        continue
