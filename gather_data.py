from helpers import *
import csv
import datetime


THRESHOLD = 3
TIME_FORMAT = "%Y-%m-%d %H:%M"


def read_started_data():
    started = {}
    with open("./data/started.csv", mode="r") as file:
        reader = csv.reader(file)
        for vid, start_time in reader:
            started[vid] = datetime.datetime.strptime(start_time, TIME_FORMAT)

    return started


def update_started_data(started):
    with open("./data/started.csv", mode="w") as file:
        writer = csv.writer(file)
        for vid in started:
            writer.writerow([vid, started[vid].strftime(TIME_FORMAT)])


def append_completed_data(completed):
    with open("./data/completed.csv", mode="a") as file:
        writer = csv.writer(file)
        for vid in completed:
            writer.writerow([vid, completed[vid]["left_at"].strftime(TIME_FORMAT),
                             completed[vid]["completed_at"].strftime(TIME_FORMAT)])


def track_buses(buses, started, log=False):
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
                print("\t\t* Added to completed.csv since %s < %s" % (bus.minutes, THRESHOLD)) if log else ""

    if log:
        print("\nIn Progress:")
        for vid in started:
            print("\t- %s" % vid)

    # Write files
    if updated_started or updated_completed:
        update_started_data(started)
    if updated_completed:
        append_completed_data(completed)


def gather_data():
    set_timezone()
    response = call_cta_api(stpid_string="%s,%s" % (os.environ["from_stpid"], os.environ["to_stpid"]), log=True)
    buses = extract_bus_info(response)
    started = read_started_data()
    track_buses(buses, started, log=True)


if __name__ == "__main__":
    load_secrets()
    gather_data()
