# Project Structure Guide

This document explains the folder organization of your robotic arm project and where to find everything.

---

## 📂 Workspace Tree

```
/home/natraj/file/
├── 📄 README.md                           (START HERE: Master project overview)
├── 📄 START_HERE.md                       (CURRENT FOCUS: ESP32-CAM setup roadmap)
├── 📄 DEPLOYMENT_READY.md                 (DEPLOYMENT: Hardware ops checklist)
├── 📄 TEST_COMMANDS_CHECKLIST.md          (TESTING: ROS 2 commands reference)
├── 📄 REMAINING_STEPS.md                  (ROADMAP: Development phases 5-12)
├── 📄 MoveIt_Simulation_Troubleshooting.md (REFERENCE: 8+ solved issues + solutions)
├── 📄 ESP32_CAM_QUICK_START.md            (ACTIVE: 7-step ESP32 flashing guide)
├── 📄 PROJECT_STRUCTURE.md                (YOU ARE HERE)
├── 📄 PACKAGE_GUIDE.md                    (See what each ROS2 package does)
├── 📄 UNDERSTANDING_THE_CODE.md           (How it all works together)
│
├── 📁 src/                                (Production ROS 2 Packages)
│   ├── robot_arm_description/             (URDF/Xacro models, meshes)
│   ├── robot_arm_gazebo/                  (Gazebo physics simulator bridge)
│   ├── robot_arm_moveit2/                 (Motion planning & IK solvers)
│   ├── robot_arm_hardware/                (Servo control & Arduino firmware)
│   ├── robot_arm_vision/                  (YOLOv8 AI vision + MJPEG streaming)
│   ├── robot_arm_gesture/                 (MediaPipe hand tracking)
│   ├── robot_arm_remote/                  (MQTT teleoperation + web UI)
│   └── robot_arm_mode_manager/            (State machine: autonomous/local/remote)
│
├── 📁 scripts/                            (Utility Scripts)
│   └── use_pendrive_env.sh                (Setup Arduino CLI from USB pendrive)
│
├── 📁 docs/                               (Extended Documentation)
│   ├── CHANGELOG.md                       (Recent updates and changes)
│   ├── PROGRESS_ARCHIVE.md                (Detailed project history)
│   ├── ESP32_CAM_DETAILED_SETUP.md        (Detailed ESP32 setup guide)
│   ├── ESP32_UTILITIES.md                 (ESP32 IP finding & utilities)
│   ├── ESP32_Hardware_Setup.md            (Comprehensive hardware reference)
│   ├── GRIPPER_LIMIT_CALIBRATION_LOG.md   (Servo calibration data)
│   ├── ARDUINO_PENDRIVE_ENV.md            (Arduino USB environment setup)
│   ├── LEARNING_GUIDE.md                  (Educational materials)
│   ├── JOURNAL.md                         (Project development journal)
│   ├── system_visual.html                 (Visual architecture diagram)
│   ├── chats/                             (Meeting notes & conversations)
│   ├── learn/                             (Learning resources)
│   ├── overview/                          (Visual overviews)
│   ├── report/                            (Generated reports)
│   └── troubleshoots/                     (Additional debugging guides)
│
├── 📁 archive/                            (Legacy Code - Not Active)
│   └── hand_gesture_demo/                 (Original MediaPipe demo - superseded)
│
├── 📁 arduino_staging/                    (Arduino Package Cache for USB Pendrive)
│   └── packages/                          (Arduino CLI board packages)
│
├── 📄 red_box.sdf                         (Gazebo model: test object)
├── 📄 red_box_demo.sdf                    (Gazebo model: demo variant)
├── 📄 red_box_multi_a.sdf                 (Gazebo model: multi-object test A)
├── 📄 red_box_multi_b.sdf                 (Gazebo model: multi-object test B)
├── 📄 red_box_multi_c.sdf                 (Gazebo model: multi-object test C)
├── 📄 test.urdf                           (Auto-generated URDF sample)
├── 📄 yolov8n.pt                          (YOLOv8 nano AI model weights - 86 MB)
│
├── 📁 build/                              (AUTO-GENERATED: ROS 2 build outputs)
│   └── [colcon build products]            (Regenerated on each colcon build)
│
├── 📁 install/                            (AUTO-GENERATED: Executables & binaries)
│   └── [colcon install products]          (Regenerated on each colcon build)
│
└── 📁 log/                                (AUTO-GENERATED: Build logs)
    └── [timestamped build logs]           (Regenerated on each build)
```

---

## 🎯 Quick Navigation Guide

### I want to...

| Goal | Go to | File/Folder |
|------|-------|-------------|
| **Understand the big picture** | README.md | Overview + architecture |
| **Get started quickly** | START_HERE.md | ESP32-CAM setup roadmap |
| **See project status** | PROJECT_PROGRESS_COMPREHENSIVE.md | 95% completion + phases |
| **Deploy to hardware** | DEPLOYMENT_READY.md | Hardware checklist |
| **Test the system** | TEST_COMMANDS_CHECKLIST.md | ROS 2 test commands |
| **Find troubleshooting solutions** | MoveIt_Simulation_Troubleshooting.md | 8+ solved issues |
| **Understand each ROS2 package** | PACKAGE_GUIDE.md | What each package does |
| **Learn how it all works** | UNDERSTANDING_THE_CODE.md | Architecture + data flow |
| **See project structure** | PROJECT_STRUCTURE.md | (You are here) |
| **Know what to edit next** | REMAINING_STEPS.md | Development roadmap |

---

## 📦 ROS 2 Packages Explained (Quick Summary)

See `PACKAGE_GUIDE.md` for detailed descriptions of each package.

