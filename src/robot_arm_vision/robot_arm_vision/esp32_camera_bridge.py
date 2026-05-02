#!/usr/bin/env python3
"""
ESP32-CAM MJPEG Stream to ROS 2 Image Bridge

Connects to an ESP32-CAM running MJPEG server firmware and publishes frames
as ROS 2 sensor_msgs/Image with camera calibration info.

Usage:
    ros2 run robot_arm_vision esp32_camera_bridge --ros-args \
        -p esp32_url:=http://192.168.1.100:81/stream \
        -p camera_frame:=camera_link
"""

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image, CameraInfo
from cv_bridge import CvBridge
import cv2
import numpy as np
import urllib.request
import threading
import time

class ESP32CameraBridge(Node):
    def __init__(self):
        super().__init__('esp32_camera_bridge')
        
        # Parameters
        self.declare_parameter('esp32_url', 'http://192.168.1.100:81/stream')
        self.declare_parameter('camera_frame', 'camera_link')
        self.declare_parameter('image_topic', '/camera/image_raw')
        self.declare_parameter('info_topic', '/camera/camera_info')
        self.declare_parameter('reconnect_interval', 2.0)
        self.declare_parameter('frame_width', 640)
        self.declare_parameter('frame_height', 480)
        # Camera intrinsics (calibrate for your specific ESP32-CAM setup)
        self.declare_parameter('fx', 500.0)
        self.declare_parameter('fy', 500.0)
        self.declare_parameter('cx', 320.0)
        self.declare_parameter('cy', 240.0)
        
        self.esp32_url = str(self.get_parameter('esp32_url').value)
        self.camera_frame = str(self.get_parameter('camera_frame').value)
        self.reconnect_interval = float(self.get_parameter('reconnect_interval').value)
        self.frame_width = int(self.get_parameter('frame_width').value)
        self.frame_height = int(self.get_parameter('frame_height').value)
        self.fx = float(self.get_parameter('fx').value)
        self.fy = float(self.get_parameter('fy').value)
        self.cx = float(self.get_parameter('cx').value)
        self.cy = float(self.get_parameter('cy').value)
        
        # Publishers
        self.image_pub = self.create_publisher(Image, str(self.get_parameter('image_topic').value), 10)
        self.info_pub = self.create_publisher(CameraInfo, str(self.get_parameter('info_topic').value), 10)
        
        self.bridge = CvBridge()
        self.cap = None
        self.running = True
        self.frame_count = 0
        self.last_log_time = time.time()
        
        self.get_logger().info(f"ESP32 Camera Bridge initialized. Connecting to: {self.esp32_url}")
        
        # Start camera thread
        self.camera_thread = threading.Thread(target=self._camera_loop, daemon=True)
        self.camera_thread.start()
        
        # Timer to monitor connection status
        self.create_timer(5.0, self._status_check)

    def _camera_loop(self):
        """Background thread for camera frame capture and publishing."""
        while self.running:
            try:
                if self.cap is None:
                    self.get_logger().info(f"Attempting to connect to {self.esp32_url}...")
                    
                    # Convert string digit to int for local USB/DroidCam cameras
                    source = int(self.esp32_url) if str(self.esp32_url).isdigit() else self.esp32_url
                    self.cap = cv2.VideoCapture(source)
                    
                    if not self.cap.isOpened():
                        self.get_logger().error(f"Failed to open camera stream. Retrying in {self.reconnect_interval}s...")
                        self.cap = None
                        time.sleep(self.reconnect_interval)
                        continue
                    self.get_logger().info("Connected to ESP32-CAM!")
                
                ret, frame = self.cap.read()
                if not ret or frame is None:
                    self.get_logger().warn("Failed to read frame. Reconnecting...")
                    self.cap.release()
                    self.cap = None
                    time.sleep(self.reconnect_interval)
                    continue
                
                # Resize to expected dimensions if needed
                if frame.shape[0] != self.frame_height or frame.shape[1] != self.frame_width:
                    frame = cv2.resize(frame, (self.frame_width, self.frame_height), interpolation=cv2.INTER_LINEAR)
                
                # Publish image
                self._publish_frame(frame)
                self.frame_count += 1
                
                # Log status periodically
                now = time.time()
                if now - self.last_log_time > 5.0:
                    self.get_logger().info(f"ESP32 Camera: {self.frame_count} frames published. Latest size: {frame.shape}")
                    self.last_log_time = now
                    
            except Exception as e:
                self.get_logger().error(f"Camera loop error: {e}")
                if self.cap is not None:
                    try:
                        self.cap.release()
                    except:
                        pass
                self.cap = None
                time.sleep(self.reconnect_interval)

    def _publish_frame(self, cv_frame):
        """Convert OpenCV frame to ROS Image and publish."""
        try:
            # Convert BGR to RGB for ROS conventions
            rgb_frame = cv2.cvtColor(cv_frame, cv2.COLOR_BGR2RGB)
            
            # Create Image message
            img_msg = self.bridge.cv2_to_imgmsg(rgb_frame, encoding='rgb8')
            img_msg.header.frame_id = self.camera_frame
            img_msg.header.stamp = self.get_clock().now().to_msg()
            self.image_pub.publish(img_msg)
            
            # Create and publish camera info (for intrinsics calibration)
            info_msg = self._create_camera_info()
            info_msg.header = img_msg.header
            self.info_pub.publish(info_msg)
            
        except Exception as e:
            self.get_logger().error(f"Frame publishing error: {e}")

    def _create_camera_info(self):
        """Create a CameraInfo message with calibration parameters."""
        info = CameraInfo()
        
        # Intrinsic matrix K: [fx 0 cx; 0 fy cy; 0 0 1]
        info.k = [
            self.fx, 0.0, self.cx,
            0.0, self.fy, self.cy,
            0.0, 0.0, 1.0
        ]
        
        # Distortion parameters (assume none for now)
        info.d = [0.0, 0.0, 0.0, 0.0, 0.0]
        
        # Rotation matrix (identity for forward-facing camera)
        info.r = [1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0]
        
        # Projection matrix P: [fx 0 cx 0; 0 fy cy 0; 0 0 1 0]
        info.p = [
            self.fx, 0.0, self.cx, 0.0,
            0.0, self.fy, self.cy, 0.0,
            0.0, 0.0, 1.0, 0.0
        ]
        
        info.width = self.frame_width
        info.height = self.frame_height
        info.distortion_model = "plumb_bob"
        
        return info

    def _status_check(self):
        """Periodic status check."""
        if self.cap is None or not self.cap.isOpened():
            self.get_logger().warn("Camera connection lost. Attempting reconnection...")

    def destroy_node(self):
        """Cleanup on shutdown."""
        self.running = False
        if self.cap is not None:
            self.cap.release()
        super().destroy_node()

def main(args=None):
    rclpy.init(args=args)
    node = ESP32CameraBridge()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
