# Project Progress Tracking

## Completed Tasks
* [x] Analyzed the initial `robot_arm_description` URDF and workspace.
* [x] Identified MoveIt 2 and Gazebo Harmonic integration issues related to `<mimic>` joints.
* [x] Created `updates.md` to document the strategy and set up `robot_arm_gazebo` package.
* [x] Created `gazebo.launch.py` and `gazebo_rviz.launch.py` to spawn the robot in Gazebo Harmonic.
* [x] Solved missing mesh errors by exporting `GZ_SIM_RESOURCE_PATH`.
* [x] Solved mimic joint capabilities in Gazebo by specifying `--physics-engine gz-physics-bullet-featherstone-plugin` in launch files.
* [x] Replaced legacy ROS 1 `libgazebo_ros_control.so` and `<transmission>` tags with ROS 2 `<ros2_control>` tags and `gz_ros2_control-system`.
* [x] Generated a complete MoveIt 2 configuration package (`robot_arm_moveit2`).
* [x] Added manually created `initial_positions.yaml` dummy values to prevent MoveIt Setup Assistant Xacro `NoneType` errors.
* [x] Tracked down and safely overrode MoveIt's trajectory generation limits (fixed `max_velocity` boundaries from 0.0 to 1.0).
* [x] Mapped `action_ns: follow_joint_trajectory` on MoveIt controllers so execution properly reaches the correct action servers locally.
* [x] Enabled 5-DOF structural IK by injecting `position_only_ik: True` into `kinematics.yaml`, solving Interactive Marker snap-back singularities. 
* [x] Handled floor crashing issues by demonstrating how to use "Scene Objects" in RViz for virtual collision boxes.
* [x] Created a comprehensive breakdown guide of debugging cases in `MoveIt_Simulation_Troubleshooting.md`.
* [x] Firmly rooted the robotic arm to the Gazebo environment by injecting a `<link name="world"/>` fix directly to `base_link` inside `robotic_arm.xacro`.
* [x] Upgraded `robotic_arm.gazebo` to use modern `gz_ros2_control::GazeboSimROS2ControlPlugin`.
* [x] Connected MoveIt 2 to Gazebo Harmonic by explicitly providing a `use_fake_hardware:=false` mapping inside `moveit_gazebo.launch.py`.
* [x] Fixed RViz timer mismatch flickering and TF jumps by configuring `use_sim_time: true` across all Controller Managers and Launch parameters.
* [x] Replaced legacy "Gazebo/Silver" Ogre materials with modern custom Gazebo Harmonic PBR material tags `<ambient>`, `<diffuse>`, and `<specular>`.
* [x] Added visual styling to the URDF (RViz and Gazebo): Orange links, Dark Grey base, and Black gripper.

## Current Issues & Roadblocks
* [ ] No major roadblocks currently. Core simulation and control logic are stable.

## Next Steps
* [ ] Proceed to Phase 2: Integrate MediaPipe live tracking directly into MoveIt 2's action server to control the simulation dynamically from the webcam.

* [x] **Phase 5**: Developed `robot_arm_vision` with YOLOv8 inference and simulated camera.
* [x] **Phase 6**: Autonomous Logic successfully implemented (detect, plan, pick, drop).
* [x] **Phase 7**: `robot_arm_gesture` finalized. MediaPipe hand tracking maps 21-point hand geometries to robotic arm IK endpoints using EMA smoothing.

## Immediate Next Steps (Phase 8 & 9)
* [ ] Create `robot_arm_remote` ROS 2 package.
* [x] Set up HiveMQ Cloud MQTT broker & UI (`index.html`) using MediaPipe.js.
* [x] Develop `mqtt_bridge_node.py` to bridge internet telemetry to ROS 2.
* [x] Create `robot_arm_mode_manager` for orchestrating state hierarchies (Autonomous vs Local Gesture vs Remote).

### Update: April 14, 2026
* [x] **Phase 7 (Local Gesture Control)**: Fixed a MediaPipe API breaking change (`mediapipe.tasks.python.BaseOptions` -> `mediapipe.tasks.BaseOptions`) in `gesture_node.py` and successfully tested real-time teleoperation mapped to Gazebo/RViz2.
* [x] **Phase 5 & 6 (Autonomous Sorting & Vision)**: Created `sorting.launch.py` to seamlessly spin up both the Vision node (OpenCV/cv_bridge) and the Sorting Planner node (MoveItPy) concurrently.
* [x] **Phase 5 & 6 (Autonomous Sorting & Vision)**: Injected `MoveItConfigsBuilder` directly into the `sorting.launch.py` node parameters to ensure `MoveItPy` correctly initializes with the robot's semantic configuration.
* [x] **Phase 5 & 6 (Autonomous Sorting & Vision)**: Updated `robot_arm_vision`'s `setup.py` to correctly install the `/launch` directory. 
* [x] **Simulation Testing**: Created a standalone `red_box.sdf` to be spawned dynamically into Gazebo to trigger the camera thresholding and the MoveIt pick-and-place logic.

* [x] **Hardware Setup**: Configured a dedicated portable ESP32 Arduino development environment entirely inside the USB Pendrive (`/media/natraj/UBUNTU 24_0/arduino_esp32_env`) using `arduino-cli` and custom `ARDUINO_DATA_DIR` mapping, to save primary laptop storage. Documented the process in `docs/ESP32_Hardware_Setup.md`.

### Update: April 16, 2026
* [x] **Hardware Validation & Calibration**: Corrected actual servo kinematic bounds by flashing strict home offsets (`{45.0, 0.0, 0.0, 45.0, 90.0, 0.0}`) deep inside the C++ `system_interface.cpp` translation parser and corresponding `.ino` logic to sync the physical arm directly to RViz.
* [x] **Phase 8 (MQTT Remote Teleoperation)**: Developed the `robot_arm_remote` package running `mqtt_bridge_node.py` to seamlessly pass target trajectories directly from a HiveMQ MQTT Broker topic (`natraj/robot_arm/teleop/target_state`) to the ROS2 controller. Fixed dependency injection issues for `paho-mqtt`.
* [x] **Phase 8 (MediaPipe Web Frontend)**: Crafted `index.html` to independently track client hand gestures parsing through JS/MediaPipe. Configured correct `wss` ports (`8884`) and TLS paths (`/mqtt`) for direct, secure public 0-infrastructure hosting natively over GitHub Pages!
* [x] **Phase 5 (ESP32-Cam AI Hardware)**: Pre-scaffolded firmware `esp32_camera.ino` (MJPEG Server) to stream frames wirelessly off the hardware alongside an integrated `esp32_cam_test.py` OpenCV YOLOv8 processor hook to prepare for subsequent hardware autonomy testing.
