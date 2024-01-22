import time

import cv2
import numpy as np
import requests


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


def send_webhook():
    url = "https://your-google-chat-webhook-url"  # Make sure to replace this with your actual webhook URL
    headers = {
        "Content-Type": "application/json; charset=UTF-8"
    }
    data = {
        "text": "Coffee cup left unattended! Please remove it from the coffee machine :)"
    }
    
    response = requests.post(url, headers=headers, json=data)
    print("Webhook sent, response:", response.text)


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
                    send_webhook()
                    start_time = None
            else:
                start_time = None
        frame_count += 1
        time.sleep(1)
finally:
    cap.release()
