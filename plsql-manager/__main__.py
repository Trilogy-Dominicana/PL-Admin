#!/usr/bin/python
from __future__ import absolute_import
import sys, getopt, json, os


# from dotenv import load_dotenv
from vivapl.database import Database 
from vivapl.files import Files
# from pip._internal.main import main as _main  # isort:skip # noqa



def _main():
    files = Files()
    db = Database()
    

if __name__ == '__main__':
    sys.exit(_main())