#!/usr/bin/python
# -*- coding: utf-8 -*-

import json

def extract_usernames():
    '''
    Funktion extrahiert die Usernames aus der erstellten Linkliste
    Dazu wird der das letzte Segment des Twitterlinks pro Seite abgetrennt
    '''
    usernames = {}
    with open('../../Daten/Social_Links_final.json', 'r') as file:
        collection = json.load(file)
    for key in collection:
        try:
            twitter_user = collection[key]['twitter'].split('/')[-1]
            usernames[twitter_user] = {'last_tweet_date':'', 'last_tweet_id':'', 'city':key}
        except KeyError:
            continue
    with open('twitter_usernames.json', 'w') as file:
        json.dump(usernames, file, indent=2)
def main():
    extract_usernames()
if __name__ == '__main__':
    main()