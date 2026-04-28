Dual-Mode Vision-Guided Robotic Arm   | Project Documentation


**PROJECT DOCUMENTATION**

**Design & Development of a Dual-Mode Vision-Guided Robotic Arm**

*for Autonomous Sorting & Human-in-the-Loop Manipulation*

|**Platform**|Ubuntu 24.04 LTS|
| :- | :- |
|**ROS2 Version**|ROS2 Jazzy Jalisco|
|**Simulation**|Gazebo Harmonic|
|**GPU**|NVIDIA RTX 3060 (6GB VRAM)|
|**Robot**|6-DOF Metal Servo Arm Kit|
|**Status**|In Development — Simulation Phase|

2025 – 2026


# **1. Project Overview**
## **1.1 Project Title**
Design and Development of a Dual-Mode Vision-Guided Robotic Arm for Autonomous Sorting and Human-in-the-Loop Manipulation

## **1.2 Purpose & Problem Statement**
This project addresses a critical gap in modern robotic systems: the inability to seamlessly transition between fully autonomous operation and direct human control. Most industrial robotic arms operate in one fixed mode — either fully automated or manually operated — requiring physical intervention to switch between the two.

This project builds a unified system where:

- The robot operates autonomously by default — detecting, classifying, and sorting objects using computer vision without any human input.
- A human can take control at any moment simply by raising their hand in front of a camera — no buttons, no UI, no interruption.
- Remote teleoperation is possible from anywhere in the world — the human can control the arm via hand gestures streamed from a mobile phone over the internet.
- Mode switching is completely hands-free and automatic — the system detects the context and responds accordingly.

|*In short: the robot sorts objects by itself, but a human can take over with just a hand gesture — whether they are standing next to the robot or on the other side of the planet.*|
| :- |

## **1.3 Core Objectives**
- **Build and simulate a 6-DOF robotic arm in Gazebo Harmonic using ROS2 Jazzy**
- Adapt ferasboulala/five-dof-robot-arm URDF to ROS2 Jazzy
- Add 6th DOF (gripper) to the existing 5-DOF model
- Integrate ros2\_control with Gazebo Harmonic for realistic simulation
- **Implement vision-based autonomous sorting**
- OpenCV color detection for fast real-time classification
- YOLOv8 (CUDA-accelerated) for advanced object detection
- Camera calibration and pixel-to-world coordinate conversion
- **Implement gesture-based control modes**
- Local gesture control: webcam captures hand, arm mirrors movement
- Remote gesture control: phone camera anywhere in world controls arm
- **Build intelligent mode management system**
- Automatic switching between AUTONOMOUS, LOCAL GESTURE, REMOTE GESTURE
- Safety timeouts and home position recovery
- **Transition simulation to real hardware using ros2\_control hardware interface**


# **2. Hardware**
## **2.1 Robotic Arm**

|**Component**|**Details**|
| :- | :- |
|Model|6-DOF Metal Servo Arm Kit (AliExpress)|
|Joints|6 Degrees of Freedom|
|Servos|4× MG996R + 2× YF6125MG|
|Frame|Black anodised aluminium brackets|
|Gripper|Claw-type, servo-actuated|
|URDF Reference|ferasboulala/five-dof-robot-arm (adapted)|

## **2.2 Electronics**

|**Component**|**Purpose**|
| :- | :- |
|ESP32|Servo PWM signal generation and serial comms|
|PCA9685 (16ch)|I2C servo driver board — controls all 6 servos|
|5V / 10A PSU|Dedicated power supply for servos|
|USB Cable|Serial link: Laptop/Network → ESP32|
|Webcam (1080p)|Primary vision for sorting + local gesture|

## **2.3 Development Machine**

|**Spec**|**Value**|
| :- | :- |
|OS|Ubuntu 24.04 LTS|
|GPU|NVIDIA RTX 3060 6GB (CUDA for YOLOv8)|
|Role|Brain — runs ROS2, Gazebo, vision, MoveIt2|
|RPi|Raspberry Pi 4/5 (planned — future phase)|

|*Current Phase: Laptop acts as the brain. Raspberry Pi integration is planned for a future phase — the architecture is designed to support it with no code changes.*|
| :- |


# **3. Software Stack**
## **3.1 Core Infrastructure**

