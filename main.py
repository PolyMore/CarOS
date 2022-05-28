#########################################
########### Main.py function ############
#########################################

#0. Import libraries
#0. Define folder paths
#0. Define functions
#1. Read current time
#2. Log engine start time
#3. Create Reboot Counter folder
#4. Check if Reboot Counter file present
#5. Create Reboot Counter file initiated at value 0
#6. Read reboot counter from text file
#7. Check if reboot counter > 5
#8. Send alert e-mail
#9. Read Car-Database JSON file for truck specific info
#10. Check if Queue Status JSON  file present for today
#11. Create blank QueueStatus.json for today
#12. Read QueueStatus.json file data
#13. Check if CarOS/Files storage below 50%
#14. Delete old folders from dev/sda/mnt/usb
#15. Check if USB drive connected and readable
#16. Try USB mount command
#17. Check if USB mount succeeded
#18. Move destination to MicroSD card
#19. Check if available storage on USB Drive is below 30%
#20. Delete the oldest daily folder with videos from /mnt/usb
#21. Create daily folder for video storage on /mnt/usb or MicroSD
#22. Capture video stream in daily folder
#23. Search if video file present in folder
#24. Check if waiting_counter greater than 3
#25. Wait 30 sec
#26. Increment waiting_counter
#27. Check if most recent video is created more than 1 minute ago
#28. Increment reboot counter
#29. Reboot system
#30. Search for 2nd most recent video in folder
#31. Update upload queue with video and attributes
#32. Check upload queue for videos with not-uploaded status
#33. Wait 5s + looped-counter * 1.5
#34. Looped-counter + 1
#35. IF not-uploaded status
#36. Grab last entry with status not-uploaded from queue
#37. Analyse for covered camera
#38. Analyse for dirt on camera
#39. Analyse for empty cup
#40. Split video into frames. Grab frame at 1/2 of video. Delete the other frames
#41. Is GPS data server accessible?
#42. Place static GPS location - car base location
#43. Send e-mail alert
#44. Get GPS data at video creation time
#45. Upload file (video / frame)
#46. Sent e-mail alert with frame attached + GPS data


#---------------------------------------------------------------
#0. Import libraries
import json
import glob
import os
import datetime
import io
from datetime import datetime
from os.path import exists
import pathlib
import time
import smtplib, ssl
import subprocess as sp
import requests
import concurrent.futures
import subprocess


#---------------------------------------------------------------
#0. Define folder paths
#CarOS_folder_path = "/Users/cristianpogan/Desktop/Python-Scripts/RaspberryPi-Scripts/Test-New-Main/CarOS/"
#All_videos_folder = "/Users/cristianpogan/Desktop/Python-Scripts/RaspberryPi-Scripts/Test-New-Main/mnt-usb/"
#Car_Database_json = "/Users/cristianpogan/Desktop/Python-Scripts/Car-Database.json"
CarOS_folder_path = "/home/pi/CarOS/"
temp_video_path = "/home/pi/CarOS/Files/"
All_videos_folder = "/mnt/usb/"
Backup_videos_folder = "/home/pi/"
E_mail_receiver = "pogancristian@gmail.com"
Client_Name = "SOMA"
Car_Name = "SB-37-SOM"

#---------------------------------------------------------------
#0. Define functions