| Package | Purpose | Status |
|---------|---------|--------|
| `robot_arm_description` | Define arm geometry (URDF/Xacro) | ✅ Complete |
| `robot_arm_gazebo` | Physics simulator bridge | ✅ Complete |
| `robot_arm_moveit2` | Motion planning + IK | ✅ Complete |
| `robot_arm_hardware` | Servo control interface | ✅ Complete |
| `robot_arm_vision` | Autonomous sorting (YOLOv8) | ✅ Complete |
| `robot_arm_gesture` | Hand tracking control | ✅ Complete |
| `robot_arm_remote` | Internet teleoperation (MQTT) | ✅ Complete |
| `robot_arm_mode_manager` | Mode orchestration (state machine) | ✅ Complete |

---

## 🔨 Building & Deployment

### Build the Workspace
```bash
cd /home/natraj/file
colcon build --symlink-install
source install/setup.bash
```

### Where build artifacts go
- **build/** — Intermediate compilation outputs (auto-generated, safe to delete)
- **install/** — Final executables and binaries (auto-generated, safe to delete)
- **log/** — Build logs (auto-generated, safe to delete)

These folders regenerate automatically when you run `colcon build`.

---

## 📖 Documentation Tiers

### Tier 1: Essential Quick-Access (Root Level)
- Active guides you reference daily
- Kept in root for immediate visibility
- Files: README, START_HERE, DEPLOYMENT_READY, TEST_COMMANDS, REMAINING_STEPS, ESP32_QUICK_START, MoveIt_Troubleshooting

### Tier 2: Extended Reference (docs/)
- Detailed guides and extended documentation
- Historical records and supplementary materials
- Files: Hardware setup, calibration logs, learning guides, changelogs

### Tier 3: Archive (archive/)
- Legacy code and superseded versions
- Preserve for historical reference
- Files: hand_gesture_demo (original MediaPipe implementation)

---

## 🗂️ File Categories

### 📋 Documentation Files
- **Quick-start guides**: START_HERE.md, ESP32_CAM_QUICK_START.md
- **Reference guides**: README.md, MoveIt_Simulation_Troubleshooting.md
- **Deployment & testing**: DEPLOYMENT_READY.md, TEST_COMMANDS_CHECKLIST.md
- **Architecture & understanding**: PROJECT_STRUCTURE.md, PACKAGE_GUIDE.md, UNDERSTANDING_THE_CODE.md
- **Extended docs**: Everything in docs/ folder

### 🎮 Source Code (src/)
- 8 ROS 2 packages containing all production code
- Each package is self-contained with dependencies clearly defined
- See PACKAGE_GUIDE.md for what each does

### 🎨 Model Files
- **SDF files**: Gazebo physics models (red boxes for testing)
- **URDF files**: Robot kinematic models
- **PT files**: PyTorch ML weights (yolov8n.pt for vision)

### ⚙️ Configuration & Scripts
- **scripts/**: Setup and utility scripts (Arduino CLI environment)
- **Arduino staging**: USB pendrive package cache

### 🗑️ Auto-Generated (Safe to Delete)
- **build/**: Colcon build intermediates
- **install/**: Colcon install outputs
- **log/**: Build logs
- These regenerate automatically on next `colcon build`

---

## 🔄 Project Workflow

```
1. UNDERSTAND (You are here)
   ↓
2. MODIFY CODE (Edit src/ packages as needed)
   ↓
3. BUILD (`colcon build --symlink-install`)
   ↓
4. TEST (Use TEST_COMMANDS_CHECKLIST.md)
   ↓
5. DEPLOY (Follow DEPLOYMENT_READY.md)
```

---

## 📊 Project Status

**Completion**: 95% (as of April 30, 2026)

- ✅ Simulation infrastructure (Gazebo + MoveIt2 + RViz)
- ✅ Vision pipeline (YOLOv8 + MJPEG streaming)
- ✅ Local control (MediaPipe hand tracking)
- ✅ Remote control (MQTT + GitHub Pages web UI)
- ✅ Hardware interface (Arduino/PCA9685 servo driver)
- ✅ Physical arm deployment and calibration
- ⏳ Future: Migrate ML inference to Raspberry Pi 4/5

For detailed phase tracking, see REMAINING_STEPS.md and PROJECT_PROGRESS_COMPREHENSIVE.md.

---

## 💡 Common Tasks

| Task | Command | Location |
|------|---------|----------|
| Build all packages | `colcon build --symlink-install` | /home/natraj/file |
| Launch MoveIt planner | `ros2 launch robot_arm_moveit2 demo.launch.py` | src/robot_arm_moveit2 |
| Launch Gazebo sim | `ros2 launch robot_arm_gazebo gazebo_rviz.launch.py` | src/robot_arm_gazebo |
| Test hardware | `ros2 run robot_arm_hardware calibration_tester` | src/robot_arm_hardware |
| Deploy autonomous | `ros2 launch robot_arm_vision hardware_sorting.launch.py serial_port:=/dev/ttyUSB0 esp32_camera_url:=http://192.168.1.100:81/stream` | src/robot_arm_vision |
| Find ESP32 IP | See ESP32_UTILITIES.md | docs/ESP32_UTILITIES.md |
| Check build errors | `colcon test` | /home/natraj/file |

---

## 🆘 If You're Lost

1. **New to the project?** → Start with README.md
2. **Setting up ESP32?** → Follow START_HERE.md then ESP32_CAM_QUICK_START.md
3. **Want to understand code?** → Read PACKAGE_GUIDE.md then UNDERSTANDING_THE_CODE.md
4. **Troubleshooting?** → Check MoveIt_Simulation_Troubleshooting.md or docs/troubleshoots/
5. **Ready to deploy?** → Follow DEPLOYMENT_READY.md
