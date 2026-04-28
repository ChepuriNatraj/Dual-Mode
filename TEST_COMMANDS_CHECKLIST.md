# Robotic Arm Test Commands Checklist

This file keeps all test commands in one place.
Run the sections in order.

## 0) Terminal Setup (run in every new terminal)
```bash
cd /home/natraj/file
source /opt/ros/jazzy/setup.bash
source install/setup.bash
```

## 1) Build Workspace
```bash
cd /home/natraj/file
source /opt/ros/jazzy/setup.bash
colcon build --symlink-install
source install/setup.bash
```

## 2) Full Bring-up (MoveIt + Gazebo Simulation)
```bash
ros2 launch robot_arm_moveit2 moveit_gazebo.launch.py
```

## 2B) Full Bring-up (MoveIt + Real Hardware via Serial)
Use this when testing the physical arm/gripper. Do NOT use Gazebo launch for real servo motion checks.
```bash
ros2 launch robot_arm_moveit2 demo.launch.py
```

### 2C) Flash Production Firmware (required before 2B)
Do this if you previously flashed any test sketch from `firmware/tests/`.
```bash
cd /home/natraj/file
export ARDUINO_DATA_DIR="/media/natraj/ARDUINO_USB/arduino_esp32_env/data"
arduino-cli compile --fqbn esp32:esp32:esp32 /home/natraj/file/src/robot_arm_hardware/firmware --config-file "$ARDUINO_DATA_DIR/arduino-cli.yaml"
arduino-cli upload -p /dev/ttyUSB0 --fqbn esp32:esp32:esp32 /home/natraj/file/src/robot_arm_hardware/firmware --config-file "$ARDUINO_DATA_DIR/arduino-cli.yaml"
```

## 3) Basic Health Checks
```bash
ros2 control list_controllers
ros2 control list_hardware_interfaces
ros2 topic hz /joint_states
ros2 topic list | grep joint_trajectory
```

For gripper testing, verify this exists and is available:
```bash
ros2 control list_hardware_interfaces | grep link_6
```

## 4) Manual Arm Trajectory Test
```bash
ros2 topic pub --once /arm_controller/joint_trajectory trajectory_msgs/msg/JointTrajectory "{joint_names: ['link_1','link_2','link_3','link_4','link_5'], points: [{positions: [0.5,0.3,0.2,0.1,0.0], time_from_start: {sec: 2, nanosec: 0}}]}"
```

Return home:
```bash
ros2 topic pub --once /arm_controller/joint_trajectory trajectory_msgs/msg/JointTrajectory "{joint_names: ['link_1','link_2','link_3','link_4','link_5'], points: [{positions: [0.0,0.0,0.0,0.0,0.0], time_from_start: {sec: 2, nanosec: 0}}]}"
```

## 5) Gripper Test
Open:
```bash
ros2 topic pub --once /gripper_controller/joint_trajectory trajectory_msgs/msg/JointTrajectory "{joint_names: ['link_6'], points: [{positions: [0.0], time_from_start: {sec: 1, nanosec: 0}}]}"
```

Close:
```bash
ros2 topic pub --once /gripper_controller/joint_trajectory trajectory_msgs/msg/JointTrajectory "{joint_names: ['link_6'], points: [{positions: [-0.8727], time_from_start: {sec: 1, nanosec: 0}}]}"
```

Hard-close ceiling (only for edge validation):
```bash
ros2 topic pub --once /gripper_controller/joint_trajectory trajectory_msgs/msg/JointTrajectory "{joint_names: ['link_6'], points: [{positions: [-1.0472], time_from_start: {sec: 1, nanosec: 0}}]}"
```

## 6) Local Gesture Control Test
```bash
ros2 run robot_arm_gesture gesture_node
```

Optional monitor:
```bash
ros2 topic hz /arm_controller/joint_trajectory
ros2 topic hz /gripper_controller/joint_trajectory
```

## 7) Remote MQTT Bridge Test
Run bridge:
```bash
ros2 run robot_arm_remote mqtt_bridge_node
```

Send one MQTT message from another terminal:
```bash
mosquitto_pub -h broker.hivemq.com -p 1883 -t natraj/robot_arm/teleop/target_state -m '{"arm_angles":[0.3,0.2,0.1,0.0,0.0],"gripper_angle":0.4}'
```

If mosquitto is missing:
```bash
sudo apt update
sudo apt install -y mosquitto-clients
```

## 8) Mode Manager Routing Test
Run mode manager:
```bash
ros2 run robot_arm_mode_manager mode_manager_node
```

Run remote bridge remapped to remote input stream:
```bash
ros2 run robot_arm_remote mqtt_bridge_node --ros-args -r /arm_controller/joint_trajectory:=/remote_controller/joint_trajectory
```

Switch mode to REMOTE:
```bash
ros2 topic pub --once /system_mode std_msgs/msg/String "{data: 'REMOTE'}"
```

Send test command:
```bash
mosquitto_pub -h broker.hivemq.com -p 1883 -t natraj/robot_arm/teleop/target_state -m '{"arm_angles":[0.2,0.1,0.0,0.0,0.0],"gripper_angle":0.3}'
```

