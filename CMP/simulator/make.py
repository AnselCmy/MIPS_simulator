#!/usr/bin/env python3
import os

os.system('pyinstaller -n CMP -F main.py')
os.system('cp -f ./dist/CMP .')
