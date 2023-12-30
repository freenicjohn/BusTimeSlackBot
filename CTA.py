import requests


class CTA:
    def __init__(self, api_key, from_list, to_list, num_list, log=False):
        self.api_key = api_key
        self.stpids = set(from_list).union(set(to_list))
        self.rt_nums = set(num_list)
        self.log = log

    def get_data(self):
        if len(self.stpids) > 10:
            raise "Max 10 stops can be tracked in one request - may change later"

        cta_url = "http://ctabustracker.com/bustime/api/v2/getpredictions?key=%s&stpid=%s&rt=%s&format=json" % \
                  (self.api_key, ",".join(list(self.stpids)), ",".join(list(self.rt_nums)))

        if self.log:
            print("Requesting: %s" % cta_url)

        data = requests.get(cta_url).json()['bustime-response']

        if 'prd' not in data:
            data = None
            if self.log:
                print("No predictions returned from API")
        else:
            data = data['prd']
            for bus in data:
                if bus['prdctdn'] == "DUE":
                    bus['prdctdn'] = 0
                elif bus['prdctdn'] == "DLY":
                    bus['prdctdn'] = 30
                else:
                    bus['prdctdn'] = int(bus['prdctdn'])
        return data
