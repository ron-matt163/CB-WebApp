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

consumer_key = "ac8YRucGrIbNHUcD2IYqpfp4s" 
consumer_secret = "ymifAZlIIJAVDqGfxcrVcmPCiEXYhxRUqyh43KVvyxmuuYG2s3"
access_key = "1033620667155984384-uKKn6iHzAan304XrH5nU8evIQJUwak"
access_secret = "6TcRuKZE4EGx5F2XTCavopZdttlw380Ms8MoyyMqZqiS2"


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

@app.route('/showTweets/<query>/<tweet_limit>',methods=['GET','POST'])
def printstats(query,tweet_limit):
    global st_count
    bully_records = []
    tweet_count = 0
    bully_count = 0
    percentage = 0.0
    if st_count == 0:
        tweet_limit = int(tweet_limit)
        print("Tweets to be collected with search keyword: " + query)
        date_since = '2021-01-23'
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
                if tweet_count>=tweet_limit:
                    break    
            if tweet_count>=tweet_limit:
                break
        percentage = round((100*float(bully_count)/tweet_count),2)  
        st_count +=1
    return render_template('show_tweets.html',bully_tweets=bully_records,tweet_count=tweet_count,bully_count=bully_count,percentage=percentage)

@app.route('/sendmessages',methods=['GET','POST'])
def sendmessages():
    offenders = []
    victims = []
    if request.method == 'POST':
        form = request.form.getlist('checking')
        for usernamex2 in form:
            username = usernamex2.split(' ')
            offenders.append(username[0])
            victims.append(username[1])
        offenders = list(dict.fromkeys(offenders))
        victims = list(dict.fromkeys(victims))
        print("Offenders" + str(offenders))
        print("Victims" + str(victims))
    return render_template('send_messages.html',offenders=offenders,victims=victims)

@app.route('/sendmessagesconfirm',methods=['GET','POST'])
def sendmessagesconfirm():
    offenders = []
    victims = []
    if request.method == 'POST':
        offenders = request.form.getlist('offenderNames')
        victims = request.form.getlist('victimNames')
        offenderMessage = request.form.getlist('offenderMessage')
        victimMessage = request.form.getlist('victimMessage')
        offenderMessage = offenderMessage[0]
        victimMessage = victimMessage[0]
        print("Offenders" + str(offenders))
        print("Victims" + str(victims))
        print("Offender Message" + str(offenderMessage))
        print("Victim Message" + str(victimMessage))
        for offender in offenders:
           recipient_id = api.get_user(offender).id
           try:
               api.send_direct_message(recipient_id,offenderMessage)
               print("Message sent to offender")
           except tweepy.TweepError as e:
               print(e.reason)

        for victim in victims:
           recipient_id = api.get_user(victim).id
           try:
               api.send_direct_message(recipient_id,victimMessage)
               print("Message sent to victim")
           except tweepy.TweepError as e:
               print(e.reason)

    return render_template('send_messages_confirm.html',offenders=offenders,victims=victims)


@app.route('/tttc')
def trendingtopictweetcollection(): 
    return render_template("trending-topic-tweet-collection.html")    

if __name__ == "__main__":
    try:
        app.run(debug=True)
    except:
        print("Exception")
    