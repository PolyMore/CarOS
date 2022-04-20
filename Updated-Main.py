#########################################
######## Main.py liniar function ########
#########################################

#0. Import libraries
#0. Define folder paths
#0. Define functions
#1. Read current time
#2. Log engine start time
#3. Check if Reboot Counter file present
#4. Create Reboot Counter file initiated at value 0
#5. Read reboot counter from text file
#6. Check if reboot counter > 5
#7. Send alert e-mail
#8. Read Car-Database JSON file for truck specific info
#9. Check if Queue Status JSON  file present for today
#10. Create blank QueueStatus.json for today
#11. Read QueueStatus.json file data
#12. Check if storage on USB Drive is above 70%
#13. Delete the oldest daily folder with videos from /mnt/usb
#14. Create daily folder for video storage on /mnt/usb
#15. Capture video stream in daily folder
#16. Search if video file present in folder
#17. Check waiting_counter if above 3
#18. Wait 30 sec
#19. Increment waiting_counter
#20. Check if most recent video is created more than 1 minute ago
#21. Increment reboot counter
#22. Reboot system
#23. Search for 2nd most recent video in folder
#24. Update upload queue with video and attributes
#25. Check upload queue for videos with not-uploaded status
#26. IF not-uploaded status
#27. Wait specific number of seconds
#28. Grab last entry with status not-uploaded from queue
#29. Analyse for covered camera
#30. Analyse for dirt on camera
#31. Analyse for empty cup
#32. Split video into frames. Grab frame at 1/2 of video. Delete the other frames
#33. Get GPS data at video creation time
#34. Upload frame
#35. Sent e-mail alert with frame attached + GPS data
#36. Get GPS data at video creation time
#37. Upload  video


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
All_videos_folder = "/mnt/usb/"
Backup_videos_folder = "/home/pi/"
E_mail_receiver = "pogancristian@gmail.com"

#---------------------------------------------------------------
#0. Define functions

def split_stream_into_chunks():
	#while True: 
	#segment_length = 30
	print("Arrived at split_stream_into_chunks")

	
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

	print("In split_stream_into_chunks")
	subprocess.run(ffmpeg_command)
	

