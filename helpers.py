from datetime import datetime, timedelta
import os
import requests
import time
import json


def load_secrets(secret_names):
    # Load secrets (that would otherwise be set in the aws configuration)
    f = open("../BusTimeSlackBot_overlays/secrets.json")
    secrets = json.load(f)
    f.close()
    for name in secret_names:
        os.environ[name] = secrets[name]


def set_timezone():
    os.environ['TZ'] = 'US/Central'
    time.tzset()


def now_plus(minutes):
    return datetime.now() + timedelta(minutes=minutes)


def file_exists(path):
    return os.path.exists(path)
