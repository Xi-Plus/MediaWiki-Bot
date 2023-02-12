# -*- coding: utf-8 -*-
import argparse
import itertools
import json
import logging
import os
import re
import sys
import uuid

os.environ['PYWIKIBOT_DIR'] = os.path.dirname(os.path.realpath(__file__))
import pywikibot
from pywikibot.data.api import Request
from config import config_page_name  # pylint: disable=E0611,W0614

os.environ['TZ'] = 'UTC'


class MarkItntalk:
    PLACEHOLDER = str(uuid.uuid1())

    def __init__(self, last_time_path, config_page_name, args):
        self.last_time_path = last_time_path
        self.config_page_name = config_page_name
        self.args = args

        self.site = pywikibot.Site()
        self.site.login()

        self.logger = logging.getLogger('mark_itntalk')
        formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(message)s')
        stdout_handler = logging.StreamHandler(sys.stdout)
        stdout_handler.setFormatter(formatter)
        self.logger.addHandler(stdout_handler)

        config_page = pywikibot.Page(self.site, config_page_name)
        self.cfg = json.loads(config_page.text)
        self.logger.debug('config: %s', json.dumps(self.cfg, indent=4, ensure_ascii=False))

    def read_last_time(self):
        try:
            with open(self.last_time_path, 'r') as f:
                last_time = f.read().strip()
        except FileNotFoundError:
            self.logger.warning('last_time.txt not found, use now time instead')
            last_time = pywikibot.Timestamp.now().isoformat()
            self.write_last_time(last_time)
        return last_time

    def write_last_time(self, last_time):
        with open(self.last_time_path, 'w') as f:
            f.write(last_time)

    def parse_wikitext(self, wikitext):
        result = set()
        rows = re.findall(r'^(?:{{\*mp\|.*?}}|\*)\s*(.*?)\n', wikitext, flags=re.M)
        for row in rows:
            pages = re.findall(r"'''\[\[([^|\]]+?)(?:\|[^\]]+)?\]\]'''", row)
            if len(pages) == 1:
                result.add(pages[0].strip())
        return result

    def convert_title(self, title):
        r = Request(site=self.site, parameters={
            'action': 'query',
            'format': 'json',
            'formatversion': 2,
            'titles': title,
            'redirects': 1,
            'converttitles': 1,
        })
        data = r.submit()
        new_title = data['query']['pages'][0]['title']
        return new_title

    def mark_talkpage(self, article_title, timestamp: pywikibot.Timestamp, oldid):
        article_title = self.convert_title(article_title)
        article_page = pywikibot.Page(self.site, article_title)
        if not article_page.exists():
            logger.warning('%s is not exists', article_title)
            return

        if article_page.isRedirectPage():
            logger.warning('%s is redirect to %s', article_title, article_page.getRedirectTarget().title())
            article_page = article_page.getRedirectTarget()

        talk_page = article_page.toggleTalkPage()
        new_param_year = timestamp.strftime('%Y年')
        new_param_date = timestamp.strftime('{}月{}日'.format(timestamp.month, timestamp.day))
        logger.info('mark %s %s %s %s %s', talk_page.title(), new_param_year, new_param_date, timestamp.isoformat(), oldid)

        new_text = talk_page.text

        template_name = 'ITNtalk'
        all_dates = []
        other_params = {}

        for title, params in talk_page.raw_extracted_templates:
            if re.search(r'^(ITNtalk|ITN[ _]+talk|新聞|新闻)$', title, flags=re.I):
                template_name = title
                # process numbered and oldid params
                for key in itertools.count(1, 2):
                    key1 = str(key)
                    key2 = str(key + 1)
                    keyid = 'oldid{}'.format(key // 2 + 1)
                    if key1 in params and key2 in params:
                        params[key1] = params[key1].strip()
                        params[key2] = params[key2].strip()
                        # Handle wrong format
                        if re.search(r'^\d+$', params[key1]):
                            params[key1] = params[key1] + '年'

                        try:
                            exist_date = pywikibot.Timestamp.strptime(params[key1] + params[key2], '%Y年%m月%d日')
                            if abs(exist_date.timestamp() - timestamp.timestamp()) < 86400 * 7:
                                logger.info('already exists: %s %s', params[key1], params[key2])
                                return
                            sort_key = exist_date.isoformat()
                        except Exception:
                            logger.warning('invalid date: %s %s', params[key1], params[key2])
                            sort_key = 'bad_date'
                        if keyid in params:
                            all_dates.append((sort_key, params[key1], params[key2], params[keyid]))
                        else:
                            all_dates.append((sort_key, params[key1], params[key2]))
                    else:
                        break
                # process other params
                for key in params:
                    if not re.search(r'^(oldid)?\d+$', key):
                        other_params[key] = params[key]

        # append new params
        all_dates.append((timestamp.isoformat(), new_param_year, new_param_date, oldid))
        all_dates.sort()

        logger.debug('all_dates: %s', all_dates)
        logger.debug('other_params: %s', other_params)

        # replace first tempalte
        new_text, sub_cnt = re.subn(r'{{\s*(ITNtalk|ITN[ _]+talk|新聞|新闻)\s*\|[^}]+?}}', self.PLACEHOLDER, new_text, flags=re.I, count=1)
        if sub_cnt == 0:
            new_text = self.PLACEHOLDER + '\n' + new_text
        # replace other templates
        new_text, sub_cnt = re.subn(r'{{\s*(ITNtalk|ITN[ _]+talk|新聞|新闻)\s*\|[^}]+?}}\n?', '', new_text, flags=re.I)

        new_template = '{{' + template_name
        # build dates
        for idx, date in enumerate(all_dates, 1):
            if len(date) == 3:
                new_template += '|{}|{}'.format(date[1], date[2])
            elif len(date) == 4:
                new_template += '|{}|{}|oldid{}={}'.format(date[1], date[2], idx, date[3])
        # build other params
        for key, value in other_params.items():
            new_template += '|{}={}'.format(key, value)
        new_template += '}}'

        new_text, sub_cnt = re.subn(self.PLACEHOLDER, new_template, new_text, count=1)
        if sub_cnt == 0:
            logger.error('failed to replace template')
            return

        if self.args.confirm or self.args.loglevel <= logging.DEBUG:
            pywikibot.showDiff(talk_page.text, new_text)

        summary = self.cfg['summary'].format(oldid)

        save = True
        if self.args.confirm:
            save = pywikibot.input_yn('Save changes with oldid {} ?'.format(oldid), 'Y')
        if save:
            logger.debug('save changes')
            talk_page.text = new_text
            talk_page.save(summary=summary, minor=False, asynchronous=True)
        else:
            logger.debug('skip save')

    def main(self):
        if not self.cfg['enable']:
            logging.warning('disabled')
            exit()

        itnpage = pywikibot.Page(self.site, 'Template:Itn')
        last_time = self.read_last_time()
        logger.info('read last time: %s', last_time)

        while True:
            revisions = itnpage.revisions(reverse=True, content=True, starttime=last_time, total=50)
            try:
                first_rev = next(revisions)
            except StopIteration:
                break
            old_pages = self.parse_wikitext(first_rev.text)

            new_last_time = last_time
            for rev in revisions:
                if rev.text is None:
                    logger.warning('rev %s is deleted', rev.revid)
                    continue
                new_pages = self.parse_wikitext(rev.text)
                for page in new_pages:
                    if page not in old_pages:
                        try:
                            self.mark_talkpage(page, rev.timestamp, rev.revid)
                        except pywikibot.bot_choice.QuitKeyboardInterrupt:
                            logger.warning('quitting')
                            logger.info('write last time: %s', last_time)
                            self.write_last_time(last_time)
                            return
                        old_pages.add(page)
                new_last_time = rev.timestamp.isoformat()

            if new_last_time == last_time:
                break
            last_time = new_last_time
            logger.info('write last time: %s', last_time)
            self.write_last_time(last_time)

        logger.info('done')


if __name__ == '__main__':
    BASE_DIR = os.path.dirname(os.path.realpath(__file__))
    LAST_TIME_PATH = os.path.join(BASE_DIR, 'last_time.txt')

    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--confirm', action='store_true')
    parser.add_argument('-d', '--debug', action='store_const', dest='loglevel', const=logging.DEBUG, default=logging.INFO)
    args = parser.parse_args()

    mark_itntalk = MarkItntalk(LAST_TIME_PATH, config_page_name, args)
    logger = logging.getLogger('mark_itntalk')
    logger.setLevel(args.loglevel)
    logger.debug('args: %s', args)
    mark_itntalk.main()