def Queue_management2(upload_queue, upload_queue_location, upload_queue_json, daily_folder_path, Reboot_counter_file_path, Reboot_counter_file, Car_Database, E_mail_receiver):
	print("Queue_management2")

	start = time.perf_counter()
	print("Upload seqence start time: ", start)
	
	
	waiting_counter = 0 
	print("Reseted waiting_counter at 0")
	waiting_counter2 = 0 
	print("Reseted waiting_counter2 at 0")

	informed_about_GPS_down = 0 

	#Find most recent video in folder 
	taggedrootdir = pathlib.Path(daily_folder_path)

	while True:
		print("While True")
		try:
			print("------------17------------")
			#---------------------------------------------------------------
			#17. Search if video file present in folder
			print("#17. Search if video file present in folder")

			newest_video_full = max([f for f in taggedrootdir.resolve().glob('*.mp4') if f.is_file()], key=os.path.getctime)
			print("newest_video_full: ", newest_video_full)

			newest_video = str(newest_video_full).split(f"{daily_folder_path}",1)[1] #get only filename 
			print("newest_video: ", newest_video)

			current = datetime.now()

			#Last time modified - taken from video filename
			s1 = f"{str(newest_video)[-12:-10]}:{str(newest_video)[-9:-7]}:{str(newest_video)[-6:-4]}" #newest_video_modified_hour, newest_video_modified_minute
			print("Current time: ", current.hour, current.minute, current.second)
			print("Latest video modified time: ", s1)

			#True - file present in folder if exection reachaces this point.
			#Otherwise, it would have thrown an exception
			print("------------21------------")
			#---------------------------------------------------------------
			#21. Check if most recent video is created more than 1 minute ago
			print("#21. Check if most recent video is created more than 1 minute ago")

			#Compare modified time with current time 
			FMT = '%H:%M:%S'
			tdelta = datetime.strptime(f"{current.hour}:{current.minute}:{current.second}", FMT) - datetime.strptime(s1, FMT)
			print("tdelta: ", tdelta, "\n")
			tdelta_string = str(tdelta)
			print("tdelta_string: ", tdelta_string)

			print("before cut")
			print("delta hours: |", tdelta_string[-8:-6], "|")
			print("delta minutes: |", tdelta_string[-5:-3], "|")
			print("delta seconds: |", tdelta_string[-2:], "|")

			#in case one of the values cannot be converted to int
			try:
				delta_hours = int(tdelta_string[-8:-6]) #delta hours
				delta_min = int(tdelta_string[-5:-3]) #delta minutes
				delta_sec = int(tdelta_string[-2:]) #delta seconds
			except:
				# Reset to 0, to wait for different current.second - to be different than 0 
				print("Except tdelta")

			print("after cut")
			print("delta hours: ", delta_hours)
			print("delta minutes: ", delta_min)
			print("delta seconds: ", delta_sec)


			#if delta_hours == 0 and delta_min < 1:
			#if delta_hours == 0 and (delta_min < 1 or delta_min == 1) and delta_sec <= 50:
			if delta_hours == 0 and delta_min < 1 and delta_sec <= 50:
				#False - less than 1 minute ago 
				print("False - less than 50 seconds ago \n")

				print("------------24------------")
				#---------------------------------------------------------------
				#24. Search for 2nd most recent video in folder
				print("#24. Search for 2nd most recent video in folder")

				try:

					second_newest_video = sorted([f for f in taggedrootdir.resolve().glob('*.mp4') if f.is_file()], key=os.path.getctime)[-2]
					#Present Get second newest video file created 
					print("second_newest_video: ", second_newest_video)

					penultimul_video = str(second_newest_video).split(f"{daily_folder_path}",1)[1] #get only filename 
					print("penultimul_video: ", penultimul_video, "\n")

					print("------------25------------")
					#---------------------------------------------------------------
					#25. Update upload queue with video and attributes
					print("#25. Update upload queue with video and attributes")

					temp_dict = {
				    "uploaded_video": 0,
				    "uploaded_frame": 0,
				    "empty_cup": 0,
				    "dirt_on_camera": 0,
				    "covered_camera": 0
					}

					#Check if 2nd most recent video already present in the upload queue
					if penultimul_video in upload_queue:
						#Present
						print("2nd video already present in queue")
					else:	
						#Not present - placing 2nd newest video file in queue
						print("2nd video not currently present in queue, inserting it in the queue")
						upload_queue[penultimul_video] = temp_dict

					print("Before JSON sync")
					print(upload_queue)
					with open(f"{upload_queue_location}{upload_queue_json}", 'w') as f:
						json.dump(upload_queue, f, indent=2)
					print("After JSON sync")

					#Flow will pass to 26
					
				except IndexError: #No video present in daily folder
					#	Not present - no second latest video file in daily folder, 
					print("Not present - from 24 - No second video found")
					#		Check upload queue for videos with not-uploaded status
					#Flow will pass to 26

				print("------------26------------")
				#---------------------------------------------------------------
				#26. Check upload queue for videos with not-uploaded status
				print("#26. Check upload queue for videos with not-uploaded status")

				#Parse JSON file
				#for video_in_list in range(len(upload_queue.keys)):
				#	vi
				for video in sorted(upload_queue, reverse=True):

					print("video: ", video)
					print("------------27------------")
					#---------------------------------------------------------------
					#27. IF not-uploaded status
					print("#27. IF not-uploaded status")

					if upload_queue[video]['uploaded_video'] == 0:
						# Found video with value 0 - not-uploaded
						print(video, " not uploaded")

						print("------------31------------")
						#---------------------------------------------------------------
						#31. Grab last entry with status not-uploaded from queue
						print("#31. Grab last entry with status not-uploaded from queue")

						print(video)

						print("------------32------------")
						#---------------------------------------------------------------
						#32. Analyse for covered camera
						print("#32. Analyse for covered camera")

						covered_camera_response = Covered_camera_check(upload_queue_location, upload_queue_json, upload_queue, video)
						if covered_camera_response == 1:
							print(f"In {video} camera is not covered")
							Split_video_into_frames(upload_queue_location, upload_queue_json, upload_queue, video, informed_about_GPS_down)
						elif covered_camera_response == 0:
							print("Camera not covered")
							pass # Move to 33. Analyse for dirt on camera
						else:
							print("Error")

						print("------------33------------")
						#---------------------------------------------------------------
						#33. Analyse for dirt on camera
						print("#33. Analyse for dirt on camera")

						dirt_on_camera_response = Dirt_on_camera_check(upload_queue_location, upload_queue_json, upload_queue, video)
						if dirt_on_camera_response == 1:
							print(f"In {video} camera there is no dirt on camera")
							Split_video_into_frames(upload_queue_location, upload_queue_json, upload_queue, video, informed_about_GPS_down)
						elif dirt_on_camera_response == 0:
							print("No dirt on camera")
							pass # Move to 34. Analyse for empty cup
						else:
							print("Error")

						print("------------34------------")
						#---------------------------------------------------------------
						#34. Analyse for empty cup
						print("#34. Analyse for empty cup")

						empty_cup_response = Empty_cup_check(upload_queue_location, upload_queue_json, upload_queue, video)
						if empty_cup_response == 1:
							print(f"In {video} cup is full")
							print("Cup empty")
							Split_video_into_frames(upload_queue_location, upload_queue_json, upload_queue, video, informed_about_GPS_down)
						elif empty_cup_response == 0:
							print("Cup not empty")
							
							informed_about_GPS_down = GPS_Data_Check(upload_queue_location, upload_queue_json, upload_queue, daily_folder_path, video, Car_Database, informed_about_GPS_down, E_mail_receiver)
						else:
							print("Error")

					else: #	No find for 0 value - not-uploaded - all uploaded

						print("Going to next element in 26. ")
						print("After list depleted, going back to 17. Queue_management")

			else: #True - more than 1 minute ago
				print("------------22------------")
				#---------------------------------------------------------------
				#22. Increment reboot counter
				print("#22-1. Increment reboot counter")
				Increment_reboot_counter(Reboot_counter_file_path, Reboot_counter_file)

				print("------------23------------")
				#---------------------------------------------------------------
				#23. Reboot system
				print("#23. Reboot system")
				os.system("sudo reboot")

		except ValueError: #No video present in daily folder
			print("No video found")

			print("------------18------------")
			#---------------------------------------------------------------
			#18. Check if waiting counter above 3
			print("18. Check if waiting counter above 3")
			if waiting_counter >= 3:
				#True
				print("------------22-2-----------")
				#---------------------------------------------------------------
				#22. Increment reboot counter
				print("#22-2. Increment reboot counter")
				print("Increment reboot counter")
				Increment_reboot_counter(Reboot_counter_file_path, Reboot_counter_file)

				print("------------23-2-----------")
				#---------------------------------------------------------------
				#23. Reboot system
				print("#23-2. Reboot system")

				print("Rebooting system")
				os.system("sudo reboot")

			else:
				#False
				print("------------19------------")
				#---------------------------------------------------------------
				#19. Wait 30 seconds
				print("#19. Wait 30 seconds")
				time.sleep(30)

				print("------------20------------")
				#---------------------------------------------------------------
				#20. Increment waiting counter
				print("#20. Increment waiting counter")
				waiting_counter = waiting_counter + 1
				print("waiting_counter: ", waiting_counter)
				pass

