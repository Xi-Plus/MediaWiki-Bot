import json
import os
import re
import sys
import unittest

BASE_DIR = os.path.realpath(os.path.join(
    os.path.dirname(os.path.realpath(__file__)), '..'))

os.environ["PYWIKIBOT_DIR"] = BASE_DIR
import pywikibot

sys.path.append(BASE_DIR)
from config import *


os.environ["TZ"] = "UTC"

site = pywikibot.Site()
site.login()

config_page = pywikibot.Page(site, config_page_name)
cfg = config_page.text
cfg = json.loads(cfg)
print(json.dumps(cfg, indent=4, ensure_ascii=False))


def readfile(filename):
    with open(os.path.join(BASE_DIR, 'unit_tests/file/infobox/{0}.txt'.format(filename))) as f:
        result = f.read()
    return result


class TestInfoboxMethods(unittest.TestCase):

    def test_all(self):
        test_cnt = 3
        imagename = 'Example image.png'
        imagename_new = 'Example image new.png'
        imageregex = "[" + imagename[0].upper() + \
            imagename[0].lower() + "]" + re.escape(imagename[1:])
        imageregex = imageregex.replace("\\ ", "[ _]")
        print('imagename =', imagename)
        print('imageregex =', imageregex)
        regex = cfg['regex']['infobox']['pattern'].format(imageregex)

        for fid in range(1, test_cnt + 1):
            print(fid)
            text = readfile('{0}_in'.format(fid))

            existother = 'en'
            existothername = '英文維基百科'

            # comment_other
            replace = cfg['regex']['infobox']['replace']['comment_other'].format(
                existothername)
            output1 = re.sub(regex, replace, text, flags=re.M)
            output2 = readfile('{0}_comment_other'.format(fid))
            self.assertEqual(output1, output2)

            # moved
            replace = cfg['regex']['infobox']['replace']['moved'].format(
                imagename_new)
            output1 = re.sub(regex, replace, text, flags=re.M)
            output2 = readfile('{0}_moved'.format(fid))
            self.assertEqual(output1, output2)

            # deleted_comment
            replace = cfg['regex']['infobox']['replace']['deleted_comment']
            output1 = re.sub(regex, replace, text, flags=re.M)
            output2 = readfile('{0}_deleted_comment'.format(fid))
            self.assertEqual(output1, output2)

            # deleted
            replace = cfg['regex']['infobox']['replace']['deleted']
            output1 = re.sub(regex, replace, text, flags=re.M)
            output2 = readfile('{0}_deleted'.format(fid))
            self.assertEqual(output1, output2)

            # comment
            replace = cfg['regex']['infobox']['replace']['comment']
            output1 = re.sub(regex, replace, text, flags=re.M)
            output2 = readfile('{0}_comment'.format(fid))
            self.assertEqual(output1, output2)


if __name__ == '__main__':
    unittest.main()
