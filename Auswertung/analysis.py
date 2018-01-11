#!/usr/bin/python
# -*- coding: utf-8 -*-


import os
import helpers
import dateutil.parser
import spacy
import json
import csv
#import de_core_news_md
import requests
from Database import database_interaction
from helpers import sort_dict
from spacy.attrs import ORTH, LEMMA
from spacy.tokenizer import Tokenizer
import regex as re
from spacy.util import update_exc
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from sklearn.externals import joblib
from sklearn.decomposition import LatentDirichletAllocation

def preprocess_string(input_string):
    words_to_replace = re.findall('Open\s+\w*', input_string, flags=re.IGNORECASE)
    input_string = input_string.replace('\n', '')
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


def get_stop_words():
    with open('stopwords.txt', 'r') as file:
        stopwords = file.read()
    return stopwords.split('\n')


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
    list_of_docs_strings = []
    nlp = spacy.load('de')
    #nlp.tokenizer.add_special_case(u'Open\sAir', [{ORTH: 'Open\sAir'}])
    stop_word_list = get_stop_words()
    stop_word_list.extend(['.', ',', '-', '_', ';', ':', '?', '!', '#', '"', '+'])

    length_twitter = len(twitter_data)
    length_fb = len(fb_data)
    length_yt = len(yt_data)
    counter = 1
    for row in twitter_data:
        if counter % 1000 == 0:
            print('Iterating Twitter Data '+str(counter)+'/'+str(length_twitter))
        string_data = row['tweet_text'].decode('utf-8').lower()
        help_list = []
        list_of_docs_strings.append(preprocess_string(string_data))
        tokens = nlp(preprocess_string(string_data))
        for token in tokens:
            if not token.is_punct:
                help_list.append(token.lemma_.lower())
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
        string_data = string_data.lower()
        list_of_docs_strings.append(preprocess_string(string_data))
        tokens = nlp(preprocess_string(string_data))
        for token in tokens:
            if not token.is_punct:
                help_list.append(token.lemma_.lower())
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
        string_data = string_data.lower()
        list_of_docs_strings.append(preprocess_string(string_data))
        tokens = nlp(preprocess_string(string_data))
        for token in tokens:
            if not token.is_punct:
                help_list.append(token.lemma_.lower())
        help_list = list(set(help_list) - set(stop_word_list))
        bag_of_words.extend(help_list)
        list_of_docs.append(help_list)
        counter += 1

    with open('all_words.json', 'w') as file:
        json.dump(bag_of_words, file, indent=2)
    with open('docs_preprocessed.json', 'w') as file:
        json.dump(list_of_docs, file, indent=2)
    with open('docs_raw.json', 'w') as file:
        json.dump(list_of_docs_strings, file, indent=2)


def print_top_words(model, feature_names, n_top_words):
    for topic_idx, topic in enumerate(model.components_):
        message = "Topic #%d: " % topic_idx
        message += " ".join([feature_names[i]
                             for i in topic.argsort()[:-n_top_words - 1:-1]])
        print(message)
    print()


def create_doc_term_matrix():
    stop_word_list = get_stop_words()
    stop_word_list.extend(['.', ',', '-', '_', ';', ':', '?', '!', '#', '"'])
    with open('docs_raw.json', 'r') as file:
        docs = json.load(file)
    count_vectorizer = CountVectorizer(stop_words=stop_word_list)
    doc_term_matrix = count_vectorizer.fit_transform(docs)
    print(doc_term_matrix)
    joblib.dump(doc_term_matrix, 'doc_term_matrix.pkl')
    joblib.dump(count_vectorizer, 'count_vectorizer.pkl')
    #joblib.load('doc_term_matrix.pkl')

    tf_vectorizer = TfidfVectorizer(stop_words=stop_word_list)
    tfidf_matrix = tf_vectorizer.fit_transform(docs)
    print(tfidf_matrix)
    joblib.dump(tf_vectorizer, 'tf_vectorizer.pkl')
    joblib.dump(tfidf_matrix, 'tfidf_matrix.pkl')
    # joblib.load('tfidf_matrix.pkl')


def use_lda(filepath):
    samples = joblib.load(filepath)
    count_vectorizer = joblib.load('count_vectorizer.pkl')
    lda = LatentDirichletAllocation(n_topics=20, learning_method='batch', verbose=1)
    lda.fit(samples)
    joblib.dump(lda, 'lda_trained.pkl')
    print_top_words(lda, count_vectorizer.get_feature_names(), 30)


def count_words(filepath):
    with open(filepath, 'r') as file:
        contents = json.load(file)
    counted_words = helpers.elem_count(contents)
    #counted_words = helpers.sort_dict(counted_words, rev=False)
    filename = 'word_count.csv'
    with open(filename, 'w', encoding='utf-8') as f:
        writer = csv.writer(f, delimiter=';')
        for key, value in counted_words.items():
            writer.writerow([key, value])
    print(counted_words)


def main():
    # create_dataset()
    count_words('all_words.json')
    # create_doc_term_matrix()
    # use_lda('doc_term_matrix.pkl')
if __name__ == '__main__':
    main()