## 9) Remote Timeout Safety Test (3s watchdog)
After step 8, stop publishing MQTT messages for more than 3 seconds.

Watch output from mode manager terminal for timeout fallback.

Optional check:
```bash
ros2 topic echo /arm_controller/joint_trajectory
```

## 10) Vision + Sorting Test
```bash
ros2 launch robot_arm_vision sorting.launch.py
```

Monitors:
```bash
ros2 topic echo /target_pose
ros2 topic hz /target_pose
```

## 11) Direct Hardware Serial Test (ESP32/PCA9685)
```bash
python3 /home/natraj/file/src/robot_arm_hardware/calibration_tester.py
```

Example inputs when prompted:
```text
90,90,90,90,90,90
45,30,60,90,120,20
```

## 12) 50-Cycle Stress Test
```bash
ros2 run robot_arm_hardware stress_tester.py
```

## 13) Useful Diagnostics
```bash
ros2 node list
ros2 topic list
ros2 topic hz /arm_controller/joint_trajectory
ros2 topic hz /gripper_controller/joint_trajectory
ros2 control list_controllers
```

## 14) Per-Servo Calibration and Limit Validation
Use these after full bring-up is running.
For physical gripper mismatch debugging, run Section 2B (hardware backend), not Section 2 (Gazebo).

### 14.1 Joint-by-joint sweep (arm joints)
Sweep each joint separately while keeping the others at zero.

J1 sweep:
```bash
ros2 topic pub --once /arm_controller/joint_trajectory trajectory_msgs/msg/JointTrajectory "{joint_names: ['link_1','link_2','link_3','link_4','link_5'], points: [{positions: [-1.0,0.0,0.0,0.0,0.0], time_from_start: {sec: 2, nanosec: 0}}, {positions: [0.0,0.0,0.0,0.0,0.0], time_from_start: {sec: 4, nanosec: 0}}, {positions: [1.0,0.0,0.0,0.0,0.0], time_from_start: {sec: 6, nanosec: 0}}, {positions: [0.0,0.0,0.0,0.0,0.0], time_from_start: {sec: 8, nanosec: 0}}]}"
```

J2 sweep:
```bash
ros2 topic pub --once /arm_controller/joint_trajectory trajectory_msgs/msg/JointTrajectory "{joint_names: ['link_1','link_2','link_3','link_4','link_5'], points: [{positions: [0.0,-0.8,0.0,0.0,0.0], time_from_start: {sec: 2, nanosec: 0}}, {positions: [0.0,0.0,0.0,0.0,0.0], time_from_start: {sec: 4, nanosec: 0}}, {positions: [0.0,0.8,0.0,0.0,0.0], time_from_start: {sec: 6, nanosec: 0}}, {positions: [0.0,0.0,0.0,0.0,0.0], time_from_start: {sec: 8, nanosec: 0}}]}"
```

J3 sweep:
```bash
ros2 topic pub --once /arm_controller/joint_trajectory trajectory_msgs/msg/JointTrajectory "{joint_names: ['link_1','link_2','link_3','link_4','link_5'], points: [{positions: [0.0,0.0,-0.8,0.0,0.0], time_from_start: {sec: 2, nanosec: 0}}, {positions: [0.0,0.0,0.0,0.0,0.0], time_from_start: {sec: 4, nanosec: 0}}, {positions: [0.0,0.0,0.8,0.0,0.0], time_from_start: {sec: 6, nanosec: 0}}, {positions: [0.0,0.0,0.0,0.0,0.0], time_from_start: {sec: 8, nanosec: 0}}]}"
```

J4 sweep:
```bash
ros2 topic pub --once /arm_controller/joint_trajectory trajectory_msgs/msg/JointTrajectory "{joint_names: ['link_1','link_2','link_3','link_4','link_5'], points: [{positions: [0.0,0.0,0.0,-0.8,0.0], time_from_start: {sec: 2, nanosec: 0}}, {positions: [0.0,0.0,0.0,0.0,0.0], time_from_start: {sec: 4, nanosec: 0}}, {positions: [0.0,0.0,0.0,0.8,0.0], time_from_start: {sec: 6, nanosec: 0}}, {positions: [0.0,0.0,0.0,0.0,0.0], time_from_start: {sec: 8, nanosec: 0}}]}"
```

J5 sweep:
```bash
ros2 topic pub --once /arm_controller/joint_trajectory trajectory_msgs/msg/JointTrajectory "{joint_names: ['link_1','link_2','link_3','link_4','link_5'], points: [{positions: [0.0,0.0,0.0,0.0,-1.0], time_from_start: {sec: 2, nanosec: 0}}, {positions: [0.0,0.0,0.0,0.0,0.0], time_from_start: {sec: 4, nanosec: 0}}, {positions: [0.0,0.0,0.0,0.0,1.0], time_from_start: {sec: 6, nanosec: 0}}, {positions: [0.0,0.0,0.0,0.0,0.0], time_from_start: {sec: 8, nanosec: 0}}]}"
```

