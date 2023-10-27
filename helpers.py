import datetime
import os
import requests
import time
import json


class Bus:
    def __init__(self, data):
        self.due = data["prdctdn"] == "DUE"
        self.dly = data["dly"]
        self.minutes = 0 if self.due or self.dly else int(data["prdctdn"])
        self.departure_time = datetime.datetime.strptime(data["prdtm"], '%Y%m%d %H:%M').strftime('%I:%M %p')
        self.vid = data["vid"]
        self.stpid = data["stpid"]
        self.departing = self.stpid == os.environ["from_stpid"]
        self.arriving = self.stpid == os.environ["to_stpid"]


def load_secrets():
    # Load secrets (that would otherwise be set in the aws configuration)
    f = open("../BusTimeSlackBot_overlays/secrets.json")
    secrets = json.load(f)
    f.close()
    secret_names = ["slack_webhook", "from_name", "from_stpid", "rt", "cta_api_key", "to_stpid"]
    for name in secret_names:
        os.environ[name] = secrets[name]


def call_cta_api(stpid_string="", vid="", log=False):
    cta_url = "http://ctabustracker.com/bustime/api/v2/getpredictions?key=%s&vid=%s&stpid=%s&rt=%s&format=json" % \
              (os.environ["cta_api_key"], vid, stpid_string, os.environ["rt"])
    if log:
        print("Requesting: %s\n" % cta_url)
    return requests.get(cta_url).json()


def extract_bus_info(data):
    buses = []
    if "prd" in data["bustime-response"]:
        data = data["bustime-response"]['prd']
        for bus_data in data:
            buses.append(Bus(bus_data))
    return buses


def set_timezone():
    os.environ['TZ'] = 'US/Central'
    time.tzset()


def now_plus(minutes):
    return datetime.datetime.now() + datetime.timedelta(minutes=minutes)


def file_exists(path):
    return os.path.exists(path)


def get_data_paths(from_stpid, to_stpid):
    completed_data_path = "%s_%s_%s_completed.csv" % (from_stpid, to_stpid, datetime.datetime.now().strftime("%Y_%m_%d"))

    return completed_data_path
