import calendar
import collections
import datetime
import json
import os

import dateutil.relativedelta
import requests

BASEDIR = os.path.dirname(os.path.realpath(__file__))
os.environ['PYWIKIBOT_DIR'] = BASEDIR
import pywikibot

from config import config_page_name  # pylint: disable=E0611,W0614

site = pywikibot.Site()
site.login()

config_page = pywikibot.Page(site, config_page_name)
cfg = json.loads(config_page.text)

if not cfg['enable']:
    exit('disabled\n')


CACHEDIR = os.path.join(BASEDIR, 'cache')
os.makedirs(CACHEDIR, exist_ok=True)


def call_api_core(start, end):
    cache_path = os.path.join(CACHEDIR, '{}-{}.json'.format(start, end))
    if os.path.exists(cache_path):
        with open(cache_path, 'r', encoding='utf8') as f:
            return json.load(f)
    url = 'https://xtools.wmflabs.org/api/project/admin_stats/zh.wikipedia/{}/{}'.format(start, end)
    data = requests.get(url).json()
    with open(cache_path, 'w', encoding='utf8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return data


def call_api(year, month):
    start = datetime.date(year, month, 1).strftime('%Y-%m-%d')
    end = datetime.date(year, month, calendar.monthrange(year, month)[1]).strftime('%Y-%m-%d')
    return call_api_core(start, end)


# fetch admin count
adminCount = 0
url = 'https://xtools.wmflabs.org/api/project/admins_groups/zh.wikipedia'
data = requests.get(url).json()
for user in data['users_and_groups'].values():
    if 'sysop' in user:
        adminCount += 1
adminCount -= len(cfg['adminbots'])

# main
res = []
actionCount = collections.defaultdict(int)

runMonth = datetime.date.today().replace(day=1)
for i in range(12):
    runMonth += dateutil.relativedelta.relativedelta(months=-1)

    data = call_api(runMonth.year, runMonth.month)

    for user in data['users'].values():
        if 'sysop' not in user['user-groups'] or user['username'] in cfg['adminbots']:
            continue
        actionCount[user['username']] += user['total']

    for threshold in cfg['thresholds']:
        count = 0
        for value in actionCount.values():
            if value >= threshold:
                count += 1
        res.append({'x': runMonth.strftime('%Y-%m-%d'), 'y': adminCount - count, 'c': threshold})


page = pywikibot.Page(site, cfg['page'])
page.text = json.dumps(res, sort_keys=False)
page.save(summary=cfg['summary'], minor=False)
