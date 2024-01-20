from threading import Timer
import os
import time
import http.server
import socketserver

import cv2
import numpy as np
import requests
from PIL import Image

# import settings
# import send_email


# Load YOLO
net = cv2.dnn.readNet("yolov3.weights", "yolov3.cfg")
layer_names = net.getLayerNames()
output_layers = [layer_names[i[0] - 1] for i in net.getUnconnectedOutLayers()]
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
            scores = detection[5:]
            class_id = np.argmax(scores)
            confidence = scores[class_id]
            if confidence > 0.5 and classes[class_id] == "cup":
                center_x = int(detection[0] * width)
                center_y = int(detection[1] * height)
                w = int(detection[2] * width)
                h = int(detection[3] * height)
                x = int(center_x - w / 2)
                y = int(center_y - h / 2)
                boxes.append([x, y, w, h])
                confidences.append(float(confidence))
                class_ids.append(class_id)

    indexes = cv2.dnn.NMSBoxes(boxes, confidences, 0.5, 0.4)
    for i in range(len(boxes)):
        if i in indexes:
            x, y, w, h = boxes[i]
            label = "{}: {:.2f}%".format(classes[class_ids[i]], confidences[i] * 100)
            cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)
            cv2.putText(frame, label, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 0, 0), 2)
    return len(indexes) > 0


def send_webhook(image):
    url = "https://your-google-chat-webhook-url"
    temp_file_path = f'/tmp/cup_{int(time.time())}.jpg'
    image.save(temp_file_path)

    # Start a simple HTTP server to serve the image
    class SimpleHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header("Content-type", "image/jpeg")
            self.end_headers()
            with open(temp_file_path, 'rb') as f:
                self.wfile.write(f.read())

    def run():
        server = socketserver.TCPServer(("", 8080), SimpleHTTPRequestHandler)
        print("Serving image at http://localhost:%s/" % server.server_address[1])
        server.serve_forever()

    # Start the server in a separate thread and wait for it to start before sending webhook
    t = Timer(0.5, run)
    t.start()
    time.sleep(0.2)  # Wait for the server to start

    payload = {"image_url": f"http://localhost:{run.server_address[1]}/cup_{int(time.time())}.jpg"}
    response = requests.post(url, json=payload)

    # Stop the HTTP server
    run.shutdown()

    os.remove(temp_file_path)  # Remove the image from local storage


# def send_email_notification(image):
#     # Load your email settings
#     with open("email_settings.txt", "r") as f:
#         lines = [line.strip() for line in f.readlines()]
#
#     from_email = lines[0]
#     to_emails = lines[1].split(",")
#     subject = lines[2]
#     content = lines[3]
#     sendgrid_api_key = lines[4]

#     # Create a list of files to be attached
#     files = [settings.template_path, settings.logo_path]  # Replace these paths with your actual paths

#     # Call the send_email function from send_email.py
#     send_email.send_email(sendgrid_api_key, from_email, to_emails, subject, content, files)

start_time = None
frame_skip = 5
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
                elif time.time() - start_time > 300:
                    image = Image.fromarray(frame)
                    send_webhook(image)
                    # send_email_notification(image)
                    start_time = None
            else:
                start_time = None
        frame_count += 1
        time.sleep(1)
finally:
    cap.release()
    cv2.destroyAllWindows()
