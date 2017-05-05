#!/usr/bin/env python3
import os

os.system('pyinstaller -n pipeline -F main.py')
os.system('cp -f ./dist/pipeline .')
