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

app=Flask(__name__)

app.config['SECRET_KEY'] = os.urandom(24)


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

@app.route('/sqt')
def searchquerytweet(): 
    return render_template("search-query-tweet.html")

@app.route('/tttc')
def trendingtopictweetcollection(): 
    return render_template("trending-topic-tweet-collection.html")    

if __name__ == "__main__":
    try:
        app.run(debug=True)
    except:
        print("Exception")
    