|**Technology**|**Version / Detail**|**Role in Project**|
| :- | :- | :- |
|Ubuntu|24\.04 LTS|Base operating system|
|ROS2 Jazzy|Jazzy Jalisco (LTS)|Robot middleware & communication|
|Gazebo|Harmonic (official Jazzy pair)|Physics simulation|
|ros2\_control|Jazzy compatible|Sim ↔ Hardware abstraction layer|
|MoveIt2|Jazzy compatible|Motion planning & inverse kinematics|
|Python 3|3\.10+|All node logic & vision pipeline|
|C++17|GCC 11+|Hardware interface plugin|

## **3.2 Vision & AI Stack**

|**Library**|**Version**|**Purpose**|
| :- | :- | :- |
|OpenCV|4\.8+|Image processing, color detection, camera calibration|
|YOLOv8 (Ultralytics)|8\.x|Object detection & classification (CUDA)|
|MediaPipe|0\.10+|21-landmark hand tracking (gesture control)|
|cv\_bridge (ROS2)|Jazzy|Convert ROS Image ↔ OpenCV Mat|
|PyTorch|2\.x + CUDA 12.1|YOLOv8 GPU acceleration|

## **3.3 Remote Control Stack**

|**Technology**|**Detail**|**Purpose**|
| :- | :- | :- |
|MQTT|Protocol v5|Lightweight pub/sub messaging over internet|
|HiveMQ Cloud|Free tier cluster|Cloud MQTT broker (no server needed)|
|Paho MQTT (Python)|1\.6+|Robot-side MQTT subscriber|
|Paho MQTT (JS)|Browser Websocket|Phone-side MQTT publisher|
|MediaPipe (Browser)|CDN via jsdelivr|Hand tracking in phone browser|
|Flask / Python HTTP|3\.x|Serve web controller app|
|ngrok|Free tier|Internet tunnel for phone access|

## **3.4 ESP32 Firmware Stack**

|**Library**|**Version**|**Purpose**|
| :- | :- | :- |
|ESP32 IDE|2\.x|Firmware development|
|Adafruit PWM Servo|Latest|PCA9685 I2C servo control|
|Wire.h|Built-in|I2C communication|
|pyserial (Python)|3\.5+|ROS2 → ESP32 bridge|


# **4. System Architecture**
## **4.1 Three Operating Modes**
The system operates in one of three modes at all times, managed by a central Mode Manager node:

|**Mode**|**Trigger**|**Behaviour**|
| :- | :- | :- |
|AUTONOMOUS|No hand detected anywhere|Camera detects objects → YOLOv8 classifies → MoveIt2 picks and sorts|
|LOCAL GESTURE|Hand detected in webcam|Webcam → MediaPipe → joint angles → arm mirrors hand in real-time|
|REMOTE GESTURE|MQTT commands arriving|Phone camera → MediaPipe in browser → MQTT → ROS2 → arm moves|

## **4.2 ROS2 Node Graph**
The following nodes form the complete ROS2 computation graph:

|**Node**|**Responsibility**|
| :- | :- |
|/camera\_node|Publishes raw camera feed to /camera/image\_raw|
|/vision\_node|YOLOv8 + OpenCV — detects & localises objects|
|/gesture\_node (local)|MediaPipe — extracts hand landmarks from webcam|
|/mqtt\_bridge\_node|Receives remote joint commands via MQTT, publishes to ROS2|
|/mode\_manager\_node|Monitors inputs, decides active mode, publishes /control\_mode|
|/sorting\_planner\_node|Maps detected object → bin → target (x,y,z) coordinates|
|/motion\_planner\_node|MoveIt2 wrapper — IK + collision-free path planning|
|/arm\_controller\_node|JointTrajectoryController — executes motion via ros2\_control|
|/arduino\_bridge|Hardware interface — comms to ESP32 + PCA9685|

## **4.3 Remote Control Data Flow**

