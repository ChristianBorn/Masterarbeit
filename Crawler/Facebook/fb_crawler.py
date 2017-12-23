#!/usr/bin/python
# -*- coding: utf-8 -*-

from facepy import GraphAPI
import datetime
from time import sleep
from facepy.exceptions import OAuthError, FacebookError
from urllib3.exceptions import ProtocolError
import time
import json
import requests
from Database import database_interaction
from Database import database_setup

# graph = facebook.GraphAPI(access_token='EAALxHU6JEoYBAGd8svR5mFzZCVx3P8h02ZBZCAbRnA9byanMYuhZBIgDZBZCGcxeYVm7Ao3pwU8teUblKZAxpHysDvBaH2PGsSdowAYBulVLSO9cSjcU2WMOK2HnmU0J9cP5vzAonX394DVCaPKRQ4RlHcanrTHLPEZD')
# users = graph.get_object('me')
# print(users)

def get_posts_from_timeline(link, city):
    print('[+] Retrieving posts for: '+city)
    if link.startswith('https://de-de.'):
        link = link.replace('de-de.','')
    conn_objects = database_interaction.connect_to_db('../../Database/main_data.db')
    all_posts = []
    likes = {}
    all_commments = {}
    reactions = {}
    page = 1
    now_timestamp = str(int(time.time()))
    graph = GraphAPI('EAALxHU6JEoYBAK61wx7SXZAVjQHJSa5bov9c2m78KbUPL2rmGu4gBy9wlgpoGJSO7gbjq5d8UHbXGZAd3mZB1ZBZAwZBgZA80w4W1wmSXxTWLqRUbkh9FcMUyrIYGFtZB5IZCxZCHnMU4nmvLfocYGXK4Rj01FIezO1fqWBLGDGqwXTQZDZD')
    user_id = graph.get(link, fields='id')['id']
    try:
        # 1508520726 is the timestamp for 20th October 2017
        #retrieved_posts = graph.get(user_id+'/posts', since='1508520726', until=now_timestamp, fields='id,created_time,message,comments,caption,description,shares,likes,reactions,type')
        retrieved_posts = graph.get(
            user_id + '/posts',
            fields='id,created_time,message,comments,caption,description,shares,likes,reactions,type')
    except OAuthError:
        with open('errors.txt','a') as outlog:
            outlog.write(e+'\n')
            outlog.write(city+' '+link+'\n'+'OAuthError\n')
        return
    all_posts.extend(retrieved_posts['data'])
    # Iterieren über die Seiten der paginierten Antwort
    while(True):
        try:
            retrieved_posts = requests.get(retrieved_posts['paging']['next']).json()
            page += 1
            print('Retrieved page '+str(page))
            all_posts.extend(retrieved_posts['data'])
        except KeyError:
            print('Last Page retrieved')
            break

    print('Number of Posts retrieved: '+str(len(all_posts)))
    for post in all_posts:
        post_id = post['id']
        likes[post_id] = []
        all_commments[post_id] = []
        reactions[post_id] = []
        try:
            likes[post_id].extend(post['likes']['data'])
            likes_page = post['likes']['paging']['next']
            while(True):
                try:
                    likes_page = requests.get(likes_page).json()
                    likes[post_id].extend(likes_page['data'])
                    likes_page = likes_page['paging']['next']
                except KeyError:
                    break
        except KeyError:
            pass
        try:
            all_commments[post_id].extend(post['comments']['data'])
            comments_page = post['comments']['paging']['next']
            while(True):
                try:
                    comments_page = requests.get(comments_page).json()
                    all_commments[post_id].extend(comments_page['data'])
                    comments_page = comments_page['paging']['next']
                except KeyError:
                    break
        except KeyError:
            pass
        try:
            reactions[post_id].extend(post['reactions']['data'])
            reactions_page = post['reactions']['paging']['next']
            while(True):
                try:
                    try:
                        reactions_page = requests.get(reactions_page).json()
                    except Exception as e:
                        with open('errors.txt', 'a') as file:
                            file.write(e + '\n')
                            file.write(city+' :'+link+'\n')
                        return
                    reactions[post_id].extend(reactions_page['data'])
                    reactions_page = reactions_page['paging']['next']
                except KeyError:
                    break
        except KeyError:
            pass
        sharecount = 0
        try:
            sharecount = post['shares']['count']
        except KeyError:
            pass
        try:
            message_to_be_added = post['message']
        except KeyError:
            message_to_be_added = None
        try:
            description_to_be_added = post['description']
        except KeyError:
            description_to_be_added = None

        insert_list = [post['id'], user_id, city, post['created_time'],
                       message_to_be_added,
                       description_to_be_added,
                       len(all_commments[post_id]),
                       sharecount,
                       len(likes[post_id]),
                       len(reactions[post_id]),
                       post['type']
                       ]
        # Insert current post into table fb_posts (Values from insert_list)
        database_interaction.insert_values_into("fb_posts", insert_list, conn_objects['Connection'], conn_objects['Cursor'])
        print('Post with likes: '+str(len(likes[post_id])))
        print('Post with reactions: ' + str(len(reactions[post_id])))
        print('Post with comments: ' + str(len(all_commments[post_id])))
    # Insert comments in fb_comments table
    print('[+] Inserting retrieved comments')
    for post_id in all_commments:
        if all_commments[post_id]:
            for comment in all_commments[post_id]:
                insert_list = [comment['id'], post_id, comment['created_time'], comment['message'], comment['from']['id'], user_id, city]
                database_interaction.insert_values_into("fb_comments", insert_list, conn_objects['Connection'],
                                                        conn_objects['Cursor'])
