import rclpy
from rclpy.node import Node
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint

import os
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

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
        
        # Publishers for controllers
        self.arm_pub = self.create_publisher(JointTrajectory, '/arm_controller/joint_trajectory', 10)
        self.gripper_pub = self.create_publisher(JointTrajectory, '/gripper_controller/joint_trajectory', 10)
        
        # Mapping ranges (Tune these based on URDF and hardware limits)
        self.link_1_range = [-1.57, 1.57]  # Base rotation
        self.link_2_range = [-1.0, 1.0]    # Shoulder
        self.link_3_range = [-1.0, 1.0]    # Elbow
        self.link_4_range = [-1.57, 1.57]  # Wrist flex
        self.link_5_range = [-1.57, 1.57]  # Wrist twist
        self.link_6_range = [-1.0, 1.0]    # Gripper bounds
        
        # MediaPipe Setup
        script_dir = os.path.dirname(os.path.abspath(__file__))
        model_path = os.path.join(script_dir, "hand_landmarker.task")
        if not os.path.exists(model_path):
            self.get_logger().error(f"Model file not found at {model_path}")
            return

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
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            self.get_logger().error("Cannot open webcam")
            return
            
        self.get_logger().info("Gesture Control Node initialized.")
        
        # Smoothing variables
        self.current_arm_angles = [0.0, 0.0, 0.0, 0.0, 0.0]
        self.current_gripper_angle = 0.0
        self.alpha = 0.7  # Increased from 0.15 -> 0.7 for much faster & more responsive movement

        # Create ROS Timer for main loop
        self.timer = self.create_timer(0.033, self.process_frame) # Increased from 20Hz (0.05) to ~30Hz (0.033)

    def clamp(self, value, min_v, max_v):
        return max(min_v, min(value, max_v))

    def map_range(self, value, in_min, in_max, out_min, out_max):
        return (value - in_min) * (out_max - out_min) / (in_max - in_min) + out_min

    def publish_arm_trajectory(self, angles):
        msg = JointTrajectory()
        msg.joint_names = ['link_1', 'link_2', 'link_3', 'link_4', 'link_5']
        point = JointTrajectoryPoint()
        point.positions = [float(a) for a in angles]
        point.time_from_start.sec = 0
        point.time_from_start.nanosec = 40_000_000 # 0.04 seconds target execution for fast snap
        msg.points.append(point)
        self.arm_pub.publish(msg)

    def publish_gripper_trajectory(self, angle):
        msg = JointTrajectory()
        msg.joint_names = ['link_6']
        point = JointTrajectoryPoint()
        point.positions = [float(angle)]
        point.time_from_start.sec = 0
        point.time_from_start.nanosec = 40_000_000 # 0.04 seconds target execution for fast snap
        msg.points.append(point)
        self.gripper_pub.publish(msg)

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
            
            wrist = hand_landmarks[0]
            index_mcp = hand_landmarks[5]
            index_tip = hand_landmarks[8]
            thumb_tip = hand_landmarks[4]

            # Anchor & Rotation Points
            focus_point = index_tip  # Use the index fingertip as the steering point
            middle_mcp = hand_landmarks[9]
            pinky_mcp = hand_landmarks[17]

            # 1. Base Joint (link_1) - Track horizontal movement of focus point
            base_angle = self.map_range(focus_point.x, 0.2, 0.8, self.link_1_range[1], self.link_1_range[0])
            target_arm_angles[0] = self.clamp(base_angle, self.link_1_range[0], self.link_1_range[1])

            # 2 & 3. Shoulder & Elbow (link_2 & link_3) - Track vertical movement of focus point
            shoulder_angle = self.map_range(focus_point.y, 0.2, 0.8, self.link_2_range[1], self.link_2_range[0])
            target_arm_angles[1] = self.clamp(shoulder_angle, self.link_2_range[0], self.link_2_range[1])
            target_arm_angles[2] = self.clamp(-shoulder_angle * 0.7, self.link_3_range[0], self.link_3_range[1])

            # 4. Wrist Flex (link_4) - Driven by the pitch (forward/back tilt) of your hand
            hand_pitch = wrist.y - middle_mcp.y
            wrist_flex = self.map_range(hand_pitch, -0.05, 0.25, self.link_4_range[0], self.link_4_range[1])
            target_arm_angles[3] = self.clamp(wrist_flex, self.link_4_range[0], self.link_4_range[1])
            
            # 5. Wrist Twist (link_5) - Driven by the roll (side-to-side twist) of your wrist
            # Difference in Y between index knuckle and pinky knuckle gives the twist
            hand_roll = pinky_mcp.y - index_mcp.y
            wrist_twist = self.map_range(hand_roll, -0.15, 0.15, self.link_5_range[1], self.link_5_range[0])
            target_arm_angles[4] = self.clamp(wrist_twist, self.link_5_range[0], self.link_5_range[1])

            # 6. Gripper (link_6) mapped from Thumb to Index finger distance
            dist = math.hypot(thumb_tip.x - index_tip.x, thumb_tip.y - index_tip.y)
            gripper_val = self.map_range(dist, 0.03, 0.15, -1.0, 1.0)
            target_gripper_angle = self.clamp(gripper_val, -1.0, 1.0)

            # Visuals
            annotated_image = np.copy(rgb_frame)
            mp_drawing.draw_landmarks(
                annotated_image, hand_landmarks, mp_hands.HAND_CONNECTIONS,
                mp_drawing_styles.get_default_hand_landmarks_style(),
                mp_drawing_styles.get_default_hand_connections_style()
            )
            display_frame = cv2.cvtColor(annotated_image, cv2.COLOR_RGB2BGR)

            # Draw a highly visible circle at the "Focus Point"
            fp_x = int(focus_point.x * display_frame.shape[1])
            fp_y = int(focus_point.y * display_frame.shape[0])
            cv2.circle(display_frame, (fp_x, fp_y), 12, (0, 0, 255), -1) # Red Target Dot
            cv2.putText(display_frame, "TARGET", (fp_x + 15, fp_y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

            cv2.putText(display_frame, f"Roll: {hand_roll:.2f} | Pitch: {hand_pitch:.2f}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            cv2.putText(display_frame, f"Gripper Dist: {dist:.3f}", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            cv2.putText(display_frame, f"Twist(J5): {target_arm_angles[4]:.2f}", (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
        else:
            display_frame = frame

        # Apply exponential smoothing
        for i in range(5):
            self.current_arm_angles[i] = (self.alpha * target_arm_angles[i]) + ((1 - self.alpha) * self.current_arm_angles[i])
        self.current_gripper_angle = (self.alpha * target_gripper_angle) + ((1 - self.alpha) * self.current_gripper_angle)

        # Publish
        self.publish_arm_trajectory(self.current_arm_angles)
        self.publish_gripper_trajectory(self.current_gripper_angle)

        cv2.imshow('Robot Arm Gesture Control', display_frame)
        cv2.waitKey(1)

def main(args=None):
    rclpy.init(args=args)
    node = GestureControlNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.cap.release()
        cv2.destroyAllWindows()
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()