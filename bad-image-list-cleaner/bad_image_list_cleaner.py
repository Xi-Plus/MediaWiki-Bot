import re
import pywikibot
import functools


class BadImageListCleaner:
    def __init__(self, site, cfg):
        self.site = site
        self.cfg = cfg

    @functools.lru_cache()
    def checkTitle(self, title):
        page = pywikibot.Page(self.site, title)
        if not page.exists():
            # print(title, 'is not exists')
            return None
        if page.isRedirectPage():
            # print(title, 'is a redirect')
            newTitle = page.getRedirectTarget().title()
            if '#' in newTitle:
                return None
            return newTitle
        return title

    def fixLine(self, text):
        m = re.search(r'^\* *\[\[:(File:.+?)\]\]', text)
        if not m:
            return text

        fileName = m.group(1)

        m = re.search(r'except on(.+?)$', text)
        newTitles = []
        if m:
            titles = re.findall(r'\[\[([^\]|]+)\]\]', m.group(1))
            for title in titles:
                newTitle = self.checkTitle(title)
                if newTitle:
                    newTitles.append(title)
        newText = '* [[:{}]]'.format(fileName)
        if len(newTitles) > 0:
            newText += ' except on '
            newTitles = list(map(lambda t: '[[{}]]'.format(t), newTitles))
            newText += ', '.join(newTitles)

        return newText

    def main(self):
        badPage = pywikibot.Page(self.site, 'MediaWiki:Bad image list')
        text = badPage.text
        lines = text.split('\n')
        for idx, line in enumerate(lines):
            newLine = self.fixLine(line)
            if line != newLine:
                lines[idx] = newLine
        newText = '\n'.join(lines)

        badPage.text = newText
        badPage.save(summary=self.cfg['summary'], minor=False, botflag=False)
