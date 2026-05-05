# Pending Work: Autonomous Sorting and Remote MQTT Control

Date: 2026-05-03

## Current Confirmed State

- Real robotic arm is the target system. Gazebo is not the current focus.
- Basic ROS 2 hardware control is working.
- Gesture control is working with:

```bash
ros2 launch robot_arm_hardware hardware_gesture.launch.py serial_port:=/dev/ttyUSB0 camera_index:=0 enable_gesture:=true
```

- The ESP32-CAM path is removed from the current plan.
- Autonomous sorting should use the laptop/mobile camera exposed as OpenCV camera index `0`.
- `/camera/image_raw` is working.
- `/target_pose` is publishing values, so the vision node is alive.
- Remote MQTT bridge starts, but end-to-end robotic arm control from the GitHub web page is not yet proven.
- The pasted MoveIt/RViz output shows controller conflicts and missing/empty semantic robot description symptoms. This likely comes from mixing launch systems or launching MoveIt while another controller manager is already active.

## Work Remaining Estimate

Overall, the project is not blocked at the low-level hardware layer. The remaining work is integration and cleanup.

- Hardware and gesture foundation: mostly complete.
- Autonomous sorting: about 45-60% remaining.
- Remote MQTT control: about 40-55% remaining.
- Highest-risk area: MoveItPy sorting planner and controller/mode routing.

## Priority 1: Make One Clean Hardware Bringup

Problem:
The working command is `hardware_gesture.launch.py`, but autonomous sorting and MoveIt testing use other launch files that can start another controller manager or conflicting controllers.

Tasks:

- [ ] Define one real-hardware base launch for all real-arm tests.
- [ ] Use `hardware_gesture.launch.py enable_gesture:=false` as the likely base for hardware-only bringup.
- [ ] Avoid running `robot_arm_moveit2 demo.launch.py` at the same time as an already-running hardware controller manager.
- [ ] Verify these after the base launch:

```bash
ros2 node list
ros2 control list_controllers
ros2 topic hz /joint_states
```

Expected:

- `joint_state_broadcaster` active.
- `arm_controller` active.
- `gripper_controller` active.
- Only one `/controller_manager`.

## Priority 2: Fix Autonomous Sorting Launch

Problem:
`hardware_sorting.launch.py` tries to start hardware, controllers, camera, vision, planner, mode manager, and RViz together. Since hardware gesture already works, this launch should be refactored to match the proven hardware path and remove old ESP32 assumptions.

Tasks:

- [ ] Update `hardware_sorting.launch.py` to use laptop/mobile camera only.
- [ ] Add launch arguments for:
  - `camera_index`
  - `frame_width`
  - `frame_height`
  - `fx`
  - `fy`
  - `cx`
  - `cy`
- [ ] Do not mention ESP32 in active launch docs/comments.
- [ ] Start camera publisher before vision node.
- [ ] Start mode manager before sorting planner.
- [ ] Delay planner startup until controllers and MoveIt parameters are ready.
- [ ] Decide whether RViz is optional. For real autonomous sorting, RViz should not be required.

## Priority 3: Stabilize Vision Target Detection

Current finding:
`/target_pose` is publishing, but values jump between targets. Example values from `target_output.md` include changing `x` and `y` positions. This means detection is happening, but target choice is not stable enough for picking.

Tasks:

- [ ] Confirm whether `ultralytics` is installed. If installed, the node uses YOLO. If not installed, it uses red-color threshold fallback.
- [ ] Add a clear detector mode parameter:

```text
detector_mode: red | yolo
```

- [ ] For the first working demo, prefer `red` mode with one red cube/object.
- [ ] Add confidence/class filtering if YOLO is used.
- [ ] Add target smoothing or locking:
  - Ignore detections outside workspace.
  - Require the target to remain stable for several frames.
  - Publish one locked target instead of a new target every frame.
- [ ] Make the existing vision parameters real ROS parameters. Currently values like `camera_height`, `workspace_z`, and workspace bounds are hard-coded in `vision_node.py`.

Validation:

```bash
ros2 topic echo /target_pose
ros2 topic hz /target_pose
```

Expected:

- Target pose changes slowly or locks onto one object.
- No rapid jumping when the object is stationary.

## Priority 4: Verify and Fix MoveItPy Sorting Planner

Likely problems in `sorting_planner_node.py`:

- [ ] Verify whether this import works:

```python
from moveit.planning import MoveItPy
```

- [ ] `pose_link="link_6"` is probably wrong because `link_6` is a joint name, not the arm tip link. The SRDF arm group uses `tip_link="link_5_1"`.
- [ ] The code calls `configuration_name="home"`, but the SRDF currently defines `initial`, not `home`.
- [ ] The code calls gripper state `open`, but the SRDF currently defines `close` only.
- [ ] The planner publishes gripper messages through `self.arm_pub` instead of `self.gripper_pub`.
- [ ] The mode manager currently forwards only arm trajectories, not gripper trajectories.
- [ ] Confirm the type returned by `plan_result.trajectory`. It may not be a plain `trajectory_msgs/JointTrajectory`.

Tasks:

- [ ] Change planner pose link to the correct tip link, likely `link_5_1`.
- [ ] Add SRDF group state `home`, or change code to use `initial`.
- [ ] Add SRDF group state `open`, or stop using MoveIt gripper group states and publish gripper trajectory directly.
- [ ] Publish gripper commands to a real autonomous gripper topic.
- [ ] Update mode manager to route autonomous gripper commands to `/gripper_controller/joint_trajectory`.
- [ ] Add a dry-run mode that logs the pick sequence before moving hardware.

