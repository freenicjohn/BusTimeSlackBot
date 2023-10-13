from helpers import *
import csv
import datetime


THRESHOLD = 3
TIME_FORMAT = "%Y-%m-%d %H:%M"


def read_started_data(data_path):
    started = {}
    if file_exists("%s/started.csv" % data_path):
        with open("%s/started.csv" % data_path, mode="r") as file:
            reader = csv.reader(file)
            for vid, start_time in reader:
                started[vid] = datetime.datetime.strptime(start_time, TIME_FORMAT)

    return started


def update_started_data(started, data_path):
    with open("%s/started.csv" % data_path, mode="w") as file:
        writer = csv.writer(file)
        for vid in started:
            writer.writerow([vid, started[vid].strftime(TIME_FORMAT)])


def append_completed_data(completed, data_path):
    with open("%s/completed.csv" % data_path, mode="a") as file:
        writer = csv.writer(file)
        for vid in completed:
            writer.writerow([vid, completed[vid]["left_at"].strftime(TIME_FORMAT),
                             completed[vid]["completed_at"].strftime(TIME_FORMAT)])


def track_buses(buses, started, data_path, log=False):
    updated_started = False
    updated_completed = False
    completed = {}

    print("Upcoming:") if log else ""
    for bus in buses:
        # Check departures
        if bus.departing:
            print("\t- Departure: %s in %s min" % (bus.vid, bus.minutes)) if log else ""
            if bus.vid not in started and bus.minutes < THRESHOLD:
                started[bus.vid] = (datetime.datetime.now() + datetime.timedelta(minutes=bus.minutes))
                updated_started = True
                print("\t\t* Added to started.csv since %s < %s" % (bus.minutes, THRESHOLD)) if log else ""
        # Check arrivals
        if bus.arriving:
            print("\t- Arrival: %s in %s min" % (bus.vid, bus.minutes)) if log else ""
            if bus.vid in started and bus.minutes < THRESHOLD:
                completed[bus.vid] = {"left_at": started.pop(bus.vid), "completed_at": now_plus(bus.minutes)}
                updated_completed = True
                updated_started = True
                print("\t\t* Added to completed.csv since %s < %s" % (bus.minutes, THRESHOLD)) if log else ""

    if log:
        print("\nIn Progress:")
        for vid in started:
            print("\t- %s" % vid)

    # Write files
    update_started_data(started) if updated_started else ""
    append_completed_data(completed) if updated_completed else ""


def gather_data():
    set_timezone()
    response = call_cta_api(stpid_string="%s,%s" % (os.environ["from_stpid"], os.environ["to_stpid"]), log=True)
    data_path = get_data_path(os.environ["from_stpid"], os.environ["to_stpid"])
    buses = extract_bus_info(response)
    started = read_started_data(data_path)
    track_buses(buses, started, data_path, log=True)


if __name__ == "__main__":
    load_secrets()
    gather_data()
