# Based on Zed code - Person Fall detection using raspberry pi camera and opencv lib. Link: https://www.youtube.com/watch?v=eXMYZedp0Uo

import cv2
import time
import requests
from datetime import datetime
from datetime import date
import argparse


class Detector:
	def __init__(self,THRESHOLD:int,mode:int) -> None:
		self.THRESHOLD = THRESHOLD
		self.last_fall = None # save time stamp of the prev fall
		self.fitToEllipse = False # Number of minutes between Falls to make an alert
		self.fgbg = cv2.createBackgroundSubtractorMOG2()
		self.j = 0
		self.username = None
		self.password = None
		self.connteced = False
		if mode == 1:
			self.cap = cv2.VideoCapture('example_video.mp4')
		elif mode == 0:
			self.cap = cv2.VideoCapture(0)
		else:
			print('Mode is 0 or 1')
			return
		width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH) + 0.5)
		height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT) + 0.5)
		size = (width, height)
		fourcc = cv2.VideoWriter_fourcc(*'XVID')
		self.out = cv2.VideoWriter(f'fall_{date.today()}.mp4', fourcc, 20.0, size)
		self.seconds_interval = 5
	
	def login(self,username:str,password:str,url:str) -> None:
		"""
		Connect user to ELS server. provide user name, password and url of local/production environment
		"""
		payload = {"username":username,"password":password}
		headers = {'Content-Type':'application/json'}
		res = requests.post(url, json=payload, headers=headers)
		if res.res.status_code == 200:
			self.connteced = True
			self.username = username
			self.password = password
		else:
			print("Wrong username / password")
		
		
	def start(self) -> None:
#		if not self.connteced:
#			print("Please login first (call login function)")
#			return
		Falled = False # For recording puproses
		while (1):
			ret, frame = self.cap.read()

			# Convert each frame to gray scale and subtract the background
			try:
				gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
				fgmask = self.fgbg.apply(gray)

				# Find contours
				contours, _ = cv2.findContours(fgmask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
				
				# if falled detected in falling interval time, record the video 
				if Falled and (datetime.now() - self.last_fall).seconds < self.seconds_interval:
					self.out.write(frame)

				if contours:
					# List to hold all areas
					areas = []

					for contour in contours:
						ar = cv2.contourArea(contour)
						areas.append(ar)

					max_area = max(areas, default=0)

					max_area_index = areas.index(max_area)

					cnt = contours[max_area_index]

					M = cv2.moments(cnt)

					x, y, w, h = cv2.boundingRect(cnt)

					cv2.drawContours(fgmask, [cnt], 0, (255, 255, 255), 3, maxLevel=0)

					if h < w:
						self.j += 1

					# Falled detected
					if self.j > 10:
						if self.last_fall is None:
							print("FALL Detected")
							self.last_fall = datetime.now() # save the time of the first fall
							Falled = True
						else:
							time_now = datetime.now()
							delta = time_now - self.last_fall
							# Checking if the falling occured after the threshold
							if self.THRESHOLD < int(delta.total_seconds()//60): 
								print("FALL Detected")
								self.last_fall = time_now
								Falled = True
						cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)

					if h > w:
						self.j = 0
						cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

					# showing the video
					cv2.imshow('video', frame)

					if cv2.waitKey(33) == 27:
						break
			except Exception as e:
				print(e)
				break
		cv2.destroyAllWindows()


if __name__ == "__main__":
	parser = argparse.ArgumentParser(description='Arguments for Falling Detector')
	parser.add_argument('Threshold', type=int,help='Threshold number in minutes')
	parser.add_argument('Mode', type=int,help='Mode for the Detector.\n 0 -> camera input, 1 -> example video input')
	args = parser.parse_args()
	detector = Detector(args.Threshold,args.Mode) # gets the number of Threshold in minutes.
	detector.start()