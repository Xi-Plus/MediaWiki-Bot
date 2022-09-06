#!/usr/bin/env python
# coding: utf-8

import bisect
import configparser
import json
import os
import re
from calendar import c
from datetime import datetime, timedelta

import pymysql

BASEDIR = os.path.dirname(os.path.realpath(__file__))
os.environ['PYWIKIBOT_DIR'] = BASEDIR
import pywikibot
import pywikibot.flow
import requests
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from config import CONFIG_PAGE_NAME, REPLICA_CONFIG_PATH, USERDB_CONFIG_PATH
from dbmodels import User

QUERY_USER_WITH_SIGN = '''
SELECT actor_user, actor_name, up2.up_value AS `nickname`
FROM recentchanges
LEFT JOIN actor ON rc_actor = actor_id
LEFT JOIN user_properties AS up1 ON actor_user = up1.up_user AND up1.up_property = 'fancysig'
LEFT JOIN user_properties AS up2 ON actor_user = up2.up_user AND up2.up_property = 'nickname'
WHERE (rc_namespace = 4 OR rc_namespace % 2 = 1)
    AND rc_timestamp > DATE_FORMAT(DATE_SUB(NOW(), INTERVAL 7 DAY), '%Y%m%d%H%i%s')
    AND actor_user IS NOT NULL
    AND up1.up_value IS NOT NULL
    AND up2.up_value IS NOT NULL
GROUP BY actor_user
ORDER BY rc_timestamp DESC
'''

REPORT_HEADER = '''{| class="wikitable sortable"
!使用者
!檢查
!簽名
!問題
'''

REPORT_ROW = '''|-
| [[Special:Contributions/{0}|{0}]]
| {1}
| {2}
| {3}
'''


def check_sign_problems(sign):
    sign_errors = set()
    hide_sign = False

    if '[[File:' in sign:
        sign_errors.add((2, 'file', None))
    if '<div' in sign:
        sign_errors.add((2, 'div', None))
        hide_sign = True
    if len(re.findall(r'{{', sign)) > len(re.findall(r'{{!}}', sign)):
        sign_errors.add((2, 'template', None))
    if '<templatestyles' in sign:
        sign_errors.add((2, 'templatestyles', None))
    if re.search(r'\[(https?)?://', sign):
        sign_errors.add((2, 'link', None))
    sign_len = len(sign.encode())
    if sign_len > 255:
        sign_errors.add((1, 'sign-too-long', sign_len))

    return sign_errors, hide_sign


def format_sign_errors(sign_errors):
    result = []
    sign_errors = sorted(list(sign_errors))

    for row in sign_errors:
        error_type = row[1]
        error_param = row[2]

        if error_type == 'file':
            result.append('檔案')
        elif error_type == 'template':
            result.append('模板')
        elif error_type == 'templatestyles':
            result.append('模板樣式')
        elif error_type == 'link':
            result.append('外部連結')
        elif error_type == 'sign-too-long':
            if error_param >= 280:
                result.append('簽名過長-{{{{red|{}}}}}'.format(error_param))
            elif error_param >= 270:
                result.append('簽名過長-{{{{orange|{}}}}}'.format(error_param))
            else:
                result.append('簽名過長-{}'.format(error_param))
        elif error_type == 'obsolete-tag':
            result.append('過時的標籤-{}'.format(error_param))
        else:
            if error_param:
                result.append('{}-{}'.format(error_type, error_param))
            else:
                result.append(error_type)

    return '、'.join(result)


def get_warn_templates(sign_errors):
    templates = set()
    for row in sign_errors:
        error_type = row[1]
        if error_type in ['template', 'templatestyles']:
            templates.add('Uw-sign-notemplate')
        elif error_type == 'link':
            templates.add('Uw-sign-external-link')
        elif error_type == 'sign-too-long':
            templates.add('Uw-sign-toolong')
    return templates


def parse_signs(signs):
    text = ''
    for username, sign in signs.items():
        text += '<!-- {0} start -->{1}<!-- {0} end -->\n'.format(username, sign)

    with open(os.path.join(BASEDIR, 'raw_signs.txt'), 'w', encoding='utf8') as f:
        f.write(text)

    API = 'https://zh.wikipedia.org/w/api.php'
    data = requests.post(API, data={
        'action': 'parse',
        'format': 'json',
        'text': text,
        'onlypst': 1,
        'contentmodel': 'wikitext',
    }).json()
    parsed_text = data['parse']['text']['*']

    parsed_signs = {}
    for username in signs:
        flag = '<!-- {} start -->'.format(username)
        idx1 = parsed_text.index(flag)
        idx2 = parsed_text.index('<!-- {} end -->'.format(username))
        parsed_sign = parsed_text[idx1 + len(flag):idx2]
        parsed_signs[username] = parsed_sign

    return parsed_signs


def lint_signs(signs):
    text = ''
    signs_idx = []
    usernames = []
    sign_errors = {}
    for username, sign in signs.items():
        cleaned_sign = re.sub(r'[^\x00-\x7F]', 'C', sign)
        text += '<div id="sign-{}">{}</div>\n'.format(username, cleaned_sign)
        signs_idx.append(len(text))
        usernames.append(username)
        sign_errors[username] = set()

    with open(os.path.join(BASEDIR, 'parsed_signs.txt'), 'w', encoding='utf8') as f:
        f.write(text)

    data = requests.post('https://zh.wikipedia.org/api/rest_v1/transform/wikitext/to/lint', data=json.dumps({
        'wikitext': text,
    }).encode(), headers={
        'Content-Type': 'application/json',
        'Accept': 'application/json',
    }).json()

    for row in data:
        idx = bisect.bisect_left(signs_idx, row['dsr'][0])
        username = usernames[idx]
        lint_type = row['type']
        lint_tag = row['params']['name']
        sign_errors[username].add((3, lint_type, lint_tag))

    return sign_errors


