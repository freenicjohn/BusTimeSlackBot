from helpers import *


def build_message():
    set_timezone()
    bus_data = call_cta_api(os.environ["from_stpid"])
    buses = extract_bus_info(bus_data)
    msg = "Upcoming %s buses @ %s:\n" % (os.environ["rt"],  os.environ["from_name"]) if len(buses) > 0 else \
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
    load_secrets()
    print(build_message())
