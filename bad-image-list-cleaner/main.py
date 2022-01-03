# -*- coding: utf-8 -*-
import argparse
import json
import logging
import os
import sys

os.environ['PYWIKIBOT_DIR'] = os.path.dirname(os.path.realpath(__file__))
import pywikibot

from bad_image_list_cleaner import BadImageListCleaner
from config import config_page_name  # pylint: disable=E0611,W0614

logger = logging.getLogger('main')
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(message)s')

stdout_handler = logging.StreamHandler(sys.stdout)
stdout_handler.setLevel(logging.INFO)
stdout_handler.setFormatter(formatter)

file_handler = logging.FileHandler('bad_image_list_cleaner.log', encoding='utf8')
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)

logger.addHandler(stdout_handler)
logger.addHandler(file_handler)


parser = argparse.ArgumentParser()
parser.add_argument('--no-remove', action='store_false', dest='remove_missing')
parser.set_defaults(remove_missing=True)
args = parser.parse_args()
logger.debug(args)

os.environ['TZ'] = 'UTC'

site = pywikibot.Site()
site.login()

config_page = pywikibot.Page(site, config_page_name)
cfg = config_page.text
cfg = json.loads(cfg)
logger.debug(cfg)

if not cfg['enable']:
    exit('disabled\n')

bilc = BadImageListCleaner(site, cfg)
bilc.REMOVE_MISSING_FILES = args.remove_missing
bilc.main()
