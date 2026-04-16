* 6-DOF custom robotic arm designed in Fusion 360 and exported to URDF.
* Operating Environment: ROS 2 Jazzy, Gazebo Harmonic, Linux.
* Current Issue: Gripper mimic joints act individually in MoveIt 2 Setup Assistant and conflict with Gazebo Harmonic physics engine.
* Planned Resolution: Define mimic fingers as "Passive Joints" in MoveIt 2 and only include the active driver joint in the planning group.
* Planned Resolution: Adjust `ros2_control` hardware interfaces to only send commands to the active joint and update Gazebo configurations to handle mimic visual states/physics.
* Completed Task: Set up a dedicated `robot_arm_gazebo` package with Launch files (Gazebo + RViz).
* Resolved Issue: Fixed classic Gazebo plugins `libgazebo_ros_control.so` to modern `gz_ros2_control-system` for Harmonic.
* Resolved Issue: Exported `GZ_SIM_RESOURCE_PATH` to resolve `model://` URI mesh not found errors.
* Resolved Issue: Changed Gazebo Harmonic physics engine to `gz-physics-bullet-featherstone-plugin` to correctly support URDF `<mimic>` joints (Dart engine lacks mimic support).
* Resolved Issue: Fixed mesh loading in Gazebo by converting `package://` URIs to `model://` in `robotic_arm.xacro` and correctly exporting the workspace install path.
* Completed Task: Modernized `<ros2_control>` tags in `robotic_arm.trans`, successfully isolating passive mimic joints from active driver joints.
* Resolved Issue: Gazebo throwing warnings for legacy Ogre `Gazebo/Silver` materials fixed by programmatically adding native Harmonic PBR `<ambient>`/`<diffuse>` blocks.
* Completed Task: Colorized the robot model across RViz & Gazebo (Dark Grey base, Orange arm, Black gripper).
* Resolved Issue: MoveIt 2 demo threw a parsing error (`'NoneType' object is not subscriptable`) because `config/initial_positions.yaml` was empty.
* Completed Task: Wrote a base `initial_positions.yaml` file so the MoveIt 2 Setup Assistant correctly parses `ros2_control.xacro`. 
* Next Task: Implement real `controllers.yaml` integration with Gazebo if required, mapping the physical trajectory bounds.
## Latest Progress: MoveIt 2 Tuning and Fixes
- Fixed MoveIt `joint_limits.yaml` to override 0.0 velocity/acceleration values, enabling Time-Optimal Trajectory planning.
- Fixed `moveit_controllers.yaml` to include correct `action_ns: follow_joint_trajectory` namespaces.
- Prevented 5-DOF IK Singularity issues by enabling `position_only_ik: True` in `kinematics.yaml`.

## Hardware Bring-up & Architecture Pivot
- Successfully reformatted a USB drive to Ext4 to bypass 4GB file size limits and Linux symlink errors (FAT32 restrictions) while installing `arduino-cli` ESP32 packages.
- Finalized the installation of `esp32:esp32@3.3.7` toolchain mounted portably to `/media/natraj/ARDUINO_USB/arduino_data`.
- Compiled and uploaded C++ `firmware.ino` for the 6-DOF MG996R robot arm.
- **Architecture Change:** Decided to keep all 6 servos routed through the PCA9685 driver via I2C for unified wiring.
- **Architecture Change:** Decided to defer MPU-6050 integration. Reverted to controlling all 6 servos tightly using the open-loop PCA9685 driver via I2C for a simplified initial hardware bring-up.
- Wrote and compiled `test_mpu6050.ino` to successfully verify I2C wiring and accelerometer gravity readings.
- Updated main `firmware.ino` to cleanly parse Serial movement commands whilst returning packed MPU telemetry `S:dX,dY,dZ|gX,gY,gZ`.
- Solved ground collision bug by teaching the addition of virtual Scene Objects in RViz.
- Status: Fully working MoveIt + ROS2 + Gazebo Harmonic pipeline!


## Remote Teleoperation & Hardware Integration Complete
- **Phase 8 (MQTT Remote Teleoperation):** Scaffolded the complete `robot_arm_remote` ROS 2 package running `mqtt_bridge_node.py` alongside a fully independent JavaScript MediaPipe client in `index.html`.
- **Public Hosting Support:** Secured the Web client to pass traffic via `wss://broker.hivemq.com:8884` using TLS paths so the static teleoperation endpoint natively hosts safely over GitHub Pages for remote zero-infrastructure UI control.
- **Python Environment Overrides:** Subverted ROS 2 `colcon` isolating python packages by correctly installing `paho-mqtt` at the system level out of the `ai_venv` boundary (`--break-system-packages` flag).
- **Phase 5 (AI Pre-scaffolding):** Scaffolded `esp32_camera.ino` (MJPEG Server firmware) and its companion YOLOv8 receiver node (`esp32_cam_test.py`) for the upcoming AI vision phase.

## Current Debugging & Optimization Findings Supported
- **Resolved Gripper Singularity/Reversal Issue:** Discovered that the gripper joint's physical servo rotation operated inversely to the MediaPipe/MoveIt assigned coordinate limits (opened when commanded close). Fixed this by updating `src/robot_arm_hardware/src/system_interface.cpp` to explicitly invert the 6th joint (`degrees = -(hw_commands_[i] * 180.0 / M_PI) + home_offsets[i]`).
- **Diagnosis of Servo Overload Under Gravity:** Documented why MG996R servos drop out, droop, or fail to hold position over time when fighting gravity without proper mechanical leverage. The servos either hit a thermal shutdown from internal overheating (stall current at high duty cycles) or the PCA9685/Power Supply causes a systemic voltage droop, resulting in loss of holding torque under heavy 6-DOF sustained loads.
