#!/usr/bin/env python
# coding: utf-8

import re

import pymysql
import pywikibot

from config import host, password, user  # pylint: disable=E0611,W0614

site = pywikibot.Site('zh', 'wikipedia')
site.login()


conn = pymysql.connect(
    host=host,
    user=user,
    password=password,
    charset="utf8"
)

with conn.cursor() as cur:
    cur.execute('use zhwiki_p')
    cur.execute("""
        SELECT ct_rev_id, user_name, ug_group, comment_text, page_namespace, page_title
        FROM (
            SELECT *
            FROM change_tag
            WHERE ct_tag_id = 1
            ORDER BY ct_id DESC
            LIMIT 5000
        ) change_tag
        LEFT JOIN revision ON ct_rev_id = rev_id
        LEFT JOIN actor ON rev_actor = actor_id
        LEFT JOIN user ON actor_user = user_id
        LEFT JOIN user_groups ON user_id = ug_user AND ug_group IN ('patroller', 'sysop')
        LEFT JOIN comment ON rev_comment_id = comment_id
        LEFT JOIN page ON rev_page = page_id
    """)
    res = cur.fetchall()


def parse_type(summary, ns, title):
    # arv
    if ns == 4 and title == '元維基用戶查核請求' and re.search(r'^(報告|报告)', summary):
        return 'arv', 'reportrfcu'
    if ns == 3 and re.search(r'通知用戶查核請求|通知用户查核请求', summary):
        return 'arv', 'noticerfcu'
    if ns == 4 and title == '当前的破坏' and re.search(r'^(報告|报告)', summary):
        return 'arv', 'reportaiv'
    if ns == 4 and title == '需要管理員注意的用戶名' and re.search(r'^(报告|新提報|新提报)', summary):
        return 'arv', 'reportuaa'

    # batch
    if re.search(r'移除已被刪除檔案', summary):
        return 'batch', 'delete'

    # block
    if ns == 3 and re.search(r'{{uw-(ublock|block1|block2|block3|vblock|dblock|3block)|{{blocked proxy}}', summary):
        return 'block', 'notice'
    if ns == 2 and re.search(r'(標記被永久封[禁鎖]的用戶頁|标记被永久封禁的用户页)', summary):
        return 'block', 'taguser'

    # close
    CLOSEREASON = (
        r'((轉移至|转移至)(維基導遊|維基詞典|维基共享资源|其他維基計劃)|快速保留|請求理由消失|请求理由消失|重定向|请求无效|請求無效|保留|删除|刪除|提删者未取得提删资格'
        + r'|提刪者未取得提刪資格|移动|并入|併入|轉交侵權|转交侵权|无共识|重複提出|移動|無共識|重复提出|目标页面或档案不存在，无效)'
    )
    if (ns == 4 and re.search(r'^(頁面存廢討論|檔案存廢討論)/記錄/', title)
            and re.search(CLOSEREASON, summary)):
        return 'close', 'close'
    if re.search(r'Wikipedia:(頁面存廢討論|檔案存廢討論)/記錄/\d+/\d+/\d+\]\]：.*' + CLOSEREASON, summary):
        return 'close', 'tagtalk'
    if re.search(r'(存廢討論關閉|存废讨论关闭)：', summary):
        return 'close', 'rmtem'

    # config
    if ns == 2 and re.search(r'(保存Twinkle参数设置|儲存Twinkle偏好設定)', summary):
        return 'config', 'config'

    # copyvio
    if ns == 4 and title == '頁面存廢討論/疑似侵權' and re.search(r'(添加|加入)\[\[', summary):
        return 'copyvio', 'report'
    if ns == 3 and re.search(r'通知：[页頁]面.+(疑似侵犯版权|疑似侵犯版權)', summary):
        return 'copyvio', 'notice'
    if re.search(r'(本頁面疑似侵犯版權|本页面疑似侵犯版权)', summary):
        return 'copyvio', 'tag'

    # fluff
    if re.search(r'^(回退|撤销|还原)', summary):
        return 'fluff', 'fluff'
        # if '回退到由' in summary:
        #     return 'fluff', 'torev'
        # if '做出的最后一个修订版本' in summary:
        #     return 'fluff', 'norm'

    # image
    if ns == 4 and title == '檔案存廢討論/快速刪除提報' and re.search(r'^(添加|加入)', summary):
        return 'image', 'report'

    # protect
    if ns == 4 and title == '请求保护页面' and re.search(r'请求对.+保护', summary):
        return 'protect', 'request'
    if ns == 4 and title == '请求保护页面' and re.search(r'(半|全)(保護|保护)', summary):
        return 'protect', 'close'
    if re.search(r'移除保護模板|(加入|添加){{pp-', summary):
        return 'protect', 'tag'
    if re.search(r'已保护|移除保护|保护等级', summary):
        return 'protect', 'protect'

    # speedy
    if ns == 2 and re.search(r'(记录对|記錄對).+(的快速删除提名|的快速刪除提名)', summary):
        return 'speedy', 'record'
    if ns == 3 and re.search(r'通知：.+(快速删除提名|快速刪除提名)', summary):
        return 'speedy', 'notice'
    if re.search('(请求|請求).*(快速删除|快速刪除)', summary):
        return 'speedy', 'tag'

    # tag
    if ns in [0, 4, 10, 118] and re.search(r'(添加|加入|移除).+(标记|標記)', summary):
        return 'tag', 'tag'
    if (ns == 6 or (ns == 4 and title == '沙盒')) and re.search(r'^添加{{', summary):
        return 'tag', 'tag'
    if ns == 4 and title == '关注度/提报' and re.search(r'(添加|加入)\[\[', summary):
        return 'tag', 'reportnp'
    if ns == 1 and re.search(r'(请求|請求).+(合并|合併)', summary):
        return 'tag', 'mergetagtalk'
    if ns == 1 and re.search(r'(请求移动至|請求移動至)', summary):
        return 'tag', 'movetagtalk'

    # talkback
    if ns == 3 and re.search(r'(回复通告|回覆通告|通知：有新郵件|有關.+的通知)', summary):
        return 'talkback', 'talkback'

    # unlink
    if re.search(r'(注释出文件使用|取消链接到)', summary):
        return 'unlink', 'unlink'

    # warn
    if ns == 3 and re.search(r'((層級|层级)(1|2|3|4|4im)|单层级通知|單層級通知|单层级警告|單層級警告|提示)：|您翻譯的質量有待改善', summary):
        return 'warn', 'warn'

    # xfd
    if ns == 4 and re.search(r'^(頁面存廢討論|檔案存廢討論)/記錄/', title) and re.search(r'(添加|加入)\[\[', summary):
        return 'xfd', 'report'
    if ns == 3 and re.search(r'通知：(页面|文件).+存废讨论提名', summary):
        return 'xfd', 'notice'
    if re.search(r'(页面存废讨论|頁面存廢討論|檔案存廢討論|文件存废讨论)：', summary):
        return 'xfd', 'tag'

    return 'unknown', 'unknown'


