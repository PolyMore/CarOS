import requests
import json
import os
import time
from datetime import datetime


api_dashboard_post = 'http://api.polymore.ro/api/log'
api_safefleet_authenticate = 'https://delta.safefleet.eu/safefleet/api/authenticate_vehicle'
api_safefleet_vehicle_info = 'https://delta.safefleet.eu/safefleet/api/vehicles/'
config_file_path = '/boot/config.json'

with open(config_file_path) as config_file:
    data = json.load(config_file)

car_license_plate = data['car_license_plate']
car_pin = data['car_pin']
dashboard_token = data['dashboard_token']
saved_video_path = data['video_path']

authenticate = requests.post(api_safefleet_authenticate, headers = {
    'Content-Type': 'application/json'
}, json = {
    'license_plate': car_license_plate,
    'pin': car_pin
})

vehicle_id = json.loads(authenticate.text)['vehicle']['vehicle_id']

while True:
    vehicle_info = requests.get(api_safefleet_vehicle_info+str(vehicle_id), cookies=authenticate.cookies)
    parsed_vehicle_info = json.loads(vehicle_info.text)

    lat = parsed_vehicle_info['current_info']['lat']
    lng = parsed_vehicle_info['current_info']['lng']
    print(lat, lng)

    image_filepath = saved_video_path+datetime.now().strftime("%d-%m-%Y-%H-%M-%S")+".mp4"
    os.system("ffmpeg -f v4l2 -framerate 40 -video_size 1280x720 -t 30 -i /dev/video0 " + image_filepath)
    dashboard_request = requests.post(api_dashboard_post, headers = {
        'x-auth-token': dashboard_token,
    }, files = {
        'photos': open(image_filepath, 'rb')
    }, data = {
        'lat': lat,
        'lng': lng,
	'licensePlate': car_license_plate
    })

    print(dashboard_request.text)
    time.sleep(10)
