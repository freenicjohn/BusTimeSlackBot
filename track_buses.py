import json
import os
import time
from BusTracker import BusTracker
from CTA import CTA


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


def track_buses(in_lambda=False):
    set_timezone()
    cta_data = CTA(os.environ["cta_bus_api_key"],
                   os.environ["rt_from"].split(","),
                   os.environ["rt_to"].split(","),
                   os.environ["rt_num"].split(","),
                   log=True).get_data()
    BusTracker(cta_data,
               os.environ["rt_from"].split(","),
               os.environ["rt_to"].split(","),
               in_lambda,
               log=True).process()


def lambda_handler(event, context):
    track_buses(in_lambda=True)


if __name__ == "__main__":
    load_secrets(["rt_from", "rt_to", "rt_num", "cta_bus_api_key"])
    track_buses()
