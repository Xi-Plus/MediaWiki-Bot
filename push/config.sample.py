# -*- coding: utf-8 -*-
import os

BASEDIR = os.path.dirname(os.path.abspath(__file__))

cfg = {}

cfg['source'] = {
    'gadgetlocal': '/home/user/sample/',
    'gadgetgithub': 'https://raw.githubusercontent.com/user/repo/master/',
}

cfg['target'] = {
    'sample': 'User:Example/sample/',
    'gadget': 'User:Example/gadget/',
}

cfg['web'] = {
    'meta': {
        'bot': False,
        'minor': False,
        'nocreate': False,
    },
    'zhwp': {
        'bot': False,
        'minor': False,
        'nocreate': False,
    },
}

cfg['project'] = {
    'sample': {
        'source': [
            'gadgetlocal',
            'gadgetgithub',
        ],
        'target': [
            'sample',
            'gadget',
        ],
        'web': [
            'meta',
            'zhwp',
        ],
        'summary': 'deploy new feature',
        'files': {
            'sample.js': 'sample.js',
        }
    },
}
