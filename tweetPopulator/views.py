from django.shortcuts import render
from django.utils import timezone
import tweepy
from django.http import HttpResponse, JsonResponse
import json
import time
from datetime import datetime
import os
from pprint import pprint
from models import Tweets
from decimal import Decimal
from geoposition import Geoposition
from django.shortcuts import render
from django.template import RequestContext
from elasticsearch import Elasticsearch
import re

#Instantiating Elasticsearch
es = Elasticsearch()

# Authentication details. To  obtain these visit dev.twitter.com
consumer_key = 'YOUR_KEY'
consumer_secret = 'YOUR_SECRET_KEY'
access_token = 'YOUR_TOKEN'
access_token_secret = 'YOUR_SECRET_TOKEN'

# This is the listener, resposible for receiving data
class StdOutListener(tweepy.StreamListener):
    def __init__(self,time_limit=60):
        self.start_time = time.time()
        self.limit = time_limit
        super(StdOutListener, self).__init__()
    
    def on_data(self, data):
        if (time.time() - self.start_time) < self.limit:
            decoded = json.loads(data)
            place = decoded.get('place')
            if place is not None:
                #print(place)
                self.append_record(decoded)
                return True
        else:
            return False

    def on_error(self, status_code):
        print("response: %s" % status_code)
        if status_code == 420:
            return False

    def append_record(self, record):
        with open('my_file_1', 'a') as f:
            json.dump(record, f)
            f.write(os.linesep)



#FIlters tweets based on the searchstring and renders it to the html
def filter(request):
    if request.method == "GET":
        if 'searchstring' in request.GET:
            query = str(request.GET.get('searchstring', ''))
            try:
                l = StdOutListener(time_limit=20)
                auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
                auth.set_access_token(access_token, access_token_secret)
                stream = tweepy.Stream(auth, l)
                stream.filter(track=[query])
                res=file_read()
                tweets=es.search(index='tweet_index', body={"from" : 0, "size" : 1000,"query":{"match_all":{}}})
                tweets=tweets['hits']['hits']
                b=[]
                for tweet in tweets:
                    source = tweet.get('_source')
                    a={}
                    #a.append(source.get('location').get('lat'))
                    #a.append(source.get('location').get('lon'))
                    #a.append(source.get('title'))
                    a['lat'] = source.get('location').get('lat')
                    a['lon'] = source.get('location').get('lon')
                    a['title'] = re.escape(source.get('title'))
                    b.append(a)
                if os.path.exists('my_file_1'):
                    os.remove('my_file_1')
                return JsonResponse({'tweets': b})
            except (AttributeError, ValueError) as v:
                print v
                return HttpResponse('Error')


#Renders the index.html on startup
def init_index(request):
    return render(request, 'index.html')


#Read the file consisting of tweets  and index it using elasticsearch
def file_read():
    with open('my_file_1') as f:
        for line in f:
            try:
                data = json.loads(line)
                place = data.get('place')
                coordinates = (place.get('bounding_box').get('coordinates')[0])[0]
                lat = coordinates[0]
                lng = coordinates[1]
                lng = Decimal(("%0.5f" % lng))
                lat = Decimal(("%0.5f" % lat))
                doc = {
                "timestamp":datetime.now(),
                "location":{
                    "lat":lng,
                    "lon":lat 
                } ,
                "title":data.get('text')
                }
                #pprint(data)
                res = es.index(index="tweet_index", doc_type='tweet', id=data.get('id'), body=doc)
            except:
                print 'Error here'
                pass
    return res
