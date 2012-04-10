from flask import Flask, request, Response, render_template, redirect
import os, urlparse, json
from functools import wraps
import boto


def check_auth(username, password):
    """This function is called to check if a username /
    password combination is valid.
    """
    return password == os.environ['POPFLY_PASSWORD']


def create_instance(conn, ttl):
    reservation = conn.run_instances(
        os.environ['AWS_AMI_IMAGE'],
        key_name=os.environ['AWS_KEY_NAME'],
        instance_type=os.environ['AWS_INSTANCE_TYPE'],
        security_groups=[os.environ['AWS_SECURITY_GROUP']],
        user_data=json.dumps({"duration": ttl, "popfly": True}))


def tunnel_cmd(instance):
    cmd = "ssh -i ~/.ssh/{}.pem {}@{} -D 2001"
    return cmd.format(os.environ['AWS_KEY_NAME'], os.environ['AWS_USER'],
                      instance.public_dns_name)


def get_instances(conn):
    for reservation in conn.get_all_instances():
        for instance in reservation.instances:
            if instance.state == 'running':
                instance.socks = tunnel_cmd(instance)
                yield instance


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
app.debug = True


@app.route("/help")
def help():
    return render_template("help.html")


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/machines/<instance_id>", methods=['POST'])
def terminate(instance_id):
    conn = boto.connect_ec2()
    for reservation in conn.get_all_instances(instance_ids=[instance_id]):
        for instance in reservation.instances:
            instance.terminate()
    return redirect("/machines")


@app.route("/machines", methods=['POST', 'GET'])
@authenticated
def machines():
    conn = boto.connect_ec2()
    if request.method == 'POST':
        create_instance(conn, int(request.form.get('ttl', 3)))
        return redirect("/machines")
    return render_template("machines.html", machines=get_instances(conn))
