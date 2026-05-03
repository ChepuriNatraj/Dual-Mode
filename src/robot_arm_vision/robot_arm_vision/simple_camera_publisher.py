#!/usr/bin/env python3
"""
Simple USB/Laptop Webcam Publisher

Publishes frames from a local USB camera to /camera/image_raw

Usage:
    python3 simple_camera_publisher.py
"""

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image, CameraInfo
from cv_bridge import CvBridge
import cv2
import threading
import time

class SimpleCameraPublisher(Node):
    def __init__(self):
        super().__init__('simple_camera_publisher')
        
        # Parameters
        self.declare_parameter('camera_index', 0)
        self.declare_parameter('frame_width', 640)
        self.declare_parameter('frame_height', 480)
        self.declare_parameter('camera_frame', 'camera_link')
        # Camera intrinsics - calibrate for your specific camera
        self.declare_parameter('fx', 500.0)
        self.declare_parameter('fy', 500.0)
        self.declare_parameter('cx', 320.0)
        self.declare_parameter('cy', 240.0)
        
        self.camera_index = int(self.get_parameter('camera_index').value)
        self.frame_width = int(self.get_parameter('frame_width').value)
        self.frame_height = int(self.get_parameter('frame_height').value)
        self.camera_frame = str(self.get_parameter('camera_frame').value)
        self.fx = float(self.get_parameter('fx').value)
        self.fy = float(self.get_parameter('fy').value)
        self.cx = float(self.get_parameter('cx').value)
        self.cy = float(self.get_parameter('cy').value)
        
        # Publishers
        self.image_pub = self.create_publisher(Image, '/camera/image_raw', 10)
        self.info_pub = self.create_publisher(CameraInfo, '/camera/camera_info', 10)
        
        self.bridge = CvBridge()
        self.cap = None
        self.running = True
        self.frame_count = 0
        
        self.get_logger().info(f"Simple Camera Publisher starting. Camera index: {self.camera_index}")
        
        # Start camera thread
        self.camera_thread = threading.Thread(target=self._camera_loop, daemon=True)
        self.camera_thread.start()

    def _camera_loop(self):
        """Background thread for camera frame capture and publishing."""
        while self.running:
            try:
                if self.cap is None:
                    self.cap = cv2.VideoCapture(self.camera_index)
                    if not self.cap.isOpened():
                        self.get_logger().error(f"Failed to open camera. Retrying...")
                        self.cap = None
                        time.sleep(2.0)
                        continue
                    self.get_logger().info("Camera opened successfully!")
                
                ret, frame = self.cap.read()
                if not ret or frame is None:
                    self.get_logger().warn("Failed to read frame. Reconnecting...")
                    self.cap.release()
                    self.cap = None
                    continue
                
                # Resize if needed
                if frame.shape[0] != self.frame_height or frame.shape[1] != self.frame_width:
                    frame = cv2.resize(frame, (self.frame_width, self.frame_height))
                
                # Publish image
                img_msg = self.bridge.cv2_to_imgmsg(frame, encoding='bgr8')
                img_msg.header.frame_id = self.camera_frame
                img_msg.header.stamp = self.get_clock().now().to_msg()
                self.image_pub.publish(img_msg)
                
                # Publish camera info
                info_msg = self._create_camera_info()
                info_msg.header = img_msg.header
                self.info_pub.publish(info_msg)
                
                self.frame_count += 1
                if self.frame_count % 30 == 0:
                    self.get_logger().info(f"Published {self.frame_count} frames")
                    
            except Exception as e:
                self.get_logger().error(f"Camera loop error: {e}")
                if self.cap is not None:
                    try:
                        self.cap.release()
                    except:
                        pass
                self.cap = None
                time.sleep(2.0)

    def _create_camera_info(self):
        """Create CameraInfo message with calibration parameters."""
        info = CameraInfo()
        info.k = [
            self.fx, 0.0, self.cx,
            0.0, self.fy, self.cy,
            0.0, 0.0, 1.0
        ]
        info.d = [0.0, 0.0, 0.0, 0.0, 0.0]
        info.r = [1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0]
        info.p = [
            self.fx, 0.0, self.cx, 0.0,
            0.0, self.fy, self.cy, 0.0,
            0.0, 0.0, 1.0, 0.0
        ]
        info.width = self.frame_width
        info.height = self.frame_height
        info.distortion_model = "plumb_box"
        return info

    def destroy_node(self):
        """Cleanup on shutdown."""
        self.running = False
        if self.cap is not None:
            self.cap.release()
        super().destroy_node()

def main(args=None):
    rclpy.init(args=args)
    node = SimpleCameraPublisher()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
