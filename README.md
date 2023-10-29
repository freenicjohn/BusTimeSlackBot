# BusTimeSlackBot(s)
Functions relating to the CTA's buses
- send_bus_times.py
  - Queries CTA's public API for a specific stop and posts the next few arrivals in a Slack channel. 
  - Designed to be run as an AWS Lambda.
- gather_data.py
  - Tracks travel time for every bus between a start and end stop and stores the data in a csv file in order to predict travel time on different days/times
## Deploy Lambda
1) Zip all py files with
```
zip result.zip *.py
```
2) Upload the zipped file to both Lambdas via the aws console
3) Layers hold dependency libs and only need to be uploaded if changed


## Run locally
```
python lambda_send_bus_times.py
# or
python gather_data.py
```

## Secrets
Secrets contain user-specific information needed to post to Slack and hit the CTA's public API. I'm using another private repo to hold these secrets. On aws, they should be entered as environment variables. Locally, they can be stored at the path shown in ```helpers/load_secrets()```.