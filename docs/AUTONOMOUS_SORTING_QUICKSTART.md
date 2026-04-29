# Autonomous Sorting Hardware - QUICKSTART

Complete end-to-end setup and testing for autonomous robotic arm sorting on real hardware with ESP32 camera.

## What Was Just Implemented

✅ **ESP32 Camera MJPEG Bridge** (`esp32_camera_bridge.py`)
   - Connects to ESP32-CAM wireless MJPEG stream
   - Publishes ROS 2 Image + CameraInfo messages
   - Automatic reconnection with configurable intervals
   - Full camera intrinsic calibration support

✅ **Hardware Autonomous Sorting Launch** (`hardware_sorting.launch.py`)
   - Complete one-command bringup for real hardware
   - Orchestrated startup: hardware → mode manager → vision → sorting planner
   - Full integration with gesture and remote modes via mode manager
   - Staggered timers to ensure clean initialization

✅ **Updated Sorting Planner** (integration with mode manager)
   - Publishes trajectories to `/auto_controller/joint_trajectory`
   - Proper mode-aware execution through mode manager

✅ **Documentation**
   - Full hardware setup guide with calibration steps
   - Firmware flashing instructions for ESP32-CAM
   - Workspace configuration guidelines
   - Troubleshooting checklist

---

## Quick Build & Test (60 seconds)

### Step 1: Build Updated Packages
```bash
cd ~/file
colcon build --packages-select \
    robot_arm_vision \
    robot_arm_moveit2 \
    robot_arm_hardware \
    robot_arm_gesture \
    robot_arm_mode_manager \
    --symlink-install --cmake-args -DCMAKE_BUILD_TYPE=Release
```

### Step 2: Source Environment
```bash
source ~/file/install/setup.bash
```

### Step 3: Launch Full Autonomous Sorting (requires configured ESP32-CAM IP)

Replace `192.168.1.100` with your actual ESP32-CAM IP:

```bash
ros2 launch robot_arm_vision hardware_sorting.launch.py \
    serial_port:=/dev/ttyUSB0 \
    baud_rate:=115200 \
    esp32_camera_url:=http://192.168.1.100:81/stream
```

### Step 4: Monitor & Test

In separate terminals:

**Terminal A - Watch object detection:**
```bash
ros2 topic echo /target_pose
# Should see PoseStamped messages when objects are in view
```

**Terminal B - Watch arm trajectories:**
```bash
ros2 topic echo /arm_controller/joint_trajectory
# Should see joint configurations as arm moves
```

**Terminal C - Check system health:**
```bash
ros2 node list  # Should see 7+ nodes
ros2 topic list | wc -l  # Should see 15+ topics
```

### Step 5: Test Autonomous Loop

1. Place a colored object in the camera's field of view (workspace)
2. Vision node detects it (look for "Published target" in terminal logs)
3. Sorting planner executes full pick-and-place sequence:
   - Pre-grasp hover
   - Open gripper
   - Descend to grasp
   - Close gripper
   - Lift
   - Move to drop bin
   - Release
   - Return home
4. Place next object → Cycle repeats!

---

## Testing Commands

### Test ESP32-CAM Stream (Before ROS)

```bash
python3 << 'EOF'
import cv2
url = "http://192.168.1.100:81/stream"
cap =cv2.VideoCapture(url)
if cap.isOpened():
    print(f"✅ Connected to {url}")
    ret, frame = cap.read()
    if ret:
        print(f"✅ Received frame: {frame.shape}")
        cv2.imshow("ESP32-CAM Test", frame)
        cv2.waitKey(3000)
        cv2.destroyAllWindows()
    else:
        print("❌ Failed to read frame")
else:
    print(f"❌ Cannot connect to {url}")
cap.release()
EOF
```

### Test Gesture Node (for quick manual control)

Quick test to ensure hardware responds to commands:

```bash
ros2 launch robot_arm_hardware hardware_gesture.launch.py \
    camera_index:=0
# Move your hand - arm should follow
```

### Test Hardware Only (no vision)

```bash
ros2 launch robot_arm_hardware hardware_gesture.launch.py \
    serial_port:=/dev/ttyUSB0 \
    baud_rate:=115200
```

### Test Vision Without Sorting

```bash
# Camera + Vision node only (no planner execution)
ros2 launch robot_arm_vision sorting.launch.py
# Watch /target_pose for detected objects
```

---

