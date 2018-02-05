#!/usr/bin/python
# -*- coding: utf-8 -*-


import os
import helpers
import dateutil.parser
import spacy
import json
import csv
import sqlite3
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
from _collections import defaultdict

def preprocess_string(input_string):
    #words_to_replace = re.findall('Open\s*+\w*', input_string, flags=re.IGNORECASE)
    input_string = input_string.replace('\n', '')
    input_string = re.sub(r'https?:\/\/.*[\r\n]*', '', input_string, flags=re.MULTILINE)
    input_string = re.sub(r'\d+', '', input_string, flags=re.MULTILINE)
    input_string = input_string.replace('  ', ' ')
    input_string = re.sub(r'\s\s+', ' ', input_string, flags=re.MULTILINE)
    input_string = input_string.strip()
    # for word in words_to_replace:
        # input_string = input_string.replace(word, word.replace(' ', ''))

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
    with open('stopwords.txt', 'r', encoding='utf-8') as file:
        stopwords = file.read().lower()
    return stopwords.lower().split('\n')


def read_topiclist():
    topicdict = {}
    with open('model1_output.txt', 'r') as file:
        topics = file.read()
    topics = topics.replace(': ', ':')
    topics = topics.split('\n')
    for elem in topics:
        topic = elem.split(':')[0]
        text = elem.split(':')[1]
        text = text.split(' ')
        topicdict[topic] = text
    return topicdict


def categorize_posts():
    topics = read_topiclist()
    with open('posts_to_categorize_lemmas.json', 'r', encoding='utf-8') as file:
        posts = json.load(file)
    for post in posts['twitter']:
        for topic in topics:
            print(posts['twitter'][post])
            print(topics[topic])
            print(bool(set(posts['twitter'][post]).intersection(topics[topic])))
        return


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
    posts_to_categorize_dict = {'twitter': {}, 'facebook': {}, 'youtube': {}}
    nlp = spacy.load('de')
    nlp.tokenizer.add_special_case(u'castrop-rauxel', [{ORTH: 'castrop-rauxel', LEMMA: 'castrop-rauxel'}])
    stop_word_list = get_stop_words()

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
        posts_to_categorize_dict['twitter'][row['tweet_id']] = help_list
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
        posts_to_categorize_dict['facebook'][row['post_id']] = help_list
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
                help_list.append(token.text.lower())
        help_list = list(set(help_list) - set(stop_word_list))
        bag_of_words.extend(help_list)
        list_of_docs.append(help_list)
        posts_to_categorize_dict['youtube'][row['video_id']] = help_list
        counter += 1

    with open('all_words.json', 'w') as file:
        json.dump(bag_of_words, file, indent=2)
    with open('docs_preprocessed.json', 'w') as file:
        json.dump(list_of_docs, file, indent=2)
    with open('docs_raw.json', 'w') as file:
        json.dump(list_of_docs_strings, file, indent=2)
    with open('posts_to_categorize_lemmas.json', 'w') as file:
        json.dump(posts_to_categorize_dict, file, indent=2)


def print_top_words(model, feature_names, n_top_words, filepath=None):
    if filepath:
        open(filepath, 'w', encoding='utf-8').close()
    for topic_idx, topic in enumerate(model.components_):
        message = "Topic #%d: " % topic_idx
        message += " ".join([feature_names[i]
                             for i in topic.argsort()[:-n_top_words - 1:-1]])
        print(message)
        if filepath:
            with open(filepath, 'a', encoding='utf-8' ) as file:
                file.write(message+'\n')
    print()


def extend_stopwords():
    stopword_list = get_stop_words()
    stopword_list.extend(['.', ',', '-', '_', ';', ':', '?', '!', '#', '"', 'rt'])
    with open('../Social_Links_final.json', 'r') as file:
        cities_dict = json.load(file)
    for elem in cities_dict.keys():
        stopword_list.extend(elem.split(' '))
        stopword_list.append(elem+'er')
    with open('stopwords.txt', 'w', encoding='utf-8') as file:
        file.write('\n'.join(stopword_list))


