# ROS 2 Package Guide

A comprehensive guide to the 8 production ROS 2 packages in your robotic arm project. Each package is self-contained and handles one specific concern.

---

## 📦 The 8 Core Packages

### 1. `robot_arm_description` — The Robot Skeleton

**Purpose**: Define what the robot looks like physically—its geometry, dimensions, and collision properties.

| Aspect | Details |
|--------|---------|
| **Language** | Xacro (XML-based templating for URDF) |
| **What it defines** | 6 servo joints, 7 links, kinematics chain, STL meshes |
| **Key files** | `urdf/robotic_arm.xacro`, `urdf/robot_arm.urdf.xacro`, mesh files in `meshes/` |
| **Used by** | Every other package (they all need to know arm geometry) |
| **When to edit** | Adding new joints, changing link lengths, updating mesh files |
| **Launch** | Not launched directly; imported by gazebo and moveit2 |

**Quick Start**:
```bash
# Convert Xacro → URDF
rosrun xacro xacro urdf/robotic_arm.xacro > robotic_arm.urdf

# View in RViz
rviz2 robotic_arm.urdf
```

**Key Concepts**:
- **URDF**: Universal Robot Description Format (XML describing robot structure)
- **Xacro**: Macro language for URDF (allows variables, loops, inheritance)
- **Meshes**: STL files for visualization (orange/grey/black segments)
- **Collision geometries**: Define crash detection boundaries

---

### 2. `robot_arm_gazebo` — Physics Simulator Bridge

**Purpose**: Connect the robot URDF to Gazebo Harmonic (physics engine) and launch the simulated world.

| Aspect | Details |
|--------|---------|
| **Language** | Python (ROS 2 launch files) + YAML (config) |
| **What it does** | Spawns robot in Gazebo, applies gravity, friction, joint controllers |
| **Key files** | `launch/gazebo_rviz.launch.py`, `urdf/gazebo_plugins.xacro`, `config/gazebo_world.yaml` |
| **Dependencies** | Requires `robot_arm_description` (robot geometry) |
| **Related package** | Works with `robot_arm_moveit2` for trajectory execution |
| **When to edit** | Tweaking physics (gravity, friction), adding new collision objects |
| **Launch** | `ros2 launch robot_arm_gazebo gazebo_rviz.launch.py` |

**Quick Start**:
```bash
# Launch Gazebo with robot + RViz
ros2 launch robot_arm_gazebo gazebo_rviz.launch.py

# Gazebo window should open with arm in simulated world
```

**Key Concepts**:
- **ros2_control**: ROS 2 abstraction for controllers (joint trajectory, etc.)
- **JointTrajectoryController**: Subscribes to `/joint_trajectory_controller/follow_joint_trajectory` from MoveIt2
- **Physics simulation**: ODE/Bullet engine with gravity, collisions
- **Visualization**: Spawns RViz alongside Gazebo for debugging

---

### 3. `robot_arm_moveit2` — Motion Planning & IK

**Purpose**: Plan collision-free motion paths and solve inverse kinematics. This is how you tell the arm "reach point (x, y, z)" without manually specifying each joint angle.

| Aspect | Details |
|--------|---------|
| **Language** | YAML (config) + Python (launch files) |
| **What it does** | Motion path planning (RRT*, ompl), IK solving (KDL), trajectory filtering |
| **Key files** | `config/robot_arm.srdf`, `config/kinematics.yaml`, `launch/demo.launch.py` |
| **Dependencies** | Requires `robot_arm_description` (robot geometry) |
| **Data flow** | Interactive markers (RViz) → MoveIt planner → trajectory (joint angles) |
| **When to edit** | Changing joint limits, tuning IK solver, modifying collision objects |
| **Launch** | `ros2 launch robot_arm_moveit2 demo.launch.py` |

**Quick Start**:
```bash
# Launch MoveIt2 interactive planner
ros2 launch robot_arm_moveit2 demo.launch.py

# In RViz:
# 1. Drag the RGB interactive marker (the tip of the arm)
# 2. Click "Plan" → plans motion without collisions
# 3. Click "Execute" → arm moves in simulation (if Gazebo is running)
```

**Key Concepts**:
- **SRDF**: Semantic Robot Description Format (MoveIt2 config: joints, groups, end-effector)
- **IK Solver**: KDL (Kinematics and Dynamics Library) converts (x,y,z) → (joint1, joint2, ...)
- **Motion Planning**: OMPL algorithms (RRT*, PRM) find collision-free paths
- **Planning groups**: Manipulator group (6 servo joints), gripper group (1-2 fingers)

---

### 4. `robot_arm_hardware` — Real Servo Control

