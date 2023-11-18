from helpers import *
from TrackBuses import TrackBuses


def gather_data(in_lambda=False):
    set_timezone()
    api_response = call_cta_api(stpid_string="%s,%s" % (os.environ["from_stpids"], os.environ["to_stpids"]), log=not in_lambda)
    bus_data = extract_bus_data(api_response)
    routes = get_routes()
    TrackBuses(bus_data, routes, in_lambda, log=True)


def lambda_handler(event, context):
    gather_data(in_lambda=True)


if __name__ == "__main__":
    load_secrets()
    gather_data()
