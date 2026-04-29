# Autonomous Sorting Hardware Setup Guide

Complete step-by-step guide for testing autonomous sorting on real hardware with an ESP32 camera.

## Prerequisites

- Physical robotic arm with servos and gripper
- ESP32 controller running the custom firmware
- PCA9685 PWM driver (I2C interface)
- ESP32-CAM module connected to WiFi
- Linux PC running ROS 2 Jazzy
- All hardware properly calibrated and powered

## Step 1: Verify Hardware Calibration

Before running autonomous sorting, ensure:

1. **Gripper calibration**: Verify open/close limits are correctly set
   ```bash
   cat ~/file/docs/GRIPPER_LIMIT_CALIBRATION_LOG.md
   ```

2. **Serial communication**: Test direct serial connection
   ```bash
   python3 ~/file/src/robot_arm_hardware/calibration_tester.py
   ```

3. **Motor responsiveness**: Quick hardware test
   ```bash
   ros2 run robot_arm_hardware ros2_control_node --ros-args -p serial_port:=/dev/ttyUSB0
   ```

## Step 2: ESP32-CAM Setup

### 2.1 Flash the ESP32-CAM Firmware

```bash
# Setup Arduino environment (if not already done)
source ~/file/scripts/use_pendrive_env.sh

# Compile the ESP32-CAM firmware
arduino-cli compile --fqbn esp32:esp32:esp32-cam \
    ~/file/src/robot_arm_vision/firmware/esp32_camera/esp32_camera.ino \
    --config-file "$ARDUINO_DATA_DIR/arduino-cli.yaml"

# Upload to ESP32-CAM
# First, put ESP32-CAM in programming mode (GPIO0 to GND)
arduino-cli upload -p /dev/ttyUSB0 --fqbn esp32:esp32:esp32-cam \
    ~/file/src/robot_arm_vision/firmware/esp32_camera \
    --config-file "$ARDUINO_DATA_DIR/arduino-cli.yaml"
```

### 2.2 Configure ESP32-CAM WiFi

Edit the firmware to match your WiFi credentials:
```cpp
const char* ssid = "YOUR_SSID";
const char* password = "YOUR_PASSWORD";
```

### 2.3 Verify MJPEG Stream

After flashing:

```bash
# Find ESP32-CAM IP from your router or serial monitor
# Then test the stream (replace 192.168.1.100 with actual IP)

python3 -c "
import cv2
cap = cv2.VideoCapture('http://192.168.1.100:81/stream')
for i in range(10):
    ret, frame = cap.read()
    print(f'Frame {i}: {\"OK\" if ret else \"FAIL\"} - Shape: {frame.shape if ret else \"N/A\"}')
    cv2.imshow('Test', frame)
    cv2.waitKey(100)
cap.release()
"
```

## Step 3: Robot Arm Controller Setup

### 3.1 Verify the Robot Controller Firmware

The main ESP32 (controlling arm/gripper via PCA9685) must be running the correct firmware:

```bash
# Check if firmware is already loaded
python3 ~/file/src/robot_arm_hardware/calibration_tester.py

# If needed, upload fresh firmware
source ~/file/scripts/use_pendrive_env.sh
arduino-cli upload -p /dev/ttyUSB0 --fqbn esp32:esp32:esp32 \
    ~/file/src/robot_arm_hardware/firmware \
    --config-file "$ARDUINO_DATA_DIR/arduino-cli.yaml"
```

### 3.2 Verify Serial Port

```bash
ls -la /dev/ttyUSB*
# Should see /dev/ttyUSB0 or /dev/ttyUSB1
```

## Step 4: Build ROS Packages

Build all updated packages:

```bash
cd ~/file
colcon build --packages-select \
    robot_arm_moveit2 \
    robot_arm_hardware \
    robot_arm_vision \
    robot_arm_gesture \
    robot_arm_mode_manager \
    robot_arm_remote \
    --symlink-install
```

Source the install space:

```bash
source ~/file/install/setup.bash
```

## Step 5: Camera Calibration

The vision system needs accurate camera intrinsics. Calibrate your ESP32-CAM:

```bash
# Using ROS calibration tools
ros2 run camera_calibration cameracalibrator --size 8x6 --square 0.05 \
    --ros-args -r image:=/camera/image_raw -r camera:=/camera
```

After calibration, update the launch parameters:
- `fx`, `fy`: Focal length in pixels
- `cx`, `cy`: Principal point (image center)