def main():
    # Reset the fb_posts and fb_comments tables
    #database_setup.create_table_fb_posts('../../Database/main_data.db')
    #database_setup.create_table_fb_comments('../../Database/main_data.db')
    with open('../../Daten/Social_Links_final.json', 'r') as file:
        link_dict = json.load(file)
        for city in link_dict:
            try:
                try:
                    get_posts_from_timeline(link_dict[city]['facebook'], city)
                except ProtocolError:
                    sleep(10)
                    get_posts_from_timeline(link_dict[city]['facebook'], city)
                except ProtocolError:
                    with open('errors.txt', 'a') as file:
                        file.write(city + ' :' + link_dict[city]['facebook'] + '\n')
                    continue
            except KeyError:
                print('[-] '+city+' has no FB Link')
            except FacebookError:
                print('Facebook Rate Limit reached, sleeping for half an hour\n'+str(datetime.datetime.today().time().isoformat()))
                sleep(1800)
                get_posts_from_timeline(link_dict[city]['facebook'], city)
            except Exception as e:
                with open('errors.txt', 'a') as file:
                    file.write(city + ' :' + link_dict[city]['facebook'] + '\n'+str(e)+'\n')
                continue
    # get_posts_from_timeline(link_dict['Aachen']['facebook'],'Aachen')
    # get_posts_from_timeline(link_dict['Bielefeld']['facebook'], 'Bielefeld')
    # get_posts_from_timeline(link_dict['Düsseldorf']['facebook'], 'Düsseldorf')
    #get_posts_from_timeline(link_dict['Köln']['facebook'], 'Köln')
    # get_posts_from_timeline(link_dict['Münster']['facebook'], 'Münster')
    # get_posts_from_timeline(link_dict['Winterberg']['facebook'], 'Winterberg')
    #get_posts_from_timeline("http://www.facebook.com/pages/Aachen-Germany/Stadt-Aachen/175038754810#/pages/Aachen-Germany/Stadt-Aachen/175038754810?v=wall#/pages/Aachen-Germany/Stadt-Aachen/175038754810?v=wall",'Aachen')

if __name__ == '__main__':
    main()