import argparse
import logging
import os
import re

import pymysql
os.environ['PYWIKIBOT_DIR'] = os.path.dirname(os.path.realpath(__file__))
import pywikibot

from config import DB, SUMMARY, SUMMARY_SUFFIX, bad_names  # pylint: disable=E0611,W0614
from util import Action


os.environ['TZ'] = 'UTC'

site = pywikibot.Site()
site.login(sysop=True)


db = pymysql.connect(host=DB['host'],
                     user=DB['user'],
                     passwd=DB['pass'],
                     db=DB['db'],
                     charset=DB['charset'])
cur = db.cursor()


def insert_log(log):
    cur.execute("""INSERT INTO `{}` (`log`) VALUES (%s)""".format(DB['table']), (log))
    db.commit()


def do_report(username):
    print('do_report', username)


def do_block(username, flag, summary):
    print('do_block', username, flag, summary)

    try:
        noemail = bool(flag & Action.BLOCK_NOMAIL)
        allowusertalk = not bool(flag & Action.BLOCK_NOTALK)

        user = pywikibot.User(site, username)

        result = site.blockuser(
            user=user,
            expiry='infinite',
            reason=summary,
            nocreate=True,
            autoblock=True,
            noemail=noemail,
            allowusertalk=allowusertalk,
        )
        msg = 'block result: {}'.format(result)
        logging.info(msg)
        insert_log(msg)
    except Exception as e:
        msg = 'error when block: {}'.format(e)
        logging.error(msg)
        insert_log(msg)


def check_username(username, dry_run):
    insert_log('checking {}'.format(username))
    action = Action.NOTHING
    summary = SUMMARY
    for bad_name in bad_names:
        if re.search(bad_name['pattern'], username):
            action |= bad_name['action']
            if 'summary' in bad_name:
                summary = bad_name['summary']

    print(username, action)
    insert_log('check {} result: {}'.format(username, action))

    if dry_run:
        print('dry_run')
        return

    if action & Action.BLOCK:
        # do block
        do_block(username, action, summary + SUMMARY_SUFFIX)

    elif action & Action.REPORT:
        # do report
        do_report(username)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('username')
    parser.add_argument('--dry-run', action='store_true')
    parser.set_defaults(dry_run=False)
    args = parser.parse_args()
    print(args)

    check_username(args.username, args.dry_run)