Or estimate based on camera specs (typically fx=fy=500 for ~60deg FOV @ 640x480).

## Step 6: Configure Workspace Bounds

Edit [`src/robot_arm_vision/robot_arm_vision/vision_node.py`](../robot_arm_vision/robot_arm_vision/vision_node.py):

```python
self.camera_height = 0.8  # Height of camera above workspace
self.workspace_z = 0.02   # Height of objects to pick
self.min_world_x = 0.15   # Min/max reach in X (forward/back)
self.max_world_x = 0.45
self.min_world_y = -0.25  # Min/max reach in Y (left/right)
self.max_world_y = 0.25
```

## Step 7: Run Autonomous Sorting

### Full Hardware Autonomous Sorting

```bash
# Terminal 1: Launch everything
ros2 launch robot_arm_vision hardware_sorting.launch.py \
    serial_port:=/dev/ttyUSB0 \
    baud_rate:=115200 \
    esp32_camera_url:=http://192.168.1.100:81/stream
```

This starts:
1. ✅ Robot state publisher (URDF/kinematics)
2. ✅ Controller manager + joint_state_broadcaster
3. ✅ Arm & gripper trajectory controllers
4. ✅ ESP32 camera MJPEG bridge
5. ✅ Vision node (YOLO detection + calibration)
6. ✅ Sorting planner (MoveIt trajectory planning)
7. ✅ Mode manager (AUTONOMOUS mode)

### Monitor the System

In separate terminals:

```bash
# See published object detections
ros2 topic echo /target_pose

# See executed arm trajectories
ros2 topic echo /arm_controller/joint_trajectory

# See vision processing frames
# (Visual window should appear showing detected objects)

# Check system diagnostics
ros2 node list
ros2 topic list
```

## Step 8: Test Autonomous Sorting Cycle

### Single Object Test

1. Place a colored object in the workspace (camera's field of view)
2. Watch the vision node detect and publish its position
3. Watch the sorting planner:
   - Move to pre-grasp position
   - Open gripper
   - Descend to grasp
   - Close gripper
   - Lift object
   - Move to drop position
   - Release object
   - Return home

### Continuous Sorting Loop

```bash
# The system runs autonomously - just keep placing objects in view!
# Watch terminal logs for:
# - "STARTED AI SORTING LOOP"
# - "CYCLE COMPLETE"

# Stop with Ctrl+C
```

## Troubleshooting

### ESP32-CAM Not Streaming

```bash
# Check WiFi connection
# Check ESP32-CAM serial output (115200 baud)
# Verify IP address and port
ping 192.168.1.100
curl http://192.168.1.100:81/stream -v  # Should show MJPEG headers
```

### Vision Node Not Detecting Objects

- Check camera calibration (fx, fy, cx, cy)
- Verify object is within workspace bounds
-Ensure good lighting (YOLOv8 needs contrast)
- Check YOLO model is loaded (see logs)

### Arm Not Moving

1. Check hardware bringup logs:
   ```bash
   ros2 launch robot_arm_hardware hardware_gesture.launch.py
   ```

2. Verify mode manager is in AUTONOMOUS:
   ```bash
   ros2 topic pub /system_mode std_msgs/String "{data: AUTONOMOUS}"
   ```

3. Check if vision is publishing targets:
   ```bash
   ros2 topic echo /target_pose
   ```

### Gripper Not Opening/Closing

- Verify gripper controller is spawned
- Test manually: `ros2 topic pub --once /gripper_controller/joint_trajectory ...`

## Performance Tuning

### Reduce Latency

- Increase vision publish rate (reduce sleep in vision_node.py)
- Reduce planning timeout (sorting_planner_node.py)
- Use faster camera (higher FPS)

### Improve Accuracy

- Recalibrate camera intrinsics
- Verify object heights (workspace_z parameter)
- Use more detection confidence threshold

### Safety

- Always have emergency stop nearby (Ctrl+C)
- Test with empty workspace first
- Verify gripper force is gentle (tunable in hardware)
- Check arm never exceeds joint limits (in URDF)

## Next Steps

- [ ] Test 50-cycle continuous autonomous sorting
- [ ] Integrate with mode switching (switch between AUTONOMOUS and GESTURE)
- [ ] Add MQTT telemetry integration
- [ ] Implement object classification by color/size
- [ ] Add dynamic bin selection based on object class
