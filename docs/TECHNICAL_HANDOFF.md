# Technical Handoff: Dual-Mode Vision-Guided Robotic Arm

Last validated: 2026-05-01
Primary intent: hardware deployment and code-level runtime understanding.

## 1) System Purpose and Scope

This repository implements a ROS 2 Jazzy robotic arm stack with three control ingress paths:
- AUTONOMOUS: ESP32-CAM -> vision -> planning -> trajectory execution.
- LOCAL: webcam hand tracking (MediaPipe) -> trajectory execution.
- REMOTE: MQTT payloads -> trajectory execution.

Core goals:
- End-to-end pick and place in autonomous mode using YOLOv8 detections.
- Human override/control paths for local and remote operation.
- Common ros2_control backend for both simulation and physical arm execution.

## 2) Active Package Map (src)

1. robot_arm_description
- Robot geometry and visual/collision model.
- Key file: urdf/robotic_arm.xacro

2. robot_arm_gazebo
- Gazebo launch and simulation bridge.
- Key launch: launch/gazebo_rviz.launch.py

3. robot_arm_moveit2
- MoveIt2 planning configs and launch workflows.
- Key launch: launch/demo.launch.py, launch/moveit_gazebo.launch.py
- Key config: config/robotic_arm.urdf.xacro, config/ros2_controllers.yaml

4. robot_arm_hardware
- C++ ros2_control system plugin with serial write path.
- Key file: src/system_interface.cpp
- Key launch: launch/hardware_gesture.launch.py

5. robot_arm_vision
- ESP32 camera bridge, vision target publisher, sorting planner.
- Key launch: launch/hardware_sorting.launch.py
- Key nodes: robot_arm_vision/esp32_camera_bridge.py, robot_arm_vision/vision_node.py, robot_arm_vision/sorting_planner_node.py

6. robot_arm_gesture
- MediaPipe hand landmark control node.
- Key node: robot_arm_gesture/gesture_node.py

7. robot_arm_remote
- MQTT bridge node for internet teleoperation.
- Key node: robot_arm_remote/mqtt_bridge_node.py

8. robot_arm_mode_manager
- Arm command arbitration between autonomous/local/remote sources.
- Key node: robot_arm_mode_manager/mode_manager_node.py

## 3) Launch Matrix and What Each Launch Actually Starts

A. Autonomous hardware launch
- Command:
  ros2 launch robot_arm_vision hardware_sorting.launch.py serial_port:=/dev/ttyUSB0 baud_rate:=115200 esp32_camera_url:=http://<ip>:81/stream
- Starts:
  - robot_state_publisher
  - controller_manager ros2_control_node
  - controller spawners: joint_state_broadcaster, arm_controller, gripper_controller
  - mode_manager_node
  - esp32_camera_bridge
  - vision_node
  - sorting_planner_node (arm trajectory remapped to /auto_controller/joint_trajectory)

B. Hardware gesture launch
- Command:
  ros2 launch robot_arm_hardware hardware_gesture.launch.py serial_port:=/dev/ttyUSB0
- Starts:
  - robot_state_publisher
  - controller_manager ros2_control_node
  - controller spawners: joint_state_broadcaster, arm_controller, gripper_controller
  - gesture_node (optional through enable_gesture argument)

C. Simulation planning
- Command:
  ros2 launch robot_arm_moveit2 demo.launch.py
- MoveIt2 + RViz planner stack (non-hardware workflow).

D. Simulation physics + MoveIt
- Command:
  ros2 launch robot_arm_moveit2 moveit_gazebo.launch.py
- Gazebo + delayed move_group + RViz with sim time.

## 4) Runtime Topic Contracts (Code-Verified)

### 4.1 Autonomous pipeline

1. Camera ingestion
- Node: esp32_camera_bridge
- Input: HTTP MJPEG stream (esp32_url parameter)
- Publishes:
  - /camera/image_raw (sensor_msgs/Image)
  - /camera/camera_info (sensor_msgs/CameraInfo)

2. Vision target generation
- Node: vision_node
- Subscribes:
  - /camera/image_raw
  - /camera/camera_info
- Publishes:
  - /target_pose (geometry_msgs/PoseStamped, frame_id=world)

3. Planning and trajectory publication
- Node: sorting_planner_node
- Subscribes:
  - /target_pose
- Publishes:
  - /auto_controller/joint_trajectory (after launch remap from /arm_controller/joint_trajectory)
  - /auto_controller/gripper_trajectory (declared publisher, currently not used in execution path)

4. Mode arbitration
- Node: mode_manager_node
- Subscribes:
  - /auto_controller/joint_trajectory
  - /local_controller/joint_trajectory
  - /remote_controller/joint_trajectory
  - /system_mode (std_msgs/String)
- Publishes:
  - /arm_controller/joint_trajectory

### 4.2 Local gesture path

- Node: gesture_node
- Publishes:
  - /arm_controller/joint_trajectory (default)
  - /gripper_controller/joint_trajectory (default)
  - optional mirror: /local_controller/joint_trajectory

Note:
- By default mirror_to_local_controller is false, so mode_manager is bypassed unless launch parameters are changed.

### 4.3 Remote MQTT path

- Node: mqtt_bridge_node
- MQTT input topic default: natraj/robot_arm/teleop/target_state
- Publishes:
  - /arm_controller/joint_trajectory
  - /gripper_controller/joint_trajectory
- Telemetry topic default: natraj/robot_arm/teleop/state

Note:
- Current node publishes directly to controller topics; mode_manager remote arbitration path is not used by default.

