# Understanding the Code: Architecture & Data Flow

This document explains **how your robotic arm system works**—the key concepts, data flow, architecture, and where different pieces of code execute.

---

## 🏗️ System Architecture Overview

Your system has **8 independent modules** that work together through ROS 2 messages. Think of it like an orchestra: each musician (package) plays their part independently, and the conductor (mode_manager) decides which instrument sounds at what time.

```
┌────────────────────────────────────────────────────────────────────┐
│                    ROBOTIC ARM SYSTEM ARCHITECTURE                  │
└────────────────────────────────────────────────────────────────────┘

INPUT SOURCES (Ways to command the arm):
├── Vision Camera (ESP32-CAM) → YOLOv8 AI detection → autonomous_sorting.py
├── Hand Tracking (Webcam) → MediaPipe landmarks → gesture_controller.py
└── Mobile/Browser → MQTT messages → mqtt_bridge.py

                            ↓ ↓ ↓
                        
                     MODE MANAGER
            (state machine: picks ONE mode at a time)
                     
                    ↓ Unified Commands ↓

MOTION PLANNING LAYER:
├── robot_arm_moveit2
│  └─ Inverse Kinematics solver (hand pose → joint angles)
│  └─ Motion planner (point A → point B collision-free)
│  └─ Trajectory generator (smooth joint motion)

                         ↓ Trajectories ↓

EXECUTION LAYER:
├── robot_arm_hardware
│  └─ Serial communication to Arduino Mega
│  └─ Arduino controls PCA9685 PWM driver
│  └─ PWM signals drive servo motors

                         ↓ Physical Motion ↓

PLANT:
└── 6 servo motors (joints 1-6)
    └─ End effector (gripper)

SIMULATION ALTERNATIVE:
└── robot_arm_gazebo (Gazebo physics engine)
    └─ Simulates all joint movements without hardware
```

---

## 📊 Data Flow Diagram

### Complete System Signal Flow

```
AUTONOMOUS MODE:
┌─────────────┐
│ ESP32-CAM   │ → MJPEG stream (HTTP)
└─────────────┘
                ↓
        ┌──────────────────┐
        │ vision_pipeline  │
        │ (YOLOv8)         │ → Detected objects + grasping pose
        └──────────────────┘
                ↓
        ┌──────────────────┐
        │ autonomous_sort  │
        │ logic            │ → Desired end-effector pose (x, y, z, rx, ry, rz)
        └──────────────────┘
                ↓
        ┌──────────────────┐
        │ mode_manager     │ → "AUTONOMOUS mode active"
        └──────────────────┘
                ↓
        ┌──────────────────┐
        │ MoveIt2 IK       │
        │ Planner          │ → Joint angles (j1, j2, j3, j4, j5, j6)
        └──────────────────┘
                ↓
        ┌──────────────────┐
        │ hardware_interface│
        │ (C++)            │ → Serial protocol to Arduino
        └──────────────────┘
                ↓
        ┌──────────────────┐
        │ Arduino Mega     │ → PWM signals to PCA9685
        └──────────────────┘
                ↓
        ┌──────────────────┐
        │ Servo Motors     │ → Physical arm movement
        └──────────────────┘


LOCAL MODE (GESTURE):
┌─────────────┐
│ Webcam      │ → Video stream
└─────────────┘
                ↓
        ┌──────────────────┐
        │ MediaPipe        │
        │ Hand Detector    │ → 21 hand landmarks + confidence
        └──────────────────┘
                ↓
        ┌──────────────────┐
        │ Hand-to-Arm      │
        │ Mapping          │ → End-effector pose (x, y, z, rx, ry, rz)
        └──────────────────┘ [SAME AS AUTONOMOUS FROM HERE]
                ↓
        ┌──────────────────┐
        │ mode_manager     │ → "LOCAL mode active"
        └──────────────────┘
                ↓
        [REST SAME AS AUTONOMOUS]


REMOTE MODE (INTERNET):
┌─────────────┐
│ Mobile      │
│ Phone App   │ → MQTT message (HiveMQ cloud)
└─────────────┘   Topic: /robot/command/move
                  Payload: {"x": ..., "y": ..., "z": ...}
                ↓
        ┌──────────────────┐
        │ MQTT Bridge      │
        │ (Python node)    │ → End-effector pose
        └──────────────────┘
                ↓
        ┌──────────────────┐
        │ mode_manager     │ → "REMOTE mode active"
        └──────────────────┘
                ↓
        [REST SAME AS AUTONOMOUS]
```

### ROS 2 Topic/Service Flow

