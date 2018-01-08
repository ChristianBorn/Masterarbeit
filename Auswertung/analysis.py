#!/usr/bin/python
# -*- coding: utf-8 -*-


import dateutil.parser
import json
import requests
from Database import database_interaction


def format_fb_dates():
    connection_object = database_interaction.connect_to_db('../Database/main_data.db')
    fb_data = database_interaction.get_data('fb_posts', ['post_id', 'creation_date'],
                                            connection_object['Connection'])
    for row in fb_data:
        connection_object['Cursor'].execute("UPDATE fb_posts SET creation_date=? WHERE post_id=?",
                                            (dateutil.parser.parse(row['creation_date'], ignoretz=True), row['post_id']))
        print(row['post_id'])
    connection_object['Connection'].commit()

def create_dataset():
    connection_object = database_interaction.connect_to_db('../Database/main_data.db')
    min_date_twitter = database_interaction.get_data('tweets', ['MIN(creation_date)'], connection_object['Connection'], min_max=True).fetchone()[0]
    max_date_twitter = database_interaction.get_data('tweets', ['MAX(creation_date)'], connection_object['Connection'], min_max=True)
    max_date_fb = database_interaction.get_data('fb_posts', ['MAX(creation_date)'], connection_object['Connection'], min_max=True)
    max_date_yt = database_interaction.get_data('yt_videos', ['MAX(creation_date)'], connection_object['Connection'], min_max=True)
    max_date_all = min([max_date_fb.fetchone()[0], max_date_twitter.fetchone()[0], max_date_yt.fetchone()[0]])
    max_date_all = str(dateutil.parser.parse(max_date_all, ignoretz=True))
    twitter_data = database_interaction.get_data('tweets', ['tweet_id', 'city','creation_date', 'tweet_text'],
                                                 connection_object['Connection'], before=max_date_all,
                                                 after=min_date_twitter)
    fb_data = database_interaction.get_data('fb_posts', ['post_id', 'city', 'creation_date', 'message', 'description'],
                                                 connection_object['Connection'], before=max_date_all,
                                                 after=min_date_twitter)
    yt_data = database_interaction.get_data('yt_videos', ['video_id', 'city', 'creation_date', 'title', 'description', 'tags'],
                                            connection_object['Connection'], before=max_date_all,
                                            after=min_date_twitter)
    for row in fb_data:
        print(row.keys())

def main():
    create_dataset()
    #format_fb_dates()

if __name__ == '__main__':
    main()


