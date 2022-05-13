# -*- coding: utf-8 -*-
import argparse
import json
import os
import re
import time
from datetime import datetime, timezone

import pymysql

os.environ["PYWIKIBOT_DIR"] = os.path.dirname(os.path.realpath(__file__))
import pywikibot

from config import (config_page_name, database,  # pylint: disable=E0611,W0614
                    skip_time, skip_title, use_db)

REGEX = [
    # infobox
    {
        'pattern': r'(\|\s*)((?:\d+|image[ _-]?(?:|\d+|file[LR]?\d*|flag|map|name|seal|shield|skyline|coat|coat[ _]of[ _]arms|blank[ _]emblem|hans|hant|cn|hk|mo|sg|tw)?|img_\d+|(?:map|dual|net|vfig|uniform|ship|logo|kit|stdg|hans|hant|cn|hk|mo|sg|tw)[ _-]?image|logo[ _-]?(?:file|filename|pic)?|(?:company|uniform)[ _-]?logo|photo\d*[a-c]?|coa[ _-]pic|img|filename|chart|screenshot|cover|symbol|audio[ _-]file|signature|album|(?:city)?[ _-]?seal|map[ _-]?(?:img|location)?|(?:range|Alternative)[ _-]?map|patch|badge|coatofarms|session[ _-]room|static[ _-]image[ _-]name|mapofstate|ribbon|uniform|insignia|zh-?(?:hans|hant|cn|hk|mo|sg|tw)?|flag_[sp]\d+|flag alias[A-Za-z\- ]*|BILDPFAD_KARTE|(?:代表)?(?:圖片|图片|圖像|图像|画像)(?:名称|名稱|\d+)?|電視網商標檔案|[頻频]道[圖图]片(?:檔案|文件)|電臺圖片檔案|路線圖|正面|背面|项目符号文件名称|地图档名|簽名|签名|照片|市旗|市徽|景观照片文件名|画像ファイル)\s*=\s*(?:<!--[^\n]+-->)?\s*)((?:File|Image|文件|檔案|圖像):)? *({0})(?:#.+?)?(\s*?(?:<!--[^\n]+-->)?\s*?(?:\||}}|\n))',
        'replace': {
            'comment_other': r'\1\2<!-- 檔案不存在 \3\4 ，可從{0}取得 -->\5',
            'moved': r'\1\2\g<3>{0}\5',
            'deleted_comment': r'\1\2<!-- 檔案已被刪除 \3\4 -->\5',
            'deleted': r'\1\2\5',
            'comment': r'\1\2<!-- 檔案不存在 \3\4 -->\5'
        }
    },
    # normal_whole_line
    {
        'pattern': r'(^|\n)[ \t]*(\[\[(?:File|Image|文件|檔案|圖像):) *({0})(?:#.+?)?(\s*(?:\|(?:\[\[[^[\]]*\]\]|\[[^[\]]*\]|[^[\]])*)?\]\])[ \t]*(\n|$)',
        'replace': {
            'comment_other': r'\1<!-- 檔案不存在 \2\3\4 ，可從{0}取得 -->\5',
            'moved': r'\1\g<2>{0}\4\5',
            'deleted_comment': r'\1<!-- 檔案已被刪除 \2\3\4 -->\5',
            'deleted': r'\1',
            'comment': r'\1<!-- 檔案不存在 \2\3\4 -->\5'
        }
    },
    # normal
    {
        'pattern': r'(\[\[(?:File|Image|文件|檔案|圖像):) *({0})(?:#.+?)?(\s*(?:\|(?:\[\[[^[\]]*\]\]|[^[\]])*)?\]\])([ \t]*)',
        'replace': {
            'comment_other': r'<!-- 檔案不存在 \1\2\3 ，可從{0}取得 -->',
            'moved': r'\g<1>{0}\3\4',
            'deleted_comment': r'<!-- 檔案已被刪除 \1\2\3 -->',
            'deleted': r'',
            'comment': r'<!-- 檔案不存在 \1\2\3 -->'
        }
    },
    # gallery
    {
        'pattern': r'(<gallery[^>\n]*?>[\s\S]*?\n)((?:File|Image|文件|檔案|圖像):)? *({0})(?:#.+?)?([ \t]*)(\|[^\n]*?)?\n([\s\S]*?</gallery>)',
        'replace': {
            'comment_other': r'\1<!-- 檔案不存在 \2\3\4\5 ，可從{0}取得 -->\n\6',
            'moved': r'\1\g<2>{0}\4\5\n\6',
            'deleted_comment': r'\1<!-- 檔案已被刪除 \2\3\4\5 -->\n\6',
            'deleted': r'\1\6',
            'comment': r'\1<!-- 檔案不存在 \2\3\4\5 -->\n\6'
        }
    },
    # Flagicon image
    {
        'pattern': r'({{{{(?:flagicon image|Wide image|Spoken Wikipedia)\|)({0})(?:#.+?)?((?:\|[^{{}}]*?)?}}}})([ \t]*)',
        'replace': {
            'comment_other': r'<!-- 檔案不存在 \1\2\3 ，可從{0}取得 -->',
            'moved': r'\g<1>{0}\3\4',
            'deleted_comment': r'<!-- 檔案已被刪除 \1\2\3 -->',
            'deleted': r'',
            'comment': r'<!-- 檔案不存在 \1\2\3 -->'
        }
    }
]

