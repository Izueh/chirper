from flask.views import MethodView
from elasticsearch_dsl import Search
from flask import request, jsonify, session, Response, send_file
from messages import CODE_ERROR, CODE_OK, NOT_LOGGED_IN
from db import db, fs, es
from time import time
from bson import ObjectId
import sys
from bson.json_util import dumps
from uuid import uuid1, UUID
from io import BytesIO


class AddItem(MethodView):
    def post(self):
        json = request.get_json()
        item = {}
        item['content'] = json['content']
        item['timestamp'] = time()
        item['username'] = session['username']
        if 'parent' not in json:
            item['parent'] = None
        else:
            item['parent'] = json['parent']
        if 'media' in json:
            item['media'] = json['media']
        obj_id = ObjectId()
        item['_id'] = obj_id
        item['id'] = str(obj_id)
        result = db.items.insert_one(item)
        if result.acknowledged:
            # if json['parent']:
            # json['_id']=json['id']
            #db.items.update_one({'_id':ObjectId(json['parent'])},{'$push':{'replies':json}, '$inc': {'interest_score': 1} })
            return jsonify({'status': 'OK', 'id': str(obj_id)})
        else:
            return jsonify(CODE_ERROR)


class Item(MethodView):
    def get(self, id):
        result = db.items.find_one({'_id': ObjectId(id)})
        if result:
            result['_id'] = str(result['_id'])
            return jsonify({'status': 'OK', 'item': result})
        else:
            return jsonify(CODE_ERROR)

    def delete(self, id):
        result = db['items'].find_one_and_delete({"_id": ObjectId(id)})
        if 'media' in result:
            media = list(map(lambda x: ObjectId(x), result['media']))
            if media:
                db.media.delete_many({"_id": {"$in": media}})
        if result:
            return jsonify({'status': 'OK'})
        else:
            return jsonify({'status': 'error', "error": "not found"})

    def post(self, id):
        json = request.get_json()
        tweet = db.items.find_one({'_id': ObjectId(id)})
        if 'likes' not in tweet:
            tweet['likes'] = []
        if 'interest_score' not in tweet:
            tweet['interest_score'] = 0
        if json['like']:
            if session['username'] in tweet['likes']:
                return jsonify({'status': 'error',
                                'error': 'user already likes this tweet'})
            tweet['likes'].append(session['username'])
            tweet['interest_score'] = tweet['interest_score'] + 1
        else:
            if session['username'] in tweet['likes']:
                tweet['likes'].remove(session['username'])
                tweet['interest_score'] = tweet['interest_score'] - 1
            else:
                return jsonify(
                    {'status': 'error', 'error': 'user has not liked this'})
        db.items.replace_one({'_id': tweet['_id']}, tweet)
        return jsonify({'status': 'OK'})

# Search seems to be only related to tweets at least for their api,
# we could just have this implementation to conform to their api.


class OldSearch(MethodView):
    def post(self):
        json = request.get_json()
        username = json.pop('username') if 'username' in json else None
        following = True
        if 'following' in json:
            following = json.pop('following')
        else:
            if username:
                following = True
        timestamp = json.pop('timestamp') if 'timestamp' in json else time()
        search = 'q' in json
        limit = json.pop(
            'limit') if 'limit' in json and json['limit'] <= 100 else 50
        following_list = db.user.find_one({'username': session['username']})[
            'following']  # do we only need this is following=true?
        query = {'timestamp': {'$lte': timestamp}}
        if search:
            query['$text'] = {'$search': json['q']}
        if username:
            if following:
                query['username'] = username if username in following_list else ''
            else:
                query['username'] = username
        else:
            if following:
                query['username'] = {'$in': following_list}
        # my code
        if 'parent' in json:
            query['parent'] = json['parent']
        if 'replies' not in json:
            json['replies'] = True
        if not json['replies']:
            query['parent'] = None
        # endmy code

        if 'rank' not in json:
            json['rank'] = 'interest'

        if json['rank'] == 'time':
            sort_key = 'timestamp'
        else:
            sort_key = 'interest_score'
        sort_dir = -1

        #results = db.items.find(query).sort(sort_key, sort_dir).limit(limit)
        #results = db.items.find(filter=query, limit=limit, sort=sort_by)
        results = db.items.aggregate(
            [{'$match': query}, {'$limit': limit}, {'$sort': {sort_key: sort_dir}}])
        return Response(response=dumps(
            {'status': 'OK', 'items': list(results)}), mimetype='application/json')

