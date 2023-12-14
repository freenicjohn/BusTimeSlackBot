from helpers import *
from TrackBuses import TrackBuses
from CtaData import CtaData


def gather_data(in_lambda=False):
    set_timezone()
    cta_data = CtaData(os.environ["cta_bus_api_key"],
                       os.environ["rt_from"].split(","),
                       os.environ["rt_to"].split(","),
                       os.environ["rt_num"].split(","),
                       True)
    TrackBuses(cta_data, in_lambda, log=True)


def lambda_handler(event, context):
    gather_data(in_lambda=True)


if __name__ == "__main__":
    secret_names = ["slack_webhook", "from_name", "rt_from", "rt_to", "rt_num", "cta_bus_api_key"]
    load_secrets(secret_names)
    gather_data()
