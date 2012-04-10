#!/usr/bin/env python
import boto
import base64
import json
from datetime import datetime


def seconds_from_hours(hours):
    return hours * 60 * 60


def should_kill(instance):
    attributes = instance.get_attribute("userData")

    if attributes['userData'] == None:
        return False

    user_data = base64.b64decode(attributes['userData'])

    try:
        data = json.loads(user_data)
    except ValueError:
        return False

    if not data.get("popfly"):
        return False

    if instance.state != "running":
        return False

    start = datetime.strptime(instance.launch_time, "%Y-%m-%dT%H:%M:%S.%fZ")
    end = datetime.utcnow()
    life = start - end

    return life.total_seconds() >= seconds_from_hours(data['duration'])


def kill(instance):
    print "BOOM"


conn = boto.connect_ec2()
for reservation in conn.get_all_instances():
    for instance in reservation.instances:
        if should_kill(instance):
            kill(instance)
            print "Killing {}".format(instance.id)
        else:
            print "Sparing {}".format(instance.id)
