"""
This is a setup.py script generated by py2applet

Usage:
    python setup.py py2app
"""

from setuptools import setup

APP = ['apply_perma.py']
DATA_FILES = ['footnotes/config.json', 'footnotes/abbreviations.txt']
OPTIONS = {
    'packages': ['footnotes', 'aiohttp', 'multidict'],
    'argv_emulation': True,
    'plist': {
        'CFBundleIdentifier': 'org.yalelawjournal.Autopull',
        'CFBundleURLTypes': ['file'],
    }
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
