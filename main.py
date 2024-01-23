#!/usr/bin/env python3
"""Detect a coffee cup in a video stream from a webcam."""
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
MESSAGE = config(
    'MESSAGE',
    default='Coffee cup left unattended! Please remove it from the coffee machine :)'
)
WEBHOOK_URL = config('WEBHOOK_URL')


# Function to download YOLO files if not present
def download_yolo_files():
    """Download the YOLO model files if they are not present."""
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
NET = cv2.dnn.readNet("yolov3.weights", "yolov3.cfg")
# Get a list containing the names of all layers in the network
layer_names = NET.getLayerNames()
# Get a 1D array with the indices of output layers
output_layers_indices = NET.getUnconnectedOutLayers().flatten()
# Extract the names of output layers based on their indices
output_layers = [layer_names[i - 1] for i in output_layers_indices]
# Initialize an empty list for storing class labels
classes = []
with open("coco.names", "r", encoding="utf-8") as f:
    classes = [line.strip() for line in f.readlines()]

# Initialize webcam
cap = cv2.VideoCapture(0)


def detect_cup(frame):
    """Detect a coffee cup in a frame."""
    # Get the shape of the frame (height, width, and number of color channels)
    height, width, channels = frame.shape
    # Prepare the frame for input into the neural network
    blob = cv2.dnn.blobFromImage(frame, 0.00392, (416, 416), (0, 0, 0), True, crop=False)
    NET.setInput(blob)
    # Forward pass through the network and get the output from the specified layers (output_layers)
    outs = NET.forward(output_layers)

    # Initialize empty lists for storing class IDs, confidence scores, and bounding boxes
    class_ids = []
    confidences = []
    boxes = []

    for out in outs:
        for detection in out:
            # Extract the confidence scores for each class from the current detection
            scores = detection[5:]
            # Find the index of the maximum score in the confidence scores list
            class_id = np.argmax(scores)
            # Extract the confidence value corresponding to the class with the highest confidence
            confidence = scores[class_id]
            # Filter out detections that do not meet minimum confidence threshold or not of interest
            if confidence > 0.5 and classes[class_id] == "cup":
                # Calculate the coordinates of the bounding box's center by scaling the
                # relative coordinates provided by the model to the frame dimensions
                center_x = int(detection[0] * width)
                center_y = int(detection[1] * height)
                # Calculate the width and height of the bounding box by scaling the
                # relative coordinates provided by the model to the frame dimensions
                w = int(detection[2] * width)
                h = int(detection[3] * height)
                # Calculate the coordinates of the top-left corner of the bounding box
                # using the center coordinates and frame dimensions
                x = int(center_x - w / 2)
                y = int(center_y - h / 2)
                # Save the calculated bounding box coordinates, confidence value, and class ID
                # corresponding to the current detection as a dictionary in the detections list
                boxes.append([x, y, w, h])
                confidences.append(float(confidence))
                class_ids.append(class_id)

    # Perform Non-Maximum Suppression (NMS) on the bounding boxes based on their confidence scores
    # and spatial overlap to filter out overlapping detections with lower confidence
    indexes = cv2.dnn.NMSBoxes(boxes, confidences, 0.5, 0.4)
    for i in range(len(boxes)):
        # Check if a bounding box is among those selected by the NMS algorithm
        if i in indexes:
            # Extract the coordinates of the current bounding box from the list
            x, y, w, h = boxes[i]
            # Format a label containing the class name and confidence score of the current detection
            label = "{}: {:.2f}%".format(classes[class_ids[i]], confidences[i] * 100)
            # Draw the bounding box on the frame using its coordinates
            cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)
            # Display the label above the bounding box
            cv2.putText(frame, label, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 0, 0), 2)
    # Return True if any valid detections were made and False otherwise
    return len(indexes) > 0


def send_webhook():
    """Send a Google Chat webhook."""
    headers = {
        "Content-Type": "application/json; charset=UTF-8"
    }
    data = {
        "text": MESSAGE
    }

    response = requests.post(WEBHOOK_URL, headers=headers, json=data)
    print("Webhook sent, response:", response.text)


START_TIME = None
FRAME_COUNT = 0
frame_skip = FRAME_SKIP

try:
    while True:
        # Capture the next frame from the video stream and store it in a variable
        ret, frame = cap.read()
        if not ret:
            break   # Exit the loop if no more frames are available

        # Process every n-th frame (frame_skip) to reduce processing load
        if FRAME_COUNT % frame_skip == 0:
            if detect_cup(frame):
                if START_TIME is None:
                    # Record the time when the first "cup" was detected
                    START_TIME = time.time()
                # Check if (DETECTION_TIME) has passed since the first detection
                elif time.time() - START_TIME > DETECTION_TIME:
                    # Convert the frame to an image object for further processing
                    image = Image.fromarray(frame)
                    send_webhook()
                    START_TIME = None   # Reset the START_TIME variable
            else:
                # If no "cup" was detected, reset the START_TIME variable
                START_TIME = None
        FRAME_COUNT += 1   # Increment the frame counter
        time.sleep(1)
finally:
    cap.release()
