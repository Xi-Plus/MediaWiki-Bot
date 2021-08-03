#!/usr/bin/env python
# coding: utf-8

import argparse
import os
import re
from datetime import date

import pymysql

os.environ['PYWIKIBOT_DIR'] = os.path.dirname(os.path.realpath(__file__))
import pywikibot
import pywikibot.cosmetic_changes
from dateutil.relativedelta import relativedelta

from config import host, password, user  # pylint: disable=E0611,W0614


parser = argparse.ArgumentParser()
parser.add_argument('--page')
parser.add_argument('--months', type=int, default=0)
args = parser.parse_args()
print(args)

title = args.page
if title is None:
    rundate = date.today() + relativedelta(months=args.months)
    title = 'Wikipedia:維基百科政策簡報/存檔/{:04}-{:02}'.format(rundate.year, rundate.month)


site = pywikibot.Site('zh', 'wikipedia')
site.login()


print(title)
page = pywikibot.Page(site, title)
if not page.exists():
    print('page is not exists')
    exit()


text = page.text

# cosmetic changes
cc_toolkit = pywikibot.cosmetic_changes.CosmeticChangesToolkit(page)
text = cc_toolkit.change(text)
text = re.sub(r'\[\[(?:Special|特殊):(?:Diff|差异|差異|编辑差异)', '[[Special:Diff', text)
text = re.sub(r'\[\[(?:Special|特殊):(?:PermanentLink|Permalink|固定链接|永久链接)', '[[Special:Permalink', text)
text = re.sub(r'\[\[(?:Special|特殊):(?:Recentchangeslinked|RelatedChanges|链出更改|鏈出更改|連出更改|最近链出更改|相关更改)/', '[[Special:链出更改/', text)

# print(text)


