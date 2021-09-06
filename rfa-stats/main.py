# -*- coding: utf-8 -*-
import argparse
import hashlib
import json
import os
import re
import time
from datetime import datetime, timezone

os.environ['PYWIKIBOT_DIR'] = os.path.dirname(os.path.realpath(__file__))
import pywikibot

os.environ['TZ'] = 'UTC'

parser = argparse.ArgumentParser()
parser.add_argument('page')
parser.add_argument('--starttime')
parser.add_argument('--endtime')
args = parser.parse_args()

STARTTIME = args.starttime
ENDTIME = args.endtime
if isinstance(STARTTIME, str):
    STARTTIME = STARTTIME.ljust(14, '0')
if isinstance(ENDTIME, str):
    ENDTIME = ENDTIME.ljust(14, '0')

site = pywikibot.Site()
site.login()

rfaPage = pywikibot.Page(site, args.page)

if not rfaPage.exists():
    print('{} is not exists'.format(args.page))
    exit()

BASEDIR = os.path.dirname(os.path.realpath(__file__))
DATAPATH = os.path.join(BASEDIR, 'data')
os.makedirs(DATAPATH, exist_ok=True)

FILENAME = re.sub(r'[:/ ]', '_', rfaPage.title())

RESULTPATH = os.path.join(DATAPATH, FILENAME + '.json')

oldresult = []
try:
    with open(RESULTPATH, 'r', encoding='utf8') as f:
        oldresult = json.load(f)
except Exception:
    pass

oldresultdict = {}
for rev in oldresult:
    oldresultdict[rev['revid']] = rev

print('Loaded {} old results'.format(len(oldresultdict)))


def getInfoFromText(text):
    res = {
        'support': 0,
        'oppose': 0,
        'neutral': 0,
    }

    m = re.search(r'\n=====支持(（非由聯署帶出的）)?=====', text)
    if not m:
        print('Warning: Cannot find support section')
        return res
    supportPos = m.start()

    m = re.search(r'\n=====反對=====', text)
    if not m:
        print('Warning: Cannot find oppose section')
        return res
    opposePos = m.start()

    m = re.search(r'\n=====中立=====', text)
    if not m:
        print('Warning: Cannot find neutral section')
        return res
    neutralPos = m.start()

    m = re.search(r'\n=====(其他)?意[見见]=====', text)
    if not m:
        print('Warning: Cannot find comment section')
        return res
    commentPos = m.start()

    supportText = text[supportPos:opposePos]
    res['support'] = len(re.findall(r'^#[^#:*].+\n', supportText, flags=re.M))

    opposeText = text[opposePos:neutralPos]
    res['oppose'] = len(re.findall(r'^#[^#:*].+\n', opposeText, flags=re.M))

    neutralText = text[neutralPos:commentPos]
    res['neutral'] = len(re.findall(r'^#[^#:*].+\n', neutralText, flags=re.M))

    return res


allrevs = list(rfaPage.revisions(reverse=True, starttime=STARTTIME, endtime=ENDTIME))
print('Found {} revs to process'.format(len(allrevs)))
newresult = []
try:
    for rev in allrevs:
        if rev.revid not in oldresultdict:
            if rev.revid not in rfaPage._revisions:  # pylint: disable=W0212
                rfaPage.revisions(content=True, reverse=True, starttime=rev.timestamp, total=50)

            print('#{} Parsing {} {}'.format(len(newresult) + 1, rev.timestamp, rev.revid))
            text = rfaPage.getOldVersion(rev.revid)

            res = {}
            res['timestamp'] = rev.timestamp.isoformat()
            res['revid'] = rev.revid
            res['user'] = rev.user
            res.update(getInfoFromText(text))
        else:
            res = oldresultdict[rev.revid]

        if res['oppose'] == 0:
            res['ratio'] = 0
        else:
            res['ratio'] = round(res['support'] / (res['support'] + res['oppose']) * 100, 2)

        newresult.append(res)
except KeyboardInterrupt:
    pass

newresult.sort(key=lambda v: v['revid'])

print('Writing result')
with open(RESULTPATH, 'w', encoding='utf8') as f:
    json.dump(newresult, f, ensure_ascii=False)
