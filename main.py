import requests
import json
import os
import time
from datetime import datetime

api_dashboard_post = 'http://api.polymore.ro/api/log'
api_safefleet_authenticate = 'https://delta.safefleet.eu/safefleet/api/authenticate_vehicle'
api_safefleet_vehicle_info = 'https://delta.safefleet.eu/safefleet/api/vehicles/'
config_file_path = 'config.json'

with open(config_file_path) as config_file:
    data = json.load(config_file)

car_license_plate = data['car_license_plate']
car_pin = data['car_pin']
dashboard_token = data['dashboard_token']

authenticate = requests.post(api_safefleet_authenticate, headers = {
    'Content-Type': 'application/json'
}, json = {
    'license_plate': car_license_plate,
    'pin': car_pin
})

print(car_license_plate, car_pin)


print(authenticate.text)

vehicle_id = json.loads(authenticate.text)['vehicle']['vehicle_id']
vehicle_info = requests.get(api_safefleet_vehicle_info+str(vehicle_id), cookies=authenticate.cookies)
parsed_vehicle_info = json.loads(vehicle_info.text)

lat = parsed_vehicle_info['current_info']['lat']
lng = parsed_vehicle_info['current_info']['lng']

print(lat, lng)

image_filepath = "/home/xyn/PolyMore/"+datetime.now().strftime("%d-%m-%Y-%H-%M-%S")+".jpg"
os.system("fswebcam -S 25 -r 1280x720 --no-banner " + image_filepath)
time.sleep(1)
dashboard_request = requests.post(api_dashboard_post, headers = {
    'x-auth-token': dashboard_token,
}, files = {
    'photos': open(image_filepath, 'rb')
}, data = {
    'lat': lat,
    'lng': lng
})

print(dashboard_request.text)