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
            if os.path.exists(self.data_path):
                with open(self.data_path, mode="r") as file:
                    reader = csv.reader(file)
                    self.parse_csv_data(reader)

    def parse_csv_data(self, lines):
        for vid, *data in lines:
            # Each line is vid-trip_id,from_id,start(,to_id, end)
            if len(data) == 2:
                self.buses[vid] = {'from': data[0], 'start': data[1]}
            elif len(data) == 4:
                self.buses[vid] = {'from': data[0], 'start': data[1], 'to': data[2], 'end': data[3]}

    def update_bus_info(self):
        for bus in self.cta_data:
            if bus['prdctdn'] < THRESHOLD:
                uid = "%s-%s" % (bus['vid'], bus['tatripid'])
                stpid = bus['stpid']
                prdtm = bus['prdtm']
                if stpid in self.rt_from and uid not in self.buses:  # Bus is departing
                    self.buses[uid] = {'from': stpid, 'start': prdtm}
                    self.updated_data = True
                elif stpid in self.rt_to and uid in self.buses:  # Bus is arriving
                    self.buses[uid]['to'] = stpid
                    self.buses[uid]['end'] = prdtm
                    self.updated_data = True

        if self.log:
            for uid in self.buses:
                tmp = "VID-Trip ID: %s | From: %s | Start: %s" % (uid,
                                                                  self.buses[uid]["from"],
                                                                  self.buses[uid]["start"])
                if len(self.buses[uid]) != 2:
                    tmp += " | To: %s | End: %s" % (self.buses[uid]["to"], self.buses[uid]["end"])
                print(tmp)

    def write_csv_data(self):
        if self.updated_data:
            if self.in_lambda:
                data = ""
                for uid in self.buses:
                    data += self.formatted_csv_line(uid)
                self.s3_client.put_object(Body=data, Bucket='bus-time-lambda-bucket', Key=self.data_path)
            else:
                with open(self.data_path, mode="w") as file:
                    writer = csv.writer(file)
                    for uid in self.buses:
                        writer.writerow(self.formatted_csv_line(uid))

    def formatted_csv_line(self, uid):
        if len(self.buses[uid]) == 2:
            tmp = [uid, self.buses[uid]['from'], self.buses[uid]['start']]
        else:
            tmp = [uid, self.buses[uid]['from'], self.buses[uid]['start'], self.buses[uid]['to'],
                   self.buses[uid]['end']]

        return ",".join(tmp) + "\n" if self.in_lambda else tmp
