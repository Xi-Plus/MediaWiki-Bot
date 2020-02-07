# -*- coding: utf-8 -*-
import argparse
import json
import os
import re

os.environ['PYWIKIBOT_DIR'] = os.path.dirname(os.path.realpath(__file__))
import pywikibot
from config import config_page_name  # pylint: disable=E0611,W0614


ACTION_WHITE_ADD = 'add'
ACTION_WHITE_REMOVE = 'remove'
ACTION_BLACK_ADD = 'badd'

parser = argparse.ArgumentParser()
parser.add_argument('black')
parser.add_argument('white')
parser.add_argument('action', choices=[ACTION_WHITE_ADD, ACTION_WHITE_REMOVE, ACTION_BLACK_ADD])
parser.add_argument('username')
parser.add_argument('diffid')
args = parser.parse_args()
print(args)

USERNAME = args.username
ACTION = args.action
BLACK = args.black
WHITE = args.white
DIFFID = args.diffid

os.environ['TZ'] = 'UTC'

site = pywikibot.Site()
site.login()

config_page = pywikibot.Page(site, config_page_name)
cfg = config_page.text
cfg = json.loads(cfg)
print(json.dumps(cfg, indent=4, ensure_ascii=False))

if not cfg['enable']:
    exit('disabled\n')

USERNAME = pywikibot.User(site, USERNAME).username
USERREGEX = r'^User( talk)?:{}(\/|$)'.format(re.escape(USERNAME))

blackpage = pywikibot.Page(site, BLACK)
whitepage = pywikibot.Page(site, WHITE)

blackdata = json.loads(blackpage.text)
whitedata = json.loads(whitepage.text)


def get_list(data):
    result = []
    for item in data['targets']:
        result.append(item['title'])
    return result


blacklist = get_list(blackdata)
whitelist = get_list(whitedata)


def check_on_list(regex, titlelist):
    for title in titlelist:
        if re.search(regex, title):
            return True
    return False


on_black = check_on_list(USERREGEX, blacklist)
on_white = check_on_list(USERREGEX, whitelist)
print('Username: {}, Action: {}, On blacklist: {}, On Whitelist: {}'.format(USERNAME, ACTION, on_black, on_white))

summary = ''
edit_black = False
edit_white = False

if ACTION == ACTION_WHITE_ADD and on_black:
    print('Removing user from blacklist')
    for i in range(len(blackdata['targets']) - 1, -1, -1):
        if re.search(USERREGEX, blackdata['targets'][i]['title']):
            del blackdata['targets'][i]
    summary = cfg['summary_add'].format('User:{}'.format(USERNAME), DIFFID)
    edit_black = True

elif ACTION == ACTION_WHITE_REMOVE and not on_white and not on_black:
    print('Adding user to blacklist')
    blackdata['targets'].append({'title': 'User:{}'.format(USERNAME)})
    summary = cfg['summary_remove'].format('User:{}'.format(USERNAME), DIFFID)
    edit_black = True

elif ACTION == ACTION_BLACK_ADD and on_white:
    print('Removing user from whitelist')
    for i in range(len(whitedata['targets']) - 1, -1, -1):
        if re.search(USERREGEX, whitedata['targets'][i]['title']):
            del whitedata['targets'][i]
    summary = cfg['summary_black_add'].format('User:{}'.format(USERNAME), DIFFID)
    edit_white = True

else:
    print('Nothing to do')
    exit()


if edit_black:
    text = json.dumps(blackdata, ensure_ascii=False, indent=4)
    pywikibot.showDiff(blackpage.text, text)
    blackpage.text = text
    print(summary)
    blackpage.save(summary=summary, minor=False)
elif edit_white:
    text = json.dumps(whitedata, ensure_ascii=False, indent=4)
    pywikibot.showDiff(whitepage.text, text)
    whitepage.text = text
    print(summary)
    whitepage.save(summary=summary, minor=False)
