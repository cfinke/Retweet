#!/usr/bin/python
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""A bot that republishes Twitter messages sent to it. Put your settings in settings.py."""

__author__ = 'chris@efinke.com'
__version__ = '1.3'

import sys
import re
import sqlite3
import datetime

import twitter
import settings

def retweet(initial_status_id=None):
    DB_PATH = settings.DB_DIR + "%s.sqlite"

    for USER, PASS in settings.ACCOUNTS:
        connection = sqlite3.connect(DB_PATH % USER)
        cursor = connection.cursor()
        
        if initial_status_id is not None:
            try:
                cursor.execute("""INSERT INTO retweets_2 (status_id, timestamp) VALUES ('%s', '%s')""" % (initial_status_id, datetime.datetime.now()))
                connection.commit()
            except sqlite3.IntegrityError:
                # Already inserted
                pass
        
        # Find the last tweet we retweeted
        cursor.execute("""SELECT MAX(status_id) FROM retweets_2""")
        rows = cursor
    
        max_status_id = None
    
        for row in rows:
            max_status_id = row[0]
            break
        
        # Create privileged twitter API
        api = twitter.Api(username=USER, password=PASS)
        api.SetSource("retweetpy")
        
        # Get replies to our account
        replies = api.GetReplies(since_id=max_status_id)
    
        if len(replies) > 0:
            # Strip off the leading @username
            cut_reply = re.compile(r"^@%s:?\s*" % USER, re.IGNORECASE)
            clean_reply = re.compile(r'^[^a-z0-9\s]*@', re.IGNORECASE)
            
            for reply in replies:
                is_banned = False
                
                # Build the new tweet
                retweeting_from = reply.user.screen_name.lower()
                
                # Check if this user is banned.
                cursor.execute("""SELECT username FROM bans WHERE username='%s'""" % retweeting_from)
                rows = cursor
                
                for row in rows:
                    is_banned = True
                    break
                
                if not is_banned:
                    reply_text = clean_reply.sub("@", reply.text)
                
                    if not reply_text.lower().startswith("@%s" % USER.lower()):
                        continue
                
                    clean_tweet = cut_reply.sub("", reply_text).strip()
                    
                    new_tweet = "RT @%s %s" % (retweeting_from, clean_tweet)
                    
                    # If it's over 140 chars, cut it down, adding ellipses
                    # The "in reply to" will link to the original
                    if len(new_tweet) > 140:
                        new_tweet = new_tweet[:140]
                
                        i = 137
                
                        while i > 0:
                            # Add the ellipses in a word break
                            if new_tweet[i] == " ":
                                new_tweet = "%s..." % new_tweet[:i]
                                break
                            else:
                                new_tweet = new_tweet[:i]
                    
                            i -= 1
            
                    try:
                        # Send it.
                        api.PostUpdate(new_tweet)
                        
                        cursor.execute("""INSERT INTO retweets_2 (status_id, timestamp) VALUES ('%s', '%s')""" % (reply.id, datetime.datetime.now()))
                        connection.commit()
                    except Exception, e:
                        print e
        
        cursor.close()
        connection.close()

def ban(username, account):
    DB_PATH = settings.DB_DIR + "%s.sqlite"

    connection = sqlite3.connect(DB_PATH % account)
    cursor = connection.cursor()

    try:
        cursor.execute("""INSERT INTO bans (username) VALUES ('%s')""" % username)
        connection.commit()
    except sqlite3.IntegrityError:
        print "Already banned."
    
    cursor.close()
    connection.close()

def setup():
    DB_PATH = settings.DB_DIR + "%s.sqlite"
    
    for USER, PASS in settings.ACCOUNTS:
        connection = sqlite3.connect(DB_PATH % USER)
        cursor = connection.cursor()
        
        cursor.execute("""SELECT tbl_name FROM sqlite_master""")
        table_rows = cursor.fetchall()
        
        tables = []
        
        for table in table_rows:
            tables.append(table[0])
        
        if "bans" not in tables:
            cursor.execute("""CREATE TABLE bans (username TEXT PRIMARY KEY)""")
            connection.commit()
        
        if "retweets_2" not in tables:
            cursor.execute("""CREATE TABLE retweets_2 (status_id INTEGER PRIMARY KEY, timestamp TEXT)""")
            
            if "retweets" in tables:
                cursor.execute("""INSERT INTO retweets_2 SELECT CAST(status_id AS INTEGER), timestamp FROM retweets""")
        
            connection.commit()
            
        if "retweets" in tables:
            cursor.execute("""DROP TABLE retweets""")
            connection.commit()
        
        cursor.close()
        connection.close()


if __name__ == "__main__":
    setup()
    
    if len(sys.argv) > 1:
        to_ban = None
        ban_account = None
        
        for arg in sys.argv:
            if arg.startswith("--ban="):
                to_ban = arg.split("=")[1]
            elif arg.startswith("--account="):
                ban_account = arg.split("=")[1]
        
        if to_ban and ban_account:
            ban(username=to_ban, account=ban_account)
        else:
            retweet(initial_status_id=sys.argv[1])
    else:
        retweet()
    