|<p>PHONE ANYWHERE IN WORLD</p><p>`  `└─ Browser opens web app (ngrok URL)</p><p>`  `└─ Front camera activates</p><p>`  `└─ MediaPipe.js detects 21 hand landmarks</p><p>`  `└─ Maps landmarks → 6 joint angles (degrees)</p><p>`  `└─ Publishes JSON to HiveMQ MQTT broker (SSL)</p><p>`         `│</p><p>`    `INTERNET  (~30-80ms)</p><p>`         `│</p><p>`  `└─ mqtt\_bridge\_node.py receives JSON</p><p>`  `└─ Converts degrees → radians</p><p>`  `└─ Publishes JointTrajectory to /arm\_controller</p><p>`  `└─ MoveIt2 executes → Arm moves</p><p>`  `└─ Feedback sent back to phone (latency display)</p><p></p><p>Total end-to-end latency: ~230-290ms (fully usable)</p>|
| :- |


# **5. ROS2 Package Structure**

|<p>arm\_ws/</p><p>├── src/</p><p>│   ├── my\_arm\_description/        ← URDF, meshes, ros2\_control config</p><p>│   │   ├── urdf/</p><p>│   │   │   └── my\_arm.urdf.xacro  ← Main robot description</p><p>│   │   ├── config/</p><p>│   │   │   └── controllers.yaml   ← JointTrajectoryController config</p><p>│   │   ├── launch/</p><p>│   │   │   ├── display.launch.py  ← RViz with joint sliders</p><p>│   │   │   └── gazebo.launch.py   ← Full Gazebo Harmonic sim</p><p>│   │   └── worlds/</p><p>│   │       └── sorting\_world.sdf  ← Table + colored blocks scene</p><p>│   │</p><p>│   ├── my\_arm\_moveit\_config/      ← Auto-generated by Setup Assistant</p><p>│   │   ├── config/</p><p>│   │   │   ├── my\_arm.srdf</p><p>│   │   │   ├── kinematics.yaml</p><p>│   │   │   └── controllers.yaml</p><p>│   │   └── launch/</p><p>│   │       └── moveit\_rviz.launch.py</p><p>│   │</p><p>│   ├── my\_arm\_vision/             ← OpenCV + YOLOv8 detection</p><p>│   │   └── my\_arm\_vision/</p><p>│   │       ├── vision\_node.py     ← Color detect + YOLO classify</p><p>│   │       └── camera\_calib.py    ← Pixel → world coordinate convert</p><p>│   │</p><p>│   ├── my\_arm\_gesture/            ← Local MediaPipe gesture control</p><p>│   │   └── my\_arm\_gesture/</p><p>│   │       └── gesture\_node.py</p><p>│   │</p><p>│   ├── my\_arm\_remote/             ← MQTT bridge for internet control</p><p>│   │   └── my\_arm\_remote/</p><p>│   │       └── mqtt\_bridge\_node.py</p><p>│   │</p><p>│   ├── my\_arm\_mode\_manager/       ← AUTO / LOCAL / REMOTE switching</p><p>│   │   └── my\_arm\_mode\_manager/</p><p>│   │       └── mode\_manager\_node.py</p><p>│   │</p><p>│   └── my\_arm\_hardware/           ← C++ ros2\_control hardware plugin</p><p>│       └── src/</p><p>│           └── arm\_hardware\_interface.cpp</p><p>│</p><p>├── web\_controller/</p><p>│   └── index.html                 ← Phone browser gesture controller</p><p>│</p><p>└── esp32/</p><p>`    `└── arm\_firmware/</p><p>`        `└── arm\_firmware.ino       ← PCA9685 servo controller</p>|
| :- |


# **6. Development Phases & Timeline**

|**Phase**|**Goals**|**Status**|
| :- | :- | :- |
|Phase 1 — Workspace Setup|Install ROS2 Jazzy, Gazebo Harmonic, MoveIt2, vision libraries. Verify CUDA on RTX 3060.|In Progress|
|Phase 2 — URDF & RViz|Adapt ferasboulala URDF → ROS2 Jazzy Xacro. Add 6th DOF. View in RViz with joint sliders.|Planned|
|Phase 3 — Gazebo Sim|Launch arm in Gazebo Harmonic. ros2\_control + JointTrajectoryController. Move arm via CLI commands.|Planned|
|Phase 4 — MoveIt2|Run MoveIt2 Setup Assistant. Motion planning in RViz. Execute trajectories in Gazebo.|Planned|
|Phase 5 — Vision Pipeline|OpenCV color detection node. Camera calibration. Pixel → world coordinate conversion.|Planned|
|Phase 6 — Autonomous Sort|YOLOv8 integration. Full pick-sort-return cycle in simulation. Test reliability.|Planned|
|Phase 7 — Gesture Control|MediaPipe local gesture node. Arm mirrors hand in Gazebo. Smoothing filter.|Planned|
|Phase 8 — Remote Control|MQTT bridge node. Browser web app. Phone controls arm over internet.|Planned|
|Phase 9 — Mode Manager|Unified AUTO ↔ LOCAL ↔ REMOTE switching. Safety timeouts. Demo-ready sim.|Planned|
|Phase 10 — Hardware|ESP32 firmware. PCA9685 wiring. ros2\_control hardware interface (C++).|Future|
|Phase 11 — Integration|Full system on real arm. Calibration. 50+ cycle stress test.|Future|
|Phase 12 — RPi Migration|Move ROS2 stack to Raspberry Pi. Network-based multi-machine setup.|Future|