m = re.search(r'過去一個月（(\d+)年(\d+)月(\d+)日至(\d+)年(\d+)月(\d+)日）內', text)
if m:
    time1 = '{:04d}{:02d}{:02d}000000'.format(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    time2 = '{:04d}{:02d}{:02d}235959'.format(int(m.group(4)), int(m.group(5)), int(m.group(6)))
    print(time1, time2)
else:
    exit('Failed to get date range')


if not page.botMayEdit():
    print('page is locked')
    exit()


ignoreRevids = []


pos1 = text.index("'''方針與指引重要變動'''")
pos2 = text.index("'''其他方針與指引雜項修訂'''")
policyText = text[pos1:pos2]
# print(policyText)
for temp in re.findall(r'\[\[Special:Diff/(\d+)/(\d+)\|', policyText):
    ignoreRevids.append((int(temp[0]), int(temp[1])))

for temp in re.findall(r'\[\[Special:Permalink/(\d+)\|', policyText):
    ignoreRevids.append((0, int(temp)))

talkPage = page.toggleTalkPage()
if talkPage.exists():
    talkText = talkPage.text
    try:
        pos1 = talkText.index('<!-- bot ignore start -->')
        pos2 = talkText.index('<!-- bot ignore end -->')
        talkText = talkText[pos1:pos2]
        print(talkText)
        for temp in re.findall(r'\[\[Special:Diff/(\d+)/(\d+)(?:\||\]\])', talkText):
            ignoreRevids.append((int(temp[0]), int(temp[1])))
    except ValueError:
        print('cannot find flag')


print('ignoreRevids', ignoreRevids)


conn = pymysql.connect(
    host=host,
    user=user,
    password=password,
    charset="utf8"
)


# https://quarry.wmflabs.org/query/33421
with conn.cursor() as cur:
    cur.execute('use zhwiki_p')
    cur.execute("""
        SELECT
        rev_id, rev_parent_id, rev_timestamp,
        page_id, page_title, comment_text
        FROM revision
        LEFT JOIN page ON revision.rev_page = page.page_id
        LEFT JOIN comment ON revision.rev_comment_id = comment.comment_id
        WHERE
        revision.rev_timestamp >= '{}' AND revision.rev_timestamp <= '{}'
        AND revision.rev_page IN
        (
            SELECT page.page_id
            FROM pagelinks
            LEFT JOIN page ON pagelinks.pl_title = page.page_title AND pagelinks.pl_namespace = page.page_namespace
            WHERE pl_from = 1608664 AND pl_namespace = 4
                AND page_id NOT IN (
                    590741, # 嵌入包含
                    977277 # 模板文檔頁模式
                )
        )
        ORDER BY revision.rev_timestamp ASC
    """.format(time1, time2))
    res = cur.fetchall()


record = {}
revid2page_id = {}
for row in res:
    rev_id = row[0]
    rev_parent_id = row[1]
    rev_timestamp = row[2].decode()
    page_id = row[3]
    page_title = row[4].decode()

    revid2page_id[rev_id] = page_id
    revid2page_id[rev_parent_id] = page_id

    if page_id not in record:
        record[page_id] = {
            'page_title': page_title,
            'history': [],
        }
    record[page_id]['history'].append({
        'revid': rev_id,
        'rev_parent_id': rev_parent_id,
        'rev_timestamp': rev_timestamp,
        'minor': True
    })


for revids in ignoreRevids:
    if revids[1] not in revid2page_id:
        continue
    page_id = revid2page_id[revids[1]]
    idx1 = 0
    if revids[0] != 0:
        while record[page_id]['history'][idx1]['rev_parent_id'] != revids[0]:
            idx1 += 1
    idx2 = 0
    while record[page_id]['history'][idx2]['revid'] != revids[1]:
        idx2 += 1

    for i in range(idx1, idx2 + 1):
        record[page_id]['history'][i]['minor'] = False


# print(json.dumps(record, indent=4, ensure_ascii=False))


policyList = [
    1040126,  # IP封禁例外
    661388,  # 新頁面巡查
    35,  # 方針與指引
    138006,  # 五大支柱
    140143,  # 忽略所有规则
    314,  # 中立的观点
    1007580,  # 可供查證
    1007588,  # 非原创研究
    3036,  # 避免地域中心
    796,  # 维基百科不是什么
    22766,  # 维基百科不是词典
    621588,  # 自傳
    1165683,  # 生者傳記
    586519,  # 用戶查核方針
    70668,  # 快速删除方针
    351,  # 文件使用方针
    1089503,  # 侵犯著作权
    121628,  # 保護方針
    311,  # 命名常规
    318685,  # 命名常规_(人名)
    6023660,  # 命名常规_(化学)
    3570009,  # 命名常规_(电子游戏)
    6628518,  # 命名常规_(页面分类)
    104452,  # 文明
    142344,  # 共识
    139444,  # 不要人身攻击
    40126,  # 編輯戰
    1187041,  # 編輯禁制方針
    16795,  # 编辑方针
    1497462,  # 修訂巡查
    828098,  # 騷擾
    122511,  # 破坏
    138734,  # 条目所有权
    1050650,  # 封禁方针
    1041919,  # 删除方针
    1279762,  # 修訂版本刪除
    3905475,  # 存廢覆核方針
    7426,  # 用户名
    5757315,  # 機械人方針
    1454,  # 管理员
    160825,  # 管理員的離任
    503284,  # 管理戰
    6890438,  # 权限申请
    5902631,  # 解除權限方針
    1001002,  # 回退功能
    919595,  # 基金會行動
    1082699,  # 傀儡
    6134707,  # 儿童保护
    1038748,  # 监督
    1696159,  # 人事任免投票資格
    1139217,  # 志愿者回复团队
    1466707,  # 机器用户
    282654,  # 行政员
    5323514,  # 大量帳號建立者
    6108916,  # 檔案移動員
    6213290,  # 介面管理員
    5373689,  # 使用条款
    5373678,  # 有償編輯方針
    267252,  # 誹謗
    6786601,  # 版权信息
    5307465,  # 非歧视方针
    1077124,  # 非自由内容使用准则
    5723648,  # 模板編輯員
]


minorPolicyChanges = {}
minorGuidelineChanges = {}
for page_id in record:
    idx1 = 0
    while idx1 < len(record[page_id]['history']):
        if record[page_id]['history'][idx1]['minor']:
            idx2 = idx1
            while idx2 < len(record[page_id]['history']) and record[page_id]['history'][idx2]['minor']:
                idx2 += 1
            if page_id in policyList:
                if page_id not in minorPolicyChanges:
                    minorPolicyChanges[page_id] = {
                        'page_title': record[page_id]['page_title'],
                        'first_time': int(record[page_id]['history'][idx1]['rev_timestamp']),
                        'changes': [],
                    }
                minorPolicyChanges[page_id]['changes'].append((
                    record[page_id]['history'][idx1]['rev_parent_id'],
                    record[page_id]['history'][idx2 - 1]['revid'],
                ))
            else:
                if page_id not in minorGuidelineChanges:
                    minorGuidelineChanges[page_id] = {
                        'page_title': record[page_id]['page_title'],
                        'first_time': int(record[page_id]['history'][idx1]['rev_timestamp']),
                        'changes': [],
                    }
                minorGuidelineChanges[page_id]['changes'].append((
                    record[page_id]['history'][idx1]['rev_parent_id'],
                    record[page_id]['history'][idx2 - 1]['revid'],
                ))
            idx1 = idx2
        idx1 += 1
# print(minorPolicyChanges)
# print(minorGuidelineChanges)


minorPolicyChanges = list(minorPolicyChanges.values())
minorPolicyChanges.sort(key=lambda v: v['first_time'])
minorGuidelineChanges = list(minorGuidelineChanges.values())
minorGuidelineChanges.sort(key=lambda v: v['first_time'])
# print(minorPolicyChanges)
# print(minorGuidelineChanges)


chineseNumber = ['一', '二', '三', '四', '五']


def formatTitle(title, isPolicy):
    if title == '可靠来源/布告板/评级指引':
        return '可靠来源布告板评级指引'

    title = re.sub(r'/(条目指引)', r'\1', title)
    title = re.sub(r'^(.+)/(.+)$', r'\g<1>（\g<2>）', title)
    title = re.sub(r'^(.+)_\((.+)\)$', r'\g<1>（\g<2>）', title)
    if not re.search(r'方[針针]|指引|格式手[冊册]|五大支柱|维基百科不是什么|命名常规|忽略所有规则|游戏维基规则|不要伤害新手', title):
        if isPolicy:
            title = re.sub(r'^(.+?)(（.+?）)?$', r'\g<1>方針\g<2>', title)
        else:
            title = re.sub(r'^(.+?)(（.+?）)?$', r'\g<1>指引\g<2>', title)

    title = re.sub(r'名字空[间間]', '命名空間', title)

    return title


policyTextList = []
for change in minorPolicyChanges:
    title = formatTitle(change['page_title'], True)
    if len(change['changes']) == 1:
        policyTextList.append('《[[Special:Diff/{}/{}|{}]]》'.format(
            change['changes'][0][0],
            change['changes'][0][1],
            title,
        ))
    else:
        diffList = []
        for i, revids in enumerate(change['changes']):
            diffList.append('[[Special:Diff/{}/{}|{}]]'.format(
                revids[0],
                revids[1],
                chineseNumber[i],
            ))
        policyTextList.append('《{}》（{}）'.format(
            title,
            '、'.join(diffList),
        ))
# print('policyTextList', policyTextList)


guidelineTextList = []
for change in minorGuidelineChanges:
    title = formatTitle(change['page_title'], False)
    if len(change['changes']) == 1:
        guidelineTextList.append('《[[Special:Diff/{}/{}|{}]]》'.format(
            change['changes'][0][0],
            change['changes'][0][1],
            title,
        ))
    else:
        diffList = []
        for i, revids in enumerate(change['changes']):
            diffList.append('[[Special:Diff/{}/{}|{}]]'.format(
                revids[0],
                revids[1],
                chineseNumber[i],
            ))
        guidelineTextList.append('《{}》（{}）'.format(
            title,
            '、'.join(diffList),
        ))
# print('guidelineTextList', guidelineTextList)


newPolicyText = ''
if len(policyTextList) >= 2:
    newPolicyText = '、'.join(policyTextList[:-1]) + '及' + policyTextList[-1]
elif len(policyTextList) == 1:
    newPolicyText = policyTextList[0]
else:
    newPolicyText = '無'
# print('newPolicyText', newPolicyText)


newGuidelineText = ''
if len(guidelineTextList) >= 2:
    newGuidelineText = '、'.join(guidelineTextList[:-1]) + '及' + guidelineTextList[-1]
elif len(guidelineTextList) == 1:
    newGuidelineText = guidelineTextList[0]
else:
    newGuidelineText = '無'
# print('newGuidelineText', newGuidelineText)


text = re.sub(r'(\[\[Special:链出更改/Category:维基百科方针\|方針]]：).*', r'\1' + newPolicyText + '。', text)
text = re.sub(r'(\[\[Special:链出更改/Category:维基百科指引\|指引]]：).*', r'\1' + newGuidelineText + '。', text)


# print(text)

if page.text == text:
    print('No diff')
    exit()

print('Diff:')
pywikibot.showDiff(page.text, text)
print('-' * 50)

page.text = text
page.save(summary='[[User:A2093064-bot/task/36|機器人36]]：自動更新雜項修訂', minor=False, apply_cosmetic_changes=True)