## Key Parameters to Tune

**Camera Calibration** (`hardware_sorting.launch.py`):
```python
{'fx': 500.0},      # Focal length X (pixels)
{'fy': 500.0},      # Focal length Y (pixels)
{'cx': 320.0},      # Image center X (pixels)
{'cy': 240.0},      # Image center Y (pixels)
```

**Workspace Bounds** (`vision_node.py`):
```python
self.camera_height = 0.8      # Height of camera above table
self.workspace_z = 0.02       # Height of objects to pick

self.min_world_x = 0.15       # Forward (minimum)
self.max_world_x = 0.45       # Forward (maximum)
self.min_world_y = -0.25      # Left/right (minimum)
self.max_world_y = 0.25       # Left/right (maximum)
```

**Gripper Calibration** (`sorting_planner_node.py`):
```python
pt.positions = [0.0]          # Open gripper (fully open)
pt.positions = [-1.0472]      # Close gripper (~60° from open)
```

---

## Common Issues & Fixes

| Issue | Solution |
|-------|----------|
| `Cannot connect to ESP32-CAM` | Check WiFi IP, verify camera powered, test with curl |
| `No objects detected` | Improve lighting, check YOLO min confidence, verify workspace params |
| `Arm not moving` | Test hardware_gesture.launch.py first, check serial port, verify controller status |
| `Gripper stuck` | Run gripper calibration test, check PCA9685 I2C connection |
| `Slow planning` | Reduce planning timeout, use faster IK seed, pre-compute common positions |

---

## Architecture Overview

```
Physical Hardware
├── ESP32-CAM (WiFi MJPEG stream)
│   └─→ esp32_camera_bridge (ROS node)
│       └─→ /camera/image_raw (ROS Image topic)
│
├── ESP32 + PCA9685 (Arm & Gripper)
│   └─→ ros2_control SystemInterface (C++ hardware plugin)
│
└─→ robot_state_publisher
    ├─→ /joint_states (from joint_state_broadcaster)
    └─→ /tf (kinematics transforms)

Vision Pipeline
├─→ vision_node (IP camera frames → OpenCV/YOLO)
    └─→ /target_pose (detected object 3D world coordinates)
    
└─→ sorting_planner_node (MoveIt trajectory planning)
    └─→ /auto_controller/joint_trajectory (planned motion)

Control Arbitration
└─→ mode_manager_node (AUTONOMOUS/LOCAL/REMOTE selector)
    ├─ Listens: /auto_controller, /local_controller, /remote_controller
    └─ Publishes: /arm_controller/joint_trajectory (active mode only)

Hardware Execution
└─→ arm_controller (ros2_control follower)
    └─→ SystemInterface (serial to ESP32)
        └─→ PCA9685 PWM → Servo Motors
```

---

## Next Steps

- [ ] Calibrate camera intrinsics (fx, fy, cx, cy)
- [ ] Define exact workspace bounds for your table setup
- [ ] Test 10-cycle continuous sorting (consistency check)
- [ ] Tune gripper open/close positions for your specific hardware
- [ ] Adjust pre-grasp hover distance to prevent collisions
- [ ] Integrate object classification (by color, size, type)
- [ ] Add dynamic bin selection based on object class
- [ ] Test mode switching (AUTONOMOUS ↔ GESTURE) during execution

---

## Support Files

- **Setup Guide**: [docs/HARDWARE_AUTONOMOUS_SORTING_SETUP.md](../docs/HARDWARE_AUTONOMOUS_SORTING_SETUP.md)
- **Vision Node**: [src/robot_arm_vision/robot_arm_vision/vision_node.py](../src/robot_arm_vision/robot_arm_vision/vision_node.py)
- **Sorting Planner**: [src/robot_arm_vision/robot_arm_vision/sorting_planner_node.py](../src/robot_arm_vision/robot_arm_vision/sorting_planner_node.py)
- **ESP32 Camera Bridge**: [src/robot_arm_vision/robot_arm_vision/esp32_camera_bridge.py](../src/robot_arm_vision/robot_arm_vision/esp32_camera_bridge.py)
- **Hardware Sorting Launch**: [src/robot_arm_vision/launch/hardware_sorting.launch.py](../src/robot_arm_vision/launch/hardware_sorting.launch.py)

---

**Ready to sort! 🤖**

build, source environment, and launch `hardware_sorting.launch.py` with your ESP32-CAM IP.
