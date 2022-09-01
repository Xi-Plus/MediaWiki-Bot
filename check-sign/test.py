from edit import warn_user
import os
BASEDIR = os.path.dirname(os.path.realpath(__file__))
os.environ['PYWIKIBOT_DIR'] = BASEDIR
import pywikibot
from config import CONFIG_PAGE_NAME
import json

site = pywikibot.Site('zh', 'wikipedia')
site.login()

config_page = pywikibot.Page(site, CONFIG_PAGE_NAME)
cfg = config_page.text
cfg = json.loads(cfg)

warn_user(
    site,
    username='A2093064-test',
    sign='[[User:A2093064-test|A2093064-test]]（[[User talk:A2093064-test|Talk]]）',
    warns={'Uw-sign-toolong'},
    cfg=cfg
)
# rev = get_rev_text(site, 73382287)
# print(rev)
