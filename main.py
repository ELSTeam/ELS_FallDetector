# Based on Zed code - Person Fall detection using raspberry pi camera and opencv lib. Link: https://www.youtube.com/watch?v=eXMYZedp0Uo
import json
import os

import cv2
import time
import requests
from datetime import datetime
from datetime import date
import argparse
import threading


class Detector:
    def __init__(self, THRESHOLD: int, mode: int, url: str) -> None:
        self.THRESHOLD = THRESHOLD
        self.server_url = url
        self.last_fall = None  # save time stamp of the prev fall
        self.fitToEllipse = False  # Number of minutes between Falls to make an alert
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
        self.video_fall_name = f'fall_{date.today()}.mp4'
        self.out = cv2.VideoWriter(self.video_fall_name, fourcc, 20.0, size)
        self.seconds_interval = 5

    def login(self, username: str, password: str) -> None:
        """
        Connect user to ELS server. provide user name, password and url of local/production environment
        """
        payload = {"username": username, "password": password}
        headers = {'Content-Type': 'application/json'}
        res = requests.post(f'{self.server_url}/sign_in', json=payload, headers=headers)
        if res.status_code == 200:
            self.connteced = True
            self.username = username
            self.password = password
        else:
            print("Wrong username / password")

    def start(self) -> None:
        if not self.connteced:
            print("Please login first (call login function)")
            return
        while (1):
            ret, frame = self.cap.read()
            self.frame = frame

            # Convert each frame to gray scale and subtract the background
            try:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                fgmask = self.fgbg.apply(gray)

                # Find contours
                contours, _ = cv2.findContours(fgmask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

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
                            self.last_fall = datetime.now()  # save the time of the first fall
                            threading.Thread(target=self.send_falling_post).start()
                            print("FALL Detected")
                        else:
                            time_now = datetime.now()
                            delta = time_now - self.last_fall
                            # Checking if the falling occured after the threshold
                            if self.THRESHOLD < int(delta.total_seconds() // 60):
                                self.last_fall = time_now
                                threading.Thread(target=self.send_falling_post).start()
                                print("FALL Detected")
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

    def send_falling_post(self):
        while (datetime.now() - self.last_fall).seconds < self.seconds_interval:
            self.out.write(self.frame)
            time.sleep(0.05)
        print("Finished filming")
        payload = {"username": self.username}
        json_obj = json.dumps(payload)
        with open("j.json", "w") as outfile:
            outfile.write(json_obj)
        current_working_path = os.getcwd() + os.sep
        video_fall_path = current_working_path + self.video_fall_name
        json_fall_path = current_working_path + "j.json"
        files = {'file': open(video_fall_path, "rb"),
                 'data': open(json_fall_path, "rb")}
        res = requests.post(f'{self.server_url}/fall_detected', files=files)
        if res.status_code != 200:
            print("Error sending post")
            exit(1)
        os.remove(video_fall_path)
        os.remove(json_fall_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Arguments for Falling Detector')
    parser.add_argument('Threshold', type=int, help='Threshold number in minutes')
    parser.add_argument('Mode', type=int, help='Mode for the Detector.\n 0 -> camera input, 1 -> example video input')
    parser.add_argument('URL', type=str, help='The URL of the server')
    args = parser.parse_args()
    detector = Detector(args.Threshold, args.Mode, args.URL)  # gets the number of Threshold in minutes.
    detector.login("omerap12", "Aa123456!")
    detector.start()
