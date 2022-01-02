# -*- coding: utf-8 -*-
import argparse
import datetime
import json
import os
import re
import time

os.environ['PYWIKIBOT_DIR'] = os.path.dirname(os.path.realpath(__file__))
import pywikibot
from bad_image_list_cleaner import BadImageListCleaner

from config import config_page_name  # pylint: disable=E0611,W0614

os.environ['TZ'] = 'UTC'

site = pywikibot.Site()
site.login()

config_page = pywikibot.Page(site, config_page_name)
cfg = config_page.text
cfg = json.loads(cfg)

if not cfg['enable']:
    exit('disabled\n')

BadImageListCleaner(site, cfg).main()