reader = configparser.ConfigParser()
reader.read(USERDB_CONFIG_PATH)
USERDB_HOST = reader.get('client', 'host')
USERDB_PORT = reader.get('client', 'port')

engine = create_engine(
    f'mysql+pymysql://{USERDB_HOST}:{USERDB_PORT}',
    connect_args={'read_default_file': USERDB_CONFIG_PATH},
    future=True,
)


def warn_user(site, username, sign, warns, cfg):
    print('warn', username, warns)
    TALK_NAMESPACES = list(filter(lambda v: v >= 0 and v % 2 == 1 or v == 4, site.namespaces))
    TIMELIMIT = datetime.now() - timedelta(days=7)

    session = Session(engine)
    user = session.scalars(select(User).where(User.name == username)).first()
    if user is None:
        user = User(
            name=username,
        )
        session.add(user)
        session.commit()

    if user.last_warn > TIMELIMIT:
        print('recent warned')
        return

    contributions = site.usercontribs(
        user=username,
        total=500,
        namespaces=TALK_NAMESPACES,
        end=TIMELIMIT,
    )
    has_recent_edit = False
    for contris in contributions:
        print(contris)
        page = pywikibot.Page(site, contris['title'])
        old_text = page.getOldVersion(contris['parentid']) if contris['parentid'] > 0 else ''
        new_text = page.getOldVersion(contris['revid'])
        old_cnt = old_text.count(sign)
        new_cnt = new_text.count(sign)
        if new_cnt > old_cnt:
            print('recent edit', contris['revid'], old_cnt, new_cnt)
            has_recent_edit = True
            break
    if not has_recent_edit:
        print('no recent edit')
        return

    if user.warn_count >= 3:
        pass
    else:
        title = '簽名問題'

        talk_page = pywikibot.Page(site, 'User talk:' + username)
        if talk_page.is_flow_page():
            board = pywikibot.flow.Board(talk_page)
            content = ''
            for template in warns:
                content += '{{subst:' + template + '}}\n'
            print(content)
            input('Save?')
            board.new_topic(title, content)
        else:
            new_text = talk_page.text
            if new_text != '':
                new_text += '\n\n'
            new_text += '== {} ==\n'.format(title)
            for template in warns:
                new_text += '{{subst:' + template + '}}--~~~~\n'
            pywikibot.showDiff(talk_page.text, new_text)
            input('Save?')
            talk_page.text = new_text
            talk_page.save(summary='提醒簽名問題', minor=False)

        user.warn_count += 1
        user.last_warn = datetime.now()
        session.commit()


def main():
    site = pywikibot.Site('zh', 'wikipedia')
    site.login()

    config_page = pywikibot.Page(site, CONFIG_PAGE_NAME)
    cfg = config_page.text
    cfg = json.loads(cfg)
    print(json.dumps(cfg, indent=4, ensure_ascii=False))

    if not cfg['enable']:
        print('disabled')
        exit()

    conn = pymysql.connect(read_default_file=REPLICA_CONFIG_PATH)

    with conn.cursor() as cur:
        cur.execute(QUERY_USER_WITH_SIGN)
        res = cur.fetchall()

    user_ids = {}
    raw_signs = {}
    usernames = []
    for row in res:
        user_id = row[0]
        username = row[1].decode()
        sign = row[2].decode()

        user_ids[username] = user_id
        raw_signs[username] = sign
        usernames.append(username)

    print('Process {} users'.format(len(usernames)))

    parsed_signs = parse_signs(raw_signs)

    sign_errors = {}
    hide_sign = {}
    for username, sign in parsed_signs.items():
        sign_errors[username], hide_sign[username] = check_sign_problems(sign)

    lint_sign_errors = lint_signs(parsed_signs)
    for username, errors in lint_sign_errors.items():
        sign_errors[username].update(errors)

    report_text = REPORT_HEADER
    warned_users = set()
    for username in sorted(usernames):
        error = sign_errors[username]
        if len(error) > 0:
            check_link = '[https://signatures.toolforge.org/check/zh.wikipedia.org/{} check]'.format(username.replace(' ', '%20'))
            sign = ''
            if not hide_sign[username]:
                sign = parsed_signs[username]
            error_text = format_sign_errors(error)
            report_text += REPORT_ROW.format(username, check_link, sign, error_text)

            warn_templates = get_warn_templates(error)
            if len(warn_templates) > 0:
                warned_users.add(username)
                warn_user(
                    site=site,
                    username=username,
                    sign=parsed_signs[username],
                    warns=warn_templates,
                    cfg=cfg,
                )

    report_text += '|}'

    page = pywikibot.Page(site, cfg['output_page'])

    print('Diff:')
    pywikibot.showDiff(page.text, report_text)
    print('-' * 50)

    page.text = report_text
    # page.save(summary=cfg['report_summary'], minor=False)

    session = Session(engine)
    for user in session.query(User).all():
        if user.name not in warned_users:
            print('Remove {} from table'.format(user.name))
            session.delete(user)
    session.commit()


if __name__ == '__main__':
    main()
