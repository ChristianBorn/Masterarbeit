#!/usr/bin/python
# -*- coding: utf-8 -*-

import sqlite3

conn = sqlite3.connect('main_data.db')
c = conn.cursor()

c.execute('''DROP TABLE if exists test_table''')
c.execute('''CREATE TABLE test_table
            (tweet_id INTEGER,
            tweet_text TEXT
            )''')
c.execute('''DROP TABLE if exists tweets''')
c.execute('''CREATE TABLE tweets
            (tweet_id TEXT,
            screenname TEXT,
            municipality TEXT,
            date TEXT,
            tweet_text TEXT,
            source TEXT,
            reply_to TEXT,
            is_quote INTEGER,
            retweeted_count INTEGER,
            favorited_count INTEGER,
            hashtags TEXT,
            retweeted_text TEXT,
            retweeted_user TEXT
            )''')