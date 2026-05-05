import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image, CameraInfo
from geometry_msgs.msg import PoseStamped
from cv_bridge import CvBridge
import cv2
import numpy as np
import time

try:
    from ultralytics import YOLO
    HAVE_YOLO = True
except ImportError:
    HAVE_YOLO = False

class VisionNode(Node):
    def __init__(self):
        super().__init__('vision_node')
        self.bridge = CvBridge()
        
        # Declare parameters
        self.declare_parameter('detector_mode', 'red')
        self.declare_parameter('camera_height', 0.8)
        self.declare_parameter('workspace_z', 0.02)
        self.declare_parameter('min_world_x', 0.15)
        self.declare_parameter('max_world_x', 0.45)
        self.declare_parameter('min_world_y', -0.25)
        self.declare_parameter('max_world_y', 0.25)
        self.declare_parameter('stable_frames_required', 15)
        self.declare_parameter('stability_tolerance', 0.02)
        
        # Retrieve parameters
        self.detector_mode = self.get_parameter('detector_mode').value
        self.camera_height = self.get_parameter('camera_height').value
        self.workspace_z = self.get_parameter('workspace_z').value
        self.min_world_x = self.get_parameter('min_world_x').value
        self.max_world_x = self.get_parameter('max_world_x').value
        self.min_world_y = self.get_parameter('min_world_y').value
        self.max_world_y = self.get_parameter('max_world_y').value
        self.stable_frames_required = self.get_parameter('stable_frames_required').value
        self.stability_tolerance = self.get_parameter('stability_tolerance').value
        
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
        self.image_pub = self.create_publisher(Image, '/camera/image_annotated', 10)
        
        # Camera parameters
        self.fx = None
        self.fy = None
        self.cx = None
        self.cy = None
        self.last_log_time = 0.0
        
        # Target smoothing state
        self.target_candidate = None
        self.stable_frame_count = 0
        self.locked_target = None
        self.last_publish_time = 0.0
        
        # YOLO setup
        self.yolo_model = None
        if self.detector_mode == 'yolo':
            if HAVE_YOLO:
                self.get_logger().info('YOLO detector enabled. Loading model...')
                self.yolo_model = YOLO("yolov8n.pt") 
            else:
                self.get_logger().warn('YOLOv8 not found! Falling back to RED color thresholding. To use YOLO, run: pip install ultralytics')
                self.detector_mode = 'red'
        else:
            self.get_logger().info('RED detector enabled.')
            
        self.get_logger().info('Vision node initialization complete.')

    def info_callback(self, msg):
        self.fx = msg.k[0]
        self.fy = msg.k[4]
        self.cx = msg.k[2]
        self.cy = msg.k[5]

    def pixel_to_world(self, u, v):
        if self.fx is None:
            return None
            
        Z_c = self.camera_height - self.workspace_z
        X_c = (u - self.cx) * Z_c / self.fx
        Y_c = (v - self.cy) * Z_c / self.fy
        
        world_x = 0.25 + Y_c
        world_y = 0.0 + X_c
        world_z = self.workspace_z
        
        return (world_x, world_y, world_z)

    def publish_pose(self, world_coords):
        if world_coords is None:
            return
            
        now = time.time()
        # Rate limit publishing of the locked target
        if now - self.last_publish_time < 0.5:
            return

        msg = PoseStamped()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = "world"
        
        msg.pose.position.x = world_coords[0]
        msg.pose.position.y = world_coords[1]
        msg.pose.position.z = world_coords[2]
        
        msg.pose.orientation.x = 0.0
        msg.pose.orientation.y = 1.0 # 180 deg pitch (pointing down)
        msg.pose.orientation.z = 0.0
        msg.pose.orientation.w = 0.0
        
        self.pose_pub.publish(msg)
        self.last_publish_time = now
        
        if now - self.last_log_time > 2.0:
            self.get_logger().info(f'Published LOCKED target: X={world_coords[0]:.3f}, Y={world_coords[1]:.3f}')
            self.last_log_time = now

    def is_within_workspace(self, world_xyz):
        if world_xyz is None:
            return False
        return (
            self.min_world_x <= world_xyz[0] <= self.max_world_x and
            self.min_world_y <= world_xyz[1] <= self.max_world_y
        )

    def image_callback(self, msg):
        try:
            frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
            target_pixel = None
            
            if self.detector_mode == 'yolo' and self.yolo_model is not None:
                results = self.yolo_model(frame, verbose=False)
                annotated_frame = results[0].plot()
                if len(results[0].boxes) > 0:
                    # Filter basic by confidence and type if necessary
                    # Just taking best box for now
                    box = results[0].boxes[0]
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    cx = (x1 + x2) / 2.0
                    cy = (y1 + y2) / 2.0
                    target_pixel = (int(cx), int(cy))
                frame = annotated_frame
            else:
                hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
                mask1 = cv2.inRange(hsv, np.array([0, 120, 70]), np.array([10, 255, 255]))
                mask2 = cv2.inRange(hsv, np.array([170, 120, 70]), np.array([180, 255, 255]))
                mask = mask1 + mask2
                contours, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
                valid = [c for c in contours if cv2.contourArea(c) > 250]
                if valid:
                    frame_h, frame_w = frame.shape[:2]
                    center = np.array([frame_w * 0.5, frame_h * 0.5])
                    def contour_score(c):
                        x, y, w, h = cv2.boundingRect(c)
                        cxy = np.array([x + w * 0.5, y + h * 0.5])
                        return np.linalg.norm(cxy - center)

                    best = min(valid, key=contour_score)
                    x, y, w, h = cv2.boundingRect(best)
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                    cx = x + w // 2
                    cy = y + h // 2
                    cv2.circle(frame, (cx, cy), 5, (255, 0, 0), -1)
                    target_pixel = (cx, cy)
                        
            # Target Smoothing Logic
            world_xyz = None
            if target_pixel is not None and self.fx is not None:
                world_xyz = self.pixel_to_world(target_pixel[0], target_pixel[1])
                
                if self.is_within_workspace(world_xyz):
                    if self.target_candidate is None:
                        self.target_candidate = world_xyz
                        self.stable_frame_count = 1
                    else:
                        dx = abs(world_xyz[0] - self.target_candidate[0])
                        dy = abs(world_xyz[1] - self.target_candidate[1])
                        
                        if dx < self.stability_tolerance and dy < self.stability_tolerance:
                            self.stable_frame_count += 1
                        else:
                            # Reset if it jumps
                            self.target_candidate = world_xyz
                            self.stable_frame_count = 1
                            self.locked_target = None
                            
                    if self.stable_frame_count >= self.stable_frames_required:
                        # Lock on the target
                        self.locked_target = self.target_candidate
                        cv2.putText(frame, "LOCKED", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2)
                else:
                    self.target_candidate = None
                    self.stable_frame_count = 0
                    cv2.putText(frame, "Target out of workspace", (10, 30),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            else:
                self.target_candidate = None
                self.stable_frame_count = 0

            # Draw target info
            if self.locked_target is not None:
                cv2.putText(frame, f"X:{self.locked_target[0]:.2f} Y:{self.locked_target[1]:.2f}", 
                            (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                self.publish_pose(self.locked_target)
            elif world_xyz is not None and self.is_within_workspace(world_xyz):
                 cv2.putText(frame, f"Wait:{self.stable_frame_count}/{self.stable_frames_required}", 
                            (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
            
            try:
                annotated_msg = self.bridge.cv2_to_imgmsg(frame, encoding='bgr8')
                annotated_msg.header = msg.header
                self.image_pub.publish(annotated_msg)
            except Exception as e:
                self.get_logger().error(f'Failed to republish annotated image: {e}')
                
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
