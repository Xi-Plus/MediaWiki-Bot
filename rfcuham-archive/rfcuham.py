# -*- coding: utf-8 -*-
import os
import pywikibot
import mwparserfromhell
import json
import re
from datetime import datetime
import time
from config import *

os.environ['TZ'] = 'UTC'

site = pywikibot.Site()
site.login()

config_page = pywikibot.Page(site, config_page_name)
cfg = config_page.text
cfg = json.loads(cfg)
print(json.dumps(cfg, indent=4, ensure_ascii=False))

cupage = pywikibot.Page(site, cfg["main_page_name"])
text = cupage.text

wikicode = mwparserfromhell.parse(text)

archivelist = {}
count = 0
for section in wikicode.get_sections()[2:]:
	title = str(section.get(0).title)
	print(title, end="\t")
	for template in section.filter_templates():
		if template.name.lower() == "status2":
			if template.has(1):
				status = template.get(1)
			else:
				status = "(empty)"
			print("status", status, end="\t")
			if status in cfg["status_to_archive"]:
				lasttime = datetime(1, 1, 1)
				for m in re.findall("(\d{4})年(\d{1,2})月(\d{1,2})日 \(.\) (\d{2}):(\d{2}) \(UTC\)", str(section)):
					d = datetime(int(m[0]), int(m[1]), int(m[2]), int(m[3]), int(m[4]))
					lasttime = max(lasttime, d)
				print(lasttime, end="\t")
				if time.time() - lasttime.timestamp() > cfg["time_to_live"] and lasttime != datetime(1, 1, 1):
					target = (lasttime.year, lasttime.month)
					if target not in archivelist:
						archivelist[target] = []
					archivestr = str(section).strip()
					archivestr = re.sub(r"{{bot-directive-archiver\|no-archive-begin}}.+?{{bot-directive-archiver\|no-archive-end}}\n?", "", archivestr)
					archivelist[target].append(archivestr)
					count += 1
					section.remove(section)
					print("archive", end="\t")
				break
			break
	print()

text = str(wikicode)
if cupage.text == text:
	exit("nothing changed")

pywikibot.showDiff(cupage.text, text)
cupage.text = text
cupage.save(summary=cfg["main_page_summary"].format(count), minor=False)

for target in archivelist:
	targetpage = pywikibot.Page(site, cfg["archive_page_name"].format(target[0], target[1]))
	text = targetpage.text
	print(targetpage.title())
	if not targetpage.exists():
		text = cfg["archive_page_preload"]
	text += "\n\n"+"\n\n".join(archivelist[target])

	pywikibot.showDiff(targetpage.text, text)
	targetpage.text = text
	targetpage.save(summary=cfg["archive_page_summary"].format(len(archivelist[target])), minor=False)