# **7. Installation & Setup Commands**
## **7.1 ROS2 Jazzy + Gazebo Harmonic Packages**

|<p>sudo apt update</p><p>sudo apt install ros-jazzy-ros-gz ros-jazzy-ros-gz-sim ros-jazzy-ros-gz-bridge -y</p><p>sudo apt install ros-jazzy-gz-ros2-control ros-jazzy-ros2-control -y</p><p>sudo apt install ros-jazzy-ros2-controllers ros-jazzy-joint-trajectory-controller -y</p><p>sudo apt install ros-jazzy-joint-state-broadcaster -y</p><p>sudo apt install ros-jazzy-moveit ros-jazzy-moveit-setup-assistant -y</p><p>sudo apt install ros-jazzy-moveit-ros-planning-interface -y</p><p>sudo apt install ros-jazzy-xacro ros-jazzy-joint-state-publisher-gui -y</p><p>sudo apt install ros-jazzy-robot-state-publisher ros-jazzy-cv-bridge -y</p><p>sudo apt install ros-jazzy-vision-opencv ros-jazzy-camera-calibration -y</p>|
| :- |

## **7.2 Python Vision Libraries (with CUDA)**

|<p># PyTorch with CUDA 12.1 (for RTX 3060)</p><p>pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121</p><p></p><p># Vision libraries</p><p>pip install opencv-python numpy ultralytics mediapipe</p><p></p><p># MQTT and serial</p><p>pip install paho-mqtt pyserial flask</p><p></p><p># Verify CUDA is available</p><p>python3 -c "import torch; print('CUDA:', torch.cuda.is\_available())"</p>|
| :- |

## **7.3 Workspace Build**

|<p>mkdir -p ~/arm\_ws/src && cd ~/arm\_ws/src</p><p>git clone https://github.com/ferasboulala/five-dof-robot-arm.git</p><p>cd ~/arm\_ws</p><p>rosdep install --from-paths src --ignore-src -r -y</p><p>colcon build --symlink-install</p><p>source install/setup.bash</p>|
| :- |

## **7.4 Launch Commands**

|<p># View arm in RViz (joint sliders)</p><p>ros2 launch my\_arm\_description display.launch.py</p><p></p><p># Full Gazebo Harmonic simulation</p><p>ros2 launch my\_arm\_description gazebo.launch.py</p><p></p><p># MoveIt2 motion planning (run alongside Gazebo)</p><p>ros2 launch my\_arm\_moveit\_config moveit\_rviz.launch.py use\_sim\_time:=True</p><p></p><p># Check controllers are active</p><p>ros2 control list\_controllers</p><p></p><p># Send test joint command</p><p>ros2 topic pub --once /arm\_controller/joint\_trajectory \</p><p>`  `trajectory\_msgs/msg/JointTrajectory \</p><p>`  `'{joint\_names: [joint1,joint2,joint3,joint4,joint5,joint6], \</p><p>`    `points: [{positions: [0.785,0.0,0.5,0.0,0.0,0.0], \</p><p>`    `time\_from\_start: {sec: 2}}]}'</p>|
| :- |


# **8. Real-World Applications**
The dual-mode architecture (autonomous + human-in-the-loop) makes this system applicable across a broad range of industries. Below are the most directly relevant applications:

## **8.1 Manufacturing & Quality Control**
- Defect sorting — vision detects faulty products, arm removes them from the line
- PCB component sorting — classify resistors, ICs, capacitors by visual markings
- Pharmaceutical tablet inspection — detect broken or discoloured tablets