def split_stream_into_chunks():
	#print("Arrived at split_stream_into_chunks")
	ffmpeg_command = ["ffmpeg",
			"-video_size", "1280x720",
			"-framerate", "9",
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

	#print("In split_stream_into_chunks")
	subprocess.run(ffmpeg_command)

def Queue_management(upload_queue, upload_queue_location, upload_queue_json, \
					daily_folder_path, reboot_reasons_location, reboot_reasons_json, \
					Car_Database, E_mail_receiver, Car_Name):
	#print("------Queue_management------")

	##start = time.perf_counter()
	##print("Upload seqence start time: ", start)
	
	#print("--------------------22------------------------")
	#print("#22. Initialize waiting counter at 0")
	
	waiting_counter = 0 
	#print("Resetted waiting_counter at 0")
	waiting_counter2 = 0 
	#print("Resetted waiting_counter2 at 0")
	loop_counter = 0 

	informed_about_GPS_down = 0 

	#Find most recent video in folder 
	taggedrootdir = pathlib.Path(daily_folder_path)


	while True:

		#print("--------------------23------------------------")
		#print("#23. Check if video file present in folder")

		try:
			newest_video_full = max([f for f in taggedrootdir.resolve().glob('*.mp4') if f.is_file()], key=os.path.getctime)
			#print("newest_video_full: ", newest_video_full)

			newest_video = str(newest_video_full).split(f"{daily_folder_path}",1)[1] #get only filename 
			#print("newest_video: ", newest_video)


		except ValueError:
			#print("folder empty - No video found - ffmpeg not started")

			#print("--------------------24------------------------")
			#print("#24. Check if waiting_counter greater than 3")
			if waiting_counter >= 3:
				#True
				reason = f"Waiting counter is {waiting_counter}"
				#print(reason)

				Manage_lack_of_new_video(reboot_reasons_location, reboot_reasons_json, reason, E_mail_receiver)

			elif waiting_counter < 3:
				#False
				#print("--------------------25------------------------")
				#print("#25. Wait 30 sec, increment waiting_counter")
				time.sleep(30)

				waiting_counter = waiting_counter + 1
				#print("Incremented waiting_counter: ", waiting_counter)

				#print("--------------------26------------------------")
				#print("#26. Write to RebootReason.JSON, waited x for new video in folder y")

				reason = f"waited {waiting_counter} times for new video in folder {daily_folder_path}"
				Write_to_reboot_reason(reboot_reasons_location, reboot_reasons_json, reason)
			
				#print("--------------------27------------------------")
				#print("#27. Send e-mail alert with cause, car name and IP")
				Send_email_alert(E_mail_receiver, reason)

			else:
				#print("Error - waiting counter is not >= 3 and not < 3")
				#print(f"waiting counter value: {waiting_counter}")
				pass


		#Video file found
		#print("--------------------28------------------------")
		#print("#28. Check if most recent video is created more than 1 minute ago")

		current = datetime.now()

		#Last time modified - taken from video filename
		s1 = f"{str(newest_video)[-12:-10]}:{str(newest_video)[-9:-7]}:{str(newest_video)[-6:-4]}" 
		#newest_video_modified_hour, newest_video_modified_minute
		#print("Current time: ", current.hour, current.minute, current.second)
		#print("Latest video modified time: ", s1)

		#Compare modified time with current time 
		FMT = '%H:%M:%S'
		tdelta = datetime.strptime(f"{current.hour}:{current.minute}:{current.second}", FMT) - datetime.strptime(s1, FMT)
		#print("tdelta: ", tdelta, "\n")
		tdelta_string = str(tdelta)
		#print("tdelta_string: ", tdelta_string)

		#print("before cut")
		#print("delta hours: |", tdelta_string[-8:-6], "|")
		#print("delta minutes: |", tdelta_string[-5:-3], "|")
		#print("delta seconds: |", tdelta_string[-2:], "|")
	
		delta_hours = int(tdelta_string[-8:-6]) #delta hours
		delta_min = int(tdelta_string[-5:-3]) #delta minutes
		delta_sec = int(tdelta_string[-2:]) #delta seconds

		#print("after cut")
		#print("delta hours: ", delta_hours)
		#print("delta minutes: ", delta_min)
		#print("delta seconds: ", delta_sec)

		if delta_hours == 0 and delta_min < 1 and delta_sec <= 50:
			#False - less than 50 seconds ago 
			#print("False - less than 50 seconds ago \n")

			#print("--------------------33------------------------")
			#print("#33. Check if 2nd newest file present in video folder")

			videos_in_folder = sorted([f for f in taggedrootdir.resolve().glob('*.mp4') if f.is_file()], key=os.path.getctime)
			if len(videos_in_folder) > 1:
				#True - present 
				#print("More than 1 video file in folder.")
				#print(f"there are {len(videos_in_folder)} videos")

				Manage_all_video_files(taggedrootdir, videos_in_folder, upload_queue_location, \
									upload_queue_json, upload_queue, \
									informed_about_GPS_down)

			else:
				#False - not present
				#print("--------------------34------------------------")
				#print("#34. Wait 30 sec - no alert needed")
				time.sleep(30)
				
		else:
			#True
			#True - more than 50 seconds ago

			reason = "True - more than 50 seconds ago"
			#print(reason)

			Manage_lack_of_new_video(reboot_reasons_location, reboot_reasons_json, reason, E_mail_receiver)



def Manage_all_video_files(taggedrootdir, videos_in_folder, upload_queue_location, upload_queue_json, upload_queue, informed_about_GPS_down):

	#print("in Manage_all_video_files")

	#print("--------------------35------------------------")
	#print("#35. Iterate from 2nd most recent to the oldest video")

	#print("all videos_in_folder")
	#print(videos_in_folder)

	for num_of_vides in range(len(videos_in_folder) -1 ):
		
		#print("#In num_of_vides in range(len(videos_in_folder) -1 ) loop")
		
		#Must start from -1 even for 0 value of num_of_videos
		video_index = (-2) - num_of_vides 
		#print("loop counter: ", num_of_vides)
		#print("video index: ", video_index)
		try:
			video = str(sorted([f for f in taggedrootdir.resolve().glob('*.mp4') if f.is_file()], key=os.path.getctime)[video_index])
		except Exception as ex:
			template = "An exception of type {0} occurred. Arguments:\n{1!r}"
			message = template.format(type(ex).__name__, ex.args)
			#print("Error message: ", message)

		#print("video in full: ", video)
		video = str(video[20:])
		#print("video right part: ", video)

		#print("--------------------36------------------------")
		#print("#36. Check if video in list is present in Upload Queue")

		if video in upload_queue:
			#True - Present in list
			#print(f"video {video} ")
			#print(f"is in \n {upload_queue}")
			
			#print("--------------------38------------------------")
			#print("#38. Check if video has status 1 uploaded")
			if upload_queue[video]['uploaded_video'] == 1:
				#True - video has value 1 in queue - status uploaded
				
				#print(video, " is present in Upload Queue")
				#print("Back to num_of_vides in range(len(videos_in_folder) -1 ) loop?")
				pass
				
			
			elif upload_queue[video]['uploaded_video'] == 0:
				#False - video has value 0 in queue - status not-uploaded
				#print(video, " is NOT present in Upload Queue")
				
				Process_video_file(video, upload_queue, informed_about_GPS_down)

			else:
				#print(f"Error reading status for video {video}")
				#Handle similar to exception cases 
				pass


		else:
			#False - not present in list
			#print(f"video {video} \nis NOT in \n{upload_queue}\n")

			#print("--------------------37------------------------")
			#print("37. Place video in upload_queue with status 0")

			temp_dict = {
		    "uploaded_video": 0,
		    "uploaded_frame": 0,
		    "empty_cup": 0,
		    "dirt_on_camera": 0,
		    "covered_camera": 0
			}

			#print("video: ", video)
			#print("temp_dict: ", temp_dict)
			#print(" ")
			upload_queue[video] = temp_dict

						
			with open(f"{upload_queue_location}{upload_queue_json}", 'w') as f:
				json.dump(upload_queue, f, indent=2)
			
			Process_video_file(video, upload_queue, informed_about_GPS_down)

	#print("#Looped through all current files")
	#print("Sleeping 20 sec")
	time.sleep(20)


def Process_video_file(video, upload_queue, informed_about_GPS_down):
	#print("In Process_video_file")

	#print("--------------------34------------------------")
	#print("#34. Analyse for covered camera")

	covered_camera_response = Covered_camera_check(upload_queue_location, upload_queue_json, upload_queue, video)
	if covered_camera_response == 1:
		#print(f"In {video} camera is not covered")
		Split_video_into_frames(upload_queue_location, upload_queue_json, upload_queue, video, informed_about_GPS_down)
	elif covered_camera_response == 0:
		#print("Camera not covered")
		pass # Move to 38. Analyse for dirt on camera
	else:
		#Place error in Errors.json
		#print("Error")
		error_message = str(f"ERROR at covered camera analysis.")
		Write_to_reboot_reason(reboot_reasons_location, reboot_reasons_json, error_message)

	#print("--------------------35------------------------")
	#print("#35. Analyse for dirt on camera")

	dirt_on_camera_response = Dirt_on_camera_check(upload_queue_location, upload_queue_json, upload_queue, video)
	if dirt_on_camera_response == 1:
		#print(f"In {video} camera there is no dirt on camera")
		Split_video_into_frames(upload_queue_location, upload_queue_json, upload_queue, video, informed_about_GPS_down)
	elif dirt_on_camera_response == 0:
		#print("No dirt on camera")
		pass # Move to 39. Analyse for empty cup
	else:
		#Place error in Errors.json
		#print("Error")
		error_message = str(f"ERROR at dirt on camera analysis.")
		Write_to_reboot_reason(reboot_reasons_location, reboot_reasons_json, error_message)

	#print("--------------------36------------------------")
	#print("#36. Analyse for empty cup")

	empty_cup_response = Empty_cup_check(upload_queue_location, upload_queue_json, upload_queue, video)
	if empty_cup_response == 1:
		#print(f"In {video} cup is full")
		#print("Cup empty")
		Split_video_into_frames(upload_queue_location, upload_queue_json, upload_queue, video, informed_about_GPS_down)
	elif empty_cup_response == 0:
		#print("Cup not empty")

		GPS_Data_Check(upload_queue_location, upload_queue_json, upload_queue, \
					daily_folder_path, video, Car_Database, informed_about_GPS_down, \
					E_mail_receiver, Car_Name)
	else:
		#Place error in Errors.json
		#print("Error")
		error_message = str(f"ERROR at empty cup analysis.")
		#print("Error message: ", error_message)
		Write_to_reboot_reason(reboot_reasons_location, reboot_reasons_json, error_message)



def Send_email_alert(receiver, message1):
	sender_email = "PolyMore.Systems@gmail.com"
	port = 465  #For SSL
	password = "PolyMore1"
	context = ssl.create_default_context()
	message = f"Subject: Car {Car_Name} \n" + message1
	#print("Sent e-mail")

	#Check if there is GSM signal for e-mail sending
	try:
		with smtplib.SMTP_SSL("smtp.gmail.com", port, context=context) as server:
		    server.login(sender_email, password)
		    server.sendmail(sender_email, receiver, message)
	except Exception as ex:
		error_message1 = " {0} occurred. Arguments:\n{1!r}".format(type(ex).__name__, ex.args)
		error_message = str(f"ERROR Cannot send e-mail: {ex}. ") + error_message1
		#print("Error message: ", error_message)


def Write_to_reboot_reason(reboot_reasons_location, reboot_reasons_json, reason):

	if os.path.isfile(f"{reboot_reasons_location}{reboot_reasons_json}") and os.access(reboot_reasons_location, os.R_OK):
		#print("Reboot Reason JSON file exists and is readable")

		try:
			#Read current file
			with open(f"{reboot_reasons_location}{reboot_reasons_json}") as json_file:
				reasons_dict = json.load(json_file)

			#Add reason to dict from file
			time_stamp = f"{datetime.now().hour}-{datetime.now().minute}-{datetime.now().second}" 
			reasons_dict[time_stamp] = reason
			#print("reasons_dict: ") 
			#print(reasons_dict)

			#Add updated reasons to JSON file
			with io.open(os.path.join(reboot_reasons_location, reboot_reasons_json), 'w') as js_file:
				json.dump(reasons_dict, js_file)

			#Print for check
			#print("Read reboot_reasons_json")
			#print(reasons_dict)
			#print("")

		except:
			#print("JSON file cannot be read.")
			with io.open(os.path.join(reboot_reasons_location, reboot_reasons_json), 'w') as js_file:
				js_file.write(json.dumps({})) #Write empty file 

	else:
		#print("File is missing or is not readable")
		
		#If reboot reasons JSON is not created, create it now
		with io.open(os.path.join(reboot_reasons_location, reboot_reasons_json), 'w') as js_file:
			js_file.write(json.dumps({})) #Write empty file 
		pass


def Manage_lack_of_new_video(reboot_reasons_location, reboot_reasons_json, reason, E_mail_receiver):

	#print("--------------------29------------------------")
	#print("#29.  Write to RebootReasons JSON file reason for reboot - no new video found")
	
	Write_to_reboot_reason(reboot_reasons_location, reboot_reasons_json, reason)	

	#print("--------------------30------------------------")
	#print("#30. Send e-mail alert with cause for reboot")

	Send_email_alert(E_mail_receiver, reason)
	
	#print("--------------------31------------------------")
	#print("#31. Wait 30 seconds - for log in at troubleshooting")
	time.sleep(30)

	#print("--------------------32------------------------")
	#print("#32. Wait 30 seconds - for log in at troubleshooting")

	os.system("sudo reboot")


def Covered_camera_check(upload_queue_location, upload_queue_json, upload_queue, video):
	#Do the check 
	#Return 1 if found
	#Return 0 if not found
	return 0

def Dirt_on_camera_check(upload_queue_location, upload_queue_json, upload_queue, video):
	#Do the check 
	#Return 1 if found
	#Return 0 if not found
	return 0

def Empty_cup_check(upload_queue_location, upload_queue_json, upload_queue, video):
	#Do the check 
	#Return 1 if found
	#Return 0 if not found
	return 0

def Split_video_into_frames(upload_queue_location, upload_queue_json, upload_queue, video, Car_Database, informed_about_GPS_down, E_mail_receiver):

	#print("--------------------37------------------------")
	#print("#37. Split video into frames. Grab frame at 1/2 of video. Delete the other frames")

	GPS_Data_Check(upload_queue_location, upload_queue_json, upload_queue, daily_folder_path, video, Car_Database, informed_about_GPS_down, E_mail_receiver)
	#return path and file generated after frame splitting

def Upload_file(upload_queue_location, upload_queue_json, upload_queue, daily_folder_path, video, Car_Database, lat, lng):

	#print("--------------------43------------------------")
	#print("#43. Upload file (video / frame)")

	api_dashboard_post = 'http://api.polymore.ro/api/log'
	#print(api_dashboard_post)

	#print("upload_queue:")
	#print(upload_queue)
	#print("")
	
	#print("video:")
	#print(video)
	#print("")

	#print("upload_queue[video]:")
	#print(upload_queue[video])
	#print("")

	#print("upload_queue[video]['uploaded_video']:")
	#print(upload_queue[video]['uploaded_video'])
	#print("")

	upload_queue[video]['uploaded_video'] = 1
	#print("upload_queue[video]['uploaded_video']: ", upload_queue[video]['uploaded_video'])

	upload_queue[video]['uploaded_frame'] = -1
	#print("upload_queue[video]['uploaded_frame']: ", upload_queue[video]['uploaded_frame'])

	#print("token: ", Car_Database['token'])
	

	dashboard_token = Car_Database['token']
	#print("----")

	#print(f"At location {upload_queue_location}")
	#print(f"In queue {upload_queue}")
	#print(f"Element {video} is being uploaded")


	car_license_plate = Car_Name
	file = daily_folder_path + video

	#In case there is no signal for video upload, 
	#don't interrupt the function from storing it locally
	#print("before try in Upload_file")
	try:
		#print("in try in Upload_file")
		
		dashboard_request = requests.post(api_dashboard_post, headers = {
			'x-auth-token': dashboard_token,
		}, files = {
				'photos': open(file, 'rb')
		}, data = {
			'lat': lat,
			'lng': lng,
			'licensePlate': car_license_plate
		})
		#print(dashboard_request.text)


		with io.open(os.path.join(upload_queue_location, upload_queue_json), 'w') as js_file:
	    		json.dump(upload_queue, js_file)
	    
		#print(f"Uploaded {file}")

	except Exception as ex:
		error_message1 = " {0} occurred. Arguments:\n{1!r}".format(type(ex).__name__, ex.args)
		error_message = str(f"ERROR at Upload file: {ex}. ") + error_message1
		#print("Error message: ", error_message)
		Write_to_reboot_reason(reboot_reasons_location, reboot_reasons_json, error_message)


		
def Alert_with_frame(upload_queue_location, upload_queue_json, upload_queue, video, E_mail_receiver):

	#print("--------------------42------------------------")
	#print("#42. Sent e-mail alert with frame attached + GPS data")
	message1 = "Covered camera / Dirt on camera / Empty cup. "
	Send_email_alert(E_mail_receiver, message1)
	##end = time.perf_counter()
	##print("end: ", end)
	##print(end - start)	
	#Write to queue and JSON queue status update for video for which alert has been sent 

def GPS_Data_Check(upload_queue_location, upload_queue_json, upload_queue, \
				daily_folder_path, video, Car_Database, \
				informed_about_GPS_down, E_mail_receiver, Car_Name):

	#print("Which video is received in GPS_Data_Check?")
	#print("video: ", video)

	#print("in GPS data check")
	api_safefleet_authenticate = 'https://delta.safefleet.eu/safefleet/api/authenticate_vehicle'
	api_safefleet_vehicle_info = 'https://delta.safefleet.eu/safefleet/api/vehicles/'

	car_license_plate = Car_Name
	#print("car_license_plate: ", car_license_plate)

	car_pin = Car_Database['pin']
	#print("car_pin: ", car_pin)

	#print("--------------------38------------------------")
	#print("#38. Check if authentication to GPS platform successful")

	try:
		#True, platform accessible
		authenticate = requests.post(api_safefleet_authenticate, \
			headers = {'Content-Type': 'application/json'}, json = {
			'license_plate': car_license_plate,
			'pin': car_pin
		})
		#print(authenticate)
		#print(authenticate.text)


		#print("--------------------41------------------------")
		#print("41. Get GPS data at video creation time")

		#GPS Presences 
		#Get_GPS_Presence(video)



		#This gets current lat, lng values

		vehicle_id = json.loads(authenticate.text)['vehicle']['vehicle_id']
		vehicle_info = requests.get(api_safefleet_vehicle_info + str(vehicle_id), cookies=authenticate.cookies)
		parsed_vehicle_info = json.loads(vehicle_info.text)

		lat = parsed_vehicle_info['current_info']['lat']
		lng = parsed_vehicle_info['current_info']['lng']
		#print(lat, lng)

		
	except Exception as ex:
		error_message1 = " {0} occurred. Arguments:\n{1!r}".format(type(ex).__name__, ex.args)
		error_message = str(f"ERROR Safefleet platform not accesible: {ex}. ") + error_message1
		#print("Error message: ", error_message)
		Write_to_reboot_reason(reboot_reasons_location, reboot_reasons_json, error_message)


		#False, platform inaccessible

		#Safefleet platform not accesible 
		#No GSM signal
		#Place error in Error.json

		#print("--------------------39------------------------")
		#print("#39. Place static GPS location - car base location")

		lat = Car_Database['base-GPS-lat']
		lng = Car_Database['base-GPS-lng']

		#Put 00 / 00 if error 

		#print("lat: ", lat)
		#print("lng: ", lng)

		#print("--------------------40------------------------")
		#print("#40. Send e-mail alert")
		#Send the e-mail only once. Have a variable informed_about_GPS_down = 0
		#This stops the function to alert at every 30 seconds

		if informed_about_GPS_down == 0:
			message1 = "GPS Data not accesible. "
			Send_email_alert(E_mail_receiver, message1)
			#print("Sent e-mail. informed_about_GPS_down = 1")
			informed_about_GPS_down = 1

	Upload_file(upload_queue_location, upload_queue_json, upload_queue, daily_folder_path, video, Car_Database, lat, lng)

	#Alert_with_frame()
	#Boolean parameter in GPS_Data_Check for upload_frame and another one for upload_video
	#For choosing which function to call here Upload_file / Send e-mail alert with attached frame

	return informed_about_GPS_down


def Get_GPS_Presence(file):

	#print("# Authentificate in Safefleet platform")
	api_safefleet_authenticate_platform = 'https://delta.safefleet.eu/safefleet/api/authenticate'
	authenticate = requests.post(api_safefleet_authenticate_platform, \
	               headers = {'Content-Type': 'application/json'}, \
	               json = {'username': "polymore", 'password': "123456"})
	#print(f"authenticate: {authenticate}")
	#print(f"authenticate.text: {authenticate.text}")

	#5. Get every video in folder
	#print(f'{file}')

	#6. Find start_moment and stop_moment
	v_year = file[-17:-13]
	v_month = file[-20:-18]
	v_day = file[-23:-21]
	v_hour = file[-12:-10]
	v_minute = file[-9:-7]
	v_second = file[-6:-4]
	
	#print(f'v_year: {v_year}')
	#print(f'v_month: {v_month}')
	#print(f'v_day: {v_day}')
	#print(f'v_hour: {v_hour}')
	#print(f'v_minute: {v_minute}')
	#print(f'v_second: {v_second}')

	stop_moment = f"{v_year}-{v_month}-{v_day}T{v_hour}:{v_minute}:{v_second}Z"
	#print(f'stop_moment: {stop_moment}')

	#If subtracting a delay minute that is under 1, subtract 1 hour, subtract 59 - delay
	if int(v_minute) - delay_start_stop_moment <= 1: 
		#subtract 1 hour
		v_temp = int(v_hour) - 1
		
		if int(v_hour) < 10: 
			#if hour smaller than 10, insert 0 as first character
			v_hour = str("0" + str(v_temp))
			#print("Hour smaller than 10: ", v_hour)
		
		else:
			#else only subtract 1
			v_hour = str(v_temp)
			#print("Hour larger than 10: ", v_hour)
		#subtract 59 - delay
		v_minute = 59 - (delay_start_stop_moment - 1)

	
	elif int(v_minute) - delay_start_stop_moment > 1:
		#else, only subtract delay from current minute, keep same hour
		#keep hour
		#subtract delay
		v_temp = int(v_minute) - delay_start_stop_moment

		if int(v_temp) < 10: 
			#if new minute is smaller than 10, insert 0 as first character
			#print("Start minute is smaller than 10: ", v_minute)
			v_minute = str("0" + str(v_temp))
			#print("Adjusted characters: ", v_minute)

		else:
			#else only subtract delay
			#print("Start minute larger than 10: ", v_minute)
			v_minute = str(v_temp)
			#print("Subtracted: ", v_minute)

	else:
		#print("Error")
		#else, Error
		pass


	start_moment = f"{v_year}-{v_month}-{v_day}T{v_hour}:{v_minute}:{v_second}Z"
	
	#print("--------")
	#print(f'start_moment: {start_moment}')
	#print(f'stop_moment:  {stop_moment}')
	#print("--------")
	
	api_safefleet_presences = f"https://delta.safefleet.eu/safefleet/api/vehicles/{vehicle_id}/presences/?start_moment={start_moment}&stop_moment={stop_moment}"#&filter_dist_percent={filter_dist_percent}"
	#print(api_safefleet_presences)
	
	#try - if query not ok
	presences1 = requests.get(api_safefleet_presences, cookies = authenticate.cookies)
	#print(type(presences1))
	#print((presences1))
	presences = json.loads(presences1.text)
	#print("Presences: ", presences)
	if len(presences) == 0:
		count_missing = count_missing + 1 
		#print("count_missing: ", count_missing)


		#Return lat, lng for car-base


	else: 

		#Presences return is not empty
		#Compare all returned presences in response

		#4. Check in presences the closest presence to the video name
		for x in range(len(presences)):
		
			a = presences[x]
			#print(a)

			b = a['moment']
			#print(b)

			pres_day = b[8:10]
			pres_hour = b[-9:-7]
			pres_min = b[-6:-4]
			pres_sec = b[-3:-1]

			#print(f"pres_day: {pres_day}")
			#print(f"pres_hour: {pres_hour}")
			#print(f"pres_min: {pres_min}")
			#print(f"pres_sec: {pres_sec}")

			#for element in presences
			s1 = f"{v_hour}:{v_minute}:{v_second}"
			s2 = f"{pres_hour}:{pres_min}:{pres_sec}"
			
			#Compare modified time with current time 
			FMT = '%H:%M:%S'
			tdelta = datetime.strptime(s1, FMT) - datetime.strptime(s2, FMT)
			#print("tdelta: ", tdelta, "\n")
			tdelta_string = str(tdelta)
			#print("tdelta_string: ", tdelta_string)


			#in case one of the values cannot be converted to int
			try:
				delta_hours = int(tdelta_string[-8:-6]) #delta hours
				delta_min = int(tdelta_string[-5:-3]) #delta minutes
				delta_sec = int(tdelta_string[-2:]) #delta seconds
			except:
				# Reset to 0, to wait for different current.second - to be different than 0 
				#print("Except tdelta")
				pass

			#print("delta hours: ", delta_hours)
			#print("delta minutes: ", delta_min)
			#print("delta seconds: ", delta_sec)

			if delta_hours == 0 and delta_min < 1 and delta_sec <= 30:
				#print("yes")
				#print(a['lat'])
				#print(a['lng'])
				pass

	#if presences1.status_code != 200:
	#	sys.exit()
	#print(" ")

	#print("Len presences: ", len(presences))
	#print(presences[1]['moment'])
	#print(type(presences))
	#print(" ")

	

print("--------------------1------------------------")
print("#1. Read current date")

#Add a 0 to day if lower than 10 - to have 2 characters consistently
current_day = datetime.now().day 
current_day = "0" + str(current_day) if current_day < 10 else str(datetime.now().day)
print(current_day)

#Add a 0 to month if lower than 10 - to have 2 characters consistently
current_month = datetime.now().month
current_month = "0" + str(current_month) if current_month < 10 else str(datetime.now().month)
print(current_month)

current_year = str(datetime.now().year)
print(current_year)


#print("--------------------2------------------------")

dt_split(datetime.datetime.now())

def str_from_dt(dt, fmt='%Y-%m-%d %H:%M:%S.%f'):
    return dt.strftime(fmt)


def dt_from_str(dt, fmt='%Y-%m-%d %H:%M:%S.%f'):
    return datetime.datetime.strptime(dt, fmt)


def is_datetime(x): return isinstance(x, (datetime.datetime, datetime.date, datetime.time))

def dt_split(dt):
    if is_datetime(dt):
        dt = str_from_dt(dt)

    date, time = dt.split(' ')
    year, month, day = date.split('-')
    h, m, s, milli = time.replace('.', ':').split(':')
    return (year, month, day), (h, m, s, milli)


#print("--------------------2------------------------")
#print("#2. Send e-mail info - new engine start time")

engine_start_time = f"Engine ON at: {current_year}-{current_month}-{current_day}-{datetime.now().hour}-{datetime.now().minute}-{datetime.now().second}"
test_message = "Engine Started"
Send_email_alert(E_mail_receiver, test_message)
#print(engine_start_time)

#print("--------------------3------------------------")
#print("#3. Create RebootReasons folder")

reboot_reasons_location = CarOS_folder_path + "RebootReasons/" #CarOS/RebootReasons/
os.system(f"mkdir {reboot_reasons_location}")

#print("--------------------4------------------------")
#print("#4. Check if Reboot-Reason-daily.json file present")

reboot_reasons_json = "RebootReasons-" + datetime.now().strftime("%d-%m-%Y") + ".json"
reboot_reasons = {} 
#print(f"{reboot_reasons_location}{reboot_reasons_json}")

if os.path.isfile(f"{reboot_reasons_location}{reboot_reasons_json}") and os.access(reboot_reasons_location, os.R_OK):
	#Present
	#print("File exists and is readable")

	#print("--------------------6------------------------")
	#print("#6. Read RebootReason.json file data")

	try:
		with open(f"{reboot_reasons_location}{reboot_reasons_json}") as json_file:
			reboot_reasons = json.load(json_file)
	except:
		#print("JSON file cannot be read.")
		with io.open(os.path.join(reboot_reasons_location, reboot_reasons_json), 'w') as js_file:
			js_file.write(json.dumps({})) #Write empty file 

	#print("Read reboot_reasons_json")
	#print(reboot_reasons)
	#print("")

else:
	#RebootReason.json is missing or is not readable, creating file
	#print("RebootReason.json is missing or is not readable, creating file")
	
	#print("--------------------5------------------------")
	#print("#5. Create blank RebootReason-daily.json for today")
	with io.open(os.path.join(reboot_reasons_location, reboot_reasons_json), 'w') as js_file:
		js_file.write(json.dumps({})) #Write empty file 

#print(reboot_reasons)

#print("--------------------7------------------------")
#print("#7. Check if Car-Database JSON file for truck data is present and readable")
Car_Database_json = CarOS_folder_path + "Car-Database.json"

try:
	#Present - if entire block is executed 
	#print("--------------------9------------------------")
	#print("#9. Read Car-Dabase.json for specific truck data")

	with open(Car_Database_json) as json_file:
		Car_Database1 = json.load(json_file)
	Car_Database = Car_Database1['client'][Client_Name][Car_Name]
	#print("Car_Database: ")
	#print(Car_Database)


except FileNotFoundError as ex:
	error_message1 = " {0} occurred. Arguments:\n{1!r}".format(type(ex).__name__, ex.args)
	error_message = str(f"ERROR Car_Database file not present!: {ex}. ") + error_message1
	#print("Error message: ", error_message)
	Write_to_reboot_reason(reboot_reasons_location, reboot_reasons_json, error_message)

	#print("--------------------8------------------------")
	#print("8. Send e-mail alert for JSON file presence")

	#If CarDatabase JSON file not found, send e-mail
	message =  f"Car_Database file not present!"
	Send_email_alert(E_mail_receiver, message)




#print("--------------------10------------------------")
#print("#10. Check if Queue Status JSON file present for today")

upload_queue_location = CarOS_folder_path + "Upload-Queues/" #CarOS/Upload-Queues/
upload_queue_json = "Upload_queue-" + datetime.now().strftime("%d-%m-%Y") + ".json"
upload_queue = {} 
#print(f"{upload_queue_location}{upload_queue_json}")

if os.path.isfile(f"{upload_queue_location}{upload_queue_json}") and os.access(upload_queue_location, os.R_OK):
	#Present

	#print("--------------------12------------------------")
	#print("#12. Read QueueStatus.json file data")

	#print("File exists and is readable")

	try:
		with open(f"{upload_queue_location}{upload_queue_json}") as json_file:
			upload_queue = json.load(json_file)
	except:
		#print("JSON file cannot be read.")
		with io.open(os.path.join(upload_queue_location, upload_queue_json), 'w') as js_file:
			js_file.write(json.dumps({})) #Write empty file 

	#print("Read upload_queue")
	#print(upload_queue)
	#print("")

else:
	#Not Present
	#print("--------------------11------------------------")
	#print("#11. Create blank QueueStatus.json for today")
	
	#If foder with upload queues is not created, create it now
	os.system(f"mkdir {upload_queue_location}")
	#print("File is missing or is not readable, creating file")
	
	#If upload queue is not created, create it now
	with io.open(os.path.join(upload_queue_location, upload_queue_json), 'w') as js_file:
		js_file.write(json.dumps({})) #Write empty file 

	#print("Created upload_queue")
	#print(upload_queue)
	#print("")

#print("--------------------13------------------------")
#print("#13. Check if CarOS.log file larger than 500 MB")

carOS_log_file = '/home/pi/CarOS.log'
carOS_log_size = os.path.getsize(carOS_log_file)
#print(carOS_log_size)
#print(type(carOS_log_size))

#Compare CarOS.log size to 500 MB
if carOS_log_size >= 500000000:
	#True - file larger than 500Mb
	#print("CarOS.log greater than 500 Mb")

	#print("--------------------14------------------------")
	#print("#14. Send e-mail info for CarOS.log file too large")
	message =  f"CarOS.log file greater than 500 MB. {carOS_log_size} MB!"
	Send_email_alert(E_mail_receiver, message)

else:
	#False - file smaller than 500Mb
	#print("Smaller")
	pass


#print("--------------------15------------------------")
#print("#15. Check if /mnt/usb  storage can be read")

Disk_space2 = sp.getoutput('df -h')
#print("Disk_space2: ", Disk_space2)

try:
	#True /mnt/usb storage can be read
	Disk_space1 = Disk_space2.rpartition('/mnt/usb')[0][-6:-2]
	Disk_space = [int(s) for s in Disk_space1.split() if s.isdigit()]

	#print("/mnt/usb: |", Disk_space[0], "|")
	#print(type(Disk_space[0]))

	#print("--------------------18------------------------")
	#print("#18. Check if /mnt/usb storage occupancy above 70%")
	for x in range(0,3):
		try:
			if int(Disk_space[0]) >= 70:
				#print("Disk full: ", Disk_space)
				
				#print("--------------------19------------------------")
				#print("#19. Delete oldest folder from mnt/usb")
				
				try:
					oldest_video_folder = sorted(glob.glob(os.path.join(All_videos_folder, '*/')), key=os.path.getmtime)[-1]
					#print(f"Removing {oldest_video_folder}")
					os.system(f"rm -r {oldest_video_folder}/")
				except Exception as ex:#IndexError:
					#print("No folder found")
					error_message1 = " {0} occurred. Arguments:\n{1!r}".format(type(ex).__name__, ex.args)
					error_message = str(f"ERROR Cannot delete from /mnt/usb: {ex}. ") + error_message1
					#print("Error message: ", error_message)
					Write_to_reboot_reason(reboot_reasons_location, reboot_reasons_json, error_message)
					pass
				
		except Exception as ex: #TypeError:
			error_message1 = " {0} occurred. Arguments:\n{1!r}".format(type(ex).__name__, ex.args)
			error_message = str(f"ERROR Cannot compare /mnt/usb value to 70: {ex}. ") + error_message1
			#print("Error message: ", error_message)
			#Write_to_reboot_reason(reboot_reasons_location, reboot_reasons_json, error_message)
		
except Exception as ex:
	template = "An exception of type {0} occurred. Arguments:\n{1!r}"
	message = template.format(type(ex).__name__, ex.args)

	Write_to_reboot_reason(reboot_reasons_location, reboot_reasons_json, message)
	#print("Error message: ", message)
	#print(f"ERROR : {ex}")
	#False - cannot be read

	#print("--------------------16------------------------")
	#print("#16. Check if storage occupancy on /dev/root < 70%")
	
	try:
		#In case issue arrises also with /dev/root reading
		result = Disk_space2.split("/dev/root",1)[1] #grab all text after "/dev/root"
		index = result.find("%") #find first occurance of "%"

		result1 = result[:index] #cut and grab only first part of string, before "%"
		OS_space = int(result1[-3:])

		#print("OS_space: ", OS_space)

		for x in range(0,3):
			try:
				if OS_space >= 70:
					#print("/dev/root full: ", OS_space)
					
					#print("--------------------17------------------------")
					#print("#17. Delete oldest folder from dev/sda/mnt/usb")
					
					try:
						oldest_video_folder = sorted(glob.glob(os.path.join(All_videos_folder, '*/')), key=os.path.getmtime)[-1]
						#print(f"Removing {oldest_video_folder}")
						os.system(f"rm -r {oldest_video_folder}/")

					except Exception as ex: #IndexError:
						#print("No folder found")
						error_message1 = " {0} occurred. Arguments:\n{1!r}".format(type(ex).__name__, ex.args)
						error_message = str(f"ERROR Cannot delete from /dev/sda: {ex}. ") + error_message1
						#print("Error message: ", error_message)
						Write_to_reboot_reason(reboot_reasons_location, reboot_reasons_json, error_message)
						
				else:
					#print("Enough space available")
					pass
					
			except Exception as ex:#TypeError:
				error_message1 = " {0} occurred. Arguments:\n{1!r}".format(type(ex).__name__, ex.args)
				error_message = str(f"ERROR Cannot compare /root/dev/ value to 70: {ex}. ") + error_message1
				#print("Error message: ", error_message)
				Write_to_reboot_reason(reboot_reasons_location, reboot_reasons_json, error_message)

				message =  f"Cannot compare /root/dev/ value to 70"
				Send_email_alert(E_mail_receiver, message)
				#print("Sent e-mail alert: Cannot compare /root/dev/ value to 70.")
				
				
	except Exception as ex:
		error_message1 = " {0} occurred. Arguments:\n{1!r}".format(type(ex).__name__, ex.args)
		error_message = str(f"ERROR -16-: {ex}. ") + error_message1
		#print("Error message: ", error_message)
		Write_to_reboot_reason(reboot_reasons_location, reboot_reasons_json, error_message)
		

#print("--------------------20------------------------")
#print("#20. Create daily folder for video storage on /mnt/usb")

daily_folder_name = str(current_day) + "-" + str(current_month) + "-" + str(current_year) + "/"
#print(daily_folder_name)

daily_folder_path = f"{All_videos_folder}{daily_folder_name}"
#Make daily folder for videos
os.system(f"sudo mkdir {daily_folder_path}")
os.system(f"sudo chmod 777 {daily_folder_path}")

#print("--------------------21------------------------")
#print("#21. Capture video stream in daily folder")

current = datetime.now()
current_hour = current.hour
if current_hour < 10:
	current_hour = "0" + str(current_hour)

current_minute = current.minute
if current_minute < 10:
	current_minute = "0" + str(current_minute)

current_second = current.second
if current_second < 10:
	current_second = "0" + str(current_second)

image_filepath = f"{daily_folder_path}{Car_Name}-%d-%m-%Y-%H-%M-%S.mp4"
#print("image_filepath: ", image_filepath)


with concurrent.futures.ProcessPoolExecutor() as executor:
	f1 = executor.submit(split_stream_into_chunks)

	#print("PRINT5: Sleeping 5 sec\n")
	time.sleep(5)
	#print("PRINT6: Slept for 5 sec\n")

	f2 = executor.submit(Queue_management, upload_queue, upload_queue_location, \
						upload_queue_json, daily_folder_path, reboot_reasons_location, \
						reboot_reasons_json, Car_Database, E_mail_receiver, Car_Name)