os.environ["TZ"] = "UTC"

parser = argparse.ArgumentParser()
parser.add_argument('-f', '--force', dest='force', action='store_true')
parser.add_argument('--category', type=str, default=None)
parser.add_argument('--page', type=str, default=None)
parser.add_argument('--confirm', action='store_true')
parser.add_argument('--limit', type=int, default=0)
parser.add_argument('--skiplimit', type=int, default=100)
parser.add_argument('--debug', action='store_true')
parser.set_defaults(force=False, confirm=False, debug=False)
args, _ = parser.parse_known_args()
pywikibot.log(args)

site = pywikibot.Site()
site.login()
sitecommons = pywikibot.Site("commons", "commons")

config_page = pywikibot.Page(site, config_page_name)
cfg = config_page.text
cfg = json.loads(cfg)

if not cfg['enable'] and not args.force:
    print('disabled')
    exit()

if args.category:
    cats = [args.category]
else:
    cats = cfg["category"]

skippages = []
if use_db:
    db = pymysql.connect(
        host=database['host'],
        user=database['user'],
        passwd=database['passwd'],
        db=database['db'],
        charset=database['charset']
    )
    cur = db.cursor()

    cnt = cur.execute("""DELETE FROM `remove_broken_file_pages` WHERE `time` < FROM_UNIXTIME(%s)""",
                      (time.time() - skip_time))
    pywikibot.log('Deleted {} rows from remove_broken_file_pages'.format(cnt))

    cnt = cur.execute("""DELETE FROM `remove_broken_file_files` WHERE `page` NOT IN ( SELECT `page` FROM `remove_broken_file_pages` )""")
    pywikibot.log('Deleted {} rows from remove_broken_file_files'.format(cnt))

    db.commit()

    cur.execute("""SELECT `page` FROM `remove_broken_file_pages`""")
    rows = cur.fetchall()
    for row in rows:
        skippages.append(row[0])


def add_skip_page(skip_page, files):
    if not use_db:
        return
    cur.execute("""DELETE FROM `remove_broken_file_pages` WHERE `page` = %s""",
                (skip_page))
    cur.execute("""INSERT INTO `remove_broken_file_pages` (`page`) VALUES (%s)""",
                (skip_page))

    cur.execute("""DELETE FROM `remove_broken_file_files` WHERE `page` = %s""",
                (skip_page))
    for missing_file in files:
        cur.execute("""INSERT INTO `remove_broken_file_files` (`page`, `file`) VALUES (%s, %s)""",
                    (skip_page, missing_file))

    db.commit()


def checkImageExists(title):
    image = pywikibot.FilePage(site, title)
    if image.exists():
        return True
    try:
        if image.file_is_shared():
            return True
    except Exception:
        pass
    return False


def followMove(title, commons=False):
    if commons:
        runsite = sitecommons
    else:
        runsite = site
    logs = []
    first_title = title
    while True:
        data = pywikibot.data.api.Request(site=runsite, parameters={
            "action": "query",
            "letitle": title,
            "list": "logevents",
            "letype": "move",
            "lelimit": "1"
        }).submit()
        if len(data["query"]["logevents"]) > 0:
            movelog = data["query"]["logevents"][0]
            movelog["params"]["target_title_without_ns"] = pywikibot.Page(
                site, movelog["params"]["target_title"]).titleWithoutNamespace()
            logs.append(movelog)
            title = movelog["params"]["target_title"]

            if checkImageExists(title):
                return logs

            if title == first_title:
                return []
        else:
            break
    return logs


