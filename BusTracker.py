import boto3
import csv
import os

THRESHOLD = 5


class BusTracker:
    def __init__(self, cta_data, rt_from, rt_to, in_lambda=False, log=False):
        self.cta_data = cta_data
        self.rt_from = rt_from
        self.rt_to = rt_to
        self.in_lambda = in_lambda
        self.log = log

        self.s3_client = None
        self.updated_data = False
        self.buses = {}
        self.data_path = "%s.csv" % self.cta_data[0]['tmstmp'].split(' ')[0]

    def process(self):
        if self.cta_data:
            self.read_csv_data()
            self.update_bus_info()
            self.write_csv_data()

    def read_csv_data(self):
        if self.in_lambda:
            self.s3_client = boto3.client('s3')
            try:
                obj = self.s3_client.get_object(Bucket='bus-time-lambda-bucket', Key=self.data_path)
                lines = [line.split(',') for line in obj['Body'].read().decode('utf-8').split('\n')]
                self.parse_csv_data(lines)
            except Exception as e:
                print(e)
        else:
            if file_exists(self.data_path):
                with open(self.data_path, mode="r") as file:
                    reader = csv.reader(file)
                    self.parse_csv_data(reader)

    def parse_csv_data(self, lines):
        for vid, *data in lines:
            # Each line is vid,trip_id,from_id,start(,to_id, end)
            if len(data) == 3:
                self.buses[vid] = {'trip_id': data[0], 'from': data[1], 'start': data[2]}
            if len(data) == 5:
                self.buses[vid] = {'trip_id': data[0], 'from': data[1], 'start': data[2], 'to': data[3], 'end': data[4]}

    def update_bus_info(self):
        for bus in self.cta_data:
            if bus['prdctdn'] < THRESHOLD:
                vid = bus['vid']
                stpid = bus['stpid']
                prdtm = bus['prdtm']
                trip_id = bus['tatripid']
                if stpid in self.rt_from and vid not in self.buses:  # Bus is departing
                    self.buses[vid] = {'trip_id': trip_id, 'from': stpid, 'start': prdtm}
                    self.updated_data = True
                elif stpid in self.rt_to and vid in self.buses and trip_id == self.buses[vid]['trip_id']:  # Bus is arriving
                    self.buses[vid]['to'] = stpid
                    self.buses[vid]['end'] = prdtm
                    self.updated_data = True

        if self.log:
            for vid in self.buses:
                tmp = "VID: %s | Trip ID: %s | From: %s | Start: %s" % (vid, self.buses[vid]["trip_id"],
                                                                        self.buses[vid]["from"],
                                                                        self.buses[vid]["start"])
                if len(self.buses[vid]) == 4:
                    tmp += " | To: %s | End: %s" % (self.buses[vid]["to"], self.buses[vid]["end"])
                print(tmp)

    def write_csv_data(self):
        if self.updated_data:
            if self.in_lambda:
                data = ""
                for vid in self.buses:
                    data += self.formatted_csv_line(vid)
                self.s3_client.put_object(Body=data, Bucket='bus-time-lambda-bucket', Key=self.data_path)
            else:
                with open(self.data_path, mode="w") as file:
                    writer = csv.writer(file)
                    for vid in self.buses:
                        writer.writerow(self.formatted_csv_line(vid))

    def formatted_csv_line(self, vid):
        if len(self.buses[vid]) == 3:
            tmp = [vid, self.buses[vid]['trip_id'], self.buses[vid]['from'], self.buses[vid]['start']]
        else:
            tmp = [vid, self.buses[vid]['trip_id'], self.buses[vid]['from'], self.buses[vid]['start'],
                   self.buses[vid]['to'], self.buses[vid]['end']]

        return ",".join(tmp) + "\n" if self.in_lambda else tmp


def file_exists(path):
    return os.path.exists(path)
