# -*- coding: utf-8 -*-
import json
import os
import re
import sys
from datetime import datetime, timedelta

import mwparserfromhell
os.environ['PYWIKIBOT_DIR'] = os.path.dirname(os.path.realpath(__file__))
import pywikibot
from pywikibot.data.api import Request

from config import *


site = pywikibot.Site()
site.login()

config_page = pywikibot.Page(site, config_page_name)
cfg = config_page.text
cfg = json.loads(cfg)
print(json.dumps(cfg, indent=4, ensure_ascii=False))

if not cfg["enable"]:
	exit("disabled\n")

def converttitle(title):
	r = Request(site=site, parameters={
		'action': 'query',
		'titles': title,
		"redirects": 1,
		"converttitles": 1
		})
	data = r.submit()
	return list(data['query']['pages'].values())[0]['title']

def fix(pagename):
	afdpage = pywikibot.Page(site, pagename)
	text = afdpage.text

	wikicode = mwparserfromhell.parse(text)

	for section in wikicode.get_sections()[2:]:
		title = str(section.get(0).title)
		print(title)
		if re.search(r"{{\s*(delh|TalkendH)\s*\|", str(section), re.IGNORECASE) != None:
			print("  closed, skip")
			continue

		m = re.search(r"^\[\[([^\]]+)\]\]$", title, re.IGNORECASE)
		if m != None:
			title = m.group(1)
			start = ""
			if title[0] == ":":
				start = ":"
				title = title[1:]

			title = converttitle(title)

			title = "[["+start+title+"]]"

			if str(section.get(0).title) != title:
				if str(section.get(0).title).replace("_", " ") != title:
					section.insert(1, "\n{{formerly|"+str(section.get(0).title)+"}}")
				print("  set new title = "+title)
				section.get(0).title = title
			continue

		m = re.search(r"^(\[\[[^\]]+\]\][、，])+\[\[[^\]]+\]\]$", title, re.IGNORECASE)
		if m != None:
			titlelist = m.group(0).replace("]]，[[", "]]、[[").split("、")
			newtitlelist = []
			for title in titlelist:
				if title.startswith("[[") and title.endswith("]]"):
					title = title[2:-2]

					if title[0] == ":":
						title = title[1:]

					title = converttitle(title)

					newtitlelist.append(title)
				else :
					print("  wrong title: "+title)
					return
			title = "{{al|"+"|".join(newtitlelist)+"}}"
			if str(section.get(0).title) != title:
				print("  set new title = "+title)
				section.get(0).title = title
			continue

		m = re.search(r"^{{al\|([^\]]+\|)+[^\]]+}}$", title, re.IGNORECASE)
		if m != None:
			titlelist = m.group(0)[5:-2].split("|")
			newtitlelist = []
			for title in titlelist:
				if title[0] == ":":
					title = title[1:]

				title = converttitle(title)

				newtitlelist.append(title)
			title = "{{al|"+"|".join(newtitlelist)+"}}"
			if str(section.get(0).title) != title:
				print("  set new title = "+title)
				section.get(0).title = title
			continue

		print("  unknown format, skip")

	text = str(wikicode)

	if afdpage.text == text:
		print("  nothing changed")
		return

	pywikibot.showDiff(afdpage.text, text)
	summary = cfg["summary"]
	print(summary)
	afdpage.text = text
	afdpage.save(summary=summary, minor=False)

fix(cfg['pagename'])
