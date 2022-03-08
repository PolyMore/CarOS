import subprocess
import requests
import json
import os
import time
import concurrent.futures
from datetime import datetime
import glob

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

vehicle_info = requests.get(api_safefleet_vehicle_info+str(vehicle_id), cookies=authenticate.cookies)
parsed_vehicle_info = json.loads(vehicle_info.text)

lat = parsed_vehicle_info['current_info']['lat']
lng = parsed_vehicle_info['current_info']['lng']
print(lat, lng)

image_filepath = saved_video_path + ("%d-%m-%Y-%H-%M-%S")+".mp4"

def split_stream_into_chunks():
    ffmpeg_command = ["ffmpeg",
             "-video_size", "1280x720",
             "-framerate", "40",
             "-f", "v4l2",
             "-i", "/dev/video0",
             "-f", "segment",
             "-g", '1',
             "-strftime", "1",
             "-segment_time", "30",
             "-segment_format", "mp4",
             "-reset_timestamps", "1",
             "-force_key_frames", "expr:gte(t,n_forced*30)", # set the number same as the segment length
             image_filepath]

    subprocess.run(ffmpeg_command)

def send_files_to_server(seconds):
    previous_file_path = ""
    print("PRINT1: previous_file_path: ", previous_file_path, "\n")
    while True:
        file_type = r'*.mp4'
        print("PRINT2: file_type: ", file_type, "\n")
        files = glob.glob(saved_video_path + file_type)
        
        print("PRINT3: files: ", files, "\n")
        #file_path = max(files, key=os.path.getctime)
        file_path = sorted(files, key=os.path.getctime)[-2]
        #file_path = sorted(glob.iglob('*.mp4'), key=os.path.getctime)[-2]
        
        print("PRINT4: Al 2-lea cel mai recent - file_path: ", file_path, "\n")
        if file_path != previous_file_path:
            dashboard_request = requests.post(api_dashboard_post, headers = {
                'x-auth-token': dashboard_token,
            }, files = {
                'photos': open(file_path, 'rb')
            }, data = {
                'lat': lat,
                'lng': lng,
                'licensePlate': car_license_plate
            })
            print(dashboard_request.text)
            previous_file_path = file_path
        time.sleep(seconds)

with concurrent.futures.ProcessPoolExecutor() as executor:
    f1 = executor.submit(split_stream_into_chunks)
    print("PRINT5: Sleeping 40 sec\n")
    time.sleep(40)
    print("PRINT6: Slept for 40 sec\n")
    f2 = executor.submit(send_files_to_server, 10)