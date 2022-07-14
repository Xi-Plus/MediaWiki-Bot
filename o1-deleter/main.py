# -*- coding: utf-8 -*-
import argparse
import datetime
import json
import os
import re
import time

os.environ['PYWIKIBOT_DIR'] = os.path.dirname(os.path.realpath(__file__))
import pywikibot

from config import config_page_name  # pylint: disable=E0611,W0614

os.environ['TZ'] = 'UTC'

site = pywikibot.Site()
site.login()

config_page = pywikibot.Page(site, config_page_name)
cfg = config_page.text
cfg = json.loads(cfg)

if not cfg['enable']:
    print('disabled')
    exit()


def deletePage(page, args):
    print(page.title())

    # 頁面已刪
    if not page.exists():
        return 'deleted'

    # 檢查機器人是否應該編輯
    if not page.botMayEdit():
        return 'bot should not edit'

    # 必須位於使用者命名空間
    if page.namespace().id not in [2]:
        return 'not in user namespace'

    # 不處理 .js/.css/.json
    if re.search(r'\.(js|css|json)$', page.title()):
        return 'not work on js/cs/json'

    text = page.text

    # 檢查刪除標記
    if not re.search(r'{{\s*(Delete|Db-reason|D|Deletebecause|Db|速删|速刪|Speedy|SD|快删|快刪|CSD|QD)\s*\|\s*(O1|G10)\s*}}', text, flags=re.I):
        return 'cannot find o1 template'

    logs = list(site.logevents(page=page, total=1, logtype='create'))
    if len(logs) == 0:
        return 'no logs'

    createLog = logs[0]
    if createLog.pageid() != page.pageid:
        return 'not create on the same name'

    lastTimestamp = page.editTime().replace(tzinfo=datetime.timezone.utc).timestamp()
    if time.time() - lastTimestamp < 10 * 60:
        return 'last edit in 10 mins'

    owner = re.sub(r'^([^/]+).*$', r'\1', page.title(with_ns=False))

    if len(set(page.contributors().keys()) - set([owner]) - set(cfg['bots'])) > 0:
        return 'there are others edits'

    if args.check and input('Delete? ').lower() not in ['', 'y', 'yes']:
        return 'this should be deleted but cancelled'

    if args.dry_run:
        return 'this should be deleted'

    page.delete(reason=cfg['summary'], prompt=False)
    return 'page deleted'


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('page', nargs='?')
    parser.add_argument('-c', '--check', action='store_true', dest='check')
    parser.add_argument('--dry_run', action='store_true', dest='dry_run')
    parser.set_defaults(check=False, dry_run=False)
    args = parser.parse_args()

    pages = []
    if args.page:
        pages = [pywikibot.Page(site, args.page)]
    else:
        cat = pywikibot.Page(site, cfg['csd_category'])
        pages = site.categorymembers(cat)

    for page in pages:
        res = deletePage(page, args)
        if args.dry_run:
            print('\t', res)