def Sent_email_alert(receiver, message1):
	sender_email = "PolyMore.Systems@gmail.com"
	port = 465  #For SSL
	password = "PolyMore1"
	context = ssl.create_default_context()
	message = "Subject: Car SB-30-SOM \n" + message1
	print("Sent e-mail")
	#with smtplib.SMTP_SSL("smtp.gmail.com", port, context=context) as server:
	#    server.login(sender_email, password)
	#    server.sendmail(sender_email, receiver, message)

def Create_reboot_counter(Reboot_counter_file_path, Reboot_counter_file):
	with open(f"{Reboot_counter_file_path}{Reboot_counter_file}", 'w') as f:
		f.truncate(0)
		f.write(f"0")
	print("Wrote 0 to new reboot counter file.")

def Read_reboot_counter(Reboot_counter_file_path, Reboot_counter_file):
	#Try to open file 
	try: 
		with open(f"{Reboot_counter_file_path}{Reboot_counter_file}", 'r+') as f:
			#Read reboot counter 
			Reboot_counter1 = f.readlines()
			print("Reboot_counter1 ", Reboot_counter1)
			Reboot_counter = int(Reboot_counter1[0]) #Read value in file
			print("Reboot_counter ", Reboot_counter)
			return Reboot_counter

	except (ValueError, FileNotFoundError, IndexError):
		print("Reboot counter not found")
		# If file not present, create file 
		Create_reboot_counter(Reboot_counter_file_path, Reboot_counter_file)
		return 0

def Write_to_reboot_counter(Reboot_counter_file_path, Reboot_counter_file, value):
	with open(f"{Reboot_counter_file_path}{Reboot_counter_file}", 'r+') as f:
		f.truncate(0)
		f.write(f"{value}")	
	print("Wrote" , value, " to reboot counter file.")