### 14.2 Home-offset match (real arm vs RViz)
Command exact home and verify both physical arm and RViz reach the same neutral pose.
```bash
ros2 topic pub --once /arm_controller/joint_trajectory trajectory_msgs/msg/JointTrajectory "{joint_names: ['link_1','link_2','link_3','link_4','link_5'], points: [{positions: [0.0,0.0,0.0,0.0,0.0], time_from_start: {sec: 3, nanosec: 0}}]}"
ros2 topic pub --once /gripper_controller/joint_trajectory trajectory_msgs/msg/JointTrajectory "{joint_names: ['link_6'], points: [{positions: [0.0], time_from_start: {sec: 2, nanosec: 0}}]}"
```

### 14.3 Gripper inversion and open/close consistency
If inversion is correct: command direction should always map to the same open/close behavior.

First, monitor commanded gripper trajectory:
```bash
ros2 topic echo /gripper_controller/joint_trajectory
```

Then test negative-to-positive sweep in ROS units (radians):
```bash
ros2 topic pub --once /gripper_controller/joint_trajectory trajectory_msgs/msg/JointTrajectory "{joint_names: ['link_6'], points: [{positions: [-1.0], time_from_start: {sec: 2, nanosec: 0}}]}"
sleep 2
ros2 topic pub --once /gripper_controller/joint_trajectory trajectory_msgs/msg/JointTrajectory "{joint_names: ['link_6'], points: [{positions: [-0.5], time_from_start: {sec: 2, nanosec: 0}}]}"
sleep 2
ros2 topic pub --once /gripper_controller/joint_trajectory trajectory_msgs/msg/JointTrajectory "{joint_names: ['link_6'], points: [{positions: [1.0], time_from_start: {sec: 2, nanosec: 0}}]}"
sleep 2
ros2 topic pub --once /gripper_controller/joint_trajectory trajectory_msgs/msg/JointTrajectory "{joint_names: ['link_6'], points: [{positions: [0.0], time_from_start: {sec: 2, nanosec: 0}}]}"
sleep 2
ros2 topic pub --once /gripper_controller/joint_trajectory trajectory_msgs/msg/JointTrajectory "{joint_names: ['link_6'], points: [{positions: [0.5], time_from_start: {sec: 2, nanosec: 0}}]}"
sleep 2
ros2 topic pub --once /gripper_controller/joint_trajectory trajectory_msgs/msg/JointTrajectory "{joint_names: ['link_6'], points: [{positions: [1.0], time_from_start: {sec: 2, nanosec: 0}}]}"
```

Direct hardware-only gripper test (bypass ROS mapping):
```bash
python3 /home/natraj/file/src/robot_arm_hardware/calibration_tester.py
```

At the prompt, change only the 6th value (J5) to test pure servo behavior:
```text
45,0,0,45,90,0
45,0,0,45,90,45
45,0,0,45,90,90
45,0,0,45,90,135
```

If direct serial behaves correctly but ROS gripper does not, the mismatch is in ROS rad->degree mapping/inversion.

Optional: quick mapping sanity check with current conversion logic:
```bash
python3 - <<'PY'
import math
vals=[-1.0,-0.5,0.0,0.5,1.0]
for v in vals:
	deg = -(v*180.0/math.pi) + 0.0
	deg = max(0.0,min(180.0,deg))
	print(f"rad={v:+.2f} -> deg={deg:.1f}")
PY
```

### 14.4 Hard-stop collision safety check (command extremes)
Run conservative near-extreme values first. If safe, gradually increase.
```bash
ros2 topic pub --once /arm_controller/joint_trajectory trajectory_msgs/msg/JointTrajectory "{joint_names: ['link_1','link_2','link_3','link_4','link_5'], points: [{positions: [1.2,0.9,0.8,0.8,1.2], time_from_start: {sec: 4, nanosec: 0}}]}"
sleep 3
ros2 topic pub --once /arm_controller/joint_trajectory trajectory_msgs/msg/JointTrajectory "{joint_names: ['link_1','link_2','link_3','link_4','link_5'], points: [{positions: [-1.2,-0.9,-0.8,-0.8,-1.2], time_from_start: {sec: 4, nanosec: 0}}]}"
sleep 3
ros2 topic pub --once /arm_controller/joint_trajectory trajectory_msgs/msg/JointTrajectory "{joint_names: ['link_1','link_2','link_3','link_4','link_5'], points: [{positions: [0.0,0.0,0.0,0.0,0.0], time_from_start: {sec: 3, nanosec: 0}}]}"
```

Pass criteria:
- Motion is smooth and repeatable for each individual joint sweep.
- Physical joint direction matches expected RViz direction.
- Home command consistently lands at the same physical neutral pose.
- Gripper open/close direction is stable across repeated cycles and changes for both negative and positive command tests.
- No mechanical binding, clicking, or hard-stop impact at tested near-extreme values.

## Notes
- Run Section 0 in each new terminal before ROS commands.
- Keep one terminal for bring-up logs and use extra terminals for test commands.
- Current mode manager routes arm trajectories only. Gripper is not multiplexed by mode manager yet.
