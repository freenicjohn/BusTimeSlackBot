from helpers import *
import csv
import datetime
import boto3

s3_client = None
THRESHOLD = 3
TIME_FORMAT = "%Y-%m-%d %H:%M"


def save_locally(started, completed, path):
    with open(path, mode="w") as file:
        writer = csv.writer(file)
        for bus_id in completed:
            writer.writerow([bus_id, completed[bus_id]["start"].strftime(TIME_FORMAT),
                             completed[bus_id]["end"].strftime(TIME_FORMAT)])
        for bus_id in started:
            writer.writerow([bus_id, started[bus_id]["start"].strftime(TIME_FORMAT)])


def save_s3(started, completed, data_path):
    global s3_client
    data = ""

    for bus_id in completed:
        data += "%s,%s,%s\n" % (bus_id, completed[bus_id]["start"].strftime(TIME_FORMAT),
                                completed[bus_id]["end"].strftime(TIME_FORMAT))
    for bus_id in started:
        data += "%s,%s\n" % (bus_id, started[bus_id]["start"].strftime(TIME_FORMAT))

    s3_client.put_object(Body=data, Bucket='bus-time-lambda-bucket', Key=data_path.split("/")[-1])


def read_data(from_stpid, to_stpid, in_lambda=False):
    global s3_client
    started = {}
    completed = {}
    path = get_data_path(from_stpid, to_stpid)

    if in_lambda:
        s3_client = boto3.client('s3')
        try:
            obj = s3_client.get_object(Bucket='bus-time-lambda-bucket', Key=path.split("/")[-1])
            lines = [line.split(',') for line in obj['Body'].read().decode('utf-8').split('\n')]
            started, completed = parse_data(lines)
        except Exception as e:
            print(e)
    else:
        if file_exists(path):
            with open(path, mode="r") as file:
                reader = csv.reader(file)
                started, completed = parse_data(reader)

    return started, completed


def parse_data(lines):
    started = {}
    completed = {}

    for vals in lines:
        if len(vals) == 2:
            started[vals[0]] = {"start": datetime.datetime.strptime(vals[1], TIME_FORMAT)}
        if len(vals) == 3:
            completed[vals[0]] = {"start": datetime.datetime.strptime(vals[1], TIME_FORMAT),
                                  "end": datetime.datetime.strptime(vals[2], TIME_FORMAT)}

    return started, completed


def track_buses(buses, started, completed, from_stpid, to_stpid, in_lambda=False, log=False):
    updated_data = False

    for bus in buses:
        # Check departures
        if bus.departing:
            if bus.vid not in started and bus.minutes < THRESHOLD:
                started[bus.vid] = {"start": (datetime.datetime.now() + datetime.timedelta(minutes=bus.minutes))}
                updated_data = True
        # Check arrivals
        if bus.arriving:
            if bus.vid in started and bus.minutes < THRESHOLD:
                completed[bus.vid] = {"start": started.pop(bus.vid)["start"], "end": now_plus(bus.minutes)}
                updated_data = True

    if log:
        print("\n".join(["%s | start: %s" % (vid, started[vid]["start"]) for vid in started]))
        print("\n".join(["%s | start: %s | end: %s" % (vid, completed[vid]["start"], completed[vid]["end"]) for vid in completed]))

    if updated_data:
        data_path = get_data_path(from_stpid, to_stpid)
        if in_lambda:
            save_s3(started, completed, data_path)
        else:
            save_locally(started, completed, data_path)


def gather_data(in_lambda=False):
    set_timezone()
    response = call_cta_api(stpid_string="%s,%s" % (os.environ["from_stpids"], os.environ["to_stpids"]), log=not in_lambda)
    for from_stpid, to_stpid in zip(os.environ["from_stpids"].split(","), os.environ["to_stpids"].split(",")):
        buses = extract_bus_info(response, from_stpid, to_stpid)
        started, completed = read_data(from_stpid, to_stpid, in_lambda)
        track_buses(buses, started, completed, from_stpid, to_stpid, in_lambda, log=True)


def lambda_handler(event, context):
    gather_data(in_lambda=True)


if __name__ == "__main__":
    load_secrets()
    gather_data()
