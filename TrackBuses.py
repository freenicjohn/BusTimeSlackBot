from datetime import datetime, timedelta
import boto3
import csv
from helpers import now_plus, file_exists

THRESHOLD = 3
TIME_FORMAT = "%Y-%m-%d %H:%M"


class TrackBuses:
    def __init__(self, cta_data, in_lambda=False, log=False):
        self.in_lambda = in_lambda
        self.s3_client = None
        self.buses = {}
        self.log = log
        self.routes = cta_data.routes
        self.data_path = "%s.csv" % datetime.now().strftime("%Y_%m_%d")

        self.read_data()
        self.update_data(cta_data)

    def save_locally(self):
        with open(self.data_path, mode="w") as file:
            writer = csv.writer(file)
            for bus in self.buses.values():
                if bus.completed():
                    writer.writerow([bus.from_id, bus.to_id, bus.rt, bus.vid, bus.start.strftime(TIME_FORMAT),
                                 bus.end.strftime(TIME_FORMAT)])
                else:
                    writer.writerow([bus.from_id, bus.to_id, bus.rt, bus.vid, bus.start.strftime(TIME_FORMAT)])

    def save_s3(self):
        data = ""

        for bus in self.buses.values():
            if bus.completed():
                data += "%s,%s,%s,%s,%s,%s\n" % (bus.from_id, bus.to_id, bus.rt, bus.vid, bus.start.strftime(TIME_FORMAT),
                                 bus.end.strftime(TIME_FORMAT))
            else:
                data += "%s,%s,%s,%s,%s\n" % (bus.from_id, bus.to_id, bus.rt, bus.vid, bus.start.strftime(TIME_FORMAT))

        self.s3_client.put_object(Body=data, Bucket='bus-time-lambda-bucket', Key=self.data_path)

    def print_status(self):
        #for route in self.routes:
            #print("\nFrom: %s To: %s" % (route["from"], route["to"]))
        for bus in self.buses.values():
            bus.print_status()

    def update_data(self, cta_data):
        updated_data = False
        buses = cta_data.get_buses()
        for bus in buses:
            if bus.minutes < THRESHOLD:
                if bus.departing:
                    if bus.vid not in self.buses:
                        self.buses[bus.vid] = self.TrackedBus(bus.stpid, -1, bus.rt, bus.vid,
                                                              (datetime.now() + timedelta(minutes=bus.minutes)))
                        updated_data = True
                if bus.arriving:
                    if bus.vid in self.buses and not self.buses[bus.vid].completed():
                        self.buses[bus.vid].end = now_plus(bus.minutes)
                        self.buses[bus.vid].to_id = bus.stpid
                        updated_data = True

        if self.log:
            self.print_status()

        if updated_data:
            if self.in_lambda:
                self.save_s3()
            else:
                self.save_locally()

    def read_data(self):
        if self.in_lambda:
            self.s3_client = boto3.client('s3')
            try:
                obj = self.s3_client.get_object(Bucket='bus-time-lambda-bucket', Key=self.data_path)
                lines = [line.split(',') for line in obj['Body'].read().decode('utf-8').split('\n')]
                self.parse_data(lines)
            except Exception as e:
                print(e)
        else:
            if file_exists(self.data_path):
                with open(self.data_path, mode="r") as file:
                    reader = csv.reader(file)
                    self.parse_data(reader)

    def parse_data(self, lines):
        for vals in lines:
            # Each line is from_id,to_id,rt,vid,start(,end)
            if len(vals) == 5:
                self.buses[vals[3]] = self.TrackedBus(vals[0], vals[1], vals[2], vals[3],
                                                      datetime.strptime(vals[4], TIME_FORMAT))
            if len(vals) == 6:
                self.buses[vals[3]] = self.TrackedBus(vals[0], vals[1], vals[2], vals[3],
                                                      datetime.strptime(vals[4], TIME_FORMAT),
                                                      datetime.strptime(vals[5], TIME_FORMAT))

    class TrackedBus:
        def __init__(self, from_id, to_id, rt, vid, start, end=None):
            self.from_id = from_id
            self.to_id = to_id
            self.rt = rt
            self.vid = vid
            self.start = start
            self.end = end

        def completed(self):
            return self.end is not None

        def print_status(self):
            if self.completed():
                print("From: %s | To: %s | VID: %s | Route: #%s | Start: %s | End: %s" % (self.from_id, self.to_id, self.vid, self.rt, self.start.strftime(TIME_FORMAT),
                                                         self.end.strftime(TIME_FORMAT)))
            else:
                print("From: %s | VID: %s | Route: #%s | Start: %s" % (self.from_id, self.vid, self.rt, self.start.strftime(TIME_FORMAT)))
