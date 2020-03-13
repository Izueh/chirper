from pymongo import MongoClient
# from cassandra.cluster import Cluster
from gridfs import GridFS
from elasticsearch import Elasticsearch

client = MongoClient(
    'localhost',
    27017,
    maxPoolSize=None,
    minPoolSize=180,
    socketKeepAlive=True)
db = client.twitter
fs = GridFS(db)
es = Elasticsearch(['search', 'search-1', 'search-2'], sniff_on_start=True)
#cluster = Cluster(['cassandra'])
#cassandra = cluster.connect('dirdemo')