def checkReplace(oldText, newText):
    if re.search(r'<!--.*<!--.*-->.*-->', newText):
        return oldText
    return newText


if args.page:
    pages = [pywikibot.Page(site, args.page)]
else:
    pages = []
    for cat in cats:
        pages.extend(list(site.categorymembers(pywikibot.Page(site, cat))))

limit = 1
skiplimit = 0
for page in pages:
    if args.limit > 0 and limit > args.limit:
        pywikibot.log('Reach the limit. Quitting.')
        break
    if args.skiplimit > 0 and skiplimit >= args.skiplimit:
        pywikibot.log('Reach the skiplimit. Quitting.')
        break

    pagetitle = page.title()
    pywikibot.log('{} {}'.format(limit, pagetitle))

    if page.namespace().id in [8]:
        pywikibot.log('Skip page in specify namespace.')
        continue

    lastEditTime = list(page.revisions(total=1))[0]['timestamp']
    lastEditTimestamp = datetime(lastEditTime.year, lastEditTime.month, lastEditTime.day,
                                 lastEditTime.hour, lastEditTime.minute, tzinfo=timezone.utc).timestamp()
    if time.time() - lastEditTimestamp < cfg['interval'] and not args.force:
        pywikibot.log('Skip. Last edit on {0}'.format(lastEditTime))
        continue

    is_skip = False
    for skip_regex in cfg['skip_title']:
        if re.search(skip_regex, pagetitle):
            pywikibot.log('skip ({0})'.format(skip_regex))
            is_skip = True
            break
    if re.search(skip_title, pagetitle):
        is_skip = True
    if is_skip:
        continue
    if pagetitle in skippages and not args.page:
        pywikibot.log("skip")
        continue
    text = page.text
    summary_comment = []
    summary_moved = []
    summary_deleted = []
    missing_files = []
    try:
        for image in page.imagelinks():
            if cfg['removal_limit_one_edit'] > 0 and len(summary_comment) + len(summary_moved) + len(summary_deleted) >= cfg['removal_limit_one_edit']:
                pywikibot.log('Reach removal limit in one edit')
                break

            if not image.exists():
                try:
                    if image.file_is_shared():
                        continue
                except Exception as e:
                    pass

                image_fullname = image.title()
                missing_files.append(image_fullname)
                imagename = image.title(with_ns=False)

                imageregex = "[" + imagename[0].upper() + \
                    imagename[0].lower() + "]" + re.escape(imagename[1:])
                imageregex = imageregex.replace("\\ ", "[ _]+")

                # comment_other start
                existother = None
                for wiki in cfg["check_other_wiki"]:
                    if pywikibot.Page(site, "{}:File:{}".format(wiki, imagename)).exists():
                        existother = wiki
                        break

                if existother is not None:
                    pywikibot.log("{} exist on {}".format(image_fullname, existother))

                    for regex_rule in REGEX:
                        regex = regex_rule["pattern"].format(
                            imageregex)
                        replace = regex_rule["replace"]["comment_other"].format(
                            cfg["check_other_wiki"][existother])
                        if args.debug:
                            pywikibot.log('comment_other regex: {}'.format(regex))
                            pywikibot.log('comment_other replace: {}'.format(replace))

                        newtext, count = re.subn(
                            regex, replace, text, flags=re.M | re.I)
                        text = checkReplace(text, newtext)

                        if count > 0:
                            break

                    summary_comment.append(
                        cfg['summary']["comment_other"].format(imagename, existother))

                    continue
                # coment_other end

                # moved start
                movelog = followMove(image_fullname)
                if len(movelog) > 0:
                    if checkImageExists(imagename):
                        pywikibot.log("File:{} moved".format(imagename))

                        for regex_rule in REGEX:
                            regex = regex_rule["pattern"].format(
                                imageregex)
                            replace = regex_rule["replace"]["moved"].format(
                                movelog[-1]["params"]["target_title_without_ns"])
                            if args.debug:
                                pywikibot.log('moved regex: {}'.format(regex))
                                pywikibot.log('moved replace: {}'.format(replace))

                            newtext, count = re.subn(
                                regex, replace, text, flags=re.M | re.I)
                            text = checkReplace(text, newtext)

                            if count > 0:
                                break

                        summary_temp = image_fullname
                        for log in movelog:
                            summary_temp = cfg['summary']["moved"].format(
                                summary_temp, log["params"]["target_title_without_ns"], log["user"], log["logid"], log["comment"])
                        summary_moved.append(summary_temp)

                        continue
                    else:
                        image_fullname = movelog[-1]["params"]["target_title"]
                        pywikibot.log("Info: File moved to {}".format(image_fullname))

                # moved end

                # deleted start
                deleted_local = False
                deleted_commons = False
                deleted_comment = False
                deleted_f6 = False

                data = pywikibot.data.api.Request(site=site, parameters={
                    "action": "query",
                    "letitle": image_fullname,
                    "list": "logevents",
                    "leaction": "delete/delete",
                    "lelimit": "1"
                }).submit()
                if len(data["query"]["logevents"]) > 0:
                    deleted_local = True
                    deletelog = data["query"]["logevents"][0]
                    if re.search(cfg["ignored_csd_comment"], deletelog["comment"]):
                        deleted_comment = True
                    elif re.search(cfg["drv_csd_comment"], deletelog["comment"]):
                        deleted_comment = True
                        deleted_f6 = True
                if not deleted_local:
                    data = pywikibot.data.api.Request(site=sitecommons, parameters={
                        "action": "query",
                        "letitle": image_fullname,
                        "list": "logevents",
                        "leaction": "delete/delete",
                        "lelimit": "1"
                    }).submit()
                    if len(data["query"]["logevents"]) > 0:
                        deleted_commons = True
                        deletelog = data["query"]["logevents"][0]

                if deleted_local:
                    summary_prefix = imagename
                    for log in movelog:
                        summary_prefix = cfg['summary']["moved_deleted"].format(
                            summary_prefix, log["params"]["target_title_without_ns"], log["logid"])

                if deleted_comment:
                    pywikibot.log("{} deleted by F6".format(image_fullname))

                    for regex_rule in REGEX:
                        regex = regex_rule["pattern"].format(
                            imageregex)
                        replace = regex_rule["replace"]["deleted_comment"]
                        if args.debug:
                            pywikibot.log('deleted_comment regex: {}'.format(regex))
                            pywikibot.log('deleted_comment replace: {}'.format(replace))

                        newtext, count = re.subn(
                            regex, replace, text, flags=re.M | re.I)
                        text = checkReplace(text, newtext)

                        if count > 0:
                            break

                    summary_comment.append(cfg['summary']["deleted"]["local"].format(
                        summary_prefix, deletelog["user"], deletelog["logid"], deletelog["comment"]))

                    if deleted_f6 and page.namespace().id == 0:
                        drv_page = pywikibot.Page(site, cfg["drv_page"])
                        drv_page_text = drv_page.text.strip()
                        if image_fullname not in drv_page_text:
                            drv_page_text += cfg["drv_append_text"].format(
                                image_fullname, pagetitle, deletelog["user"], deletelog["comment"], deletelog["logid"])
                            pywikibot.showDiff(drv_page.text, drv_page_text)
                            summary = cfg["drv_summary"]
                            pywikibot.output("summary = {}".format(summary))

                            if args.confirm:
                                save = input("save?")
                            else:
                                save = "Yes"
                            if save in ["Yes", "yes", "Y", "y", ""]:
                                drv_page.text = drv_page_text
                                drv_page.save(summary=summary,
                                              minor=False, botflag=False,
                                              apply_cosmetic_changes=False)
                        else:
                            pywikibot.log('Already reported to DRV.')

                    continue

                if deleted_local or deleted_commons:
                    if deleted_local:
                        pywikibot.log("{} deleted on local".format(image_fullname))
                    elif deleted_commons:
                        pywikibot.log("{} deleted on commons".format(image_fullname))

                    for regex_rule in REGEX:
                        regex = regex_rule["pattern"].format(
                            imageregex)
                        replace = regex_rule["replace"]["deleted"]
                        if args.debug:
                            pywikibot.log('deleted regex: {}'.format(regex))
                            pywikibot.log('deleted replace: {}'.format(replace))

                        newtext, count = re.subn(
                            regex, replace, text, flags=re.M | re.I)
                        text = checkReplace(text, newtext)

                        if count > 0:
                            break

                    if deleted_commons:
                        comment = re.sub(r"\[\[:?([^\[\]]+?)]]",
                                         r"[[:c:\1]]", deletelog["comment"])
                        summary_deleted.append(cfg['summary']["deleted"]["commons"].format(
                            imagename, deletelog["user"], deletelog["logid"], comment))
                    elif deleted_local:
                        summary_deleted.append(cfg['summary']["deleted"]["local"].format(
                            summary_prefix, deletelog["user"],
                            deletelog["logid"], deletelog["comment"]))

                    continue

                # deleted end

                # comment start
                uploaded = False

                data = pywikibot.data.api.Request(site=site, parameters={
                    "action": "query",
                    "letitle": image_fullname,
                    "list": "logevents",
                    "letype": "upload",
                    "lelimit": "1"
                }).submit()
                if len(data["query"]["logevents"]) > 0:
                    uploaded = True
                if not uploaded:
                    data = pywikibot.data.api.Request(site=sitecommons, parameters={
                        "action": "query",
                        "letitle": image_fullname,
                        "list": "logevents",
                        "letype": "upload",
                        "lelimit": "1"
                    }).submit()
                    if len(data["query"]["logevents"]) > 0:
                        uploaded = True

                if not uploaded:
                    pywikibot.log("{} never uploaded".format(image_fullname))

                    for regex_rule in REGEX:
                        regex = regex_rule["pattern"].format(
                            imageregex)
                        replace = regex_rule["replace"]["comment"]
                        if args.debug:
                            pywikibot.log('comment regex: {}'.format(regex))
                            pywikibot.log('comment replace: {}'.format(replace))

                        newtext, count = re.subn(
                            regex, replace, text, flags=re.M | re.I)
                        text = checkReplace(text, newtext)

                        if count > 0:
                            break

                    summary_comment.append(
                        cfg['summary']["comment"].format(imagename))

                    continue

                # comment end

                # unknown start
                pywikibot.log("{} missed for unknown reason".format(image_fullname))
                # unknown end
    except Exception as e:
        pywikibot.error(e)

    summary = []
    if len(summary_comment) == 1:
        summary.append(
            cfg['summary']['prepend']['comment'] + '、'.join(summary_comment))
    elif len(summary_comment) > 1:
        summary.append(cfg['summary']['prepend']['comment'] + '{}個檔案'.format(len(summary_comment)))
    if len(summary_moved) == 1:
        summary.append(
            cfg['summary']['prepend']['moved'] + '、'.join(summary_moved))
    elif len(summary_moved) > 1:
        summary.append(cfg['summary']['prepend']['moved'] + '{}個檔案'.format(len(summary_moved)))
    if len(summary_deleted) == 1:
        summary.append(
            cfg['summary']['prepend']['deleted'] + '、'.join(summary_deleted))
    elif len(summary_deleted) > 1:
        summary.append(cfg['summary']['prepend']['deleted'] + '{}個檔案'.format(len(summary_deleted)))
    summary = cfg['summary']["prepend"]["all"] + "；".join(summary)
    pywikibot.log("summary = {}".format(summary))

    if page.text == text:
        pywikibot.log("nothing changed")
        if args.confirm:
            input()
        add_skip_page(pagetitle, missing_files)
        skiplimit += 1
        if args.skiplimit > 0 and skiplimit >= args.skiplimit:
            pywikibot.log('Reach the skiplimit. Quitting.')
            break
        continue

    pywikibot.showDiff(page.text, text)

    if args.confirm:
        save = input("save?")
    else:
        save = "Yes"
    if save in ["Yes", "yes", "Y", "y", ""]:
        page.text = text
        try:
            page.save(summary=summary, minor=False, apply_cosmetic_changes=True)
            limit += 1
        except pywikibot.exceptions.PageSaveRelatedError as e:
            pywikibot.error(e)
            summary = re.sub(r'\[https?://(.+?)\]', r'\1', summary)
            summary = re.sub(r'https?://', '', summary)
            pywikibot.log('Trying to remove url in summary and save again.')
            pywikibot.output("summary = {}".format(summary))
            try:
                page.save(summary=summary, minor=False, apply_cosmetic_changes=True)
                limit += 1
            except pywikibot.exceptions.PageSaveRelatedError as e:
                pywikibot.error(e)
                if args.confirm:
                    input()
                add_skip_page(pagetitle, missing_files)
                skiplimit += 1
    else:
        pywikibot.log("skip")
        add_skip_page(pagetitle, missing_files)