def create_doc_term_matrix():
    print('Creating Matrices...')
    stop_word_list = get_stop_words()

    with open('docs_preprocessed.json', 'r') as file:
        docs = json.load(file)
    if type(docs[0]) == list:
        docs_joined = []
        for termlist in docs:
            docs_joined.append(' '.join(termlist))
        docs = docs_joined
        print(docs)
    count_vectorizer1 = CountVectorizer(stop_words=stop_word_list, max_df=0.7, min_df=1)
    count_vectorizer2 = CountVectorizer(stop_words=stop_word_list, max_df=0.8, min_df=1)
    count_vectorizer3 = CountVectorizer(stop_words=stop_word_list, max_df=0.9, min_df=1)
    doc_term_matrix1 = count_vectorizer1.fit_transform(docs)
    doc_term_matrix2 = count_vectorizer2.fit_transform(docs)
    doc_term_matrix3 = count_vectorizer3.fit_transform(docs)

    print('Pickling matrices...')
    joblib.dump(doc_term_matrix1, 'doc_term_matrix1.pkl')
    joblib.dump(count_vectorizer1, 'count_vectorizer1.pkl')
    joblib.dump(doc_term_matrix2, 'doc_term_matrix2.pkl')
    joblib.dump(count_vectorizer2, 'count_vectorizer2.pkl')
    joblib.dump(doc_term_matrix3, 'doc_term_matrix3.pkl')
    joblib.dump(count_vectorizer3, 'count_vectorizer3.pkl')
    #joblib.load('doc_term_matrix.pkl')

    tf_vectorizer = TfidfVectorizer(stop_words=stop_word_list)
    tfidf_matrix = tf_vectorizer.fit_transform(docs)
    joblib.dump(tf_vectorizer, 'tf_vectorizer.pkl')
    joblib.dump(tfidf_matrix, 'tfidf_matrix.pkl')
    # joblib.load('tfidf_matrix.pkl')ö


def use_lda(samples_filepath, vectorizer_filepath, model_filepath, output_filepath):
    print('Training LDA on '+samples_filepath)
    samples = joblib.load(samples_filepath)
    count_vectorizer = joblib.load(vectorizer_filepath)
    alpha = 0.01
    beta = 0.01
    lda = LatentDirichletAllocation(n_topics=40, learning_method='batch', doc_topic_prior=alpha, topic_word_prior=beta, verbose=1)
    lda.fit(samples)
    joblib.dump(lda, model_filepath)
    print('Writing results to '+output_filepath)
    print_top_words(lda, count_vectorizer.get_feature_names(), 30, filepath=output_filepath)


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


def analyze_dataset():
    counting_dict = defaultdict(int)
    connection_object = database_interaction.connect_to_db('../Database/main_data.db')
    c = connection_object['Cursor']
    min_date_twitter = database_interaction.get_data('tweets', ['MIN(creation_date)'], connection_object['Connection'],
                                                     min_max=True).fetchone()[0]
    max_date_twitter = database_interaction.get_data('tweets', ['MAX(creation_date)'], connection_object['Connection'],
                                                     min_max=True)
    max_date_fb = database_interaction.get_data('fb_posts', ['MAX(creation_date)'], connection_object['Connection'],
                                                min_max=True)
    max_date_yt = database_interaction.get_data('yt_videos', ['MAX(creation_date)'], connection_object['Connection'],
                                                min_max=True)
    max_date_all = min([max_date_fb.fetchone()[0], max_date_twitter.fetchone()[0], max_date_yt.fetchone()[0]])
    max_date_all = str(dateutil.parser.parse(max_date_all, ignoretz=True))
    twitter_data = c.execute('SELECT city, count(city) from tweets '
                             'WHERE date(creation_date)<? AND date(creation_date)>?'
                             'GROUP BY city ORDER BY city asc;', [max_date_all, min_date_twitter]).fetchall()

    fb_data = c.execute('SELECT city, count(city) from fb_posts '
                             'WHERE date(creation_date)<? AND date(creation_date)>?'
                             'GROUP BY city ORDER BY city asc;', [max_date_all, min_date_twitter]).fetchall()

    yt_data = c.execute('SELECT city, count(city) from yt_videos '
                             'WHERE date(creation_date)<? AND date(creation_date)>?'
                             'GROUP BY city ORDER BY city asc;', [max_date_all, min_date_twitter]).fetchall()
    for elem in twitter_data+fb_data+yt_data:
        counting_dict[elem[0]] += elem[1]
    filename = 'city_count.csv'
    with open(filename, 'w', encoding='utf-8') as f:
        writer = csv.writer(f, delimiter=';')
        for key, value in counting_dict.items():
            writer.writerow([key, value])
    print(counting_dict)