Validation:

```bash
ros2 run robot_arm_vision sorting_planner_node
ros2 topic echo /auto_controller/joint_trajectory
ros2 topic echo /auto_controller/gripper_trajectory
```

Expected:

- A stable `/target_pose` triggers one pick-place cycle.
- Arm and gripper commands are both produced.
- Planner does not continuously restart on every frame.

## Priority 5: Mode Manager Must Route Arm and Gripper

Current issue:
`mode_manager_node.py` only publishes `/arm_controller/joint_trajectory`. It does not route gripper trajectories.

Best architecture:
Use mode manager for autonomous, local, and remote arm/gripper streams. This is safer than letting every control source publish directly to the hardware controller.

Tasks:

- [ ] Add publishers:

```text
/arm_controller/joint_trajectory
/gripper_controller/joint_trajectory
```

- [ ] Add subscribers:

```text
/auto_controller/joint_trajectory
/auto_controller/gripper_trajectory
/local_controller/joint_trajectory
/local_controller/gripper_trajectory
/remote_controller/joint_trajectory
/remote_controller/gripper_trajectory
```

- [ ] Route both arm and gripper only for the active mode.
- [ ] On timeout, send safe home arm pose and safe open gripper pose.
- [ ] Optionally publish current mode on `/current_system_mode`.

## Priority 6: Finish Remote MQTT Control

Current issue:
`mqtt_bridge_node.py` publishes directly to `/arm_controller/joint_trajectory` and `/gripper_controller/joint_trajectory`. That can work, but it bypasses mode safety. Best path is to publish into the remote input stream and let mode manager forward it when mode is `REMOTE`.

Tasks:

- [ ] Add configurable output topics to `mqtt_bridge_node.py`.
- [ ] Default MQTT bridge outputs should be:

```text
/remote_controller/joint_trajectory
/remote_controller/gripper_trajectory
```

- [ ] Keep an optional direct-hardware mode only for quick testing.
- [ ] Add or document a remote launch flow:

```bash
ros2 launch robot_arm_hardware hardware_gesture.launch.py serial_port:=/dev/ttyUSB0 enable_gesture:=false
ros2 run robot_arm_mode_manager mode_manager_node
ros2 run robot_arm_remote mqtt_bridge_node
ros2 topic pub --once /system_mode std_msgs/msg/String "{data: 'REMOTE'}"
```

- [ ] Test command-line MQTT first:

```bash
mosquitto_pub -h broker.emqx.io -p 1883 -t natraj/robot_arm/teleop/target_state -m '{"arm_angles":[0.2,0.1,0.0,0.0,0.0],"gripper_angle":-0.3}'
```

- [ ] Confirm the GitHub web page uses the same:
  - broker: `broker.emqx.io`
  - topic: `natraj/robot_arm/teleop/target_state`
  - payload keys: `arm_angles`, `gripper_angle`
- [ ] Confirm browser WebSocket MQTT port:
  - HTTP page: `8083`
  - HTTPS GitHub Pages: `8084` with SSL
- [ ] Add visible telemetry or logs so it is obvious when messages arrive.

Validation:

```bash
ros2 topic echo /remote_controller/joint_trajectory
ros2 topic echo /remote_controller/gripper_trajectory
ros2 topic echo /arm_controller/joint_trajectory
ros2 topic echo /gripper_controller/joint_trajectory
```

Expected:

- MQTT message appears first on remote controller topics.
- When `/system_mode` is `REMOTE`, mode manager forwards it to hardware controller topics.
- Arm moves only while remote mode is active.

## Priority 7: Update Documentation and Commands

Tasks:

- [ ] Update `commands.md` with two clean workflows:
  - Real hardware autonomous sorting.
  - Real hardware remote MQTT control.
- [ ] Remove ESP32-CAM commands from active workflow docs or mark them as archived.
- [ ] Add a warning: do not run multiple hardware launches at the same time.
- [ ] Add a short debug tree:
  - Camera works?
  - Target pose works?
  - Planner works?
  - Mode manager forwards?
  - Controller receives?
  - Servo moves?

## Suggested Next Implementation Order

1. Fix mode manager to route both arm and gripper for all modes.
2. Change MQTT bridge to publish to remote controller topics by default.
3. Test MQTT with `mosquitto_pub` before using GitHub web page.
4. Fix sorting planner link names, group states, and gripper publishing.
5. Stabilize vision target detection.
6. Refactor `hardware_sorting.launch.py` around the proven real hardware launch path.
7. Run one-object autonomous pick test at low speed.

## Immediate Next Test Commands

Use these to establish the exact current state before editing behavior:

```bash
ros2 node list
ros2 topic list
ros2 control list_controllers
ros2 topic hz /camera/image_raw
ros2 topic echo /target_pose
```

For MoveItPy:

```bash
python3 -c "from moveit.planning import MoveItPy; print('MoveItPy OK')"
```

For MQTT:

```bash
ros2 run robot_arm_remote mqtt_bridge_node
mosquitto_pub -h broker.emqx.io -p 1883 -t natraj/robot_arm/teleop/target_state -m '{"arm_angles":[0.2,0.1,0.0,0.0,0.0],"gripper_angle":-0.3}'
```