**Purpose**: Convert MoveIt2 motion plans into physical servo commands sent to Arduino/PCA9685 PWM driver.

| Aspect | Details |
|--------|---------|
| **Language** | C++ (hardware interface) + Arduino (firmware) |
| **What it does** | Serial comms to Arduino, PWM→servo angle mapping, calibration offsets |
| **Key files** | `src/hardware_interface.cpp`, `arduino/servo_driver.ino`, `config/calibration.yaml` |
| **Dependencies** | Works with `robot_arm_moveit2` (receives trajectory commands) |
| **Hardware** | Arduino Mega + PCA9685 PWM driver (up to 16 servos) |
| **When to edit** | Adding new servos, adjusting calibration offsets, changing serial port |
| **Launch** | `ros2 launch robot_arm_hardware hardware.launch.py` (runs in background) |

**Quick Start**:
```bash
# Hardware deployment (requires Arduino connected)
# Step 1: Set serial port and ESP32-CAM URL
ros2 launch robot_arm_hardware hardware.launch.py serial_port:=/dev/ttyUSB0

# Step 2: Verify servos respond
# Watch /servo_feedback topic:
ros2 topic echo /servo_feedback

# Step 3: Calibrate joints (if needed)
# Run calibration tester:
ros2 run robot_arm_hardware calibration_tester
```

**Key Concepts**:
- **hardware_interface**: ROS 2 abstraction layer for hardware drivers
- **PCA9685**: I2C PWM driver (controls servo pulse width)
- **Calibration offsets**: Map ROS joint angles → Arduino PWM values
- **Serial protocol**: Custom binary protocol to Arduino Mega

**Files to Know**:
- `config/joint_calibration.yaml` — Per-servo offset tuning
- `arduino/` — Arduino firmware for servo driving
- `docs/GRIPPER_LIMIT_CALIBRATION_LOG.md` — Tested safe limits

---

### 5. `robot_arm_vision` — Autonomous Sorting (YOLOv8 AI)

**Purpose**: See objects via ESP32-CAM, detect them with AI (YOLOv8), plan autonomous grasp, and execute sorting.

| Aspect | Details |
|--------|---------|
| **Language** | Python (ROS 2 node) + Arduino (ESP32 firmware) |
| **What it does** | MJPEG video streaming, object detection, autonomous manipulation |
| **Key files** | `src/autonomous_sorting.py`, `src/vision_pipeline.py`, `arduino/esp32_mjpeg_server.ino` |
| **Dependencies** | Requires `robot_arm_moveit2` (motion planning), `robot_arm_hardware` (servo control) |
| **AI Model** | YOLOv8 nano (`yolov8n.pt` — 86 MB, real-time detection) |
| **Hardware** | ESP32-CAM (OV2640 camera) at http://ESP32_IP:81/stream |
| **When to edit** | Changing detection classes, tuning grasping logic, adjusting confidence thresholds |
| **Launch** | `ros2 launch robot_arm_vision hardware_sorting.launch.py serial_port:=/dev/ttyUSB0 esp32_camera_url:=http://192.168.1.100:81/stream` |

**Quick Start**:
```bash
# Step 1: Ensure ESP32-CAM is running and has IP (e.g., 192.168.1.100)
# See docs/ESP32_UTILITIES.md for IP finding

# Step 2: Launch autonomous sorting
ros2 launch robot_arm_vision hardware_sorting.launch.py \
  serial_port:=/dev/ttyUSB0 \
  esp32_camera_url:=http://192.168.1.100:81/stream

# Step 3: Watch the arm pick objects!
# Subscribe to detection topic:
ros2 topic echo /detected_objects
```

**Key Concepts**:
- **YOLOv8**: Real-time object detector (80 classes by default)
- **MJPEG**: Motion JPEG streaming (video over HTTP)
- **cv_bridge**: Converts OpenCV images ↔ ROS messages
- **Autonomous loop**: Detect → Plan grasp → Execute → Repeat

---

### 6. `robot_arm_gesture` — Hand Tracking Control (Local)

**Purpose**: Show your hand to webcam → arm mirrors your hand gestures in real-time (local teleoperation).

| Aspect | Details |
|--------|---------|
| **Language** | Python (ROS 2 node) |
| **What it does** | MediaPipe hand detection, 21-point landmark tracking, hand pose → arm IK mapping |
| **Key files** | `src/gesture_controller.py`, `src/hand_tracker.py` |
| **Dependencies** | Requires `robot_arm_moveit2` (IK solver), `robot_arm_hardware` (servo control) |
| **Hardware** | USB webcam (any standard camera) |
| **Latency** | ~50-100 ms real-time (hand tracking → servo movement) |
| **When to edit** | Adjusting smoothing/filtering, changing mapping algorithm, tuning confidence threshold |
| **Launch** | `ros2 launch robot_arm_gesture gesture_control.launch.py` |