def create_corpus(span=None):
    stopwords = get_stop_words()
    nlp = spacy.load('de')
    connection_object = database_interaction.connect_to_db('../Database/main_data.db')
    connection_object['Connection'].row_factory = sqlite3.Row
    c = connection_object['Connection'].cursor()
    doclist = {'facebook': [], 'twitter': [], 'youtube': []}
    # For later export to json-file, which is used to classify the posts after LDA
    exportlist = {}
    with open('thementerme.txt', 'r') as file:
        topics = file.read().lower().split('\n')
    for topic in topics:
        topic = '%'+topic+'%'
        sql_statement = "SELECT post_id as post_id,city as city,creation_date as creation_date, " \
                        "message as message,description as description " \
                        "FROM fb_posts " \
                        "WHERE message like ? OR description like ?"
        results = c.execute(sql_statement, [topic, topic]).fetchall()
        doclist['facebook'].extend(results)
        sql_statement = "SELECT tweet_id as tweet_id,city as city,creation_date as creation_date, " \
                        "tweet_text as tweet_text " \
                        "FROM tweets " \
                        "WHERE tweet_text like ?"
        results = c.execute(sql_statement, [topic, ]).fetchall()
        doclist['twitter'].extend(results)
        sql_statement = "SELECT video_id as video_id,city as city,creation_date as creation_date, " \
                        "title as title, description as description, tags as tags " \
                        "FROM yt_videos " \
                        "WHERE title like ? OR description like ? OR tags like ?"
        results = c.execute(sql_statement, [topic, topic, topic]).fetchall()
        doclist['youtube'].extend(results)

    for elem in doclist['twitter']:
        help_list = []
        exportlist[elem['tweet_id']] = elem['tweet_text'].decode('utf-8')
        tweet_text = extract_context(preprocess_string(elem['tweet_text'].decode('utf-8')).lower())
        # for topic in topics:
        #     tweet_text = tweet_text.replace(topic, '')
        tweet_text_tokens = nlp(tweet_text)
        for token in tweet_text_tokens:
            if not token.is_punct:
                help_list.append(token.lemma_.lower())
        tweet_text = ' '.join(list(set(help_list) - set(stopwords)))
        with open('Kontexte/'+elem['tweet_id']+'.txt', 'w', encoding='utf-8') as file:
            file.write(tweet_text)

    for elem in doclist['facebook']:
        help_list = []
        if elem['message'] and elem['description']:
            post_text = elem['message']+' '+elem['description']
        elif elem['message']:
            post_text = elem['message']
        elif elem['description']:
            post_text = elem['description']
        # for topic in topics:
        #     post_text = post_text.replace(topic, '')
        exportlist[elem['post_id']] = post_text
        post_text = extract_context(preprocess_string(post_text).lower())
        post_text_tokens = nlp(post_text)
        for token in post_text_tokens:
            if not token.is_punct:
                help_list.append(token.lemma_.lower())
        post_text = ' '.join(list(set(help_list) - set(stopwords)))

        with open('Kontexte/' + elem['post_id'] + '.txt', 'w', encoding='utf-8') as file:
            file.write(post_text)

    for elem in doclist['youtube']:
        help_list = []
        video_text = elem['title']
        if elem['description']:
            video_text = video_text + ' ' + elem['description']
        if elem['tags']:
            video_text = video_text + ' ' + elem['tags']
        exportlist[elem['video_id']] = video_text
        video_text = extract_context(preprocess_string(video_text).lower())
        # for topic in topics:
        #     video_text = video_text.replace(topic, '')
        video_text_tokens = nlp(video_text)
        for token in video_text_tokens:
            if not token.is_punct:
                help_list.append(token.lemma_.lower())
        video_text = ' '.join(list(set(help_list) - set(stopwords)))

        with open('Kontexte/' + elem['video_id'] + '.txt', 'w', encoding='utf-8') as file:
            file.write(video_text)

    with open('open_government_docs.json', 'w') as file:
        json.dump(exportlist, file, indent=2)
    #print(len(doclist['youtube']))


