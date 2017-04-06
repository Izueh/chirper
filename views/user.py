from flask import jsonify, request, session
from flask.views import MethodView
from db import db
import messages

class User(MethodView):
    def get(self, username):
        user = db.user.find_one({'username':username})
        user['_id'] = str(user['_id'])
        return jsonify({'status':'OK','user':user})
        
class Following(MethodView):
    def get(username):
        user = db.user.find_one({'username':username})
        return jsonify({'status':'OK', 'users':user['following']})

class Followers(MethodView):
    def get(username):
        user = db.user.find_one({'username':username})
        return jsonify({'status':'OK', 'users':user['followers']})


class Follow(MethodView):
    def post(self):
        json = request.get_json()
        follow = True
        if 'follow' in json:
            follow = json.pop('follow')
        if follow:
            db.user.update_one({'username':session['username']},{ '$push':{'followers':json['username']}})
            db.user.update_one({'username':json['username']},{'&push':{'followers':session['username']}})
        else:
            db.user.update_one({'username':session['username']},{ '$pull':{'followers':json['username']}})
            db.user.update_one({'username':json['username']},{'&pull':{'followers':session['username']}})

        return jsonify(CODE_OK)
