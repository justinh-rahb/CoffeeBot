import os
import time
import wget

from decouple import config
import cv2
import numpy as np
import requests
from PIL import Image


# Environment variables
FRAME_SKIP = config('FRAME_SKIP', default=10, cast=int)
DETECTION_TIME = config('DETECTION_TIME', default=300, cast=int)
MESSAGE = config('MESSAGE', default='Coffee cup left unattended! Please remove it from the coffee machine before it gets cold :)')
WEBHOOK_URL = config('WEBHOOK_URL')


# Function to download YOLO files if not present
def download_yolo_files():
    files = [
        ("https://pjreddie.com/media/files/yolov3.weights", "yolov3.weights"),
        ("https://raw.githubusercontent.com/pjreddie/darknet/master/cfg/yolov3.cfg", "yolov3.cfg"),
        ("https://raw.githubusercontent.com/pjreddie/darknet/master/data/coco.names", "coco.names"),
    ]
    for url, file in files:
        if not os.path.exists(file):
            print(f"Downloading {file}...")
            wget.download(url, file)


# Check and download YOLO model files
download_yolo_files()

# Load YOLO
net = cv2.dnn.readNet("yolov3.weights", "yolov3.cfg")
layer_names = net.getLayerNames()
output_layers_indices = net.getUnconnectedOutLayers().flatten()
output_layers = [layer_names[i - 1] for i in output_layers_indices]
classes = []
with open("coco.names", "r") as f:
    classes = [line.strip() for line in f.readlines()]

# Initialize webcam
cap = cv2.VideoCapture(0)


def detect_cup(frame):
    height, width, channels = frame.shape
    blob = cv2.dnn.blobFromImage(frame, 0.00392, (416, 416), (0, 0, 0), True, crop=False)
    net.setInput(blob)
    outs = net.forward(output_layers)

    class_ids = []
    confidences = []
    boxes = []

    for out in outs:
       for detection in out:
           scores = detection[5:]   # Extract the confidence scores for each class from the current detection
           class_id = np.argmax(scores)   # Find the index of the maximum score in the confidence scores list
           confidence = scores[class_id]   # Extract the confidence value corresponding to the class with the highest confidence
           if confidence > 0.5 and classes[class_id] == "cup":   # Filter out detections that do not meet a minimum confidence threshold or are not of interest
               # Calculate the coordinates of the bounding box's center by scaling the relative coordinates provided by the model to the frame dimensions
               center_x = int(detection[0] * width)
               center_y = int(detection[1] * height)
               # Calculate the width and height of the bounding box by scaling the relative coordinates provided by the model to the frame dimensions
               w = int(detection[2] * width)
               h = int(detection[3] * height)
               # Calculate the coordinates of the top-left corner of the bounding box using the center coordinates and frame dimensions
               x = int(center_x - w / 2)
               y = int(center_y - h / 2)
               # Save the calculated bounding box coordinates, confidence value, and class ID corresponding to the current detection
               boxes.append([x, y, w, h])
               confidences.append(float(confidence))
               class_ids.append(class_id)
    
    # Perform Non-Maximum Suppression (NMS) on the bounding boxes based on their confidence scores
    # and spatial overlap to filter out overlapping detections with lower confidence
    indexes = cv2.dnn.NMSBoxes(boxes, confidences, 0.5, 0.4)
    for i in range(len(boxes)):
       if i in indexes:   # Check if a bounding box is among those selected by the NMS algorithm
           x, y, w, h = boxes[i]   # Extract the coordinates of the current bounding box from the list
           label = "{}: {:.2f}%".format(classes[class_ids[i]], confidences[i] * 100)  # Format a string label containing the class name and confidence score
           cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)   # Draw the bounding box on the frame using its coordinates
           cv2.putText(frame, label, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 0, 0), 2)   # Display the formatted label above the bounding box
    return len(indexes) > 0   # Return True if any valid detections were made (i.e., indexes is not empty) and False otherwise


def send_webhook():
    headers = {
        "Content-Type": "application/json; charset=UTF-8"
    }
    data = {
        "text": MESSAGE
    }
    
    response = requests.post(WEBHOOK_URL, headers=headers, json=data)
    print("Webhook sent, response:", response.text)


start_time = None
frame_skip = FRAME_SKIP
frame_count = 0

try:
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if frame_count % frame_skip == 0:
            if detect_cup(frame):
                if start_time is None:
                    start_time = time.time()
                elif time.time() - start_time > DETECTION_TIME:
                    image = Image.fromarray(frame)
                    send_webhook()
                    start_time = None
            else:
                start_time = None
        frame_count += 1
        time.sleep(1)
finally:
    cap.release()
