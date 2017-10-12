#!/usr/bin/python
# -*- coding: utf-8 -*-

import urllib.request
from bs4 import BeautifulSoup
from bs4 import SoupStrainer
from urllib.parse import urlparse
import requests
import json
import codecs
import pandas
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
#from requests.exceptions import HTTPError
from urllib.error import HTTPError
from socket import error as SocketError
from http.cookiejar import CookieJar
from collections import Counter
import helpers

def count_channels(filepath):
    channels = []
    with open(filepath, 'r') as file:
        contents = json.load(file)
    for key in contents:
        for channel in contents[key]['all_channels']:
            channels.append(channel)
    counted_channels = dict(Counter(channels))
    counted_channels = helpers.sort_dict(counted_channels)
    with open('Channel_count.json', 'w') as file:
        json.dump(counted_channels, file, indent=2)
    print(counted_channels)

def main():
    count_channels('Social_Links_filtered.json')
if __name__ == '__main__':
    main()