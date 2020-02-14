# -*- coding: utf-8 -*-
from util import Action

SUMMARY = '不當用戶名'
SUMMARY_SUFFIX = 'Bot: '
USER_AGENT = ''

bad_names = [
    {'pattern': r'mail', 'action': Action.BLOCK},
    {'pattern': r'mail', 'action': Action.BLOCK & Action.BLOCK_NOMAIL},
    {'pattern': r'talk', 'action': Action.BLOCK & Action.BLOCK_NOTALK},
    {'pattern': r'report', 'action': Action.REPORT},
]

DB = {
    'host': 'localhost',
    'user': '',
    'pass': '',
    'db': '',
    'charset': 'utf8mb4',
    'table': '',
}
