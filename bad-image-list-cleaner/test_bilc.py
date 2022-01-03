# -*- coding: utf-8 -*-
import os
import unittest

from bad_image_list_cleaner import BadImageListCleaner

os.environ['PYWIKIBOT_DIR'] = os.path.dirname(os.path.realpath(__file__))
import pywikibot


class TestBILC(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        site = pywikibot.Site()
        site.login()
        self.bilc = BadImageListCleaner(site, {})

    def test_fix_redirect(self):
        self.assertEqual(self.bilc.process_text(
            '* [[:File:Example.jpg]] except on [[Wikipedia]]',
            []
        ),
            '* [[:File:Example.jpg]] except on [[维基百科]]'
        )

    def test_remove_not_exists_page_single(self):
        self.assertEqual(self.bilc.process_text(
            '* [[:File:Example.jpg]] except on [[Not exists page]]',
            []
        ),
            '* [[:File:Example.jpg]]'
        )

    def test_remove_not_exists_page_some(self):
        self.assertEqual(self.bilc.process_text(
            '* [[:File:Example.jpg]] except on [[维基百科]], [[Not exists page]], [[中文维基百科]]',
            []
        ),
            '* [[:File:Example.jpg]] except on [[维基百科]], [[中文维基百科]]'
        )

    def test_not_exists_file(self):
        self.assertEqual(self.bilc.process_text(
            '* [[:File:Not exists file.jpg]] except on [[维基百科]]',
            []
        ),
            ''
        )

    def test_merge_new(self):
        self.assertEqual(self.bilc.process_text(
            '''== English Wikipedia ==
{}
== Other =='''.format(self.bilc.INSERT_FLAG),
            ['File:Shiroisuna no Akuatopu Key Visual.jpg']
        ),
            '''== English Wikipedia ==
* [[:File:Shiroisuna no Akuatopu Key Visual.jpg]] except on [[白沙的Aquatope]]
{}
== Other =='''.format(self.bilc.INSERT_FLAG)
        )

    def test_merge_exists(self):
        self.assertEqual(self.bilc.process_text(
            '''== English Wikipedia ==
* [[:File:Shiroisuna no Akuatopu Key Visual.jpg]] except on [[白沙的Aquatope]]
{}
== Other =='''.format(self.bilc.INSERT_FLAG),
            ['File:Shiroisuna no Akuatopu Key Visual.jpg']
        ),
            '''== English Wikipedia ==
* [[:File:Shiroisuna no Akuatopu Key Visual.jpg]] except on [[白沙的Aquatope]]
{}
== Other =='''.format(self.bilc.INSERT_FLAG)
        )

    def test_new_line(self):
        self.assertEqual(self.bilc.process_text(
            '''Foo

Bar''',
            []
        ),
            '''Foo

Bar'''
        )


if __name__ == '__main__':
    unittest.main()
