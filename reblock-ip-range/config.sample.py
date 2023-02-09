# -*- coding: utf-8 -*-
config_page_name = ''

import configparser
import os
host = 'zhwiki.analytics.db.svc.eqiad.wmflabs'

reader = configparser.ConfigParser()
reader.read(os.path.expanduser('~/replica.my.cnf'))
user = reader.get('client', 'user')
password = reader.get('client', 'password')
