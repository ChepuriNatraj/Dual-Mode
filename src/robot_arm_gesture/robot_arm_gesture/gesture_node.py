import rclpy
from rclpy.node import Node
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint

import os
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

from pathlib import Path

import cv2
import mediapipe as mp
import numpy as np
import math

mp_hands = mp.tasks.vision.HandLandmarksConnections
mp_drawing = mp.tasks.vision.drawing_utils
mp_drawing_styles = mp.tasks.vision.drawing_styles

class GestureControlNode(Node):
    def __init__(self):
        super().__init__('gesture_control_node')

        self.declare_parameter('arm_topic', '/arm_controller/joint_trajectory')
        self.declare_parameter('gripper_topic', '/gripper_controller/joint_trajectory')
        self.declare_parameter('mirror_to_local_controller', False)
        self.declare_parameter('local_arm_topic', '/local_controller/joint_trajectory')
        self.declare_parameter('model_path', '')
        self.declare_parameter('camera_index', 0)
        self.declare_parameter('smoothing_alpha', 0.15)

        self.arm_topic = str(self.get_parameter('arm_topic').value)
        self.gripper_topic = str(self.get_parameter('gripper_topic').value)
        self.mirror_to_local_controller = bool(self.get_parameter('mirror_to_local_controller').value)
        self.local_arm_topic = str(self.get_parameter('local_arm_topic').value)
        self.camera_index = int(self.get_parameter('camera_index').value)

        # Publishers for controllers
        self.arm_pub = self.create_publisher(JointTrajectory, self.arm_topic, 10)
        self.gripper_pub = self.create_publisher(JointTrajectory, self.gripper_topic, 10)
        self.local_arm_pub = None
        if self.mirror_to_local_controller:
            self.local_arm_pub = self.create_publisher(JointTrajectory, self.local_arm_topic, 10)
        
        # Mapping ranges (Tune these based on URDF and hardware limits)
        self.link_1_range = [-3.14, 3.14]  # Base rotation (Expanded for full workspace access)
        self.link_2_range = [-1.0, 1.0]    # Shoulder
        self.link_3_range = [-1.0, 1.0]    # Elbow
        self.link_4_range = [-1.57, 1.57]  # Wrist flex
        self.link_5_range = [-1.57, 1.57]  # Wrist twist
        # Calibrated gripper bounds: open=0.0 rad, close=-1.0472 rad (~60 deg hardware clamp)
        self.link_6_range = [-1.0472, 0.0]
        
        # MediaPipe Setup
        model_path = self._resolve_model_path()
        if model_path is None:
            raise RuntimeError(
                "hand_landmarker.task not found. Pass --ros-args -p model_path:=<path_to_task_file>."
            )

        self.get_logger().info(f"Using hand landmarker model: {model_path}")

        base_options = mp.tasks.BaseOptions(model_asset_path=model_path)
        options = mp.tasks.vision.HandLandmarkerOptions(
            base_options=base_options,
            num_hands=1,
            min_hand_detection_confidence=0.5,
            min_hand_presence_confidence=0.5,
            min_tracking_confidence=0.5
        )
        self.landmarker = mp.tasks.vision.HandLandmarker.create_from_options(options)

        # Video Capture
        self.cap = cv2.VideoCapture(self.camera_index)
        if not self.cap.isOpened():
            raise RuntimeError(f"Cannot open webcam at camera_index={self.camera_index}")
            
        self.get_logger().info("Gesture Control Node initialized.")
        self.get_logger().info(
            f"Publishing arm -> {self.arm_topic}, gripper -> {self.gripper_topic}, "
            f"mirror_to_local_controller={self.mirror_to_local_controller}"
        )
        
        # Smoothing variables
        self.current_arm_angles = [0.0, 0.0, 0.0, 0.0, 0.0]
        self.current_gripper_angle = 0.0
        self.alpha = float(self.get_parameter('smoothing_alpha').value)
        self.alpha = self.clamp(self.alpha, 0.01, 1.0)

        self.publish_count = 0
        self.last_diag_publish_count = 0
        self.seen_hand_once = False

        # Create ROS Timer for main loop
        self.timer = self.create_timer(0.05, self.process_frame)
        self.diag_timer = self.create_timer(2.0, self.log_diagnostics)

    def _resolve_model_path(self):
        user_model = str(self.get_parameter('model_path').value).strip()
        candidates = []

        if user_model:
            candidates.append(Path(user_model))

        env_model = os.environ.get('HAND_LANDMARKER_PATH', '').strip()
        if env_model:
            candidates.append(Path(env_model))

        # Workspace default used in this repository.
        candidates.append(Path('/home/natraj/file/archive/hand_gesture_demo/hand_landmarker.task'))

        for candidate in candidates:
            if candidate.exists() and candidate.is_file():
                return str(candidate)
        return None

    def clamp(self, value, min_v, max_v):
        return max(min_v, min(value, max_v))

    def map_range(self, value, in_min, in_max, out_min, out_max):
        return (value - in_min) * (out_max - out_min) / (in_max - in_min) + out_min

    def publish_arm_trajectory(self, angles):
        msg = JointTrajectory()
        msg.joint_names = ['link_1', 'link_2', 'link_3', 'link_4', 'link_5']
        point = JointTrajectoryPoint()
        point.positions = angles
        point.time_from_start.sec = 0
        point.time_from_start.nanosec = 100_000_000 # 0.1 seconds target duration
        msg.points.append(point)
        self.arm_pub.publish(msg)
        if self.local_arm_pub is not None:
            self.local_arm_pub.publish(msg)

    def publish_gripper_trajectory(self, angle):
        msg = JointTrajectory()
        msg.joint_names = ['link_6']
        point = JointTrajectoryPoint()
        point.positions = [angle]
        point.time_from_start.sec = 0
        point.time_from_start.nanosec = 100_000_000
        msg.points.append(point)
        self.gripper_pub.publish(msg)

    def log_diagnostics(self):
        arm_subs = self.arm_pub.get_subscription_count()
        grip_subs = self.gripper_pub.get_subscription_count()
        local_subs = self.local_arm_pub.get_subscription_count() if self.local_arm_pub is not None else 0
        delta_published = self.publish_count - self.last_diag_publish_count
        self.last_diag_publish_count = self.publish_count

        self.get_logger().info(
            f"diag: published_last_2s={delta_published}, arm_subs={arm_subs}, "
            f"gripper_subs={grip_subs}, local_arm_subs={local_subs}, hand_seen={self.seen_hand_once}"
        )

        if arm_subs == 0 and local_subs == 0:
            self.get_logger().warn(
                "No subscriber detected on arm command topics. Make sure controller manager "
                "and arm trajectory controller are running."
            )

    def process_frame(self):
        if not self.cap.isOpened():
            return

        ret, frame = self.cap.read()
        if not ret:
            return

        # Flip for mirror and prep for Mediapipe
        frame = cv2.flip(frame, 1)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)

        result = self.landmarker.detect(mp_image)

        target_arm_angles = self.current_arm_angles.copy()
        target_gripper_angle = self.current_gripper_angle

        if result.hand_landmarks:
            hand_landmarks = result.hand_landmarks[0]
            self.seen_hand_once = True
            
            wrist = hand_landmarks[0]
            index_mcp = hand_landmarks[5]
            index_tip = hand_landmarks[8]
            thumb_tip = hand_landmarks[4]
            pinky_mcp = hand_landmarks[17]

            # 1. Base Joint (link_1)
            # Reduced X-bounds so a smaller hand sweep provides full workspace reach.
            base_angle = self.map_range(wrist.x, 0.3, 0.7, self.link_1_range[1], self.link_1_range[0])
            target_arm_angles[0] = self.clamp(base_angle, self.link_1_range[0], self.link_1_range[1])

            # 2. Shoulder & Elbow (link_2 & link_3)
            # wrist.z is relative and stays near 0. Instead, compute apparent hand size
            # (distance from wrist to index_mcp) as a reliable proxy for physical depth.
            hand_size = math.hypot(wrist.x - index_mcp.x, wrist.y - index_mcp.y)
            
            vertical_component = self.map_range(wrist.y, 0.2, 0.8, self.link_2_range[1], self.link_2_range[0])
            # Larger hand_size means hand is close (move forward), smaller means hand is far (move backward)
            depth_component = self.map_range(hand_size, 0.08, 0.25, self.link_2_range[0], self.link_2_range[1])
            
            # Blend depth and vertical: prioritize apparent depth for forward/back motion
            shoulder_angle = (0.7 * depth_component) + (0.3 * vertical_component)
            target_arm_angles[1] = self.clamp(shoulder_angle, self.link_2_range[0], self.link_2_range[1])
            # Elbow follows shoulder with opposite sign but reduced magnitude
            target_arm_angles[2] = self.clamp(-shoulder_angle * 0.5, self.link_3_range[0], self.link_3_range[1])

            # 3. Wrist flex (link_4)
            # Fix inversion: use index_mcp relative to wrist so upward wrist tilts make the robot
            # move in the same intuitive direction.
            hand_tilt_y = index_mcp.y - wrist.y
            wrist_flex = self.map_range(hand_tilt_y, -0.3, 0.3, self.link_4_range[0], self.link_4_range[1])
            target_arm_angles[3] = self.clamp(wrist_flex, self.link_4_range[0], self.link_4_range[1])

            # 4. Wrist twist (link_5) - derive from hand rotation (index -> pinky vector)
            # Compute roll-like angle from the index->pinky vector projected to image plane.
            vec_x = index_mcp.x - pinky_mcp.x
            vec_y = index_mcp.y - pinky_mcp.y
            hand_roll = math.atan2(vec_y, vec_x)
            # Map roll to wrist twist joint range
            wrist_twist = self.map_range(hand_roll, -math.pi/2, math.pi/2, self.link_5_range[0], self.link_5_range[1])
            target_arm_angles[4] = self.clamp(wrist_twist, self.link_5_range[0], self.link_5_range[1])

            # 5. Gripper (link_6)
            dist = math.hypot(thumb_tip.x - index_tip.x, thumb_tip.y - index_tip.y)
            # Pinch mapping aligned with hardware calibration:
            # small pinch distance => close (negative), large pinch distance => open (0.0)
            gripper_val = self.map_range(dist, 0.05, 0.15, self.link_6_range[0], self.link_6_range[1])
            target_gripper_angle = self.clamp(gripper_val, self.link_6_range[0], self.link_6_range[1])

            # Visuals
            annotated_image = np.copy(rgb_frame)
            mp_drawing.draw_landmarks(
                annotated_image, hand_landmarks, mp_hands.HAND_CONNECTIONS,
                mp_drawing_styles.get_default_hand_landmarks_style(),
                mp_drawing_styles.get_default_hand_connections_style()
            )
            display_frame = cv2.cvtColor(annotated_image, cv2.COLOR_RGB2BGR)

            cv2.putText(display_frame, f"Pinch: {dist:.3f}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 0), 2)
            cv2.putText(display_frame, f"Arm J1: {target_arm_angles[0]:.2f}", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 0), 2)
        else:
            display_frame = frame

        # Apply exponential smoothing
        for i in range(5):
            self.current_arm_angles[i] = (self.alpha * target_arm_angles[i]) + ((1 - self.alpha) * self.current_arm_angles[i])
        self.current_gripper_angle = (self.alpha * target_gripper_angle) + ((1 - self.alpha) * self.current_gripper_angle)

        # Publish
        self.publish_arm_trajectory(self.current_arm_angles)
        self.publish_gripper_trajectory(self.current_gripper_angle)
        self.publish_count += 1

        cv2.imshow('Robot Arm Gesture Control', display_frame)
        cv2.waitKey(1)

def main(args=None):
    rclpy.init(args=args)
    node = None
    try:
        node = GestureControlNode()
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    except Exception as e:
        if node is not None:
            node.get_logger().error(f'Fatal initialization error: {e}')
        else:
            print(f'Fatal initialization error: {e}')
    finally:
        if node is not None and hasattr(node, 'cap') and node.cap is not None:
            node.cap.release()
        cv2.destroyAllWindows()
        if node is not None:
            node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()