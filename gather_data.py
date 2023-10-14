from helpers import *
import csv
import datetime


THRESHOLD = 3
TIME_FORMAT = "%Y-%m-%d %H:%M"


def save_to_file(data, path, overwrite):
    dir_path = "/".join(path.split("/")[:-1])
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
    with open(path, mode="w" if overwrite else "a+") as file:
        writer = csv.writer(file)
        for key in data:
            writer.writerow([key, *[data[key][key2].strftime(TIME_FORMAT) for key2 in data[key]]])


def read_started_data(data_path):
    started = {}
    if file_exists(data_path):
        with open(data_path, mode="r") as file:
            reader = csv.reader(file)
            for vid, start_time in reader:
                started[vid] = {"left_at": datetime.datetime.strptime(start_time, TIME_FORMAT)}
    return started


def track_buses(buses, started, started_data_path, completed_data_path, log=False):
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
    save_to_file(started, started_data_path, overwrite=True) if updated_started else ""
    save_to_file(completed, completed_data_path, overwrite=False) if updated_completed else ""


def gather_data():
    set_timezone()
    response = call_cta_api(stpid_string="%s,%s" % (os.environ["from_stpid"], os.environ["to_stpid"]), log=True)
    buses = extract_bus_info(response)
    started_data_path, completed_data_path = get_data_paths(os.environ["from_stpid"], os.environ["to_stpid"])
    started = read_started_data(started_data_path)
    track_buses(buses, started, started_data_path, completed_data_path, log=True)


if __name__ == "__main__":
    load_secrets()
    gather_data()
