from datetime import datetime
import os
import requests


class CtaData:
    def __init__(self, api_key, from_list, to_list, num_list, log=False):
        self.routes = []
        self.data = {}
        self.api_key = api_key
        self.log = log

        self.get_routes(from_list, to_list, num_list)

    def get_routes(self, from_list, to_list, num_list):
        if not(len(from_list) == len(to_list) and len(to_list) == len(num_list)):
            raise "Length of from_list, to_list, and num_list must be equal"

        for i in range(len(from_list)):
            self.routes.append({"from": from_list[i],
                                "to": to_list[i],
                                "num": num_list[i]})

    def get_buses(self):
        rts = set([rt["num"] for rt in self.routes])
        stpids = set([rt["from"] for rt in self.routes]).union(set([rt["to"] for rt in self.routes]))

        if len(stpids) > 10:
            raise "Max 10 stops can be tracked in one request - may change later"

        cta_url = "http://ctabustracker.com/bustime/api/v2/getpredictions?key=%s&stpid=%s&rt=%s&format=json" % \
                  (self.api_key, ",".join(list(stpids)), ",".join(list(rts)))
        if self.log:
            print("Requesting: %s" % cta_url)

        self.data = requests.get(cta_url).json()

        return self.extract_bus_data()

    def extract_bus_data(self):
        bus_data = []
        if "prd" in self.data["bustime-response"]:
            data = self.data["bustime-response"]['prd']
            for bus in data:
                bus_data.append(BusRecord(bus, self.routes))
        return bus_data


class BusRecord:
    def __init__(self, data, routes):
        self.due = data["prdctdn"] == "DUE"
        self.dly = data["dly"]
        self.minutes = 0 if self.due or self.dly else int(data["prdctdn"])
        self.departure_time = datetime.strptime(data["prdtm"], '%Y%m%d %H:%M').strftime('%I:%M %p')
        self.rt = data["rt"]
        self.vid = data["vid"]
        self.stpid = data["stpid"]
        self.departing = self.stpid in [route["from"] for route in routes]
        self.arriving = self.stpid in [route["to"] for route in routes]
