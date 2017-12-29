#!/usr/bin/python
# -*- coding: utf-8 -*-

import time
import json
import requests
from Database import database_interaction
from Database import database_setup
from apiclient.discovery import build
from googleapiclient.errors import HttpError
import urllib.request
from bs4 import BeautifulSoup
from bs4 import SoupStrainer
from urllib.parse import urlparse
from link_extractor import open_website


DEVELOPER_KEY = 'AIzaSyBGx9aV4FNp8spikeDSoE4jlQcCLMqltTo'
YOUTUBE_API_SERVICE_NAME = 'youtube'
YOUTUBE_API_VERSION = 'v3'

def get_channel_id(link):
    website = open_website(link)
    channel_page = BeautifulSoup(website, 'html.parser')
    channel_page = json.loads(channel_page.find('script', type='application/ld+json').text)
    channel_id = channel_page['url'].split('/')[-1]
    return channel_id


def get_videos(link, city):
    conn_objects = database_interaction.connect_to_db('../../Database/main_data.db')
    print('[+] Getting videos for city: '+city)
    videos_data = {}
    youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, developerKey=DEVELOPER_KEY)
    channel_id = get_channel_id(link)
    # results_for_url = youtube.search().list(q=link.split('/')[-1], part='id,snippet', type='channel').execute()
    # try:
    #     channel_id = results_for_url['items'][0]['id']['channelId']
    #     user_name = results_for_url['items'][0]['snippet']['title']
    #     # for elem in results_for_url['items']:
    #     #         print(link.split('/')[-1])
    #     #         print(elem)
    #     #         if elem['snippet']['title'] == link.split('/')[-1]:
    #     #             channel_id = elem['id']['channelId']
    #     #             user_name = elem['snippet']['title']
    # except IndexError:
    #     with open('errors.txt','w') as errorlog:
    #         errorlog.write(city+': '+link+'\n')
    #     print('[-] Encountered error')
    #     return


    search_results = youtube.search().list(channelId=channel_id, part='id,snippet', type='video').execute()
    print('-- Number of results retrieved: '+str(search_results['pageInfo']['totalResults']))
    next_page = search_results['nextPageToken']
    #Todo: Einzelne VideoIds nochmal mit videos.list abrufen und die komplette Description extrahieren https://developers.google.com/youtube/v3/docs/videos/list
    for elem in search_results['items']:
        description = elem['snippet']['description']
        # Check if description is empty
        if not description:
            description = None
        videos_data[elem['id']['videoId']] = {'creation_date': elem['snippet']['publishedAt'],
                                         'title': elem['snippet']['title'],
                                         'description': description}
        # print(elem['id']['videoId'])
        # print(elem['snippet'])
    while next_page != 'last_page':
        try:
            search_results = youtube.search().list(channelId=channel_id, part='id,snippet', type='video', pageToken=next_page).execute()
            next_page = search_results['nextPageToken']
            for elem in search_results['items']:
                description = elem['snippet']['description']
                # Check if description is empty
                if not description:
                    description = None
                videos_data[elem['id']['videoId']] = {'creation_date': elem['snippet']['publishedAt'],
                                                      'title': elem['snippet']['title'],
                                                      'description': description}
        except KeyError:
            break
    for video_id in videos_data:
        try:
            results_comments = youtube.commentThreads().list(videoId=video_id, part='id,snippet').execute()
            #comment_thread_id = results_comments['id']
            videos_data[video_id]['comments'] = []
            videos_data[video_id]['comment_count'] = 0
            if results_comments['items']:
                videos_data[video_id]['comment_count'] = len(results_comments['items'])
                for comment in results_comments['items']:
                    videos_data[video_id]['comments'].append(comment['snippet']['topLevelComment']['snippet'])
            videos_data[video_id]['commentable'] = True
        except HttpError:
            videos_data[video_id]['commentable'] = False
            videos_data[video_id]['comment_count'] = 0
        results_videos = youtube.videos().list(id=video_id, part='id,snippet,statistics', pageToken=None).execute()
        for elem in results_videos['items']:
            try:
                videos_data[video_id]['tags'] = ','.join(elem['snippet']['tags'])
            except KeyError:
                videos_data[video_id]['tags'] = None
                pass
            videos_data[video_id]['category'] = elem['snippet']['categoryId']
            videos_data[video_id]['view_count'] = elem['statistics']['viewCount']
            try:
                videos_data[video_id]['like_count'] = elem['statistics']['likeCount']
                videos_data[video_id]['dislike_count'] = elem['statistics']['dislikeCount']
            except KeyError:
                videos_data[video_id]['like_count'] = None
                videos_data[video_id]['dislike_count'] = None
            videos_data[video_id]['favorite_count'] = elem['statistics']['favoriteCount']
    for video_id in videos_data:
        insert_list = [video_id]
        for attribute in videos_data[video_id]:
            if type(videos_data[video_id][attribute]) == list and len(videos_data[video_id][attribute]) == 0:
                videos_data[video_id][attribute] = None
            if attribute != 'comments':
                insert_list.append(videos_data[video_id][attribute])
        insert_list.append(city)
        print('Inserting in Database...')
        database_interaction.insert_values_into('yt_videos',insert_list,conn_objects['Connection'],
                                                        conn_objects['Cursor'])
    #print(search_results['items'])
    # for elem in results_for_url['items']:
    #     print(elem['id']['channelId'])
    # print(results_for_url['pageInfo'])


def main():
    # Reset the fb_posts and fb_comments tables
    with open('../../Daten/Social_Links_final.json', 'r') as file:
        link_dict = json.load(file)
        for city in link_dict:
            try:
                get_videos(link_dict[city]['youtube'], city)
            except KeyError:
                print('[-] ' + city + ' has no YT Link')
    #get_videos('https://www.youtube.com/user/AhausMarketing', 'Ahaus')
    #get_channel_id('https://www.youtube.com/user/StadtDuisburg')
    # for city in link_dict:
    #     try:
    #         get_channel_id(link_dict[city]['youtube'])
    #     except KeyError:
    #         print('[-] ' + city + ' has no YT Link')
if __name__ == '__main__':
    main()