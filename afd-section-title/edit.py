# -*- coding: utf-8 -*-
import os
os.environ['PYWIKIBOT2_DIR'] = os.path.dirname(os.path.realpath(__file__))
import sys
import json
import re
import pywikibot
import mwparserfromhell
from pywikibot.data.api import Request
from config import *

if len(sys.argv) >= 1:
	pagename = sys.argv[1]
else :
	pagename = input("afd name:")

if not pagename.startswith("Wikipedia:頁面存廢討論/記錄/"):
	pagename = "Wikipedia:頁面存廢討論/記錄/" + pagename

site = pywikibot.Site()
site.login()

config_page = pywikibot.Page(site, config_page_name)
cfg = config_page.text
cfg = json.loads(cfg)
print(json.dumps(cfg, indent=4, ensure_ascii=False))

if not cfg["enable"]:
	exit("disabled\n")

afdpage = pywikibot.Page(site, pagename)
text = afdpage.text

wikicode = mwparserfromhell.parse(text)

def converttitle(title):
	r = Request(site=site, parameters={
		'action': 'query',
		'titles': title,
		"redirects": 1,
		"converttitles": 1
		})
	data = r.submit()
	return list(data['query']['pages'].values())[0]['title']

for section in wikicode.get_sections()[1:]:
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

		# page = pywikibot.Page(site, title)
		# if not page.exists():
		# 	print("  not exists")
		# if page.isRedirectPage():
		# 	title = page.getRedirectTarget().title()
		# 	print("  follow redirect")
		# else:
		# 	title = page.title()
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

				# page = pywikibot.Page(site, title)
				# if page.isRedirectPage():
				# 	title = page.getRedirectTarget().title()
				# 	print("follow redirect")
				# else:
				# 	title = page.title()
				# title = page.title()
				title = converttitle(title)

				newtitlelist.append(title)
			else :
				exit("  wrong title: "+title)
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

			# page = pywikibot.Page(site, title)
			# if page.isRedirectPage():
			# 	title = page.getRedirectTarget().title()
			# 	print("follow redirect")
			# else:
			# 	title = page.title()
			# title = page.title()
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
	exit("  nothing changed")

pywikibot.showDiff(afdpage.text, text)
summary = cfg["summary"]
print(summary)
input("Save?")
afdpage.text = text
afdpage.save(summary=summary, minor=False)

# with open('output.txt', 'w') as file:
# 	file.write(text)
