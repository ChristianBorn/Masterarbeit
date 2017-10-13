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
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import test_data
import analyse_data

def check_social(string):
    if string == None:
        return False
    forbidden_terms = ['embedded', 'embed', 'share', 'github', 'bootstrap', 'tweet', 'maps', 'play', 'javascript', 'translate', 'rss', 'datenschutzhinweis', 'neuigkeiten', 'googlemap', '.pdf', '.jpg', 'player_embedded']
    for term in forbidden_terms:
        if term in string:
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
    data = read_file()
    #data = pandas.DataFrame({'Kommune/Kreis':'Moers','Internet':'www.staatsbad-salzuflen.de'}, index=[0])
    Kommunen = {}
    social_link_filter = SoupStrainer('a', {'href':check_social})
    counter = 0
    check_num = data.shape[0]
    selenium_num = 0
    error_num = 0
    social_channels_list = ['twitter', 'facebook', 'youtube', 'google', 
                            'flickr', 'plus.google', 'instagram',
                            'linkedin', 'xing', 'pinterest',
                            'vimeo', 'foursquare', 'tumblr']
    with open('errors.txt', 'w') as errorlog:
        errorlog.write('')
    for index, row in data.iterrows():
        Kommunenchef_titel = row.loc['Titel HVB']
        if Kommunenchef_titel.startswith('Land'):
            continue
        counter += 1
        Kommune = row.loc['Kommune/Kreis']
        link = 'http://'+row.loc['Internet'].strip(' ')
        link_https = 'https://'+row.loc['Internet'].strip(' ')
        print('[+] Getting Links for '+Kommune)
        links_dict = {}
        all_links = []
        all_channels = []
        # Abrufen der Website, erst ein http-Link, wenn fehlgeschlagen mit https
        print('[+] Opening URL '+link)
        try:    
            website = open_website(link)
        except:
            print('[-] Got invalid link')
            error_num += 1
            with open('errors.txt', 'a') as errorlog:
                errorlog.write(Kommune+': '+link)
            try:
                print('[+] Opening URL '+link_https)
                website = open_website(link_https)
            except:
                print('[-] Got invalid link')
                error_num += 1
                with open('errors.txt', 'a') as errorlog:
                    errorlog.write(Kommune+': '+link)
                continue
        social_links = BeautifulSoup(website, 'html.parser', parse_only=social_link_filter)
        # Check, wenn social_links leer ist, ob es eine Weiterleitung von der Homepage gibt
        if len(social_links) == 0:
            try:    
                link = get_url_by_selenium(link)
                print(link)
                website = open_website(link)
                selenium_num += 1
            except:
                error_num += 1
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
                if domain in social_channels_list:
                    links_dict[domain] = link_href
                    all_links.append(link_href)
                    all_channels.append(domain)
                else:
                    raise AttributeError
            # Falls die Kommune nur Redirects auf Ihre Kanäle hat
            except AttributeError:
                # Überprüfung, ob der Redirect über einen relativen oder absoluten Link erfolgt
                if link_href.startswith('https') or link_href.startswith('http'):
                    complete_link = link_href
                    all_links.append(complete_link)
                # Falls relativer Link, muss Domain vor den relativen Link gesetzt werden
                else:
                    if link_href.startswith('/'):
                        complete_link = urlparse(link).hostname+link_href
                        all_links.append(complete_link)
                    else:
                        complete_link = urlparse(link).hostname+'/'+link_href
                        all_links.append(complete_link)
                for elem in social_channels_list:
                    if elem in link_href:
                        links_dict[elem] = complete_link
                        all_channels.append(elem)
        print(' [+] Number of Links: '+str(len(all_links)))
        print(' [+] Number of Channels: '+str(len(all_channels)))
        Kommunen[Kommune] = {}
        Kommunen[Kommune]['link_per_channel'] = links_dict
        Kommunen[Kommune]['all_links'] = all_links
        Kommunen[Kommune]['all_channels'] = list(set(all_channels))
    print('[+] Dumping to JSON')
    with open('Social_Links.json', 'w') as file:
        json.dump(Kommunen, file, indent=2)
    print('Number of Links checked: '+str(counter)+' of '+str(check_num))
    print('Number of selenium openings: '+str(selenium_num))
    print('Number of errors in URLs: '+str(error_num))
    print(['Done'])

        #link = link.get('href')
        #print(check_social(link))
    # print(links)
    # print(len(links))
def get_url_by_selenium(link):
    driver = webdriver.Chrome()
    driver.get(link)
    url = driver.current_url
    driver.close()
    return url
def open_website(link):
    website = urllib.request.Request(link,headers={'User-Agent' : "Magic Browser"})
    cj = CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    website = opener.open(website)
    return website

def main():
    get_links()
    test_data.main()
    analyse_data.main()
    #get_links_test()
    #read_file()

if __name__ == '__main__':
    main()