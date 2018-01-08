#!/usr/bin/python
# -*- coding: utf-8 -*-


import os
import dateutil.parser
import spacy
import json
#import de_core_news_md
import requests
from Database import database_interaction
from helpers import sort_dict
from spacy.attrs import ORTH, LEMMA
from spacy.tokenizer import Tokenizer
import regex as re
from spacy.util import update_exc
from stop_words import get_stop_words


def preprocess_string(input_string):
    words_to_replace = re.findall('Open\s+\w*', input_string, flags=re.IGNORECASE)
    input_string.replace('\n', '')
    for word in words_to_replace:
        input_string = input_string.replace(word, word.replace(' ', ''))

    return input_string


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
                                                 after=min_date_twitter).fetchall()
    fb_data = database_interaction.get_data('fb_posts', ['post_id', 'city', 'creation_date', 'message', 'description'],
                                                 connection_object['Connection'], before=max_date_all,
                                                 after=min_date_twitter).fetchall()
    yt_data = database_interaction.get_data('yt_videos', ['video_id', 'city', 'creation_date', 'title', 'description', 'tags'],
                                            connection_object['Connection'], before=max_date_all,
                                            after=min_date_twitter).fetchall()
    bag_of_words = []
    list_of_docs = []
    nlp = spacy.load('de')
    #nlp.tokenizer.add_special_case(u'Open\sAir', [{ORTH: 'Open\sAir'}])
    stop_word_list = get_stop_words('de')
    stop_word_list.extend(['.', ',', '-', '_', ';', ':', '?', '!', '#', '"'])

    length_twitter = len(twitter_data)
    length_fb = len(fb_data)
    length_yt = len(yt_data)
    counter = 1
    for row in twitter_data:
        if counter % 1000 == 0:
            print('Iterating Twitter Data '+str(counter)+'/'+str(length_twitter))
        help_list = []
        tokens = nlp(preprocess_string(row['tweet_text'].decode('utf-8')))
        for token in tokens:
            if not token.is_punct:
                help_list.append(token.lemma_)
        help_list = list(set(help_list) - set(stop_word_list))
        bag_of_words.extend(help_list)
        list_of_docs.append(help_list)
        counter += 1
    counter = 1
    for row in fb_data:
        if counter % 1000 == 0:
            print('Iterating FB Data '+str(counter)+'/'+str(length_fb))
        if not row['message'] and not row['description']:
            continue
        help_list = []
        if row['message'] and row['description']:
            string_data = row['message'] + ' ' + row['description']
        elif row['message']:
            string_data = row['message']
        elif row['description']:
            string_data = row['description']
        tokens = nlp(preprocess_string(string_data))
        for token in tokens:
            if not token.is_punct:
                help_list.append(token.lemma_)
        help_list = list(set(help_list) - set(stop_word_list))
        bag_of_words.extend(help_list)
        list_of_docs.append(help_list)
        counter += 1
    counter = 1
    for row in yt_data:
        if counter % 1000 == 0:
            print('Iterating YT Data '+str(counter)+'/'+str(length_yt))
        string_data = row['title']
        help_list = []
        if row['description']:
            string_data = string_data + ' ' + row['description']
        if row['tags']:
            string_data = string_data + ' ' + row['tags']
        tokens = nlp(preprocess_string(string_data))
        for token in tokens:
            if not token.is_punct:
                help_list.append(token.lemma_)
        help_list = list(set(help_list) - set(stop_word_list))
        bag_of_words.extend(help_list)
        list_of_docs.append(help_list)
        counter += 1
    with open('all_words.json', 'w') as file:
        json.dump(bag_of_words, file, indent=2)
    with open('docs.json', 'w') as file:
        json.dump(list_of_docs, file, indent=2)
def main():
    create_dataset()
    #format_fb_dates()
    #preprocess_string('Open Data Open Government')
if __name__ == '__main__':
    main()


