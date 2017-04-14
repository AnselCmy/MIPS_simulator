#!/usr/bin/env python3
import os

os.system('pyinstaller -F single_cycle.py')
os.system('cp -f ./dist/single_cycle .')
