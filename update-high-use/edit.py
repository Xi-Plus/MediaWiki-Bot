# -*- coding: utf-8 -*-
import argparse
import json
import os
import re

import pymysql
os.environ['PYWIKIBOT_DIR'] = os.path.dirname(os.path.realpath(__file__))
import pywikibot
from config import config_page_name, database  # pylint: disable=E0611,W0614


os.environ['TZ'] = 'UTC'

site = pywikibot.Site()
site.login()

config_page = pywikibot.Page(site, config_page_name)
cfg = config_page.text
cfg = json.loads(cfg)
print(json.dumps(cfg, indent=4, ensure_ascii=False))

if not cfg['enable']:
    exit('disabled\n')

db = pymysql.connect(host=database['host'],
                     user=database['user'],
                     passwd=database['passwd'],
                     db=database['db'],
                     charset=database['charset'])
cur = db.cursor()


def get_new_usage(templatename):
    cur.execute("""SELECT `count` FROM `{}` WHERE `wiki` = 'zhwiki' AND `title` = %s""".format(database['table']), (templatename))
    row = cur.fetchone()
    if row is None:
        return None
    return row[0]


def maintain_doc(text):
    text = re.sub(r'<includeonly><!-- 在這裡加入模板的保護標識 --></includeonly>', '', text)
    text = re.sub(r'<includeonly>\s*</includeonly>', '', text)
    return text


def update(templatename, dry_run=False, add_template=False, check=False):
    templatename = pywikibot.Page(site, templatename).title()
    print('Checking {}'.format(templatename))

    templatedoc = pywikibot.Page(site, '{}/doc'.format(templatename))

    if not templatedoc.exists():
        print('\t/doc is not exists')
        return

    if templatedoc.title() in cfg['whitelist']:
        print('\tTemplate in whitelist, Skip')
        return

    new_usage = get_new_usage(templatename)
    if new_usage is None:
        print('Cannot get new usage')
        return

    text = templatedoc.text
    m = re.search(r'{{\s*(?:High-use|High-risk|高風險模板|高风险模板|U!|High[ _]use)\s*\|\s*([0-9,+]+|)\s*(?:\||}})', text, flags=re.I)
    if m:
        old_usage = m.group(1)
        old_usage = re.sub(r'[,+]', '', old_usage)
        try:
            old_usage = int(old_usage)
        except ValueError:
            old_usage = 1
        diff = (new_usage - old_usage) / old_usage
        print('\tUsage: Old: {}, New: {}, Diff: {:+.1f}%'.format(old_usage, new_usage, diff * 100))
        if abs(diff) > cfg['diff_limit']:
            print('\tUpdate template usage to {}'.format(new_usage))
            text = re.sub(r'({{\s*(?:High-use|High-risk|高風險模板|高风险模板|U!|High[ _]use)\s*\|)\s*(?:[0-9,+]+|)\s*(\||}})', r'\g<1>{}\g<2>'.format(new_usage), text, flags=re.I)
            text = maintain_doc(text)

            summary = cfg['summary'].format(new_usage)

            pywikibot.showDiff(templatedoc.text, text)
            templatedoc.text = text
            print('\t', summary)
            if not dry_run:
                if check and input('Save?').lower() not in ['', 'y', 'yes']:
                    return
                templatedoc.save(summary=summary, minor=False)
        else:
            print('\tNot reach diff_limit')
    elif add_template:
        m2 = re.search(r'{{\s*(Template[ _]doc page viewed directly|內聯模板文件|内联模板文件|Template[ _]doc inline|内联模板文档|內聯模板文檔|Documentation[ _]subpage)\s*(\||}})', text, flags=re.I)
        templatetext = '{{{{High-use|{}}}}}\n'.format(new_usage)
        if m2:
            text = re.sub(
                r'({{\s*(?:Template[ _]doc page viewed directly|內聯模板文件|内联模板文件|Template[ _]doc inline|内联模板文档|內聯模板文檔|Documentation[ _]subpage)\s*(?:\||}}).*\n)',
                r'\1{}'.format(templatetext),
                text,
                flags=re.I,
            )
        else:
            text = templatetext + text
        text = maintain_doc(text)

        summary = cfg['summary_insert'].format(new_usage)

        pywikibot.showDiff(templatedoc.text, text)
        templatedoc.text = text
        print('\t', summary)
        if not dry_run:
            if check and input('Save?').lower() not in ['', 'y', 'yes']:
                return
            templatedoc.save(summary=summary, minor=False)
    else:
        print('\tCaanot get old usage')


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('template', nargs='?')
    parser.add_argument('--dry-run', action='store_true', dest='dry_run')
    parser.add_argument('-a', '--add', action='store_true', dest='add')
    parser.add_argument('-c', '--check', action='store_true', dest='check')
    parser.set_defaults(dry_run=False, add=False, check=False)
    args = parser.parse_args()
    print(args)

    if args.template:
        update(args.template, dry_run=args.dry_run, add_template=args.add, check=args.check)
    else:
        highusetem = pywikibot.Page(site, cfg['highuse_template'])
        for page in highusetem.embeddedin(namespaces=[10, 828]):
            title = page.title()
            if re.search(cfg['skip_titles'], title):
                continue

            update(title, dry_run=args.dry_run)
