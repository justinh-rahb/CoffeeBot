#!/usr/bin/env python3
"""Detect an object in a video stream from a webcam."""
import os
import time
import threading
from http.server import SimpleHTTPRequestHandler, HTTPServer

import wget
from decouple import config
import cv2
import numpy as np
import requests
from PIL import Image


# Environment variables
BOT_WEBHOOK_URL = config('BOT_WEBHOOK_URL') # This must be set, all other variables have defaults
BOT_MESSAGE = config(
    'BOT_MESSAGE',
    default='Coffee cup left unattended! Please remove it from the coffee machine :)'
)
OBJECT = config('OBJECT', default='cup') # The object to detect
MIN_CONFIDENCE = config('MIN_CONFIDENCE', default=0.5, cast=float) # Minimum confidence threshold
FRAME_SKIP = config('FRAME_SKIP', default=5, cast=int) # Process every n-th frame
DETECTION_TIME = config('DETECTION_TIME', default=300, cast=int) # Time object must be detected for
CAPTURE_DEVICE = config('CAPTURE_DEVICE', default=0, cast=int) # Capture device, 0 is the default webcam
SAVE_DIR = config('SAVE_DIR', default='/tmp/coffeebot') # Directory to save images to


def detect_object(frame):
    """Detect a given object in a frame."""
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
            if confidence > MIN_CONFIDENCE and classes[class_id] == OBJECT:
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
    indexes = cv2.dnn.NMSBoxes(boxes, confidences, MIN_CONFIDENCE, MIN_CONFIDENCE - 0.1)
    for i, b in enumerate(boxes):
        # Check if a bounding box is among those selected by the NMS algorithm
        if i in indexes:
            # Extract the coordinates of the current bounding box from the list
            x, y, w, h = b
            # Format a label containing the class name and confidence score of the current detection
            label = "{}: {:.2f}%".format(classes[class_ids[i]], confidences[i] * 100)
            # Draw the bounding box on the frame using its coordinates
            cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)
            # Display the label above the bounding box
            cv2.putText(frame, label, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 0, 0), 2)
    # Return True if any valid detections were made and False otherwise
    return len(indexes) > 0


def download_yolo():
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


def send_webhook():
    """Send a webhook request."""
    headers = {
        "Content-Type": "application/json; charset=UTF-8"
    }
    data = {
        "text": BOT_MESSAGE
    }

    response = requests.post(BOT_WEBHOOK_URL, headers=headers, json=data, timeout=10)
    print("Webhook sent, response:", response.text)


def start_server(port=8080, directory='/tmp/coffeebot'):
    """Start a simple HTTP server to serve the current frame."""
    os.chdir(directory)  # Change working directory to serve files from /tmp
    server_address = ('', port)
    httpd = HTTPServer(server_address, SimpleHTTPRequestHandler)
    httpd.serve_forever()


# Create the SAVE_DIR directory if it does not exist
if not os.path.exists(SAVE_DIR):
    os.makedirs(SAVE_DIR)

# Check and download YOLOv3 model files
download_yolo()

# Load YOLOv3 model files
print("Loading YOLOv3 model...")
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
print("YOLOv3 model loaded.")

# Start the web server in a new thread
server_thread = threading.Thread(target=start_server, args=(8080,))
server_thread.daemon = True  # This ensures the thread will close when the main program exits
server_thread.start()
print("Web server started on port 8080...")

start_time = None
frame_count = 0

# Main loop
try:
    # Initialize webcam
    cap = cv2.VideoCapture(CAPTURE_DEVICE)
    # write message to console
    print("Starting CoffeeBot...")

    while True:
        # Capture the next frame from the video stream and store it in a variable
        ret, frame = cap.read()
        if not ret:
            print("No frame available, exiting.")
            break   # Exit the loop if no more frames are available

        # Process every n-th frame (frame_skip) to reduce processing load
        if frame_count % FRAME_SKIP == 0:
            if detect_object(frame):
                if start_time is None:
                    # Record the time when the first OBJECT was detected
                    start_time = time.time()
                # Check if (DETECTION_TIME) has passed since the first detection
                elif time.time() - start_time > DETECTION_TIME:
                    print("Object '" + OBJECT + "' detected at " +
                          time.strftime("%H:%M:%S", time.localtime(start_time))
                          + "\nSending webhook...")
                    # Convert the frame to an image object for further processing
                    image = Image.fromarray(frame)
                    # Send a webhook request
                    send_webhook()
                    # Save the image to a file
                    image.save(os.path.join(SAVE_DIR, f"capture_{time.time()}.jpg"))
                    print(f"Image saved to {SAVE_DIR}/capture_{time.time()}.jpg")
                    start_time = None   # Reset the start_time variable
            else:
                # If no OBJECT was detected, reset the start_time variable
                start_time = None
        frame_count += 1   # Increment the frame counter
        # Save the current frame to a file
        cv2.imwrite(os.path.join(SAVE_DIR, '/tmp/coffeebot/current.jpg'), frame)
        time.sleep(1)
finally:
    cap.release()
