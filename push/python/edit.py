# -*- coding: utf-8 -*-
import os

from config import cfg  # pylint: disable=E0611,W0614
from func import file_get_contents

os.environ['TZ'] = 'UTC'

print('===== project =====')
project = None
while project is None:
    for key, val in enumerate(cfg['project'], 1):
        print('\t', key, val)
    project = input('select a project:')
    try:
        project = int(project)
        project = list(cfg['project'].values())[project - 1]
        break
    except Exception as e:
        print(e)
        project = None
print('project', project)
print()

print('===== web =====')
web = None
while web is None:
    for key, val in enumerate(project['web'], 1):
        print('\t', key, val)
    web = input('select a web:')
    try:
        web = int(web)
        webname = project['web'][web - 1]
        web = cfg['web'][webname]
        break
    except Exception as e:
        print(e)
        web = None
print('web', web)
print()

print('===== source =====')
source = None
while source is None:
    for key, val in enumerate(project['source'], 1):
        print('\t', key, val)
    source = input('select a source:')
    try:
        source = int(source)
        source = cfg['source'][project['source'][source - 1]]
        break
    except Exception as e:
        print(e)
        source = None
print('source', source)
print()

print('===== target =====')
target = None
while target is None:
    for key, val in enumerate(project['target'], 1):
        print('\t', key, val)
    target = input('select a target:')
    try:
        target = int(target)
        target = cfg['target'][project['target'][target - 1]]
        break
    except Exception as e:
        print(e)
        target = None
print('target', target)
print()

print('===== files =====')
files = {}
while len(files) == 0:
    cnt = 0
    for fromname in project['files']:
        cnt += 1
        print('\t', cnt, '\t', fromname, '\t', project['files'][fromname])
    temp = input('select a files:')
    try:
        for idx in temp.split():
            idx = int(idx)
            files[list(project['files'].keys())[idx - 1]] = list(project['files'].values())[idx - 1]
        break
    except Exception as e:
        print(e)
        files = {}
if len(files) == 0:
    for fromname in project['files']:
        files[fromname] = project['files'][fromname]
print('files', files)
print()

summary = project['summary']
print('summary:', summary)
temp = input('new summary:').strip()
if temp != '':
    summary = temp
print('summary:', summary)
print()

os.environ['PYWIKIBOT_DIR'] = os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    'user-config',
    webname
)

import pywikibot

site = pywikibot.Site()
site.login()

for fromname in files:
    toname = files[fromname]
    fromname = source + fromname
    toname = target + toname
    print(fromname, '->', toname)
    try:
        text = file_get_contents(fromname)
    except Exception as e:
        print(e)
        continue

    page = pywikibot.Page(site, toname)
    if page.text == '':
        print('New page')
    else:
        pywikibot.showDiff(page.text, text)
    save = input('Save?')
    if save.lower() in ['', 'y', 'yes']:
        page.text = text
        page.save(summary=summary, minor=web['minor'], botflag=web['bot'], nocreate=web['nocreate'])
