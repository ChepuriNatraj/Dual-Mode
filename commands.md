# Robotic Arm Commands

**⚠️ WARNING: Never run multiple hardware launches at the same time.** Running two controller managers simultaneously will cause controller conflicts and crash the stack. Close any active workspace process before starting a new one.

---

## Before Any Real Hardware Launch

Use this when `/dev/ttyUSB0` fails to open or controllers look active after a crash.

```bash
# Check that the controller board is visible
ls -l /dev/ttyUSB*

# Give your user temporary access to the serial device
sudo chmod a+rw /dev/ttyUSB0

# Make sure no old launch/serial monitor is still holding the port
fuser -v /dev/ttyUSB0

# Check for stale ROS graph state before starting a new launch
ros2 node list
ros2 control list_controllers
```

If old ROS nodes are still running, close their terminals before launching again.

---

## Workflow 1: Real Hardware Autonomous Sorting

This runs the full autonomous pick-and-place logic using MoveItPy, YOLO/Color detection, and the Mode Manager.

```bash
# Build and source
colcon build --symlink-install
source install/setup.bash

# Launch the autonomous sorting stack (uses local camera instead of ESP32)
ros2 launch robot_arm_vision hardware_sorting.launch.py \
  serial_port:=/dev/ttyUSB0 \
  camera_index:=0 \
  detector_mode:=red \
  stable_frames_required:=5 \
  use_rviz:=false
```

For autonomous sorting, the camera must be fixed relative to the robot base. The vision node assumes an overhead camera at about `x=0.25`, `y=0.0`, `z=0.8`. If the phone/laptop camera moves, `/target_pose` will move and the arm may plan to the wrong place.

### Autonomous Sorting Isolation Test

Use this after the launch is running. It bypasses the camera and sends one known reachable target to the planner.

```bash
source install/setup.bash
ros2 topic pub --once /target_pose geometry_msgs/msg/PoseStamped "{
  header: {frame_id: 'world'},
  pose: {
    position: {x: 0.25, y: 0.0, z: 0.02},
    orientation: {x: 0.0, y: 1.0, z: 0.0, w: 0.0}
  }
}"
```

If this causes `/auto_controller/joint_trajectory` and `/arm_controller/joint_trajectory` to publish, the planner and mode routing are working and the remaining issue is camera calibration/detection.

## Workflow 2: Real Hardware Remote MQTT Control

This runs the arm via MQTT from a web UI. Commands are securely routed through the Mode Manager.

```bash
# 1. Bring up the hardware base
source install/setup.bash
ros2 launch robot_arm_hardware hardware_base.launch.py serial_port:=/dev/ttyUSB0

# 2. Start the Mode Manager (in a new terminal)
source install/setup.bash
ros2 run robot_arm_mode_manager mode_manager_node

# 3. Start the MQTT Bridge (in a new terminal)
source install/setup.bash
ros2 run robot_arm_remote mqtt_bridge_node

# 4. Switch the system mode to REMOTE (in a new terminal)
source install/setup.bash
ros2 topic pub --once /system_mode std_msgs/msg/String "{data: 'REMOTE'}"
```

Testing MQTT locally via CLI:
```bash
mosquitto_pub -h broker.emqx.io -p 1883 -t natraj/robot_arm/teleop/target_state -m '{"arm_angles":[0.2,0.1,0.0,0.0,0.0],"gripper_angle":-0.3}'
```

---

## Debugging Tree

If something is not working, check the following topics/nodes in order:

1. **Are the nodes active?**
   `ros2 node list`
2. **Are the controllers loaded and active?**
   `ros2 control list_controllers`
3. **Is the camera working?**
   `ros2 topic hz /camera/image_raw`
4. **Is the Vision Node detecting a target pose?**
   `ros2 topic echo /target_pose --once`
5. **Is the MoveItPlanner creating trajectories?**
   `ros2 topic echo /auto_controller/joint_trajectory --once`
6. **Is the Mode Manager forwarding them to hardware?**
   `ros2 topic echo /arm_controller/joint_trajectory --once`
   `ros2 topic echo /gripper_controller/joint_trajectory --once`

---

## Archival / Old Commands

ESP32-CAM dependent setups have been archived. For simple local gesture testing without MoveIt/autonomous sorting:
```bash
ros2 launch robot_arm_hardware hardware_gesture.launch.py \
  serial_port:=/dev/ttyUSB0 \
  camera_index:=0 \
  enable_gesture:=true \
  smoothing_alpha:=0.08 \
  publish_rate_hz:=10.0 \
  deadband_rad:=0.03 \
  max_joint_step_rad:=0.05
```

For extra-calm motion while testing with a moving phone camera:

```bash
ros2 launch robot_arm_hardware hardware_gesture.launch.py \
  serial_port:=/dev/ttyUSB0 \
  camera_index:=0 \
  enable_gesture:=true \
  smoothing_alpha:=0.04 \
  publish_rate_hz:=6.0 \
  deadband_rad:=0.05 \
  max_joint_step_rad:=0.03
```

## Workflow 3: Blind Autonomous Sequence (Fixed Demo)

If the camera is not working or to demonstrate pure planning mechanics independently of vision, run the fixed hardcoded sequence loop (cycles between two spots endlessly).

```bash
# Build and source
colcon build --symlink-install
source install/setup.bash

# Launch fixed demo 
ros2 launch robot_arm_vision hardware_blind_sorting.launch.py serial_port:=/dev/ttyUSB0
```