## 5) Control and Hardware Execution Path

Trajectory flow to hardware:
1. A node publishes JointTrajectory to arm_controller/gripper_controller topics.
2. ros2_control controllers consume those trajectories.
3. robot_arm_hardware system plugin exports position command/state interfaces.
4. Plugin write() converts radians to degrees with per-joint home offsets.
5. Degrees are clamped to safety windows and serialized as comma-separated values.
6. Command string is written to serial device.

Relevant implementation details from system_interface.cpp:
- Home offsets used: [45, 0, 0, 45, 90, 0].
- Gripper conversion is inverted and clamped to [0, 60] deg.
- Other joints clamped to [0, 180] deg.
- read() mirrors commands as state (open-loop model, no physical encoder feedback).

## 6) Parameter Surface (Most Operationally Important)

Autonomous launch args (hardware_sorting.launch.py):
- serial_port (default /dev/ttyUSB0)
- baud_rate (default 115200)
- esp32_camera_url (default http://192.168.1.100:81/stream)
- camera_frame (default camera_link)

Camera bridge parameters:
- fx, fy, cx, cy defaults are static placeholders (500, 500, 320, 240).
- frame_width/frame_height default 640x480.

Vision parameters currently set in launch:
- camera_height=0.8
- workspace_z=0.02
- world bounds x:[0.15,0.45], y:[-0.25,0.25]

Sorting planner parameters set in launch:
- pre_grasp_hover, grasp_offset, lift_offset

Important caveat:
- sorting_planner_node currently does not declare/read these parameters; code uses hardcoded values.

## 7) Canonical Deployment Runbook (Hardware)

1. Build selected packages:
- scripts/build_autonomous_sorting.sh

2. Source workspace:
- source install/setup.bash

3. Verify devices and network:
- main controller at /dev/ttyUSB0 (or override serial_port)
- ESP32-CAM stream reachable at http://<ip>:81/stream

4. Launch autonomous stack:
- ros2 launch robot_arm_vision hardware_sorting.launch.py serial_port:=/dev/ttyUSB0 baud_rate:=115200 esp32_camera_url:=http://<ip>:81/stream

5. Basic observability checks:
- ros2 node list
- ros2 topic list
- ros2 topic echo /target_pose
- ros2 topic echo /arm_controller/joint_trajectory

## 8) Known Mismatches and Risks (High Value for Next Iteration)

1. Gripper arbitration gap
- mode_manager_node only arbitrates arm trajectories.
- No mode-managed gripper pipeline exists.
- Result: gripper commands can bypass mode control.

2. Sorting planner gripper publication inconsistency
- sorting_planner_node creates gripper publisher but gripper actions publish on arm publisher path.
- This can route gripper JointTrajectory to the wrong topic.

3. Local/remote paths bypass mode manager by default
- gesture_node and mqtt_bridge_node default to direct arm_controller/gripper_controller topics.
- mode_manager topics (/local_controller, /remote_controller) are not default ingress.

4. Launch parameter drift
- hardware_sorting.launch.py passes tuning parameters to sorting_planner_node, but node code does not consume them.

5. Serial baud parameter not fully honored by hardware plugin
- URDF provides baud_rate parameter, but on_activate currently sets B115200 directly.

6. Documentation drift in package guide
- docs/PACKAGE_GUIDE.md contains older file names/paths in several sections compared to current source layout.

7. Camera intrinsics/calibration defaults are generic
- Bridge publishes fixed CameraInfo defaults unless manually adjusted.
- Pixel-to-world mapping quality depends strongly on correct calibration.

8. MoveIt Python dependency sensitivity
- sorting_planner_node requires moveit.planning import; if missing, planner remains inactive.

## 9) Immediate Stabilization Backlog (If Implementation Work Continues)

Priority 1
1. Add full gripper mode arbitration path in mode_manager and remap all producers accordingly.
2. Fix sorting_planner_node to publish gripper trajectories on a dedicated gripper topic.
3. Make gesture and remote default outputs go through mode_manager topics.

Priority 2
1. Declare and consume planner parameters in sorting_planner_node.
2. Respect baud_rate parameter in hardware plugin setup.
3. Replace static camera intrinsics with calibrated values and documented calibration workflow.

Priority 3
1. Refresh docs/PACKAGE_GUIDE.md with actual node/launch paths.
2. Add deployment validation script for topic graph sanity checks.

## 10) Fast Troubleshooting Matrix

A. No camera data
- Check esp32_camera_url correctness and stream reachability in browser.
- Check /camera/image_raw and /camera/camera_info publication.

B. Target detected but no arm movement
- Check /target_pose publication rate.
- Check sorting_planner_node logs for MoveIt import/init failures.
- Check /auto_controller/joint_trajectory and mode_manager current mode.

C. Arm moves but gripper behavior is wrong
- Verify whether command path is bypassing mode manager.
- Inspect /gripper_controller/joint_trajectory and planner gripper publication logic.

D. Controller starts but hardware does not move
- Confirm serial port permissions and active device name.
- Inspect ros2_control_node logs and hardware plugin activation messages.

E. Unexpected mode behavior
- Monitor /system_mode and active mode logs from mode_manager_node.
- Confirm whether command sources are using /auto_controller, /local_controller, /remote_controller topics.

## 11) Source of Truth Order

When documentation conflicts with behavior:
1. Node and launch code in src is authoritative.
2. Package setup entry_points confirms executable names.
3. docs are guidance and may lag implementation.
