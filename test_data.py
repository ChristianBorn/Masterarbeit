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



def test_data():
    empty_entries = {}
    new_list = {}
    empty_counter = 0
    not_empty_counter = 0
    with open('Social_Links.json', 'r') as file:
        collection = json.load(file)
    for key in collection:
        if not collection[key]['all_channels']:
            empty_entries[key] = collection[key]
            empty_counter += 1
        if collection[key]['all_channels']:
            new_list[key] = collection[key]
            not_empty_counter += 1
    print('[+] Creating list with empty entries')
    print(' Number of empty entries: '+str(empty_counter))
    with open('empty_entries.json', 'w') as file:
        json.dump(empty_entries, file, indent=2)
    print('[+] Creating list without empty entries')
    print(' Number of entries: '+str(not_empty_counter))
    with open('Social_Links_filtered.json', 'w') as file:
        json.dump(new_list, file, indent=2)

def test_redirect():
    link = 'http://www.guetersloh.de'
    driver = webdriver.Chrome()
    driver.get(link)
    print(driver.current_url)
    driver.close()
    # req = urllib.request.Request(link)
    # opener = urllib.request.build_opener()
    # #website = urllib.request.urlopen(req)
    # website = opener.open(req)
    # r = requests.get(link, allow_redirects=True)
    # print(r.history)
    # print(website.info())
    # print(website)



def main():
    test_data()    
    #test_redirect()
if __name__ == '__main__':
    main()