def Increment_reboot_counter(Reboot_counter_file_path, Reboot_counter_file):
	counter = Read_reboot_counter(Reboot_counter_file_path, Reboot_counter_file)
	counter = counter + 1
	Write_to_reboot_counter(Reboot_counter_file_path, Reboot_counter_file, counter)

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

	print("------------35------------")
	#---------------------------------------------------------------
	#35. Split video into frames. Grab frame at 1/2 of video. Delete the other frames
	print("#35. Split video into frames. Grab frame at 1/2 of video. Delete the other frames")

	GPS_Data_Check(upload_queue_location, upload_queue_json, upload_queue, daily_folder_path, video, Car_Database, informed_about_GPS_down, E_mail_receiver)
	#return path and file generated after frame splitting

def Upload_file(upload_queue_location, upload_queue_json, upload_queue, daily_folder_path, video, Car_Database, lat, lng):

	print("------------40------------")
	#---------------------------------------------------------------
	#40. Upload file (video / frame)

	api_dashboard_post = 'http://api.polymore.ro/api/log'

	print("#40. Upload file (video / frame)")
	print(f"At location {upload_queue_location}")
	print(f"In queue {upload_queue}")
	print(f"Element {video} is being uploaded")

	upload_queue[video]['uploaded_video'] = 1
	upload_queue[video]['uploaded_frame'] = -1
	print("token: ", Car_Database['token'])
	dashboard_token = Car_Database['token']
	print("----")

	car_license_plate = "SB-30-SOM"
	file = daily_folder_path + video

	'''
	dashboard_request = requests.post(api_dashboard_post, headers = {
		'x-auth-token': dashboard_token,
	}, files = {
			'photos': open(file, 'rb')
	}, data = {
		'lat': lat,
		'lng': lng,
		'licensePlate': car_license_plate
	})
	print(dashboard_request.text)
	'''
	print(f"Uploaded {file}")

def Alert_with_frame(upload_queue_location, upload_queue_json, upload_queue, video, E_mail_receiver):

	print("------------41------------")
	#---------------------------------------------------------------
	#41. Sent e-mail alert with frame attached + GPS data
	print("#41. Sent e-mail alert with frame attached + GPS data")
	message1 = "Covered camera / Dirt on camera / Empty cup. "
	Sent_email_alert(E_mail_receiver, message1)
	#end = time.perf_counter()
	#print("end: ", end)
	#print(end - start)	
	#Write to queue and JSON queue status update for video for which alert has been sent 

def GPS_Data_Check(upload_queue_location, upload_queue_json, upload_queue, daily_folder_path, video, Car_Database, informed_about_GPS_down, E_mail_receiver):

	api_safefleet_authenticate = 'https://delta.safefleet.eu/safefleet/api/authenticate_vehicle'
	api_safefleet_vehicle_info = 'https://delta.safefleet.eu/safefleet/api/vehicles/'

	#car_license_plate = Car_Database.keys()
	#print("car_license_plate: ", car_license_plate)

	car_license_plate = "SB-30-SOM"
	car_pin = Car_Database['pin']
	print("car_pin: ", car_pin)

	print("------------36------------")
	#---------------------------------------------------------------
	#36. Is GPS data server accessible?
	print("#36. Is GPS data server accessible?")

	try:
		authenticate = requests.post(api_safefleet_authenticate, headers = {'Content-Type': 'application/json'}, json = {
			'license_plate': car_license_plate,
			'pin': car_pin
		})
		print(authenticate)
		print(authenticate.text)

		vehicle_id = json.loads(authenticate.text)['vehicle']['vehicle_id']
		vehicle_info = requests.get(api_safefleet_vehicle_info + str(vehicle_id), cookies=authenticate.cookies)
		parsed_vehicle_info = json.loads(vehicle_info.text)

		lat = parsed_vehicle_info['current_info']['lat']
		lng = parsed_vehicle_info['current_info']['lng']
		print(lat, lng)

	except:

		print("------------37------------")
		#---------------------------------------------------------------
		#37. Place static GPS location - car base location
		print("#37. Place static GPS location - car base location")

		lat = Car_Database['base-GPS-lat']
		lng = Car_Database['base-GPS-lng']

		print("lat: ", lat)
		print("lng: ", lng)

		print("------------38------------")
		#---------------------------------------------------------------
		#38. Send e-mail alert
		print("#38. Send e-mail alert")
		#Send the e-mail only once. Have a variable informed_about_GPS_down = 0
		#This stops the function to alert at every 30 seconds

		GPS_data_found = 1 
		if GPS_data_found == 0 and informed_about_GPS_down == 0:
			message1 = "GPS Data not accesible. "
			Sent_email_alert(E_mail_receiver, message1)
			print("Sent e-mail. informed_about_GPS_down = 1")
			informed_about_GPS_down = 1


	print("------------39------------")
	#---------------------------------------------------------------
	#39. Get GPS data at video creation time
	print("#39. Get GPS data at video creation time")
	
	Upload_file(upload_queue_location, upload_queue_json, upload_queue, daily_folder_path, video, Car_Database, lat, lng)

	#Alert_with_frame()
	#Bollean parameter in GPS_Data_Check for upload_frame and another one for upload_video
	#For choosing which function to call here Upload_file / Send e-mail alert with attached frame

	return informed_about_GPS_down

