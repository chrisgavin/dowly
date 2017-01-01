#!/usr/bin/env python3
import argparse
import logging
import os
import urllib
import sys

import requests
from bs4 import BeautifulSoup

_LOGGER = logging.getLogger("dowly")
_HANDLER = logging.StreamHandler(sys.stderr)
_LOGGER.addHandler(_HANDLER)
_FORMATTER = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s: %(message)s")
_HANDLER.setFormatter(_FORMATTER)

_CHUNK_SIZE = 1024

def get_listing(directory):
	_LOGGER.debug("Getting listing of %s.", directory)
	response = requests.get(directory)
	soup = BeautifulSoup(response.content, "lxml")
	links = soup.findAll("a")
	absolute_links = []
	for link in links:
		if link.has_attr("href"):
			relative_link = link.get("href")
			absolute_link = urllib.parse.urljoin(response.url, relative_link)
			absolute_links += [absolute_link]
	filtered_links = set()
	for absolute_link in absolute_links:
		parsed_link = urllib.parse.urlsplit(absolute_link)
		if parsed_link.query or parsed_link.fragment:
			continue
		if not absolute_link.startswith(response.url):
			continue
		if absolute_link == response.url:
			continue
		filtered_links.add(absolute_link)
	return filtered_links

def get_recursive_listing(directory):
	_LOGGER.info("Listing directory %s.", directory)
	top_level_listing = get_listing(directory)
	found_links = set()
	for link in top_level_listing:
		if link.endswith("/"):
			found_links.update(get_recursive_listing(link))
		else:
			found_links.add(link)
	return found_links

def get_target_directory(root, link):
	target = link[len(root):]
	target = urllib.parse.unquote(target)
	split = os.path.splitext(target)
	target = split[0] + split[1].lower()
	return (link, target)

def filter_existing(destination, links):
	filtered = set()
	for link in links:
		path = os.path.join(destination, link[1])
		if not os.path.exists(path):
			filtered.add(link)
		elif not os.path.isfile(path):
			raise Exception("The path %s exists, but it is not a file." % path)
	return filtered

def download_links(destination, links):
	_LOGGER.info("Found %d files to download.", len(links))
	for i, link in enumerate(links):
		_LOGGER.info("Downlading file %s (%d/%d).", link[1], i, len(links))
		target = os.path.join(destination, link[1])
		target_dir = os.path.dirname(target)
		if not os.path.isdir(target_dir):
			if os.path.exists(target_dir):
				raise Exception("%s exists but it is not a directory." % target_dir)
			_LOGGER.debug("Making directory %s.", target_dir)
			os.makedirs(target_dir)
		response = requests.get(link[0], stream=True)
		with open(target, "wb") as target_file:
			for chunk in response.iter_content(chunk_size=_CHUNK_SIZE):
				target_file.write(chunk)
				target_file.flush()

def main():
	parser = argparse.ArgumentParser(description="Tool for downloading the contents of an open directory.")
	parser.add_argument("url", help="The URL to download from.")
	parser.add_argument("--destination", help="The place to download files to.", default=".")
	parser.add_argument("--verbose", help="Output more log messages.", action="store_true")
	args = parser.parse_args()
	_LOGGER.setLevel(logging.DEBUG if args.verbose else logging.INFO)

	links = get_recursive_listing(args.url)
	_LOGGER.info("Finished getting directory listing. %d files found.", len(links))
	links = {get_target_directory(args.url, link) for link in links}
	links = filter_existing(args.destination, links)
	download_links(args.destination, links)

if __name__ == "__main__":
	main()