## **8.2 Healthcare & Assistive Technology**
- Lab sample sorting — sort blood vials, specimens by colour-coded labels
- Assistive robotic arm — gesture control enables mobility-impaired patients to pick up objects
- Surgical instrument pre-sorting — sterile gesture control for scrub nurses
- Medication dispensing — autonomous pill sorting for care homes

## **8.3 Agriculture**
- Fruit grading — sort produce by size, colour, and ripeness using computer vision
- Seed sorting — separate viable seeds from damaged ones
- Harvest assistance — gesture-controlled picking for delicate crops

## **8.4 Logistics & E-commerce**
- Package sorting — classify and route by size or barcode scan
- Returns processing — auto-classify returned items, gesture override for ambiguous cases
- Dark store fulfilment — pick individual products for delivery orders

## **8.5 Waste Management & Recycling**
- Waste stream sorting — classify plastic, cardboard, metal by colour and shape
- E-waste disassembly — sort circuit boards, batteries, casings for recycling

## **8.6 Defense & Hazardous Environments**
- Hazardous material handling — remote gesture control keeps humans safe from radiation/chemicals
- Bomb disposal assistance — low-cost prototype of military teleop arm systems

## **8.7 Education & Research**
- University robotics lab — standard ROS2+MoveIt2+Gazebo teaching platform
- Human-Robot Interaction research — studying when and how humans should override autonomous systems
- Computer vision benchmarking — physical testbed for new detection algorithms

|*Project Demo Application: Smart Factory Sorting Station — 3 coloured blocks on a table, arm sorts them autonomously, operator raises hand to take over, steps back and arm resumes. Demonstrates all modes in a single compelling 2-minute demo.*|
| :- |


# **9. Safety & Reliability Features**

|**Safety Feature**|**Description**|
| :- | :- |
|Remote Timeout|If no MQTT command arrives for 3 seconds, arm automatically returns to home position and switches to AUTO mode|
|Angle Clamping|All joint angles hard-clamped to safe ranges — phone cannot send values that damage servos|
|Smoothing Filter|Exponential moving average on gesture inputs — prevents sudden jerky movements from hand jitter|
|Trajectory Duration|150ms minimum per command — prevents instantaneous joint jumps|
|QoS 0 (No Queue)|Old commands dropped, never queued — prevents backlog of stale commands executing at once|
|Safe Mode Switch|Mode manager waits for current motion to complete before switching modes|
|Home Position|Any anomaly (disconnect, error, timeout) triggers return to predefined safe home position|
|Joint Limits in URDF|Physical joint limits enforced at URDF level — MoveIt2 respects them in all planning|


# **10. Skills & Learning Path**
## **10.1 Current Skill Level**

|**Skill**|**Status**|
| :- | :- |
|Linux Terminal|✅ Comfortable|
|ROS2 (Jazzy)|✅ Already experienced|
|Gazebo Simulation|✅ Already experienced|
|Python OOP & Classes|⚠️  Needs upgrade (beginner → ROS2-ready)|
|OpenCV & Computer Vision|❌ Need to learn|
|YOLOv8 Object Detection|❌ Need to learn|
|MediaPipe Hand Tracking|❌ Need to learn|
|ESP32 / C++ Firmware|❌ Need to learn (hardware phase)|
|ros2\_control HW Interface|❌ Need to learn (hardware phase)|
|MQTT / IoT Networking|❌ Need to learn (remote phase)|

## **10.2 Priority Learning Order**
1. **Python OOP (Week 1) — classes, callbacks, NumPy**
1. OpenCV basics (Week 2) — image processing, color detection, contours
1. Camera calibration + pixel-to-world transform (Week 3)
1. YOLOv8 integration with CUDA (Week 4)
1. MediaPipe gesture mapping (Week 5)
1. MQTT remote control setup (Week 6)
1. ESP32 firmware + C++ hardware interface (Hardware Phase)


# **11. Essential Links & Resources**
## **11.1 Project Code References**
**→  ferasboulala — five-dof-robot-arm (your base URDF):  <https://github.com/ferasboulala/five-dof-robot-arm>**

