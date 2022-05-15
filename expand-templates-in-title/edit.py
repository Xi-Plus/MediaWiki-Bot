import argparse
import json
import os
import re

os.environ['PYWIKIBOT_DIR'] = os.path.dirname(os.path.realpath(__file__))
import pywikibot
from pywikibot.data.api import Request

from config import config_page_name  # pylint: disable=E0611,W0614

parser = argparse.ArgumentParser()
parser.add_argument('page', nargs='?')
args = parser.parse_args()

site = pywikibot.Site()
site.login()

config_page = pywikibot.Page(site, config_page_name)
cfg = config_page.text
cfg = json.loads(cfg)
print(json.dumps(cfg, indent=4, ensure_ascii=False))

if not cfg['enable']:
    exit('disabled\n')


def format_flag(idx):
    return (
        '<span>{} start</span>'.format(idx),
        '<span>{} end</span>'.format(idx),
    )


def fix_page(pagetitle):
    print('Fix', pagetitle)

    page = pywikibot.Page(site, pagetitle)
    text = page.text

    titles = re.findall(r'(^|\n)(==+)(.+?)(\2)\s*\n', text)

    raw_text = ''
    bad_titles = []
    for title in titles:
        if '{{' in title[2]:
            raw_text += format_flag(len(bad_titles))[0] + title[2] + format_flag(len(bad_titles))[1]
            bad_titles.append(title[2])

    expand_text = site.expand_text(raw_text, pagetitle, False)

    for i, title in enumerate(bad_titles):
        idx1 = expand_text.index(format_flag(i)[0])
        idx2 = expand_text.index(format_flag(i)[1])
        new_title = expand_text[idx1 + len(format_flag(i)[0]):idx2]
        text = text.replace(title, new_title)

    if page.text == text:
        return
    pywikibot.showDiff(page.text, text)

    page.text = text
    page.save(summary=cfg['summary'], minor=True)


if args.page is None:
    for pagetitle in cfg['run_pages']:
        fix_page(pagetitle)
else:
    fix_page(args.page)
