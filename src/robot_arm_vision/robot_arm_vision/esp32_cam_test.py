import cv2
import urllib.request
import numpy as np

# Try to import YOLOv8 for Object Detection
try:
    from ultralytics import YOLO
    yolo_available = True
    model = YOLO("yolov8n.pt") # lightweight nano model
except ImportError:
    yolo_available = False
    model = None
    print("Ultralytics YOLO not found. Just displaying raw video stream.")
    print("To install yolo: pip install ultralytics")

# ====================================================
# REPLACE WITH YOUR ESP32-CAM IP ADDRESS FROM ARDUINO
# Example: "http://192.168.1.100:81/stream"
# ====================================================
esp32_cam_url = "http://10.225.40.154:81/stream"

def start_camera_stream():
    print(f"Connecting to ESP32-CAM stream at: {esp32_cam_url}")
    # We use cv2.VideoCapture to grab the HTTP Motion JPEG stream
    cap = cv2.VideoCapture(esp32_cam_url)

    if not cap.isOpened():
        print("Error: Could not open the video stream.")
        print("Check your ESP32-CAM IP Address and make sure it is powered on and connected to WiFi.")
        return

    print("Connected successfully! Press 'q' to quit.")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Dropped frame, trying to reconnect...")
            cap = cv2.VideoCapture(esp32_cam_url)
            continue

        # If YOLOv8 is installed, run prediction on the frame
        if yolo_available:
            results = model.predict(frame, conf=0.5, verbose=False)
            
            # Extract bound boxes and annotations
            for r in results:
                # draw the results on the frame
                annotated_frame = r.plot()
                
            cv2.imshow("ESP32-CAM YOLOv8 AI Sorting Vision", annotated_frame)
        else:
            cv2.imshow("ESP32-CAM Raw Stream", frame)

        # Press 'q' to quit
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == '__main__':
    start_camera_stream()