**→  akabot — Same arm kit with ROS2 Humble + MoveIt2 + Gazebo (reference):  <https://github.com/TheNoobInventor/akabot>**

**→  AntoBrandi — ESP32bot (best structured ROS2 arm project to study):  <https://github.com/AntoBrandi/esp32bot>**

## **11.2 ROS2 & Gazebo Documentation**
**→  ROS2 Jazzy Documentation:  <https://docs.ros.org/en/jazzy/index.html>**

**→  Gazebo Harmonic Documentation:  <https://gazebosim.org/docs/harmonic/getstarted>**

**→  ros2\_control Documentation:  <https://control.ros.org/jazzy/index.html>**

**→  MoveIt2 Documentation (Jazzy):  <https://moveit.picknik.ai/main/index.html>**

**→  ros\_gz (ROS2-Gazebo bridge) GitHub:  <https://github.com/gazebosim/ros_gz>**

**→  URDF Tutorial (ROS2):  <https://docs.ros.org/en/jazzy/Tutorials/Intermediate/URDF/URDF-Main.html>**

**→  Xacro Documentation:  <https://wiki.ros.org/xacro>**

## **11.3 Vision & AI Libraries**
**→  OpenCV Python Tutorials:  <https://docs.opencv.org/4.x/d6/d00/tutorial_py_root.html>**

**→  YOLOv8 by Ultralytics:  <https://docs.ultralytics.com>**

**→  MediaPipe Hand Landmarker:  <https://ai.google.dev/edge/mediapipe/solutions/vision/hand_landmarker>**

**→  PyTorch CUDA Install Guide:  <https://pytorch.org/get-started/locally/>**

**→  Roboflow (Custom YOLOv8 Training + Labelling):  <https://roboflow.com>**

## **11.4 Remote Control Infrastructure**
**→  HiveMQ Cloud (Free MQTT Broker):  <https://console.hivemq.cloud>**

**→  Eclipse Mosquitto (Local MQTT Broker):  <https://mosquitto.org>**

**→  Paho MQTT Python Client:  <https://pypi.org/project/paho-mqtt/>**

**→  ngrok (Internet Tunnel — phone access):  <https://ngrok.com>**

**→  MediaPipe JS (Browser CDN):  <https://cdn.jsdelivr.net/npm/@mediapipe/hands/hands.js>**

## **11.5 ESP32 & Hardware**
**→  Adafruit PCA9685 PWM Servo Library:  <https://github.com/adafruit/Adafruit-PWM-Servo-Driver-Library>**

**→  Adafruit PCA9685 Wiring Guide:  <https://learn.adafruit.com/16-channel-pwm-servo-driver>**

**→  ESP32 Serial Communication Guide:  <https://docs.arduino.cc/learn/communication/uart/>**

**→  ros2\_control Hardware Interface Tutorial:  <https://control.ros.org/jazzy/doc/ros2_control/hardware_interface/doc/writing_new_hardware_component.html>**

## **11.6 Learning Resources**
**→  Python OOP Tutorial — Corey Schafer (YouTube):  <https://www.youtube.com/watch?v=ZDa-Z5JzLYM>**

**→  NumPy Crash Course — Keith Galli (YouTube):  <https://www.youtube.com/watch?v=GB9ByFAIAH4>**

**→  ROS2 Jazzy Tutorials (Official):  <https://docs.ros.org/en/jazzy/Tutorials.html>**

**→  MoveIt2 Tutorial Series:  <https://moveit.picknik.ai/main/doc/tutorials/tutorials.html>**

**→  Gazebo Harmonic Tutorials:  <https://gazebosim.org/docs/harmonic/tutorials>**


# **12. Project Backup Plans**
The project has three backup plans in order of complexity. Each builds on the previous, so they are not alternatives but fallback submission options if the main project cannot be completed in time.

|**Backup**|**Title**|**What it Demonstrates**|
| :- | :- | :- |
|Backup 1 (Simplest)|Pick and Place|Basic ROS2 + MoveIt2 + fixed position pick and drop. No vision.|
|Backup 2|Object Sorting by Color|OpenCV color detection + autonomous sorting. No gesture control.|
|Backup 3|Gesture-Controlled Arm|MediaPipe local gesture control only. No autonomous mode.|
|Main Project|Dual-Mode Vision-Guided Arm|Full system: autonomous sorting + local gesture + remote internet control + mode switching.|

