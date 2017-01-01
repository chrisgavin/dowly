#!/usr/bin/env python3
from setuptools import setup

setup(
	name="dowly",
	version="0.0.1",
	description="A simple tool for downloading all the files from a generated web server directory listing.",
	url="https://github.com/chrisgavin/open-directory-downloader",
	packages=["dowly"],
	install_requires=[
		"requests",
		"bs4"
	],
	entry_points={
		"console_scripts":[
			"dowly = dowly.__main__:main"
		]
	},
	classifiers=[
		"Programming Language :: Python :: 3"
	]
)
