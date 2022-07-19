#!/bin/bash
# ref: https://wikitech.wikimedia.org/wiki/Help:Toolforge/Python#Kubernetes_python_jobs

# use bash strict mode
set -euo pipefail

# create the venv
rm -rf pyvenv
python3 -m venv pyvenv

# activate it
source pyvenv/bin/activate

# upgrade pip inside the venv and add support for the wheel package format
pip install -U pip wheel

# install some concrete packages
pip install beautifulsoup4
pip install mwparserfromhell
pip install pymysql
pip install python-dateutil
pip install requests

git clone --recursive --branch stable "https://gerrit.wikimedia.org/r/pywikibot/core" $HOME/pywikibot
pip install --upgrade "setuptools>=49.4.0, !=50.0.0, <50.2.0"
cd $HOME/pywikibot
pip install -e .