print("------------1------------")
#---------------------------------------------------------------
#1. Read current time
print("#1. Read current time") 
current = datetime.now()

current_day = current.day 
if current_day < 10:
	current_day = "0" + str(current_day)

current_month = current.month
if current_month < 10:
	current_month = "0" + str(current_month)

current_year = current.year


print("------------2------------")
#---------------------------------------------------------------
#2. Log engine start time
print("#2. Log engine start time")
print(f"Engine ON at: {current_year}-{current_month}-{current_day}-{current.hour}-{current.minute}-{current.second}")


print("------------3------------")
#---------------------------------------------------------------
#3. Check if Reboot Counter file present
print("#3. Check if Reboot Counter file present")
Reboot_counter_file_path = CarOS_folder_path + "RebootCounters/"
os.system(f"mkdir {Reboot_counter_file_path}")

print("------------4------------")
#---------------------------------------------------------------
#4. Check if Reboot Counter file present
print("#4. Check if Reboot Counter file present")
print("Reboot counter for this session is 0")
Reboot_counter_file = f"Reboot-Counter-{current_day}-{current_month}-{current_year}.txt"
Reboot_counter = 0

if exists(f"{Reboot_counter_file_path}{Reboot_counter_file}") is False:
	print("------------5------------") 
	#---------------------------------------------------------------
	#5. Create Reboot Counter file initiated at value 0
	print("#5. Create Reboot Counter file initiated at value 0")
	Create_reboot_counter(Reboot_counter_file_path, Reboot_counter_file)
	print("Reboot counter exists")

elif exists(f"{Reboot_counter_file_path}{Reboot_counter_file}") is True:
	print("------------6------------")
	#---------------------------------------------------------------
	#6. Read counter from text file
	print("#6. Read counter from text file")
	Reboot_counter = Read_reboot_counter(Reboot_counter_file_path, Reboot_counter_file)
	print("Reboot counter exists, value: ", Reboot_counter)

	print("------------7------------")
	#---------------------------------------------------------------
	#7. Check if reboot counter > 3
	print("#7. Check if reboot counter > 3")
	if Reboot_counter >= 3:

		print("------------8------------")
		#---------------------------------------------------------------
		#8. Sent alert e-mail 
		print("#8. Sent alert e-mail ")
		message =  f"Reboot counter is larger than 3."
		Sent_email_alert(E_mail_receiver, message)
		print("Sent email alert")
		

else:
	print("Eroare citire Reboot_counter")
	Reboot_counter = 0


print("------------9------------")
#---------------------------------------------------------------
#9. Read Car-Database JSON file for truck specific info
print("#9. Read Car-Database JSON file for truck specific info")
'''
Car_Database_json = CarOS_folder_path + "Car-Database.json"

try:
	with open(Car_Database_json) as json_file:
		Car_Database1 = json.load(json_file)
	Car_Database = Car_Database1['client']['SOMA']['SB-30-SOM']
	print(Car_Database)
except FileNotFoundError:
	#If CarDatabase JSON file not found, send e-mail
	message =  f"Car_Database file not present!"
	Sent_email_alert(E_mail_receiver, message)
'''
Car_Database = { 
	"ip": "172.23.0.1",
	"user": "pi",
	"pass": "Car_SIB",
	"token": "eyJhb",
	"pin": "009909",
	"vehicle_id": "11136",
	"base-GPS-lat": 45.731145,
	"base-GPS-lng": 24.1778883
	}

print("------------10------------")
#---------------------------------------------------------------
#10. Check if Queue Status JSON  file present for today
print("#10. Check if Queue Status JSON  file present for today")

