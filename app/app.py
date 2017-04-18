from flask import Flask, request, session
from pymongo import MongoClient
from views.authentication import AddUser, Login, Logout, Verify
from views.items import AddItem, Search, Item, Media
from views.user import User, Follow, Following, Followers
import messages
import logging

app = Flask(__name__)
app.secret_key = 'secret sezchuan sauce'

gunicorn_error_logger = logging.getLogger('log/gunicorn-error')
app.logger.handlers.extend(gunicorn_error_logger.handlers)
app.logger.setLevel(logging.DEBUG)

app.add_url_rule('/adduser', view_func=AddUser.as_view('adduser'),methods=['POST'])
app.add_url_rule('/login', view_func=Login.as_view('login'),methods=['POST'])
app.add_url_rule('/verify', view_func=Verify.as_view('verify'),methods=['POST'])
app.add_url_rule('/logout', view_func=Logout.as_view('logout'),methods=['POST'])
app.add_url_rule('/additem',view_func=AddItem.as_view('additem'),methods=['POST'])
app.add_url_rule('/item/<id>', view_func=Item.as_view('item'),methods=['GET', 'DELETE'])
app.add_url_rule('/item/<id>/like',view_func=Item.as_view('like'),methods=['POST'])
app.add_url_rule('/search', view_func=Search.as_view('search'),methods=['POST'])
app.add_url_rule('/media/<id>', view_func=Media.as_view('getmedia'),methods=['GET'])
app.add_url_rule('/addmedia', view_func=Media.as_view('media'),methods=['POST'])
app.add_url_rule('/user/<string:username>',defaults={'query':None},view_func=User.as_view('user'))
app.add_url_rule('/user/<string:username>/<string:query>', view_func=User.as_view('followers'))
#app.add_url_rule('/user/<string:username>/', view_func=Following.as_view('following'))
app.add_url_rule('/follow',view_func=Follow.as_view('follow'),methods=['POST'])

@app.before_request
def log_request_info():
    app.logger.debug('Headers: %s', request.headers)
    app.logger.debug('Body: %s', request.get_data())

if __name__ == '__main__':
    app.config['DEBUG']=True
    app.run()

