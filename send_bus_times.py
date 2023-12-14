from helpers import *


def build_message():
    set_timezone()
    bus_data = call_cta_api(os.environ["notify_stpid"])
    buses = extract_bus_data(bus_data)
    msg = "Upcoming %s buses @ %s:\n" % (os.environ["notify_rt"],  os.environ["notify_stop_name"]) if len(buses) > 0 else \
        "No upcoming buses\n"
    for bus in buses:
        msg += "\t- %s (%s)\n" % (bus.departure_time, "DUE" if bus.due else "%s min" % bus.minutes)

    return msg


def post_to_slack(msg):
    return requests.post(os.environ['slack_webhook'], json={'text': msg})


def lambda_handler(event, context):
    post_to_slack(build_message())

    return


if __name__ == "__main__":
    secret_names = ["slack_webhook", "cta_bus_api_key", "notify_rt", "notify_stop_name", "notify_stpid"]
    load_secrets(secret_names)
    print(build_message())
