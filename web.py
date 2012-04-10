from flask import Flask, request, Response, render_template
import redis
import os, urlparse
from functools import wraps
import boto


try:
    urlparse.uses_netloc.append('redis')
    url = urlparse.urlparse(os.environ['REDISTOGO_URL'])
    r = redis.StrictRedis(host=url.hostname, port=url.port, 
                          db=0, password=url.password)
except KeyError:
    r = redis.StrictRedis()


def check_auth(username, password):
    """This function is called to check if a username /
    password combination is valid.
    """
    return password == 'secret'


def boot_machine(ttl):
    conn = boto.connect_ec2()
    conn.run_instances(
        os.environ['AWS_AMI_IMAGE'],
        key_name=os.environ['AWS_KEY_PATH_PATH'],
        instance_type=os.environ['AWS_MACHINE_SIZE'],
        security_groups=[os.environ['AWS_SECURITY_GROUP'])


def machine(name):
    return {
        'instance_id': name,
        'tunnel': '',
    }


def machines():
    return [machine(name) for name in r.zrange("machines", 0, -1)]


def authenticate():
    """Sends a 401 response that enables basic auth"""
    return Response(
    'Could not verify your access level for that URL.\n'
    'You have to login with proper credentials', 401,
    {'WWW-Authenticate': 'Basic realm="Login Required"'})


def authenticated(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/machines")
@authenticated
def machines():
    return render_template("machines.html")