```
SUBSCRIBERS (Input):
├── Gesture Controller → subscribes to /hand_landmarks
├── Vision Pipeline → subscribes to /camera/image_raw
├── Mode Manager → subscribes to /robot/mode (command to switch modes)
├── MQTT Bridge → subscribes to MQTT topics → publishes to ROS
└── All modes → subscribe to /joint_trajectory_controller/follow_joint_trajectory

ACTION SERVERS (MoveIt2):
├── /move_group/move_action
│   ├─ Send: motion_planning_msgs/GetMotionPlan
│   └─ Receive: trajectory_msgs/JointTrajectory
└── /compute_ik
    ├─ Send: End-effector pose (link name, position, orientation)
    └─ Receive: Joint angles (j1, j2, j3, j4, j5, j6)

PUBLISHERS (Output):
├── Hardware Interface → publishes /servo_feedback (actual joint angles)
├── Vision Pipeline → publishes /detected_objects
├── Gesture Controller → publishes /hand_pose_debug
├── MQTT Bridge → publishes to MQTT /robot/status/feedback
└── Mode Manager → publishes /robot/current_mode
```

---

## 🧠 Key Concepts Explained

### 1. **End-Effector Pose** — Where the gripper is in space
```
6D Pose = (x, y, z, θx, θy, θz)
├── x, y, z — 3D position in meters (Cartesian coordinates)
├   Example: End effector at (0.3, 0.2, 0.5) = 30cm forward, 20cm left, 50cm up
│
└── θx, θy, θz — 3D rotation (roll, pitch, yaw) in radians/degrees
    Example: θz = 45° = gripper rotated 45° around vertical axis
```

### 2. **Inverse Kinematics (IK)** — Translating space to joint angles
```
INPUT (End-effector pose):          OUTPUT (Joint angles):
┌─────────────────────────┐         ┌─────────────────────┐
│ x = 0.3 m              │         │ j1 = 45°            │
│ y = 0.2 m              │  ────→  │ j2 = 60°            │
│ z = 0.5 m              │  IK     │ j3 = 30°            │
│ θx, θy, θz = ...       │         │ j4 = -20°           │
└─────────────────────────┘         │ j5 = 10°            │
                                    │ j6 = 0°             │
                                    └─────────────────────┘

The MoveIt2 IK solver (KDL) does this calculation instantly.
```

### 3. **Forward Kinematics (FK)** — Opposite direction
```
INPUT (Joint angles):               OUTPUT (End-effector pose):
┌───────────────┐                   ┌──────────────────────┐
│ j1 = 45°      │                   │ x = 0.3 m            │
│ j2 = 60°      │  ────FK────→      │ y = 0.2 m            │
│ ... (6 total) │                   │ z = 0.5 m            │
└───────────────┘                   │ θx, θy, θz = ...     │
                                    └──────────────────────┘

The hardware_interface reads actual servo angles, computes FK to track position.
```

### 4. **Collision Avoidance** — Not crashing into things
```
Plan trajectory from A → B:
Without collision check:  A ──×──┐  [hits obstacle]
                              ╱    B

With collision check:     A ──╱╲╲──┐  [detours around]
                            ╱     ╲ B
                           ╱   Obstacle
                          ╱
                         ←─ Planned path takes detour
```

MoveIt2 does this using OMPL planning algorithms.

### 5. **ROS 2 Topics & Pub/Sub** — How nodes talk to each other
```
Topic: /camera/image_raw (MJPEG frames from ESP32)

Publisher:              Subscribers:
┌──────────────┐        ┌─────────────────┐
│ ESP32-CAM    │ ───→   │ Vision Pipeline │ (uses frames for detection)
│ MJPEG Server │        │ Gesture UI      │ (displays webcam)
└──────────────┘        └─────────────────┘

One publisher, multiple subscribers. Messages pushed asynchronously.
```

### 6. **State Machine** — Mode arbitration
```
AUTONOMOUS mode: Arm is sorting objects
    ↓ [Hand shown to camera]
    → Switch to LOCAL mode: Arm follows hand
    ↓ [Hand removed, MQTT command sent]
    → Switch to REMOTE mode: Arm responds to app
    ↓ [Timeout: no signal for 30 seconds]
    → Switch to IDLE/SAFE mode: Arm returns to home
```

**Safety rule**: Only ONE mode active. Others are paused/suspended.

---

## 🎯 Key Files & Where They Execute

### Configuration Files (Interpreted at startup)

| File | Package | Role | Language |
|------|---------|------|----------|
| `urdf/robotic_arm.xacro` | description | Robot geometry definition | Xacro/XML |
| `config/robot_arm.srdf` | moveit2 | Semantic robot config + collision objects | XML |
| `config/kinematics.yaml` | moveit2 | IK solver configuration | YAML |
| `config/joint_calibration.yaml` | hardware | Per-servo offset tuning | YAML |
| `config/gazebo_*.yaml` | gazebo | Physics parameters | YAML |

