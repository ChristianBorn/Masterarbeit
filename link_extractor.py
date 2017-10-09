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
#from requests.exceptions import HTTPError
from urllib.error import HTTPError
from socket import error as SocketError
from http.cookiejar import CookieJar
from time import sleep

def check_social(string):
    if string == None:
        return False
    if 'share' in string or 'github' in string or 'bootstrap' in string or 'tweet' in string or 'maps' in string or 'play' in string:
        return False
    social_channels_list = ['twitter', 'facebook', 'youtube', 'google', 
                            'flickr', 'plus.google', 'instagram',
                            'linkedin', 'xing', 'pinterest',
                            'vimeo', 'foursquare', 'tumblr']
    social = False
    for elem in social_channels_list:
        if elem in string:
            social = True
    return social
    # elif 'facebook' in string or 'twitter' in string or 'youtube' in string or 'instagram' in string:
    #     return True
    # else:
    #     return False

def read_file():
    with open('Daten/170726kommunaladressen..csv', 'r') as file:
        read_input = pandas.read_csv(file, sep=';', encoding='utf-8')
    return read_input
    # for index,row in read_input.iterrows():
    #     print(row.loc['Kommune/Kreis'])
    # #print(read_input.iloc[0][:])

def get_links_test():
    #ToDo: Iteration über Dataframe
    data = pandas.DataFrame({'Kommune/Kreis':'Gütersloh','Internet':'www.guetersloh.de/'}, index=[0])
    Kommunen = {}
    social_link_filter = SoupStrainer('a', {'href':check_social})
    for index, row in data.iterrows():
        Kommune = row.loc['Kommune/Kreis']
        link = 'http://'+row.loc['Internet']
        print('[+] Getting Links for '+Kommune)
        links_dict = {}
        all_links = []
        all_channels = []
        check_again = {}
        print('[+] Opening URL '+link)
        req = urllib.request.Request(link)
        opener = urllib.request.build_opener()
        #website = urllib.request.urlopen(req)
        website = opener.open(req)
        print(BeautifulSoup(website).a)
        social_links = BeautifulSoup(website, 'html.parser',parse_only=social_link_filter)
        for social_link in social_links:
            link_href = social_link.get('href')
            parsed_uri = urlparse(link_href)
            try:
                domain = parsed_uri.hostname.split('.')[-2]
                links_dict[domain] = link_href
                all_links.append(link_href)
                all_channels.append(domain)
            except AttributeError:
                complete_link = urlparse(link).hostname+link_href
                all_links.append(complete_link)
                social_channels_list = ['twitter', 'facebook', 'youtube', 'google', 
                            'flickr', 'plus.google', 'instagram',
                            'linkedin', 'xing', 'pinterest',
                            'vimeo', 'foursquare', 'tumblr']
                for elem in social_channels_list:
                    if elem in link_href:
                        links_dict[elem] = complete_link
                        all_channels.append(elem)
        print(' [+] Number of Links: '+str(len(all_links)))
        print(' [+] Number of Channels: '+str(len(all_channels)))
        Kommunen[Kommune] = links_dict
        Kommunen[Kommune]['all_links'] = all_links
        Kommunen[Kommune]['all_channels'] = list(set(all_channels))
    print('[+] Dumping to JSON')
    with open('Social_Links_test.json', 'w') as file:
        json.dump(Kommunen, file, indent=2)
    print('[+] Done')
def get_links():
    #ToDo: Iteration über Dataframe
    data = read_file()
    #data = pandas.DataFrame({'Kommune/Kreis':'Moers','Internet':'www.moers.de'}, index=[0])
    Kommunen = {}
    social_link_filter = SoupStrainer('a', {'href':check_social})
    for index, row in data.iterrows():
        Kommune = row.loc['Kommune/Kreis']
        link = 'https://'+row.loc['Internet'].strip(' ')
        link_https = 'http://'+row.loc['Internet'].strip(' ')
        print('[+] Getting Links for '+Kommune)
        links_dict = {}
        all_links = []
        all_channels = []
        print('[+] Opening URL '+link)
        try:    
            website = urllib.request.Request(link,headers={'User-Agent' : "Magic Browser"})
            cj = CookieJar()
            opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
            website = opener.open(website)
        except:
            print('[-] Got invalid link')
            try:
                print('[+] Opening URL '+link_https)
                website = urllib.request.Request(link_https,headers={'User-Agent' : "Magic Browser"})
                cj = CookieJar()
                opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
                website = opener.open(website)
            except:
                print('[-] Got invalid link')
                with open('errors.txt', 'a') as errorlog:
                    errorlog.write(Kommune+': '+link)
                continue
        social_links = BeautifulSoup(website, 'html.parser', parse_only=social_link_filter)
        for social_link in social_links:
            link_href = social_link.get('href')
            parsed_uri = urlparse(link_href)
            try:
                domain = parsed_uri.hostname.split('.')[-2]
                links_dict[domain] = link_href
                all_links.append(link_href)
                all_channels.append(domain)
            # Falls die Kommune nur Redirects auf Ihre Kanäle hat
            except AttributeError:
                complete_link = urlparse(link).hostname+link_href
                all_links.append(complete_link)
                social_channels_list = ['twitter', 'facebook', 'youtube', 'google', 
                            'flickr', 'plus.google', 'instagram',
                            'linkedin', 'xing', 'pinterest',
                            'vimeo', 'foursquare', 'tumblr']
                for elem in social_channels_list:
                    if elem in link_href:
                        links_dict[elem] = complete_link
                        all_channels.append(elem)
        print(' [+] Number of Links: '+str(len(all_links)))
        print(' [+] Number of Channels: '+str(len(all_channels)))
        Kommunen[Kommune] = links_dict
        Kommunen[Kommune]['all_links'] = all_links
        Kommunen[Kommune]['all_channels'] = list(set(all_channels))
    print('[+] Dumping to JSON')
    with open('Social_Links.json', 'w') as file:
        json.dump(Kommunen, file, indent=2)
    print(['Done'])

        #link = link.get('href')
        #print(check_social(link))
    # print(links)
    # print(len(links))

def scrape_links(data,results)

def main():
    #get_links()
    get_links_test()
    #read_file()

if __name__ == '__main__':
    main()