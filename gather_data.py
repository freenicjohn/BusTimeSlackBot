from helpers import *
import csv
import datetime
import boto3

s3_client = None
THRESHOLD = 3
TIME_FORMAT = "%Y-%m-%d %H:%M"
STARTED_PATH = "./started.csv"


def save_locally(started, completed, path):
    with open(path, mode="w") as file:
        writer = csv.writer(file)
        for key in completed:
            writer.writerow([key, *[completed[key][key2].strftime(TIME_FORMAT) for key2 in completed[key]]])
        for key in started:
            writer.writerow([key, *[started[key][key2].strftime(TIME_FORMAT) for key2 in started[key]]])


def save_s3(data_path):
    global s3_client
    s3_client.put_object(Body=open(data_path, 'rb'), Bucket='bus-time-lambda-bucket', Key=data_path.split("/")[-1])


def read_data(path, in_lambda=False):
    global s3_client
    started = {}
    completed = {}
    if in_lambda:
        s3_client = boto3.client('s3')

        obj = s3_client.get_object(Bucket='bus-time-lambda-bucket', Key='started.csv')
        lines = [line.split(',') for line in obj['Body'].read().decode('utf-8').strip().split('\r\n')]
        for vid, start_time in lines:
            started[vid] = {"left_at": datetime.datetime.strptime(start_time, TIME_FORMAT)}
    else:
        if file_exists(path):
            with open(path, mode="r") as file:
                reader = csv.reader(file)
                for vals in reader:
                    if len(vals) == 2:
                        started[vals[0]] = {"left_at": datetime.datetime.strptime(vals[1], TIME_FORMAT)}
                    if len(vals) == 3:
                        completed[vals[0]] = {"left_at": datetime.datetime.strptime(vals[1], TIME_FORMAT),
                                              "completed_at": datetime.datetime.strptime(vals[2], TIME_FORMAT)}
    return started, completed


def track_buses(buses, started, completed, data_path, in_lambda=False, log=False):
    updated_data = False

    print("Upcoming:") if log else ""
    for bus in buses:
        # Check departures
        if bus.departing:
            print("\t- Departure: %s in %s min" % (bus.vid, bus.minutes)) if log else ""
            if bus.vid not in started and bus.minutes < THRESHOLD:
                started[bus.vid] = {"left_at": (datetime.datetime.now() + datetime.timedelta(minutes=bus.minutes))}
                updated_data = True
                print("\t\t* Trip beginning since %s < %s" % (bus.minutes, THRESHOLD)) if log else ""
        # Check arrivals
        if bus.arriving:
            print("\t- Arrival: %s in %s min" % (bus.vid, bus.minutes)) if log else ""
            if bus.vid in started and bus.minutes < THRESHOLD:
                completed[bus.vid] = {"left_at": started.pop(bus.vid)["left_at"], "completed_at": now_plus(bus.minutes)}
                updated_data = True
                updated_data = True
                print("\t\t* Trip completed since %s < %s" % (bus.minutes, THRESHOLD)) if log else ""

    if log:
        print("\nIn Progress:")
        for vid in started:
            print("\t- %s" % vid)

    if updated_data:
        save_locally(started, completed, data_path)
        if in_lambda:
            save_s3(data_path)


def gather_data(in_lambda=False):
    set_timezone()
    response = call_cta_api(stpid_string="%s,%s" % (os.environ["from_stpid"], os.environ["to_stpid"]), log=True)
    buses = extract_bus_info(response)
    path = get_data_path(os.environ["from_stpid"], os.environ["to_stpid"])
    started, completed = read_data(path, in_lambda)
    track_buses(buses, started, completed, path, in_lambda, log=True)


def lambda_handler(event, context):
    gather_data(in_lambda=True)


if __name__ == "__main__":
    load_secrets()
    gather_data()
