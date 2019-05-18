# -*- coding: utf-8 -*-
import os
import pywikibot
import json
import re
from config import *


os.environ["PYWIKIBOT_DIR"] = os.path.dirname(os.path.realpath(__file__))
os.environ["TZ"] = "UTC"

site = pywikibot.Site()
site.login()

cat = pywikibot.Page(site, "Category:含有受损文件链接的页面")

cnt = 1
for page in site.categorymembers(cat):
    pagetitle = page.title()
    print(cnt, pagetitle)

    text = page.text

    text = re.sub(r" ''\[\[]]''", "", text)
    text = re.sub(r":\[\[]]\n", "", text)
    text = re.sub(r"\*{{audio1\|Fr-{{PAGENAME}}\.ogg}}\n", "", text)
    text = re.sub(r"({{de-prnc\|[^\|]+?)\|[^}]+?}}", r"\1}}", text)
    text = re.sub(r"{{-pron-}}\n+{{IPA\|}}\n+({{-)", r"\1", text)
    text = re.sub(r"==={{-etym-}}===\n+(===|{{-)", r"\1", text)
    text = re.sub(r"====相关词汇====\n\*同音词：\n\*近义词：\n\*反义词：\n\*派生词：\n\*常见搭配：\n+(===)", r"\1", text)
    text = re.sub(r"\*\n", "", text)
    text = re.sub(r"====相关词组====\n+(\[\[Category)", r"\1", text)
    text = re.sub(r"====相关词汇====\n\*同音词：\n+(\[\[Category)", r"\1", text)
    text = re.sub(r"{{(-(?:akin|anton|decl|deriv|etym|expr|link|pron|refer|synon|trans|usage)-)}}", r"{{subst:\1}}", text)
    text = re.sub(r"{{(-(?:v|n|adj|adv)-)}}", r"{{subst:\1}}", text)
    text = re.sub(r"{{(-(?:de)-)}}", r"{{subst:\1}}", text)
    text = re.sub(r"({{subst:-(?:v|n|adj|adv)-}})\n+", r"\1", text)
    text = re.sub(r"({{subst:.*?}}\n)\n+", r"\1", text)
    text = re.sub(r"<!--及物动词。第组动词。变位表格见下。-->\n", "", text)
    text = re.sub(r"\n\n\n+", "\n\n", text)

    if page.text == text:
        print("nothing changed")
        input()
        continue

    pywikibot.showDiff(page.text, text)

    summary = "機器人：修復[[:Category:含有受损文件链接的页面|含有受损文件链接的页面]]及清理語法"
    print("summary = {}".format(summary))

    save = input("save?")
    if save == "":
        page.text = text
        page.save(summary=summary, minor=True, botflag=True)
        cnt += 1
    else:
        print("skip")