**Quick Start**:
```bash
# Local hand tracking (requires webcam + display)
ros2 launch robot_arm_gesture gesture_control.launch.py

# Show your hand to webcam
# Arm should follow your hand movements

# Visualize hand landmarks:
ros2 topic echo /hand_landmarks
```

**Key Concepts**:
- **MediaPipe**: Google's lightweight ML framework (hand, face, pose detection)
- **21 landmarks**: Thumb, index, middle, ring, pinky × 3 points each + palm center
- **Hand pose mapping**: Map palm position + orientation → 6-DOF arm commands
- **EMA smoothing**: Exponential Moving Average to reduce jitter

---

### 7. `robot_arm_remote` — Internet Teleoperation (Remote)

**Purpose**: Control the arm from anywhere via phone/browser over the internet using MQTT.

| Aspect | Details |
|--------|---------|
| **Language** | Python (ROS 2 MQTT bridge) + JavaScript (web UI) + HTML/CSS |
| **What it does** | MQTT message relaying, GitHub Pages web UI, PWA (offline support) |
| **Key files** | `src/mqtt_bridge.py`, `web/index.html`, `web/service_worker.js`, `web/app.js` |
| **Dependencies** | Requires `robot_arm_moveit2` (motion planning), `robot_arm_hardware` (control) |
| **Cloud broker** | HiveMQ (MQTT as a Service) |
| **Network** | Works over 4G/WiFi (any connection) |
| **UI** | Progressive Web App (works on mobile/desktop) |
| **When to edit** | Changing web UI buttons, adding new MQTT topics, modifying motion commands |
| **Launch** | `ros2 launch robot_arm_remote mqtt_bridge.launch.py` |

**Quick Start**:
```bash
# Step 1: Launch MQTT bridge node
ros2 launch robot_arm_remote mqtt_bridge.launch.py

# Step 2: Open web UI
# Option A: Local dev server (if running)
#   http://localhost:8000
# Option B: Published GitHub Pages
#   https://your-github-username.github.io/robotic-arm

# Step 3: Use mobile/browser to control
# Click desired end-effector position on screen
# Arm should respond over MQTT bridge
```

**Key Concepts**:
- **MQTT**: Message Queuing Telemetry Transport (lightweight pub/sub protocol)
- **HiveMQ Cloud**: Free tier for MQTT broker (max 100 msg/sec)
- **PWA**: Progressive Web App (works offline, no installation)
- **Service Worker**: Caches code for offline use
- **Topics**: `/robot/command/move`, `/robot/status/feedback`

---

### 8. `robot_arm_mode_manager` — State Machine & Safety

**Purpose**: Orchestrate switching between AUTONOMOUS / LOCAL (gesture) / REMOTE (internet) modes with safety guards.

| Aspect | Details |
|--------|---------|
| **Language** | Python (ROS 2 node) |
| **What it does** | Mode state machine, safety checks, timeout logic, mode arbitration |
| **Key files** | `src/mode_manager.py`, `src/safety_checks.py` |
| **Dependencies** | Subscribes to all 3 modes, publishes unified commands to hardware |
| **Operating modes** | **AUTONOMOUS** (AI sorting) / **LOCAL** (hand tracking) / **REMOTE** (MQTT) |
| **Safety** | Timeout on losing signal, collision check, joint limit enforcement |
| **When to edit** | Changing mode priority, adjusting timeout durations, adding new safety rules |
| **Launch** | `ros2 launch robot_arm_mode_manager mode_manager.launch.py` |

**Quick Start**:
```bash
# Launch mode manager
ros2 launch robot_arm_mode_manager mode_manager.launch.py

# Switch modes via topic
ros2 topic pub /robot/mode std_msgs/String "data: AUTONOMOUS"
# or: "LOCAL", "REMOTE"

# Monitor current mode:
ros2 topic echo /robot/current_mode
```

**Key Concepts**:
- **State machine**: Finite states (IDLE → AUTONOMOUS → LOCAL → REMOTE → IDLE)
- **Safety arbitration**: Only one mode active at a time
- **Timeout safety**: Arm stops if no command received after N seconds
- **Collision avoidance**: Checks planned path before execution

**Control Flow**:
```
Hand tracker (gesture)  ─┐
MQTT bridge (remote)    ├─→ Mode Manager ─→ Hardware Interface ─→ Servos
YOLOv8 vision (auto)    ─┘                (unified command)
```

