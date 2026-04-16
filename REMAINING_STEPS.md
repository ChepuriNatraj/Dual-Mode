# Remaining Steps & Project Roadmap

Based on the Dual-Mode Vision-Guided Robotic Arm Master Documentation, here is the dedicated step-by-step tracker for the remaining development phases. 

*(Phases 1 through 4 are largely complete, with the exception of the final Gazebo/MoveIt trajectory bridge).*

---

## 🟢 Immediate Next Step (Bridge Simulation)
- [x] Create `controllers.yaml` to define `joint_state_broadcaster`, `arm_controller` (JointTrajectoryController), and `gripper_controller`.
- [x] Update `gazebo.launch.py` to spawn the controllers in Gazebo Harmonic upon boot.
- [x] Verify that MoveIt plans executed in RViz successfully actuate the Gazebo physics model in real-time.

## 🔵 Phase 5: Vision Pipeline Setup
- [x] Create ROS 2 package: `robot_arm_vision`.
- [x] Add a simulated camera sensor payload to the Gazebo URDF (`camera_sensor`).
- [x] Write `vision_node.py` using OpenCV to subscribe to `/camera/image_raw` and detect specific colored blocks.
- [x] Implement camera calibration module to convert 2D pixel coordinates into 3D world (MoveIt) coordinates.

## 🔵 Phase 6: Autonomous Sorting Logic (AI)
- [x] Integrate YOLOv8 with PyTorch/CUDA into `vision_node.py` for advanced object classification.
- [x] Write `sorting_planner_node.py` using MoveIt 2 Python MoveGroup API to mathematically calculate arm endpoints.
- [x] Implement the full autonomous loop: **Detect Object -> Calculate Grasp Pose -> Plan Path -> Pick -> Drop in Bin -> Return Home**.

## 🟠 Phase 7: Local Gesture Control
- [x] Create ROS 2 package: `robot_arm_gesture`.
- [x] Implement MediaPipe Hand Landmarker script (`gesture_node.py`) capturing frames from the laptop webcam.
- [x] Map 21-point finger/hand geometries to the robot's specific joint constraints mathematically.
- [x] Apply safety angle clamping and exponential smoothing filters to prevent jerky movements hitting the virtual/real servos.

## 🟠 Phase 8: Remote Teleoperation (Internet Control)
- [x] Create ROS 2 package: `robot_arm_remote`.
- [x] Set up a free HiveMQ Cloud MQTT broker for data streaming.
- [x] Create the web controller interface (`index.html`) using MediaPipe.js and Paho MQTT to stream hand poses from a phone browser.
- [x] Write `mqtt_bridge_node.py` to listen to HiveMQ from anywhere in the world and locally publish ROS 2 joint commands.
- [x] Set up an `ngrok` tunnel for easy global phone access (optional, web controller used).

## 🟣 Phase 9: Mode Management Architecture
- [ ] Create ROS 2 package: `robot_arm_mode_manager`.
- [ ] Write the `mode_manager_node.py` state machine to orchestrate hierarchy (AUTONOMOUS vs. LOCAL GESTURE vs. REMOTE GESTURE).
- [ ] Implement system safety timeouts (e.g., if MQTT internet drops for 3 seconds, abort current motion and return to AUTONOMOUS home mode safely).

## 🟤 Phase 10: Hardware Interface (Bridging to Real World)
- [x] Write `arm_firmware.ino` using the Adafruit PWM Servo library for the PCA9685 I2C driver board.
- [x] Create ROS 2 package: `robot_arm_hardware`.
- [x] Develop the custom `ros2_control` hardware interface plugin in **C++**. This will override Gazebo's physics plugin and send JointTrajectory commands over Serial (USB) to the Arduino.

## 🟤 Phase 11 & 12: Final Integration & Migration
- [x] Deploy the software stack to the physical metallic robotic arm.
- [x] Calibrate physical servo offsets.
- [ ] Run a 50+ cycle stress test for the picking loop.
- [ ] *(Future Goal)* Migrate the primary ROS2 network and ML inference to a Raspberry Pi 4/5. 