#!/usr/bin/python
# -*- coding: utf-8 -*-

import sqlite3


def create_table_tweets():
    conn = sqlite3.connect('main_data.db')
    c = conn.cursor()
    c.execute('''DROP TABLE if exists tweets''')
    #ToDo: Datenbank für Medien aus Tweets erweitern
    c.execute('''CREATE TABLE tweets
                (tweet_id TEXT,
                screenname TEXT,
                municipality TEXT,
                creation_date TEXT,
                tweet_text TEXT,
                source TEXT,
                reply_to TEXT,
                is_quote INTEGER,
                retweeted_count INTEGER,
                favorited_count INTEGER,
                hashtags TEXT,
                retweeted_text TEXT,
                retweeted_user TEXT,
                is_retweet INTEGER
                )''')
    conn.commit()
    conn.close()
def create_table_fb_posts(path_to_db):
    conn = sqlite3.connect(path_to_db)
    c = conn.cursor()
    c.execute('''DROP TABLE if exists fb_posts''')
    print('[+] Creating table fb_posts')
    # ToDo: Datenbank für Medien aus Posts erweitern
    c.execute('''CREATE TABLE fb_posts (
        post_id	TEXT,
        user_id TEXT,
        city TEXT,
        creation_date TEXT,
        message	TEXT,
        description TEXT,
        comment_count INTEGER,
        shares_count INTEGER,
        likes_count	INTEGER,
        reactions_count	INTEGER,
        type TEXT
    )''')
    conn.commit()
    conn.close()
def create_table_fb_comments(path_to_db):
    conn = sqlite3.connect(path_to_db)
    c = conn.cursor()
    c.execute('''DROP TABLE if exists fb_comments''')
    print('[+] Creating table fb_comments')
    c.execute('''CREATE TABLE `fb_comments` (
        `comment_id`	TEXT,
        `post_id` TEXT,
        `creation_date`	TEXT,
        `message`	TEXT,
        `commenter_id`	TEXT,
        `reply_to_user`	TEXT,
        `reply_to_user_city`	TEXT,
        FOREIGN KEY(`post_id`) REFERENCES fb_posts(`post_id`) ON DELETE CASCADE
    );''')
    conn.commit()
    conn.close()


def create_table_yt_videos():
    conn = sqlite3.connect('main_data.db')
    c = conn.cursor()
    c.execute('''DROP TABLE if exists yt_videos''')
    print('[+] Creating table yt_videos')
    c.execute('''CREATE TABLE `yt_videos` (
    `video_id`	TEXT,
    `creation_date`	TEXT,
    `title`	TEXT,
    `description`	TEXT,
    `comment_count`	INTEGER,
    `tags`	TEXT,
    `category`	INTEGER,
    `view_count`	INTEGER,
    `likes_count`	INTEGER,
    `dislike_count`	INTEGER,
    `favorite_count`	INTEGER
);''')
    conn.commit()
    conn.close()

def complete_setup():
    create_table_tweets()
    create_table_fb_posts()
    create_table_fb_comments()