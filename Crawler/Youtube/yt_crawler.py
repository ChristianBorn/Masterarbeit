#!/usr/bin/python
# -*- coding: utf-8 -*-

import time
import json
import requests
from Database import database_interaction
from Database import database_setup
from apiclient.discovery import build

DEVELOPER_KEY = 'AIzaSyBGx9aV4FNp8spikeDSoE4jlQcCLMqltTo'
YOUTUBE_API_SERVICE_NAME = 'youtube'
YOUTUBE_API_VERSION = 'v3'

def get_videos(link, city):
    print('[+] Getting videos for city: '+city)
    videos = {}
    youtube = build(YOUTUBE_API_SERVICE_NAME,YOUTUBE_API_VERSION, developerKey=DEVELOPER_KEY)
    results_for_url = youtube.search().list(q=link,part='id,snippet').execute()
    channel_id = results_for_url['items'][0]['id']['channelId']
    user_name = results_for_url['items'][0]['snippet']['title']

    search_results = youtube.search().list(channelId=channel_id,part='id,snippet', type='video').execute()
    print('[+] Number of results retrieved: '+str(search_results['pageInfo']['totalResults']))
    next_page = search_results['nextPageToken']
    for elem in search_results['items']:
        videos[elem['id']['videoId']] = {'creation_date': elem['snippet']['publishedAt'],
                                         'title': elem['snippet']['title'],
                                         'desctiption': elem['snippet']['description']}
        # print(elem['id']['videoId'])
        # print(elem['snippet'])
    while next_page != 'last_page':
        try:
            search_results = youtube.search().list(channelId=channel_id, part='id,snippet', type='video', pageToken=next_page).execute()
            next_page = search_results['nextPageToken']
            for elem in search_results['items']:
                videos[elem['id']['videoId']] = {'creation_date': elem['snippet']['publishedAt'],
                                                 'title': elem['snippet']['title'],
                                                 'desctiption': elem['snippet']['description']}
        except KeyError:
            break
    for video_id in videos:
        results_comments = youtube.commentThreads().list(videoId=video_id, part='id,snippet,replies').execute()
        #comment_thread_id = results_comments['id']
        if results_comments['items']:
            for comment in results_comments['items']:
                print(comment['snippet'])
                print(comment['snippet']['topLevelComment'])
                print(comment['snippet']['topLevelComment']['snippet'])
                print(comment['snippet']['topLevelComment']['snippet']['textDisplay'])
                print('')
        # if results_comments['items']:
        #     print(results_comments['items'])
        #     print(results_comments['items'][0]['id'])
        continue
        # if results_comments['items']:
        #     print(results_comments['items'])
        results_videos = youtube.videos().list(id=video_id, part='id,snippet,statistics', pageToken=None).execute()
        for elem in results_videos['items']:
            print(elem['snippet'])
            try:
                print(elem['snippet']['tags'])
            except KeyError:
                print('No tags assigned')
                pass
            print(elem['snippet']['categoryId'])
            if results_comments['items']:
                print(results_comments['items'])
            print('')
    #print(search_results['items'])
    # for elem in results_for_url['items']:
    #     print(elem['id']['channelId'])
    # print(results_for_url['pageInfo'])

def main():
    get_videos('https://www.youtube.com/user/AhausMarketing', 'Ahaus')
if __name__ == '__main__':
    main()