upload_queue_location = CarOS_folder_path + "Upload-Queues/" #CarOS
upload_queue_json = "Upload_queue-" + current.strftime("%d-%m-%Y") + ".json"
upload_queue = {} 
print(f"{upload_queue_location}{upload_queue_json}")

#Loop starts from here
if os.path.isfile(f"{upload_queue_location}{upload_queue_json}") and os.access(upload_queue_location, os.R_OK):
	print("File exists and is readable")

	print("------------12------------")
	#---------------------------------------------------------------
	#12. Read QueueStatus.json file data
	print("#12. Read QueueStatus.json file data")

	try:
		with open(f"{upload_queue_location}{upload_queue_json}") as json_file:
			upload_queue = json.load(json_file)
	except:
		print("JSON file cannot be read.")
		with io.open(os.path.join(upload_queue_location, upload_queue_json), 'w') as js_file:
			js_file.write(json.dumps({})) #Write empty file 

	print("Read upload_queue")
	print(upload_queue)
	print("")

else:
	#If foder with upload queues is not created, create it now
	os.system(f"mkdir {upload_queue_location}")
	print("File is missing or is not readable, creating file")
	
	print("------------11------------")
	#---------------------------------------------------------------
	#11. Create blank QueueStatus.json for today
	print("#11. Create blank QueueStatus.json for today")
	with io.open(os.path.join(upload_queue_location, upload_queue_json), 'w') as js_file:
		js_file.write(json.dumps({})) #Write empty file 

print(upload_queue)

print("------------13------------")
#---------------------------------------------------------------
#13. Check if storage on USB Drive is below 30%
print("#13. Check if storage on USB Drive is below 30%")

try:
	Disk_space2 = sp.getoutput('df -h')
	print("Disk_space2: ", Disk_space2)

	Disk_space1 = Disk_space2.rpartition('/mnt/usb')[0][-6:-2]
	Disk_space = [int(s) for s in Disk_space1.split() if s.isdigit()]

	print("Disk_space: |", Disk_space[0], "|")
	print(type(Disk_space[0]))
		
except:
	#Send e-mail to alert lack of reading on disk space
	print("Disk space is not int")
	Disk_space = [50,] #force the execution to load more videos
	#Disk_space[0] = 50 #force the execution to load more videos
	message =  f"Cannot read disk space value."
	Sent_email_alert(E_mail_receiver, message)
	print("Sent e-mail alert: cannot read disk space value.")


#Loop maximum 3 times 
for x in range(0,3):
	try:
		if int(Disk_space[0]) >= 70:
			print("Disk full: ", Disk_space)
			#Remove oldest directory
			print("------------14------------")
			#---------------------------------------------------------------
			#14. Delete de oldest daily folder with videos from /mnt/usb
			print("#14. Delete de oldest daily folder with videos from /mnt/usb")
			taggedrootdir = pathlib.Path(All_videos_folder)
			oldest_video_folder = min(taggedrootdir.resolve().glob('*'), key=os.path.getctime)
			#Do not delete System Volume Information

			print(f"Removing {oldest_video_folder}")
			#os.system(f"rm -r {oldest_video_folder}")
			

			#continue to video capture
	except TypeError:
		print("Cannot compare Disk_space value to 70")


print("------------15------------")
#---------------------------------------------------------------
#15. Create daily folder for video storage on /mnt/usb
print("#15. Create daily folder for video storage on /mnt/usb")

daily_folder_name = str(current_day) + "-" + str(current_month) + "-" + str(current_year) + "/"
daily_folder_path = f"{All_videos_folder}{daily_folder_name}"
#Make daily folder for videos
os.system(f"mkdir {daily_folder_path}")
print(daily_folder_name)

print("------------16------------")
#---------------------------------------------------------------
#16. Capture video stream in daily folder
print("#16. Capture video stream in daily folder")

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

image_filepath = f"{daily_folder_path}DEV30-SOM-%d-%m-%Y-%H-%M-%S.mp4"
print("image_filepath: ", image_filepath)

with concurrent.futures.ProcessPoolExecutor() as executor:

	#------------------------------------------------------------------------------
	f1 = executor.submit(split_stream_into_chunks)
	print("PRINT5: Sleeping 5 sec\n")
	time.sleep(5)
	print("PRINT6: Slept for 5 sec\n")

	f2 = executor.submit(Queue_management2, upload_queue, upload_queue_location, upload_queue_json, daily_folder_path, Reboot_counter_file_path, Reboot_counter_file, Car_Database, E_mail_receiver)

