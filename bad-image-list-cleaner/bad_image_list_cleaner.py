# -*- coding: utf-8 -*-
import enum
import functools
import logging
import re
import sys
from unicodedata import normalize

import pywikibot

logger = logging.getLogger('bilc')
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


class BadImageListCleaner:
    REMOVE_MISSING_FILES = True
    INSERT_FLAG = '<!-- english wikipedia insertion point -->'
    cachedPages = {}

    def __init__(self, site, cfg):
        self.site = site
        self.cfg = cfg

    def get_en_list(self):
        badPage = pywikibot.Page(self.site, 'en:MediaWiki:Bad image list')
        text = badPage.text
        m = re.findall(r'^\* *\[\[:(File:.+?)\]\]', text, flags=re.MULTILINE)
        return m

    @functools.lru_cache()
    def check_title(self, oldTitle):
        if oldTitle in self.cachedPages:
            page = self.cachedPages[oldTitle]
        else:
            page = pywikibot.Page(self.site, oldTitle)
        if not page.exists():
            logger.debug('%s is not exists', oldTitle)
            return None
        if page.isRedirectPage():
            logger.debug('%s is a redirect', oldTitle)
            newTitle = page.getRedirectTarget().title()
            if '#' in newTitle:
                return None
            if re.search(r'^[A-Za-z _]+$', oldTitle):
                return None
            return newTitle
        return oldTitle

    @functools.lru_cache()
    def check_file_exists(self, title):
        file = pywikibot.FilePage(self.site, title)
        if file.exists():
            return file
        try:
            if file.file_is_shared():
                return file
        except Exception:
            pass
        return None

    def format_line(self, file_title, pages):
        text = '* [[:{}]]'.format(file_title)
        if len(pages) > 0:
            text += ' except on '
            text += ', '.join(['[[{}]]'.format(title) for title in pages])

        return text

    def fix_line(self, text):
        m = re.search(r'^\* *\[\[:(File:.+?)\]\]', text)
        if not m:
            return None, text

        file_title = m.group(1)
        if self.REMOVE_MISSING_FILES:
            file = self.check_file_exists(file_title)
            if not file:
                logger.debug('%s is not exists', file_title)
                return None, None
            file_title = file.title()

        m = re.search(r'except on(.+?)$', text)
        newTitles = []
        if m:
            titles = re.findall(r'\[\[([^\]|]+)\]\]', m.group(1))
            for title in titles:
                newTitle = self.check_title(title)
                if newTitle:
                    newTitles.append(newTitle)

        new_text = self.format_line(file_title, newTitles)

        return file_title, new_text

    def process_text(self, old_text, en_list):
        logger.info('process exists items')
        lines = old_text.splitlines()
        new_lines = []
        found_files = set()
        logger.info('total %s lines', len(lines))
        for idx, line in enumerate(lines, 1):
            if idx % 100 == 0:
                logger.info('run line %s', idx)

            file_title, new_line = self.fix_line(line)
            if file_title:
                found_files.add(file_title)
            if new_line is not None:  # accept empty line
                new_lines.append(new_line)
        new_text = '\n'.join(new_lines)

        logger.info('merge en list')
        try:
            pos = new_text.index(self.INSERT_FLAG)
        except ValueError:
            logger.warning('Failed to find insertion point')
            pos = None

        if pos:
            en_new_text = ''
            logger.info('total %s lines', len(en_list))
            for idx, file_title in enumerate(en_list, 1):
                if idx % 100 == 0:
                    logger.info('run line %s', idx)

                if file_title in found_files:
                    continue

                file_page = self.check_file_exists(file_title)
                if not file_page:
                    continue

                file_title = file_page.title()
                if file_title in found_files:
                    continue

                logger.debug('%s is new from enwiki', file_title)
                pages = []
                for page in file_page.usingPages():
                    pages.append(page.title())
                en_new_text += self.format_line(file_title, pages) + '\n'
                found_files.add(file_title)
            new_text = new_text[:pos] + en_new_text + new_text[pos:]

        return new_text

    def main(self):
        badPage = pywikibot.Page(self.site, 'MediaWiki:Bad image list')
        text = badPage.text
        logger.info('cache links')
        for page in badPage.linkedPages():
            self.cachedPages[page.title()] = page

        logger.info('get_en_list')
        en_list = self.get_en_list()
        logger.info('process_text')
        new_text = self.process_text(text, en_list)

        with open('temp.txt', 'w', encoding='utf8') as f:
            f.write(new_text)
        # pywikibot.showDiff(text, new_text)
        save = input('Save?')
        if save.lower() in ['y', 'yes']:
            badPage.text = new_text
            badPage.save(summary=self.cfg['summary'], minor=False, botflag=False)