### Runtime Executables (Actual processes)

| File | Package | What it does | Language |
|------|---------|-------------|----------|
| `src/autonomous_sorting.py` | vision | Runs YOLOv8 detection loop + grasping logic | Python |
| `src/gesture_controller.py` | gesture | Runs MediaPipe hand tracking loop | Python |
| `src/mqtt_bridge.py` | remote | Maintains MQTT connection, relays messages | Python |
| `src/hardware_interface.cpp` | hardware | C++ ROS2 node managing servo I/O | C++ |
| `src/mode_manager.py` | mode_manager | State machine: switches active mode | Python |
| `arduino/servo_driver.ino` | hardware | Firmware running ON Arduino Mega | Arduino/C |

### Launch Files (Orchestrate startup)

| File | Package | Starts what | Language |
|------|---------|------------|----------|
| `launch/demo.launch.py` | moveit2 | MoveIt2 + RViz (simulator planning) | Python |
| `launch/gazebo_rviz.launch.py` | gazebo | Gazebo physics + RViz visualization | Python |
| `launch/hardware.launch.py` | hardware | Hardware interface node | Python |
| `launch/hardware_sorting.launch.py` | vision | Vision + sorting logic (autonomous) | Python |
| `launch/gesture_control.launch.py` | gesture | Gesture tracking (local) | Python |
| `launch/mqtt_bridge.launch.py` | remote | MQTT bridge (remote) | Python |

---

## 🔄 Complete Execution Flow: From Hand to Servo

**Scenario**: You show your hand to webcam, and the arm follows.

```
STEP 1: CAPTURE
─────────────────────────────────────────────────
Location: gesture_controller.py (robot_arm_gesture package)
┌─ Webcam image captured
├─ MediaPipe detects 21 hand landmarks
└─ Confidence score checked (must be > threshold)

STEP 2: TRANSFORM
─────────────────────────────────────────────────
Location: gesture_controller.py (still)
┌─ Hand position (palm center) extracted: (px, py, pz)
├─ Hand orientation (roll, pitch, yaw) computed from landmarks
├─ EMA smoothing applied (reduces jitter)
└─ END-EFFECTOR POSE published to /robot/commanded_pose
   Message: {"x": 0.3, "y": 0.2, "z": 0.5, "rx": ..., "ry": ..., "rz": ...}

STEP 3: MODE CHECK
─────────────────────────────────────────────────
Location: mode_manager.py (robot_arm_mode_manager package)
┌─ Receives /robot/commanded_pose
├─ Checks current mode (should be LOCAL for gesture)
├─ Applies safety limits (joint limits, reachability check)
└─ Publishes MODE=LOCAL to /robot/current_mode

STEP 4: MOTION PLANNING
─────────────────────────────────────────────────
Location: MoveIt2 action server (robot_arm_moveit2 package)
┌─ mode_manager calls /compute_ik service
│  Input: target end-effector pose from gesture controller
├─ KDL IK solver computes joint angles (j1...j6)
├─ Collision check: does planned path hit obstacles?
└─ If valid: Sends /move_group/move_action with trajectory
   Message: trajectory_msgs/JointTrajectory
            └─ points[0].positions = [j1, j2, j3, j4, j5, j6]
            └─ points[0].time_from_start = 0.5 seconds

STEP 5: TRAJECTORY EXECUTION
─────────────────────────────────────────────────
Location: hardware_interface.cpp (robot_arm_hardware package)
┌─ Receives JointTrajectory on /joint_trajectory_controller/follow_joint_trajectory
├─ Extracts target joint angles: [j1, j2, j3, j4, j5, j6]
├─ Looks up servo calibration offsets (from calibration.yaml)
├─ Converts angles to PWM values
│  Formula: PWM = (angle_degrees / 180) * 2000 + offset
└─ Publishes serial message to Arduino Mega
   Format: ~MAGIC~j1_pwm~j2_pwm~j3_pwm~j4_pwm~j5_pwm~j6_pwm~

STEP 6: ARDUINO EXECUTION
─────────────────────────────────────────────────
Location: servo_driver.ino (running on Arduino Mega)
┌─ Receives serial message
├─ Parses PWM values for each servo
├─ Sets I2C commands to PCA9685 (PWM driver)
│  "Set servo 1 to 1500 µs pulse width"
│  "Set servo 2 to 1200 µs pulse width"
│  etc.
└─ PCA9685 outputs PWM signals to each servo motor

STEP 7: PHYSICAL MOTION
─────────────────────────────────────────────────
Location: 6 servo motors
┌─ Servo 1 reads 1500 µs pulse → moves to mid-position
├─ Servo 2 reads 1200 µs pulse → moves to 60% position
├─ ... (all 6 servos move in parallel)
└─ ARM FOLLOWS YOUR HAND!

LATENCY:
~50 ms: Hand capture + detection
~10 ms: Transform to pose
~5 ms: Mode manager arbitration
~30 ms: IK solving + trajectory planning
~20 ms: Serial transmission to Arduino
~5 ms: Arduino PWM update
────────
~120 ms TOTAL (feels real-time to human)
```

