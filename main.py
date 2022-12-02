from flask import Flask
from flask import request
from newspaper import Article
import spacy
from spacy.lang.en.stop_words import STOP_WORDS

from flask import jsonify

from pprint import pprint
from string import punctuation
from heapq import nlargest

from Questgen import main

qe= main.BoolQGen()  #boolQGen = Bool question generator (true or false questions)
qg= main.QGen() #This instance handles the short questions and multiple choice questions.


app = Flask(__name__)

@app.route("/")
def index():
    url = request.args.get("url", "")

    text = get_text(url) #Gets a string of all the main text on a webpage 
    text2 = text.split(" ") #Splits the text into an array of words

    question_list = [] #This is going to be the list of questions + context parts that we will return at the end
    obj = [] #This object is used to break up the large text into smaller parts, and then generate questions for each part, instead of passing in the entire text and generating questions at once. This makes sure that there isn't any information that gets skipped. 

    while len(text2) > 250: #Right now, it breaks the text into chunks of 250 words. 
        obj.append(text2[:250])
        text2 = text2[250:]

    obj.append(text2)

    obj = [' '.join(i) for i in obj] #Currently, each chunk is an array of 250 words. This .join part turns each chunk into one string so we can pass that into the question generator method.

    for chunk in obj: 
        payload = {
            "input_text": chunk
        }
        output_questions = qg.predict_shortq(payload) #Generating questions based on each chunk
        add_to_returnObj(output_questions, question_list, 'shortq') #Parses the return object and gets only the questions and the corresponding context to return and add to the question_list object. (We get a lot of information that we don't use from the question generator method, so this cleans up our data a bit)
    
    summary = summarize(text, .05) #Generates summary based on the text (takes one string as parameter, so we are passing in the original text variable instead of the one we split). The ".05" stands for how long the summary should be. 0.05 means the length of the summary will be 5% of the total length of the text
    question_list.append(summary) #Adds summary to our question_list return object
    return jsonify(question_list) #Returns the final object
    

def summarize(text, per): #Gonna be honest I really don't know exactly how this works. From what I understand, it uses tokenization and finds the most frequent words and generates a summary based on that. 
    nlp = spacy.load('en_core_web_sm')
    doc= nlp(text)
    tokens=[token.text for token in doc]
    word_frequencies={}
    for word in doc:
        if word.text.lower() not in list(STOP_WORDS):
            if word.text.lower() not in punctuation:
                if word.text not in word_frequencies.keys():
                    word_frequencies[word.text] = 1
                else:
                    word_frequencies[word.text] += 1
    max_frequency=max(word_frequencies.values())
    for word in word_frequencies.keys():
        word_frequencies[word]=word_frequencies[word]/max_frequency
    sentence_tokens= [sent for sent in doc.sents]
    sentence_scores = {}
    for sent in sentence_tokens:
        for word in sent:
            if word.text.lower() in word_frequencies.keys():
                if sent not in sentence_scores.keys():                            
                    sentence_scores[sent]=word_frequencies[word.text.lower()]
                else:
                    sentence_scores[sent]+=word_frequencies[word.text.lower()]
    select_length=int(len(sentence_tokens)*per)
    summary=nlargest(select_length, sentence_scores,key=sentence_scores.get)
    final_summary=[word.text for word in summary]
    summary=''.join(final_summary)
    return summary

def get_text(url): #Uses the newspaper3k library to get the main text from a website
    article = Article(url)
    article.download()
    article.parse()
    article.nlp()
    text = article.text
    return text

def add_to_returnObj(questions, obj, type): #This needs to be cleaned up a bit, but this just accesses the information that we want and adds it into a list to add the question_list.
    if type == 'shortq':
        statement = 'Question'
    if type == 'bool':
        statement = 'Question'
    for question in questions['questions']:
        list = {
            'question': question[statement],
            'context': question['context']
        }
        obj.append(list)


if __name__ == "__main__": #Flask hosting stuff
    app.run(host="127.0.0.1", port=8080, debug=True)
    