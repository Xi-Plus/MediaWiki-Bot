# -*- coding: utf-8 -*-
import os

os.environ['PYWIKIBOT_DIR'] = os.path.dirname(os.path.realpath(__file__))
import pywikibot
import pywikibot.flow
import requests
from pywikibot.data.api import Request

from config import API  # pylint: disable=E0611


os.environ['TZ'] = 'UTC'

site = pywikibot.Site()
site.login()

token = site.tokens['csrf']

with open('list.txt', 'r', encoding='utf8') as f:
    for topicid in f:
        topicid = topicid.strip()
        print(topicid)
        topic = requests.get(API, params={
            'action': 'flow',
            'format': 'json',
            'submodule': 'view-topic',
            'page': topicid,
            'vtformat': 'wikitext',
        }).json()

        for revisionId, reply in topic['flow']['view-topic']['result']['topic']['revisions'].items():
            if reply['content']['format'] != 'wikitext':
                continue
            postId = reply['postId']
            print('postId', postId)
            print('revisionId', revisionId)
            oldtext = reply['content']['content']

            # tech new 2019-46
            newtext = oldtext.replace(
                "{{{{{|safesubst:}}}Technews-zh/2|2019|46}}",
                "維基媒體技術社群發出最新'''[[m:Special:MyLanguage/Tech/News|技術新聞]]'''。請告知其他用戶以下變更。當然，未必所有變更都會影響閣下。[[m:Special:MyLanguage/Tech/News/2019/46|翻譯本於此]]。")

            if oldtext == newtext:
                print('no changed')
                continue

            pywikibot.showDiff(oldtext, newtext)
            save = input('Save?')

            if save.lower() in ['', 'y', 'yes']:
                data = {
                    'action': 'flow',
                    'submodule': 'edit-post',
                    'page': topicid,
                    'eppostId': postId,
                    'epprev_revision': revisionId,
                    'epcontent': newtext,
                    'token': token,
                    'format': 'json',
                }

                res = Request(site=site, parameters=data).submit()
                print(res)