---

## 💾 Memory & Persistence

### Where State is Stored

| State | Location | Persistence |
|-------|----------|------------|
| Robot geometry | `description/*.xacro` | File (static) |
| Physical limits | `moveit2/config/*.yaml` | File (static) |
| Servo calibration | `hardware/config/calibration.yaml` | File (static) |
| Current servo angles | `/servo_feedback` ROS topic | RAM (ephemeral) |
| Detection results | `/detected_objects` ROS topic | RAM (ephemeral) |
| Arm trajectory | JointTrajectory message | RAM (ephemeral, 0.5s) |
| MQTT settings | `remote/config/mqtt.yaml` | File (static) |

**Ephemeral vs. Persistent**:
- **Persistent**: Configuration files (survive reboot)
- **Ephemeral**: ROS messages (exist only while running)

### Calibration Tuning

If arm doesn't reach expected position, you adjust `calibration.yaml`:

```yaml
# calibration.yaml
servo_offsets:
  joint_1: +5    # Add 5° to servo 1
  joint_2: -3    # Subtract 3° from servo 2
  # ... etc
```

Then restart hardware node:
```bash
ros2 launch robot_arm_hardware hardware.launch.py
```

---

## 🚨 Error Handling & Timeouts

### What happens if something fails?

```
Gesture controller disconnects (camera unplugged):
  ↓
No new hand landmarks for 1 second
  ↓
mode_manager detects timeout
  ↓
mode_manager publishes IDLE mode
  ↓
Hardware returns arm to HOME position (safe pose)
  ↓
All modes disabled until new input


Vision pipeline hangs (ESP32 unreachable):
  ↓
MJPEG stream read timeout (10 seconds)
  ↓
autonomous_sorting catches exception
  ↓
Publishes ERROR state
  ↓
mode_manager switches to IDLE
  ↓
Hardware returns to HOME
```

---

## 🔍 How to Debug

### Check what's running

```bash
# List all ROS 2 nodes
ros2 node list

# Should show (when running all modes):
# /autonomous_sorting
# /gesture_controller
# /mqtt_bridge
# /hardware_interface
# /move_group (MoveIt2)
# /mode_manager
```

### Check message flow

```bash
# See all topics
ros2 topic list

# Inspect a topic's data (live)
ros2 topic echo /detected_objects

# See publish rate
ros2 topic hz /servo_feedback
# Should show: ~50 Hz (50 messages/second)

# Check if servo is moving
ros2 topic echo /joint_states
# Shows all joint angles, velocities, efforts
```

### Check errors

```bash
# See logs of a specific node
ros2 launch robot_arm_vision hardware_sorting.launch.py 2>&1 | tee ~/vision.log

# Then inspect ~/vision.log for errors
```

---

## 📚 Architecture Summary

| Layer | Components | Role |
|-------|------------|------|
| **Input** | ESP32-CAM, Webcam, MQTT | Sensor data sources |
| **Perception** | YOLOv8, MediaPipe, MQTT parsing | Interpret input → pose |
| **Decision** | mode_manager, safety checks | Decide what to do |
| **Planning** | MoveIt2 IK + OMPL | Generate motion commands |
| **Control** | hardware_interface, Arduino | Execute on physical arm |
| **Plant** | Servo motors | Produce motion |

Each layer is independent → failure in one doesn't cascade.

---

## 🎓 Key Takeaways

1. **Your system is modular**: 8 packages, each does ONE job well
2. **Data flows as ROS 2 messages**: Topics are the "nervous system"
3. **Everything converts to end-effector pose**: Common currency of commands
4. **MoveIt2 is the brain**: IK solving, collision avoidance, trajectory planning
5. **Arduino is the muscle**: Direct control of PWM/servos
6. **mode_manager is the referee**: Ensures safe switching between inputs
7. **Timeouts = safety**: If signal lost → arm returns home

---

## 🔗 See Also

- **PACKAGE_GUIDE.md** — Detailed info on each package
- **PROJECT_STRUCTURE.md** — File organization
- **TEST_COMMANDS_CHECKLIST.md** — How to test each layer
- **DEPLOYMENT_READY.md** — Hardware setup
- **MoveIt_Simulation_Troubleshooting.md** — Known issues + fixes
