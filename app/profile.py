from werkzeug.contrib.profiler import ProfilerMiddleware
from app import app

app.config['PROFILE'] = True
f = open('/home/ubuntu/log/profile.log', 'w')
app.wsgi_app = ProfilerMiddleware(app.wsgi_app, stream=f, restrictions=[10])
app.run(debug=True)