def extract_context(sentence):
    with open('thementerme.txt', 'r') as file:
        topics = file.read().lower().split('\n')
    context = ''
    for topic in topics:
        extracted_words = ' '.join(re.findall(r'(?:\w+\W+){,25}'+topic+'(?:\W+\w+){,25}', sentence))
        if not context and extracted_words:
            context = extracted_words
        elif context and extracted_words:
            context = context + ' ' + extracted_words

    return context


def extract_id_from_filename(filepath):
    filename = filepath.split('/')[-1]
    post_id = filename.replace('.txt', '')
    if re.match(r'\d+_\d+$', post_id):
        source = 'fb_posts'
        table_id = 'post_id'
    elif re.match(r'\d*$', post_id):
        source = 'tweets'
        table_id = 'tweet_id'
    else:
        source = 'yt_videos'
        table_id = 'video_id'
    return (post_id, source, table_id)


def classify_posts():
    onnection_object = database_interaction.connect_to_db('../Database/main_data.db')
    onnection_object['Connection'].row_factory = sqlite3.Row
    c = onnection_object['Connection'].cursor()
    with open('open_government_docs.json', 'r') as file:
        lookup_dict = json.load(file)
    with open('Ergebnisse LDA zum Thema Open Government/kontext_keys.txt', 'r', encoding='utf-8') as file:
        topic_terms = file.readlines()
    topic_dict = {}
    posts_dict = {}
    for topic in topic_terms:
        splitted_line = topic.split('\t')
        topic_dict[splitted_line[0]] = splitted_line[2].replace(' \n', '')
    with open('Ergebnisse LDA zum Thema Open Government/kontexte_composition.txt', 'r', encoding='utf-8') as file:
        posts = file.readlines()
    for post in posts:
        splitted_line = post.split('\t')
        posts_dict[splitted_line[1]] = splitted_line[2:]

    for filepath in posts_dict:
        post_id, source, table_id = extract_id_from_filename(filepath)
        # Gets the index of the topic with the highest probability
        prominent_topic_id = str(posts_dict[filepath].index(max(posts_dict[filepath])))
        prominent_topic = topic_dict[prominent_topic_id]
        sql_statement = "SELECT city as city, creation_date as creation_date FROM "+source+" WHERE "+table_id+" = ?"
        result = c.execute(sql_statement, [post_id]).fetchone()
        database_interaction.insert_values_into('open_data_posts_classified',
                                                [post_id, result['city'], result['creation_date'], source, lookup_dict[post_id], prominent_topic],
                                                onnection_object['Connection'], c)



def main():
    #extend_stopwords()
    # create_dataset()
    # count_words('all_words.json')
    # create_doc_term_matrix()
    # use_lda('doc_term_matrix1.pkl', 'count_vectorizer1.pkl', 'lda_trained1.pkl', 'model1_output.txt')
    # use_lda('doc_term_matrix2.pkl', 'count_vectorizer2.pkl', 'lda_trained2.pkl', 'model2_output.txt')
    # use_lda('doc_term_matrix3.pkl', 'count_vectorizer3.pkl', 'lda_trained3.pkl', 'model3_output.txt')
    #print(preprocess_string('der neue abfallkalender f\u00fcr  ist ab sofort erh\u00e4ltlich. enthalten sind darin eine \u00fcbersicht aller abholtermine f\u00fcr die verschiedenen abfallbeh\u00e4lter sowie viele informationen rund um das thema m\u00fcll'))
    #analyze_dataset()
    # read_topiclist()
    # categorize_posts()
    #create_corpus()
    classify_posts()
    #print(extract_id_from_filename('file:/C:/mallet/Kontexte/4584513645453.txt'))

    # print(extract_context("Open Data-Vorreiter Aachen! Schon gewusst? Wir sind eine der jüngsten Open Data-Kommunen in NRW! Grund genug, unsere Kollegen Partizipation Andra Mainz und Norbert Dödtmann vom IT-Management dazu mal zu Wort kommen zu lassen... Hier geht's zum Interview: http://bit.ly/1IdD7jq Und hier zu http://offenedaten.aachen.de",
    #                 'Opegadfdgn hsdhgsdData'
    #                 ))
if __name__ == '__main__':
    main()


