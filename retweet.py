import sys
import re
import sqlite3
import datetime

import twitter as twitterpy

ACCOUNTS = [("username","password")]
DB_DIR = "/full/path/to/dir/for/sqlite/"

def retweet(initial_status_id=None):
    for USER, PASS in ACCOUNTS:
        DB_PATH = DB_DIR + "%s.sqlite"

        connection = sqlite3.connect(DB_PATH % USER)
        cursor = connection.cursor()
    
        # Create the table that will hold the tweets we've retweeted.
        cursor.execute("""CREATE TABLE IF NOT EXISTS retweets (status_id VARCHAR(100) PRIMARY KEY, timestamp VARCHAR(255))""")
        connection.commit()
        
        if initial_status_id is not None:
            try:
                cursor.execute("""INSERT INTO retweets (status_id, timestamp) VALUES ('%s', '%s')""" % (initial_status_id, datetime.datetime.now()))
                connection.commit()
            except Exception, e:
                # Already inserted
                pass
        
        # Find the last tweet we retweeted
        cursor.execute("""SELECT MAX(status_id) FROM retweets""")
        rows = cursor
    
        max_status_id = None
    
        if len(rows) > 0:
            max_status_id = row[0][0]
        
        # Create privileged twitter API
        api = twitterpy.Api(username=USER, password=PASS)
        api.SetSource("retweetpy")
        
        # Get replies to our account
        replies = api.GetReplies(since_id=max_status_id)
    
        if len(replies) > 0:
            # Strip off the leading @username
            cut_reply = re.compile(r"^@%s:?\s*" % USER, re.IGNORECASE)
        
            for reply in replies:
                if not reply.text.lower().startswith("@%s" % USER.lower()):
                    continue
                
                clean_tweet = cut_reply.sub("", reply.text).strip()
            
                # Build the new tweet
                new_tweet = "RT @%s %s" % (reply.user.GetScreenName(), clean_tweet)
                
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
            
                # Send it.
                try:
                    api.PostUpdate(new_tweet, reply.id)

                    cursor.execute("""INSERT INTO retweets (status_id, timestamp) VALUES ('%s', '%s')""" % (reply.id, datetime.datetime.now()))
                    connection.commit()
                except Exception, e:
                    print e

if __name__ == "__main__":
    if len(sys.argv) > 1:
        retweet(sys.argv[1])
    else:
        retweet()
