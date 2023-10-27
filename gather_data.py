from helpers import *
import csv
import datetime
import boto3

THRESHOLD = 3
TIME_FORMAT = "%Y-%m-%d %H:%M"
STARTED_PATH = "./started.csv"


def save_to_file(data, path, overwrite):
    with open(path, mode="w" if overwrite else "a+") as file:
        writer = csv.writer(file)
        for key in data:
            writer.writerow([key, *[data[key][key2].strftime(TIME_FORMAT) for key2 in data[key]]])


def read_started_data(in_lambda=False):
    started = {}
    if in_lambda:
        s3 = boto3.client('s3')
        started = {}

        obj = s3.get_object(Bucket='bus-time-lambda-bucket', Key='started.csv')
        lines = [line.split(',') for line in obj['Body'].read().decode('utf-8').strip().split('\r\n')]
        for vid, start_time in lines:
            started[vid] = {"left_at": datetime.datetime.strptime(start_time, TIME_FORMAT)}
    else:
        if file_exists(STARTED_PATH):
            with open(STARTED_PATH, mode="r") as file:
                reader = csv.reader(file)
                for vid, start_time in reader:
                    started[vid] = {"left_at": datetime.datetime.strptime(start_time, TIME_FORMAT)}
    return started


def track_buses(buses, started, completed_data_path, in_lambda=False, log=False):
    updated_started = False
    updated_completed = False
    completed = {}

    print("Upcoming:") if log else ""
    for bus in buses:
        # Check departures
        if bus.departing:
            print("\t- Departure: %s in %s min" % (bus.vid, bus.minutes)) if log else ""
            if bus.vid not in started and bus.minutes < THRESHOLD:
                started[bus.vid] = {"left_at": (datetime.datetime.now() + datetime.timedelta(minutes=bus.minutes))}
                updated_started = True
                print("\t\t* Added to started.csv since %s < %s" % (bus.minutes, THRESHOLD)) if log else ""
        # Check arrivals
        if bus.arriving:
            print("\t- Arrival: %s in %s min" % (bus.vid, bus.minutes)) if log else ""
            if bus.vid in started and bus.minutes < THRESHOLD:
                completed[bus.vid] = {"left_at": started.pop(bus.vid)["left_at"], "completed_at": now_plus(bus.minutes)}
                updated_completed = True
                updated_started = True
                print("\t\t* Added to completed.csv since %s < %s" % (bus.minutes, THRESHOLD)) if log else ""

    if log:
        print("\nIn Progress:")
        for vid in started:
            print("\t- %s" % vid)

    # Write files
    save_to_file(started, STARTED_PATH, overwrite=True) if updated_started and not in_lambda else ""
    save_to_file(completed, completed_data_path, overwrite=False) if updated_completed and not in_lambda else ""


def gather_data(in_lambda=False):
    set_timezone()
    response = call_cta_api(stpid_string="%s,%s" % (os.environ["from_stpid"], os.environ["to_stpid"]), log=True)
    buses = extract_bus_info(response)
    completed_data_path = get_data_paths(os.environ["from_stpid"], os.environ["to_stpid"])
    started = read_started_data(in_lambda)
    track_buses(buses, started, completed_data_path, in_lambda, log=True)


def lambda_handler(event, context):
    gather_data(in_lambda=True)


if __name__ == "__main__":
    load_secrets()
    gather_data()