|*Strategy: Develop in order Backup 1 → 2 → 3 → Main. Each phase is a submittable project on its own. This guarantees you always have something to present regardless of timeline.*|
| :- |


# **13. Glossary of Terms**

|**Term**|**Meaning**|
| :- | :- |
|6-DOF|6 Degrees of Freedom — robot has 6 independent joint axes|
|ROS2|Robot Operating System 2 — middleware framework for robot software|
|Gazebo|Physics-based 3D robot simulator used with ROS2|
|URDF|Unified Robot Description Format — XML file describing robot geometry|
|Xacro|XML Macro language — URDF with variables and reusable macros|
|ros2\_control|ROS2 framework abstracting hardware — same controller code for sim and real|
|MoveIt2|ROS2 motion planning framework — handles IK, collision avoidance, path planning|
|IK|Inverse Kinematics — compute joint angles given desired end-effector position|
|JTC|JointTrajectoryController — sends smooth position trajectories to joints|
|PCA9685|16-channel I2C PWM driver IC — controls up to 16 servos from one board|
|MQTT|Message Queuing Telemetry Transport — lightweight pub/sub IoT protocol|
|MediaPipe|Google framework for real-time perception — hand tracking, pose, face|
|YOLOv8|You Only Look Once v8 — real-time object detection neural network|
|CUDA|NVIDIA parallel computing platform — enables GPU-accelerated ML inference|
|ngrok|Secure tunnel service — exposes local server to the internet via HTTPS URL|
|HiveMQ|Cloud-hosted MQTT broker service — relays messages between devices|
|HSV|Hue-Saturation-Value — colour space better than RGB for colour detection|
|cv\_bridge|ROS2 package converting between ROS Image messages and OpenCV Mat|
|QoS|Quality of Service — MQTT reliability level (0=fire-and-forget, 1=at least once)|


*End of Document*

Dual-Mode Vision-Guided Robotic Arm — Project Documentation
Confidential — Personal Project Use	Page 

## **12. Required Images & Figures Checklist**

To complete the report, the following figures must be generated or captured and placed into an `images/` directory. Each placeholder in the report should be replaced with the corresponding markdown image link (e.g., `![Figure 2 Description](./images/figure_02.png)`).

- [ ] **FIGURE 2:** Concept diagram illustrating the transition between autonomous sorting and human-guided teleoperation, highlighting the environmental triggers.
- [ ] **FIGURE 3:** Comparative timeline and architectural evolution of teleoperation interfaces vs. autonomous visual grasping frameworks.
- [ ] **FIGURE 4:** ROS 2 Node Graph (`rqt_graph`) detailing the publish/subscribe relationships between the vision, gesture, planning, and hardware nodes.
- [ ] **FIGURE 5:** Data pipeline flowchart showing the transformation of raw sensor data into final PWM signals on the ESP32.
- [ ] **FIGURE 6:** Kinematic mapping diagram illustrating how MediaPipe hand landmarks correspond to specific physical joints on the robotic arm.
- [ ] **FIGURE 7:** Finite State Machine (FSM) diagram of the Mode Manager logic.
- [ ] **FIGURE 8:** Visual representation of the URDF model rendered in RViz showing coordinate frames (TF) at each joint.
- [ ] **FIGURE 9:** Architecture diagram detailing the ROS 2 workspace package hierarchy and dependency flow.
- [ ] **FIGURE 10:** Graph showing End-to-End Latency comparison between Autonomous and Teleoperated modes across 100 trials.
- [ ] **FIGURE 11:** Bar chart detailing CPU vs GPU resource utilization during the different operational states of the robotic arm.
- [ ] **FIGURE 12:** Diagram showcasing the hardware abstraction layer, illustrating how the same ROS 2 architecture can command both a sub-scale prototype and an industrial counterpart.
- [ ] **FIGURE 13:** Example visual frame illustrating a failed YOLOv8 detection (e.g., due to occlusion or shadowing).
- [ ] **FIGURE 14:** Conceptual layout for an Edge-AI upgraded architecture featuring a decentralized processing topology with Jetson Nano / Coral Edge TPU integration.
- [ ] **FIGURE 15:** Final physical prototype of the dual-mode robotic arm grasping an object, symbolizing the project synthesis.
