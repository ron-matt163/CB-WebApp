from flask import Flask,request,jsonify,render_template,redirect,url_for,flash
import os
import pickle
import nltk
from sklearn.feature_extraction.text import CountVectorizer
import re
from nltk.stem import WordNetLemmatizer
import ssl
from nltk.corpus import stopwords
import string
import tweepy 
import sys
# Fill the X's with the credentials obtained by  
# following the above mentioned procedure. 

consumer_key = "0VVJldZQQGC3L61nBwRFwPzQu" 
consumer_secret = "HEGgY2iZ8P8yKNIgcEtmFQEytCL6IswOCI1O1vimpjciPmFPtd"
access_key = "1075785913815445506-tyt6e1UxJ6c4CAQbk5fkqFFDCixA2M"
access_secret = "BvRTNn2OTZ3gkUZT13NuaV1rg3r2QjiERwCUEXpE2S5zc"
  
auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_key,access_secret)
api = tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify = True,retry_count = 5,retry_delay = 5)


app=Flask(__name__)

app.config['SECRET_KEY'] = os.urandom(24)

st_count = 0

with open('models/NBBowTrained.sav', 'rb') as f:
    loaded_NB_classifier,loaded_func_countvectorizer = pickle.load(f)   


@app.route('/',methods=['GET','POST'])
def start_page(): 
    if request.method == 'POST':
        try:
            model_input_text = []
            form=request.form
            bullyText = form['bullyText']
            model_input_text.append(bullyText)
            print(model_input_text)
            input_vector = loaded_func_countvectorizer.transform(model_input_text)
            result = loaded_NB_classifier.predict(input_vector)
            if result[0]:
                print('The statement is bullying')
                flash('The statement is bullying','danger')
            else:
                print('The statement is harmless')
                flash('The statement is harmless','success')

            return redirect('/')

            flash('Text processed successfully: Analysing','success')
        except:
                flash('Failed to add question due to some error','danger')
    return render_template("sentence-detect.html")

@app.route('/sqt',methods=['GET','POST'])
def searchquerytweet(): 
    if request.method == 'POST':
        try:
            form = request.form
            tweet_limit = form['tweetCount']
            query = form['query']
            global st_count
            st_count = 0
            return redirect('/showTweets/{}/{}'.format(query,tweet_limit))
        except:
            flash('Error in entered data. Please check if the number you have entered is an integer.')
    return render_template("search-query-tweet.html")

@app.route('/showTweets/<query>/<tweet_limit>')
def printstats(query,tweet_limit):
    global st_count
    bully_records = []
    if st_count == 0:
        tweet_limit = int(tweet_limit)
        print("Tweets to be collected with search keyword: " + query)
        tweet_count = 0
        bully_count = 0
        date_since = '2021-01-20'
        c=0
        tweets = tweepy.Cursor(api.search, q=query,lang="en", since=date_since,result_type='popular', timeout=999999).items(10)
        for tweet in tweets:
            print("Tweet:\n")
            print(tweet.text)
            tweet_id = tweet.id
            print("Tweet ID: " + str(tweet_id))
            poster = tweet.user.screen_name
            print("\nPoster: " + poster + "\n")
            print("Replies to this tweet: \n")
            count = 0
            for reply in tweepy.Cursor(api.search,q="@"+poster, since_id=tweet_id).items(1000):
                if(reply.in_reply_to_status_id == tweet_id):
                    tweet_count += 1
                    input_text = []
                    print("Tweet index: "+str(tweet_count))
                    input_text.append(reply.text)
                    print(input_text)
                    input_vector = loaded_func_countvectorizer.transform(input_text)
                    result = loaded_NB_classifier.predict(input_vector)
                    print("\nClassification:\n")
                    print(result)
                    if(result[0]):
                        bully_row = []
                        bully_count += 1
                        bully_row.append(reply.user.screen_name)
                        bully_row.append(poster)
                        bully_row.append(reply.text)
                        bully_records.append(bully_row)
                if tweet_count>tweet_limit:
                    break    
            if tweet_count>tweet_limit:
                break  
        st_count +=1
    return render_template('show_tweets.html',bully_tweets=bully_records)


@app.route('/tttc')
def trendingtopictweetcollection(): 
    return render_template("trending-topic-tweet-collection.html")    

if __name__ == "__main__":
    try:
        app.run(debug=True)
    except:
        print("Exception")
    