---

## 🔗 Package Dependencies

```
robot_arm_description (no dependencies)
│
├─ robot_arm_gazebo (depends on: description)
│  └─ Other simulators can also use description
│
├─ robot_arm_moveit2 (depends on: description)
│  ├─ Used by: robot_arm_vision
│  ├─ Used by: robot_arm_gesture
│  ├─ Used by: robot_arm_remote
│  └─ Used by: robot_arm_mode_manager
│
├─ robot_arm_hardware (no dependencies from ROS packages)
│  └─ Receives commands from: mode_manager
│
├─ robot_arm_vision (depends on: moveit2, hardware)
│  └─ Subscribes to: /joint_trajectory_controller/follow_joint_trajectory
│
├─ robot_arm_gesture (depends on: moveit2, hardware)
│  └─ Subscribes to: /joint_trajectory_controller/follow_joint_trajectory
│
├─ robot_arm_remote (depends on: moveit2, hardware)
│  └─ Subscribes to: /joint_trajectory_controller/follow_joint_trajectory
│
└─ robot_arm_mode_manager (depends on: none, but controls all others)
   └─ Publishes unified commands that hardware/gazebo consume
```

---

## 🚀 Typical Workflows

### Workflow 1: Simulation Testing
```bash
# Terminal 1: Gazebo
ros2 launch robot_arm_gazebo gazebo_rviz.launch.py

# Terminal 2: Motion planner (RViz interactive)
ros2 launch robot_arm_moveit2 demo.launch.py

# Use RViz to drag interactive marker and test plans
```

### Workflow 2: Autonomous Sorting (Hardware)
```bash
# Terminal 1: Hardware interface
ros2 launch robot_arm_hardware hardware.launch.py serial_port:=/dev/ttyUSB0

# Terminal 2: Vision + sorting logic
ros2 launch robot_arm_vision hardware_sorting.launch.py \
  serial_port:=/dev/ttyUSB0 \
  esp32_camera_url:=http://192.168.1.100:81/stream

# Arm automatically sorts objects!
```

### Workflow 3: Local Hand Tracking
```bash
# Terminal 1: Hardware interface
ros2 launch robot_arm_hardware hardware.launch.py serial_port:=/dev/ttyUSB0

# Terminal 2: Hand tracking
ros2 launch robot_arm_gesture gesture_control.launch.py

# Show hand to webcam → arm follows
```

### Workflow 4: Internet Teleoperation
```bash
# Terminal 1: Hardware interface
ros2 launch robot_arm_hardware hardware.launch.py serial_port:=/dev/ttyUSB0

# Terminal 2: MQTT bridge + mode manager
ros2 launch robot_arm_remote mqtt_bridge.launch.py

# Open web UI in browser/mobile
# Click to control remotely
```

---

## 📋 Build & Run

### Build All Packages
```bash
cd /home/natraj/file
colcon build --symlink-install
source install/setup.bash
```

### Build Single Package
```bash
# Rebuild only robot_arm_vision (for example)
colcon build --packages-select robot_arm_vision
```

### Run Package Tests
```bash
# Test a package
colcon test --packages-select robot_arm_hardware
```

---

## 📝 Adding a New Package

To create a new ROS 2 package:

```bash
cd /home/natraj/file/src
ros2 pkg create my_new_package --build-type ament_python  # Python
# or:
ros2 pkg create my_new_package --build-type ament_cmake   # C++
```

Then add it to dependencies in other packages' `package.xml` files.

---

## 🆘 Common Issues & Fixes

| Issue | Likely Package | Solution |
|-------|-----------------|----------|
| "Can't see robot in Gazebo" | `robot_arm_gazebo` | Check URDF path, verify description works |
| "IK solver not responding" | `robot_arm_moveit2` | Check SRDF syntax, verify kinematics.yaml |
| "Arm doesn't move" | `robot_arm_hardware` | Check serial connection, verify calibration offsets |
| "Hand tracking jittery" | `robot_arm_gesture` | Increase EMA smoothing, check lighting |
| "MQTT connection fails" | `robot_arm_remote` | Check HiveMQ credentials, network connection |
| "No objects detected" | `robot_arm_vision` | Check ESP32 IP, verify MJPEG stream works, YOLOv8 confidence threshold |

---

## 🔗 See Also

- **PROJECT_STRUCTURE.md** — Folder organization
- **UNDERSTANDING_THE_CODE.md** — Data flow & architecture
- **TEST_COMMANDS_CHECKLIST.md** — Common test commands
- **DEPLOYMENT_READY.md** — Hardware setup checklist
