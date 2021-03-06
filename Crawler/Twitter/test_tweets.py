#!/usr/bin/python
# -*- coding: utf-8 -*-

import tweepy  # https://github.com/tweepy/tweepy
import csv
import time
import datetime
import json
from Database import database_interaction

# Twitter API credentials
consumer_key = "uNDgOJ3sUM5IicocPQ8riRhEg"
consumer_secret = "2U0B04VOqNgVKlMCWd7KPawdxSwvRzxqcLtC8nh9aobzt3uVVK"
access_key = "407059263-rS77JdDpBxgoAEtj4lo9xaMYkkBMpbfrUDBbNH76"
access_secret = "bg87yfK7tpc7llPQrAD5cwIJ6x73cp1wCpCw0QC5a2Pg1"


def get_all_tweets(screen_name, newest):
    # Twitter only allows access to a users most recent 3240 tweets with this method

    # authorize twitter, initialize tweepy
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_key, access_secret)
    api = tweepy.API(auth)

    # initialize a list to hold all the tweepy Tweets
    alltweets = []
    #conn_objects = database_interaction.connect_to_db('../../Database/main_data.db')

    # make initial request for most recent tweets (200 is the maximum allowed count)
    if not newest:
        new_tweets_filtered = []
        new_tweets = api.user_timeline(screen_name=screen_name, count=30, tweet_mode="extended")
        for tweet in new_tweets:
            try:
                if tweet.retweeted_status:
                    print('Got retweet!!!')
                    print(tweet.retweeted_status.created_at)
                    print(tweet.retweeted_status.text)
            except AttributeError:
                pass
            if tweet.created_at.date() == datetime.datetime.today().date():
                new_tweets_filtered.append(tweet)
                # print(tweet.created_at.date())
                # print(tweet.created_at.date() >= datetime.datetime.today().date())
        alltweets.extend(new_tweets_filtered)
    else:
        new_tweets = api.user_timeline(screen_name=screen_name, count=200, since_id=newest, max_id='929952028767506432', tweet_mode="extended", include_rts=True, exclude_replies=False)
        alltweets.extend(new_tweets)
    for tweet in new_tweets:
        helplist = [tweet.id_str, screen_name, 'city', tweet.created_at, tweet.full_text.encode("utf-8"), tweet.source, tweet.in_reply_to_screen_name, tweet.is_quote_status, tweet.retweet_count, tweet.favorite_count]
        if tweet.entities['hashtags']:
            hashtagstring = []
            for hashtag in tweet.entities['hashtags']:
                hashtagstring.append(hashtag['text'])
            hashtagstring = ','.join(hashtagstring)
        else:
            hashtagstring = None
        helplist.append(hashtagstring)
        try:
            if tweet.retweeted_status:
                helplist[4] = tweet.retweeted_status.full_text
                helplist.append(True)
            else:
                helplist.append(False)
        except AttributeError:
            helplist.append(False)
    l = []
    # for tweet in new_tweets:
    #     l.append(tweet)
    l.extend(new_tweets)
    for tweet in alltweets:
        try:
            if tweet.retweeted_status:
                print(tweet.retweeted_status.full_text)
            else:
                pass
        except AttributeError:
            pass

    # for tweet in alltweets:
    #     print(tweet.retweets()[1].retweeted_status)
        # for elem in tweet._json:
        #     print(elem)
        # for elem in l:
        #     print(elem.retweeted_status)
        # try:
        #     if tweet.retweeted_status:
        #         print(tweet.retweeted_status.text)
        #         print(tweet.retweeted_status.user.name)
        #     else:
        #         print('No Retweet')
        # except:
        #     print('Error')


    # save the id of the oldest tweet less one
    # if alltweets:
    #     newest = alltweets[0].id
    #     newest_date = alltweets[0].created_at
    #
    #     # keep grabbing tweets until there are no tweets left to grab
    #     while len(new_tweets) > 0:
    #         print("getting tweets since %s" % (newest))
    #
    #         # all subsiquent requests use the max_id param to prevent duplicates
    #         new_tweets = api.user_timeline(screen_name=screen_name, count=100, since_id=newest, tweet_mode="extended")
    #
    #         # save most recent tweets
    #         alltweets.extend(new_tweets)
    #
    #         # update the id of the oldest tweet less one
    #         if alltweets:
    #             newest = alltweets[0].id
    #             newest_date = alltweets[0].created_at
    #
    #         print("...%s tweets downloaded so far" % (len(alltweets)))
    #
    # # transform the tweepy tweets into a 2D array that will populate the csv
    # outtweets = []
    # for tweet in alltweets:
    #     helplist = [tweet.id_str, screen_name, city, tweet.created_at, tweet.full_text.encode("utf-8"), tweet.source,
    #                 tweet.in_reply_to_screen_name, tweet.is_quote_status, tweet.retweet_count, tweet.favorite_count]
    #     if tweet.entities['hashtags']:
    #         hashtagstring = []
    #         for hashtag in tweet.entities['hashtags']:
    #             hashtagstring.append(hashtag['text'])
    #         hashtagstring = ','.join(hashtagstring)
    #     else:
    #         hashtagstring = None
    #     helplist.append(hashtagstring)
    #     try:
    #         if tweet.retweeted_status:
    #             helplist.append(tweet.retweeted_status.text)
    #             helplist.append(tweet.retweeted_status.user.name)
    #         else:
    #             helplist.append(None)
    #             helplist.append(None)
    #     except AttributeError:
    #         helplist.append(None)
    #         helplist.append(None)
    #     # Inserting values in Database
    #     #database_interaction.insert_values_into("tweets", helplist, conn_objects['Connection'], conn_objects['Cursor'])
    #     # Writing list for CSV output as check
    #     outtweets.append(helplist)
    #
    # # write the csv
    # date_for_filename = datetime.datetime.today().date()
    # filename = screen_name + '_tweets_' + str(date_for_filename) + '.csv'
    # with open('Backups/' + filename, 'w', encoding='utf-8') as f:
    #     writer = csv.writer(f, delimiter=';')
    #     writer.writerow(
    #         ["tweet_id", "screenname", "city", "date", "text", "source", "reply_to", "is_quote", "retweetet_count",
    #          "favorited_count", "hashtags", "retweeted_text", "retweeted_user"])
    #     writer.writerows(outtweets)
    # return {'last_tweet_date': str(newest_date), 'last_tweet_id': newest, 'city': city}


if __name__ == '__main__':
    # with open('twitter_usernames.json', 'r') as file:
    #     collection = json.load(file)
    # for username in collection:
    #     # pass in the username of the account you want to download
    #     try:
    #         new_entry = get_all_tweets(username, collection[username]['last_tweet_id'],
    #                                    collection[username]['last_tweet_date'], collection[username]['city'])
    #         collection[username] = new_entry
    #     except TweepError:
    #         print('Ran into an error')
    #         time.sleep(5)
    #         new_entry = get_all_tweets(username, collection[username]['last_tweet_id'],
    #                                    collection[username]['last_tweet_date'], collection[username]['city'])
    #         collection[username] = new_entry
    # with open('twitter_usernames.json', 'w') as file:
    #     json.dump(collection, file, indent=2)
    # date_for_filename = datetime.datetime.today().date()
    # with open('Backups/' + str(date_for_filename) + 'twitter_usernames.json', 'w') as file:
    #     json.dump(collection, file, indent=2)
    get_all_tweets('BundesstadtBonn', '929830853601087488')