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
import link_extractor



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

def resolve_redirects():
    final_channels = ['facebook', 'twitter', 'youtube']
    not_used = ['google', 'flickr', 'plus.google', 'instagram',
                            'linkedin', 'xing', 'pinterest',
                            'vimeo', 'foursquare', 'tumblr']
    links_dict = {}
    links_dict_fb = {}
    links_dict_yt = {}
    links_dict_tw = {}
    with open('Social_Links_filtered.json', 'r') as file:
        collection = json.load(file)
    for key in collection:
        links_dict[key] = {}
        for social_link_key in collection[key]['link_per_channel']:
            link = collection[key]['link_per_channel'][social_link_key]
            
            try:
                parsed_uri = urlparse(link)
                social_link_domain = parsed_uri.hostname.split('.')[-2]
                if social_link_domain in final_channels:
                    print('[+] Following Link is valid for further processing: ')
                    print(link)
                    links_dict[key][social_link_key] = link
                    continue
                elif social_link_domain in not_used:
                    print('[-] Following Link belongs to invalid channel: ')
                    print(link)
                    continue
                else:
                    print('[+] Following Link needs to be checked: ')
                    print(link)
                    resolved_url = link_extractor.get_url_by_selenium(link)
                if urlparse(resolved_url).hostname.split('.')[-2] in final_channels:
                    links_dict[key][social_link_key] = resolved_url
                    print('[+] Following Link was retrieved by following redirect and is valid: ')
                    print(resolved_url)
                else:
                    print('[-] Link behind redirect is still invalid: ')
                    print(resolved_url)
                    continue
            except:
                print('[-] An error occured with the following link: ')
                print(link)
                resolved_url = link_extractor.get_url_by_selenium('http://'+link)
                if urlparse(resolved_url).hostname.split('.')[-2] in final_channels:
                    links_dict[key][social_link_key] = resolved_url
                    print('[+] Following Link was retrieved by following redirect and is valid: ')
                    print(resolved_url)
                else:
                    print('[-] Link behind redirect is still invalid: ')
                    print(resolved_url)
                    continue
    with open('Social_Links_final.json', 'w') as file:
        json.dump(links_dict, file, indent=2)
    # for key in collection:
    #     print(key)
    #     for social_link_key in collection[key]:
    #         if type(collection[key][social_link_key]) != list:
    #             try:
    #                 parsed_uri = urlparse(collection[key][social_link_key])
    #                 social_link_domain = parsed_uri.hostname.split('.')[-2]
    #                 if social_link_domain != social_link_key:
    #                     print(link_extractor.get_url_by_selenium(collection[key][social_link_key]))
    #             except:
    #                 print(collection[key][social_link_key])
    #                 print(link_extractor.get_url_by_selenium('https://'+collection[key][social_link_key]))

def main():
    #test_data()   
    resolve_redirects() 
    #test_redirect()
if __name__ == '__main__':
    main()