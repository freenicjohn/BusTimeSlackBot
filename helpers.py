from datetime import datetime, timedelta
import os
import requests
import time
import json


class BusRecord:
    def __init__(self, data):
        self.due = data["prdctdn"] == "DUE"
        self.dly = data["dly"]
        self.minutes = 0 if self.due or self.dly else int(data["prdctdn"])
        self.departure_time = datetime.strptime(data["prdtm"], '%Y%m%d %H:%M').strftime('%I:%M %p')
        self.rt = data["rt"]
        self.vid = data["vid"]
        self.stpid = data["stpid"]
        self.departing = self.stpid in os.environ["from_stpids"].split(",")
        self.arriving = self.stpid in os.environ["to_stpids"].split(",")


def get_routes():
    routes = {}
    for from_id, to_id in zip(os.environ["from_stpids"].split(","), os.environ["to_stpids"].split(",")):
        routes[from_id] = to_id

    return routes


def load_secrets():
    # Load secrets (that would otherwise be set in the aws configuration)
    f = open("../BusTimeSlackBot_overlays/secrets.json")
    secrets = json.load(f)
    f.close()
    secret_names = ["slack_webhook", "from_name", "from_stpids", "rts", "cta_api_key", "to_stpids", "notify_rt",
                    "notify_stop_name", "notify_stpid"]
    for name in secret_names:
        os.environ[name] = secrets[name]


def call_cta_api(stpid_string="", vid="", log=False):
    cta_url = "http://ctabustracker.com/bustime/api/v2/getpredictions?key=%s&vid=%s&stpid=%s&rt=%s&format=json" % \
              (os.environ["cta_api_key"], vid, stpid_string, os.environ["rts"])
    if log:
        print("Requesting: %s" % cta_url)
    return requests.get(cta_url).json()


def extract_bus_data(data):
    bus_data = []
    if "prd" in data["bustime-response"]:
        data = data["bustime-response"]['prd']
        for bus in data:
            bus_data.append(BusRecord(bus))
    return bus_data


def set_timezone():
    os.environ['TZ'] = 'US/Central'
    time.tzset()


def now_plus(minutes):
    return datetime.now() + timedelta(minutes=minutes)


def file_exists(path):
    return os.path.exists(path)
