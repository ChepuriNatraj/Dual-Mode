import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image, CameraInfo
from geometry_msgs.msg import PoseStamped
from cv_bridge import CvBridge
import cv2
import numpy as np

try:
    from ultralytics import YOLO
    HAVE_YOLO = True
except ImportError:
    HAVE_YOLO = False

class VisionNode(Node):
    def __init__(self):
        super().__init__('vision_node')
        self.bridge = CvBridge()
        
        # Subscriptions
        self.image_sub = self.create_subscription(
            Image,
            '/camera/image_raw',
            self.image_callback,
            10)
            
        self.info_sub = self.create_subscription(
            CameraInfo,
            '/camera/camera_info',
            self.info_callback,
            10)
            
        # Publisher
        self.pose_pub = self.create_publisher(PoseStamped, '/target_pose', 10)
        
        # Camera parameters
        self.fx = None
        self.fy = None
        self.cx = None
        self.cy = None
        self.camera_height = 0.8  # As defined in camera.xacro (z=0.8m)
        self.workspace_z = 0.025  # Height of the objects (approx 5cm / 2)
        
        # YOLO setup
        self.yolo_model = None
        if HAVE_YOLO:
            self.get_logger().info('YOLOv8 is available. Loading model...')
            # Using basic YOLOv8 nano model for speed
            self.yolo_model = YOLO("yolov8n.pt") 
        else:
            self.get_logger().warn('YOLOv8 not found! Falling back to color thresholding. To use YOLO, run: pip install ultralytics')
            
        self.get_logger().info('Vision node initialization complete.')

    def info_callback(self, msg):
        # Extract intrinsic matrix parameters from camera_info
        # K is a 3x3 row-major matrix: [fx, 0, cx, 0, fy, cy, 0, 0, 1]
        self.fx = msg.k[0]
        self.fy = msg.k[4]
        self.cx = msg.k[2]
        self.cy = msg.k[5]

    def pixel_to_world(self, u, v):
        if self.fx is None:
            return None
            
        # Depth from camera lens to object center
        Z_c = self.camera_height - self.workspace_z
        
        # Convert pixel to camera frame (camera looks down along -Z, but standard projection uses +Z)
        X_c = (u - self.cx) * Z_c / self.fx
        Y_c = (v - self.cy) * Z_c / self.fy
        
        # Transform from camera frame to world base_link frame
        # In camera.xacro: xyz="0.25 0.0 0.8" rpy="0 1.5708 0"
        # Based on standard ROS camera frame conventions mapped to a 90 degree pitch down
        world_x = 0.25 + Y_c
        world_y = 0.0 + X_c
        world_z = self.workspace_z
        
        return (world_x, world_y, world_z)

    def publish_pose(self, world_coords):
        if world_coords is None:
            return
            
        msg = PoseStamped()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = "world"
        
        msg.pose.position.x = world_coords[0]
        msg.pose.position.y = world_coords[1]
        msg.pose.position.z = world_coords[2]
        
        # Pointing down for gripper grasp
        msg.pose.orientation.x = 0.0
        msg.pose.orientation.y = 1.0 # 180 deg pitch (pointing down)
        msg.pose.orientation.z = 0.0
        msg.pose.orientation.w = 0.0
        
        self.pose_pub.publish(msg)
        self.get_logger().info(f'Published target: X={world_coords[0]:.3f}, Y={world_coords[1]:.3f}')

    def image_callback(self, msg):
        try:
            frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
            
            target_pixel = None
            
            if HAVE_YOLO and self.yolo_model is not None:
                # YOLOv8 Inference
                results = self.yolo_model(frame, verbose=False)
                
                # Visualize
                annotated_frame = results[0].plot()
                
                # Find first detected object center to grab
                if len(results[0].boxes) > 0:
                    box = results[0].boxes[0]
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    cx = (x1 + x2) / 2.0
                    cy = (y1 + y2) / 2.0
                    target_pixel = (int(cx), int(cy))
                
                frame = annotated_frame
                
            else:
                # Color threshold fallback (Red)
                hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
                mask1 = cv2.inRange(hsv, np.array([0, 120, 70]), np.array([10, 255, 255]))
                mask2 = cv2.inRange(hsv, np.array([170, 120, 70]), np.array([180, 255, 255]))
                mask = mask1 + mask2
                
                contours, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
                
                for contour in contours:
                    if cv2.contourArea(contour) > 500:
                        x, y, w, h = cv2.boundingRect(contour)
                        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                        
                        cx = x + w // 2
                        cy = y + h // 2
                        cv2.circle(frame, (cx, cy), 5, (255, 0, 0), -1)
                        
                        target_pixel = (cx, cy)
                        break # Just take the first large one
                        
            if target_pixel is not None and self.fx is not None:
                world_xyz = self.pixel_to_world(target_pixel[0], target_pixel[1])
                cv2.putText(frame, f"X:{world_xyz[0]:.2f} Y:{world_xyz[1]:.2f}", 
                            (target_pixel[0]-20, target_pixel[1]-20), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
                self.publish_pose(world_xyz)
                
            cv2.imshow("Robot Arm Vision", frame)
            cv2.waitKey(1)
            
        except Exception as e:
            self.get_logger().error(f'Vision error: {e}')

def main(args=None):
    rclpy.init(args=args)
    node = VisionNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        cv2.destroyAllWindows()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
