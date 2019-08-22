# -*- coding: utf-8 -*-
import os
import re

os.environ['PYWIKIBOT_DIR'] = os.path.dirname(os.path.realpath(__file__))
import pywikibot


os.environ['TZ'] = 'UTC'

site = pywikibot.Site()
site.login()

branchs = {
    'gadget': [],
    'xiplus': [],
}

with open('list.txt', 'r') as f:
    for user in f:
        user = user.strip()
        page = pywikibot.Page(site, 'User:{}/common.js'.format(user))
        if not page.exists():
            branchs['gadget'].append(user)
            continue
        text = page.text
        if 'Xiplus/Twinkle.js' in text:
            branchs['xiplus'].append(user)
            continue
        m = re.search(r'User:(.+?)/Twinkle.js', text)
        if m:
            if m.group(1) not in branchs:
                branchs[m.group(1)] = []
            branchs[m.group(1)].append(user)
            continue
        branchs['gadget'].append(user)
        continue

for branch in branchs:
    print(branch, branchs[branch])