user_branch = {}
users_in_branch = {}
edits_in_branch = {}


def check_branch_from_js(user):
    page = pywikibot.Page(site, 'User:{}/common.js'.format(user))
    if not page.exists():
        return 'gadget'

    text = page.text
    if 'Xiplus/Twinkle.js' in text:
        return 'xiplus'
    m = re.search(r'User:(.+?)/Twinkle.js', text)
    if m:
        return m.group(1)
    return 'gadget'


def get_branch(user):
    if user not in user_branch:
        branch = check_branch_from_js(user)
        if branch not in users_in_branch:
            users_in_branch[branch] = []
            edits_in_branch[branch] = 0
        user_branch[user] = branch
        users_in_branch[branch].append(user)

    return user_branch[user]


record = {}
alltypes = set()
ignore = 0
printunknownbranch = []
user_group = {}
for row in res:
    if row[1] is None or row[3] is None:
        # print('ignore', row)
        ignore += 1
        continue

    revid = row[0]
    user = row[1].decode()
    group = row[2].decode() if row[2] else ''
    summary = row[3].decode()
    ns = row[4]
    title = row[5].decode()

    user_group[user] = group

    atype = parse_type(summary, ns, title)
    if atype == ('unknown', 'unknown'):
        print(revid, atype, summary, ns, title, user)
    # if get_branch(user) == 'unknown':
    #     if user not in printunknownbranch:
    #         print('unknown branch', user)
    #         printunknownbranch.append(user)

    if user not in record:
        record[user] = {}
        record[user]['total'] = 0
    if atype not in record[user]:
        record[user][atype] = 0
    record[user][atype] += 1
    record[user]['total'] += 1
    alltypes.add(atype)
print('ignore', ignore)
# print(record)


alltypes = sorted(alltypes)
record = sorted(record.items(), key=lambda v: v[1]['total'], reverse=True)
# print(record)


text = """* [https://paws-public.wmflabs.org/paws-public/User:Xiplus/Twinkle%20usage.ipynb 來源]
* 本表分析了過去5000筆帶有[{} Twinkle標籤]的操作，根據摘要分析該操作屬於哪個功能
* 由於無法檢查已刪編輯，所以speedy-tag及相同性質的數據極度不正確
* 使用版本是檢查common.js而產生，不一定正確
""".format(
    'https://zh.wikipedia.org/w/index.php?hidebots=1&hideWikibase=1&tagfilter=Twinkle&limit=500&days=30&title=Special:%E6%9C%80%E8%BF%91%E6%9B%B4%E6%94%B9&urlversion=2')

text += """{| class="wikitable sortable"
!用戶
!身分
!使用版本
!總和"""


for atype in alltypes:
    text += '\n! {}<br>{}'.format(atype[0], atype[1])

for user, userrecord in record:
    text += '\n|-'
    text += '\n'
    text += '| {} |'.format(user)
    text += '| {} |'.format(user_group[user])
    text += '| v_{} |'.format(get_branch(user))
    text += '| {} |'.format(userrecord['total'])
    edits_in_branch[get_branch(user)] += userrecord['total']
    for atype in alltypes:
        if atype in userrecord:
            text += '| {} |'.format(userrecord[atype])
        else:
            text += '| |'
text += "\n|}\n\n"

text += """{| class="wikitable sortable"
!使用版本
!人數
!編輯數"""
for branch in users_in_branch:
    text += '\n|-'
    text += '\n'
    text += '| {} || {} || {}'.format(
        branch,
        len(users_in_branch[branch]),
        edits_in_branch[branch]
    )
text += "\n|}"

print(text)


page = pywikibot.Page(site, "User:Xiplus/Twinkle使用統計")
page.text = text
page.save(summary="機器人：更新使用統計", minor=False)