# class ShitMedia(MethodView):
    # def get(self, id):
        #new_id = UUID(id)
        # row = cassandra.execute(
        #"SELECT * FROM media WHERE id = %s ",
        # (new_id,)
        # )

        # if not row:
        # return jsonify({'status': 'error'})
        # else:
        #f = BytesIO(row[0].contents)
        # return
        # send_file(f,attachment_filename=row[0].filename,mimetype=row[0].mimetype)

    # def post(self):
        #f = request.files['content']
        #new_id = uuid1()

        # cassandra.execute(
        #"INSERT INTO media (id, contents, filename, mimetype) VALUES (%s,%s,%s,%s)",
        #(new_id, f.stream.read(), f.name, f.mimetype)
        # )

        # return jsonify({'status': 'OK', 'id': str(new_id)})


class ESearch(MethodView):
    def post(self):
        json = request.get_json()
        s = Search(using=es, index='twitter', doc_type='items')
        username = json.pop('username') if 'username' in json else None
        following = True
        if 'following' in json:
            following = json.pop('following')
        else:
            if username:
                following = True
        timestamp = json.pop('timestamp') if 'timestamp' in json else time()
        search = 'q' in json
        limit = json.pop(
            'limit') if 'limit' in json and json['limit'] <= 100 else 50
        following_list = db.user.find_one({'username': session['username']})[
            'following']  # do we only need this is following=true?
        #query = {'timestamp':{'$lte':timestamp}}
        s = s.filter('range', timestamp={'lte': timestamp})
        if search:
            #query['$text'] = {'$search':json['q']}
            s = s.query('match', content=json['q'])
        if username:
            if following:
                query['username'] = username if username in following_list else ''
                s = s.filter('term', username=query['username'])
            else:
                #query['username'] = username
                s = s.filter('term', username=username)
        else:
            if following:
                #query['username'] = {'$in': following_list}
                s = s.filter('terms', username=following_list)
        # my code
        if 'parent' in json:
            #query['parent'] = json['parent']
            s = s.filter('term', parent=json['parent'])
        if 'replies' not in json:
            json['replies'] = True
        if not json['replies']:
            query['parent'] = None
            s = s.filter('term', parent=None)
        # endmy code
        if 'rank' not in json:
            json['rank'] = 'interest'
        s = s[0:limit]

        if json['rank'] == 'time':
            sort_key = 'timestamp'
            s = s.sort('-timestamp')
        else:
            sort_key = 'interest_score'
            s = s.sort('-interest_score')
        #sort_dir = -1

        #results = db.items.find(query).sort(sort_key, sort_dir).limit(limit)
        #results = db.items.find(filter=query, limit=limit, sort=sort_by)
        #results = db.items.aggregate([{'$match':query}, {'$limit': limit}, {'$sort': sort_by}])
        results = s.execute()
        l = [x['_source'].to_dict() for x in results['hits']['hits']]
        return Response(response=dumps(
            {'status': 'OK', 'items': l}), mimetype='application/json')


class OldMedia(MethodView):
    def post(self):
        f = request.files['content']
        new_id = fs.put(f, content_type=f.mimetype)
        return jsonify({'status': 'OK', 'id': str(new_id)})

    def get(self, id):
        try:
            f = fs.get(ObjectId(id))
            return send_file(f, mimetype=f.content_type)
        except BaseException:
            return jsonify({'status': 'error', 'error': 'file not present'})


class Media(MethodView):
    def post(self):
        f = request.files['content']
        media = {}
        media['content'] = f.stream.read()
        media['content_type'] = f.mimetype
        result = db.media.insert_one(media)
        if result.acknowledged:
            return jsonify({"status": "OK", "id": str(result.inserted_id)})
        else:
            return jsonify({"status": "error", "error": "failed to insert"})

    def get(self, id):
        result = db.media.find_one({"_id": ObjectId(id)})
        if result:
            f = BytesIO(result['content'])
            return send_file(f, mimetype=result['content_type'])
        else:
            return jsonify({"status": "error", "error": "file not found"})
