# ELS_FallDetector
#How it works
For each frame of video:<br>
Convert the frame into gray<br>
Remove background<br>
Find the contours and draw them<br>
If height of the contour is lower than width -> may be fall so we add 1 to count.<br>
If count > 10 -> fall<br>

#How to run
pip install -r requirements.txt
python3 main.py
