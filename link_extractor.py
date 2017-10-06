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

def check_social(string):
    if string == None:
        return False
    if 'share' in string:
        return False
    elif 'facebook' in string or 'twitter' in string or 'youtube' in string or 'instagram' in string:
        return True
    else:
        return False

def read_file():
    with open('Daten/170726kommunaladressen..csv', 'r') as file:
        read_input = pandas.read_csv(file, sep=';', encoding='utf-8')
    return read_input
    # for index,row in read_input.iterrows():
    #     print(row.loc['Kommune/Kreis'])
    # #print(read_input.iloc[0][:])

def get_links():
    #ToDo: Iteration über Dataframe
    data = read_file()
    Kommunen = {}
    social_link_filter = SoupStrainer('a', {'href':check_social})
    linklist = ['https://www.duesseldorf.de/']
    for link in linklist:
        links_dict = {}
        all_links = []
        all_channels = []
        website = urllib.request.urlopen(link)
        social_links = BeautifulSoup(website, 'html.parser', parse_only=social_link_filter)
        for link in social_links:
            parsed_uri = urlparse(link.get('href'))
            domain = parsed_uri.hostname
            domain = domain.split('.')[-2]
            links_dict[domain] = link.get('href')
            all_links.append(link.get('href'))
            all_channels.append(domain)
        Kommunen['Düsseldorf'] = links_dict
        Kommunen['Düsseldorf']['all_links'] = all_links
        Kommunen['Düsseldorf']['all_channels'] = list(set(all_channels))
    print(Kommunen)
        #link = link.get('href')
        #print(check_social(link))
    # print(links)
    # print(len(links))

def main():
    get_links()
    #read_file()

if __name__ == '__main__':
    main()