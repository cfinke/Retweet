retweet.py requires at least python 2.5.  If the default version of python on your system is 2.4 or lower,
you may be able to specify run retweet.py by specifying "python2.5" instead of just "python" when you run it.

== Getting Started ==

1. Replace "USERNAME" and "PASSWORD" at the top of settings.py with your account credentials. 
   (You can manage multiple accounts by adding another username/password pair to the ACCOUNTS variable.) 
2. Change the DB_DIR variable in settings.py to point to the directory where you'll keep your SQLite databases.
3. Optionally, add this line to your crontab:

*/2 * * * * python /full/path/to/retweet.py

(Some users have reported needing to include the full path to python here instead of just "python".)

This will run retweet.py every other minute, republishing any tweets that start with "@username", where 
"username" is your Twitter account's name.

The only thing it stores in the SQLite database are the status ids of the tweets it has republished. 

If the new message is longer than 140 characters, it chops words off of the end, replacing them with "..." 
until it's under the 140 character limit.

== Banning a User ==

To ban a user from being retweeted, run this command.

$ python retweet.py --ban=user_to_ban --account=retweeting_account

== Replacing an Existing Bot ==

If you're using this script to replace an existing retweet bot, you can supply it with the status id of the 
last message it re-published so that you don't end up republishing a bunch of old tweets. To do that, just run 
it once like this:

$ python retweet.py 12345

where 12345 is the status id of the last message your existing bot published.