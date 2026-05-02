# Dual-Mode Vision-Guided Robotic Arm

Design and development of a 6-DOF robotic arm that seamlessly bridges fully autonomous operation and human-in-the-loop teleoperation.

The system is designed to sort objects across a workspace completely hands-free using edge AI (OpenCV + YOLOv8). By simply showing a hand to a camera or a mobile phone from anywhere over the internet, a human operator can instantly seize remote teleoperation (via MediaPipe kinematics mapping), effectively providing a zero-UI override for industrial and assistive robotic arms. 

## Operating Environment
- **OS:** Ubuntu 24.04 LTS
- **Middleware:** ROS 2 Jazzy Jalisco
- **Simulation:** Gazebo Harmonic
- **Motion Planning:** MoveIt 2
- **Hardware Profile:** Custom 6-DOF Metal Servo Arm + Arduino Mega / PCA9685

---

## 🎯 Current Project Status: Hardware Integration & Remote Teleoperation Complete

The core architectural simulation infrastructure is fully established, and we have successfully bridged the gap to physical hardware and remote AI control. The custom C++ ROS 2 hardware interface correctly mirrors MoveIt 2 trajectories to physical servos via an Arduino/ESP32, calibrated with custom joint offsets. Additionally, a secure MediaPipe-driven web interface hosted on GitHub Pages enables full 0-infrastructure remote internet teleoperation via HiveMQ MQTT.

**Milestone Checklist:**
- [x] URDF ROS 2 migration and Jazzy compliance
- [x] MoveIt 2 Setup Assistant generation and parameterization tuning
- [x] Resolution of Gazebo physics constraints dropping mimic meshes
- [x] KDL Inverse Kinematics modifications for smooth 5-DOF Interactive Markers
- [x] Connect MoveIt RViz execution directly to Gazebo simulated JointTrajectoryControllers
- [x] Implement OpenCV/YOLOv8 vision pipeline (`robot_arm_vision`)
- [x] Implement MediaPipe gesture capturing (`robot_arm_gesture`)
- [x] Develop MQTT Bridge for internet-based control (`robot_arm_remote`)
- [x] Construct custom ROS2 C++ `hardware_interface` for physical servos

For deep tracking of solved challenges, see [MoveIt_Simulation_Troubleshooting.md](./docs/MoveIt_Simulation_Troubleshooting.md).
For granular steps forward, refer to [REMAINING_STEPS.md](./docs/REMAINING_STEPS.md).
For external Arduino/ESP32 USB environment handoff details, see [docs/ARDUINO_PENDRIVE_ENV.md](./docs/ARDUINO_PENDRIVE_ENV.md).
For gripper calibration note-taking and tested safe limits, see [docs/GRIPPER_LIMIT_CALIBRATION_LOG.md](./docs/GRIPPER_LIMIT_CALIBRATION_LOG.md).

---

## 📁 Repository Structure

```text
.
├── src/
│   ├── robot_arm_description/      # Xacro URDF, STL material meshes, legacy configs
│   ├── robot_arm_gazebo/           # Launch files bridging ROS 2 to Gazebo Harmonic
│   ├── robot_arm_moveit2/          # MoveIt2 semantic format (SRDF), kinematics, trajectories
│   ├── robot_arm_hardware/         # C++ ROS2 hardware interface, Arduino firmware, calibration
│   ├── robot_arm_vision/           # ESP32-CAM MJPEG server and YOLOv8 AI sorting logic
│   ├── robot_arm_gesture/          # Local MediaPipe webcam hand tracking control
│   └── robot_arm_remote/           # MQTT Bridge and GitHub Pages Web UI
├── progress.md                     # Raw checklist of accomplished tasks
├── PROGRESS.md                     # Detailed phases and bug fixes tracking
├── docs/REMAINING_STEPS.md              # Live checklist for the remaining Vision & AI phases
├── docs/MoveIt_Simulation_Troubleshooting.md # Guide covering 8 major MoveIt/Gazebo bugs faced
└── (Build artifacts naturally excluded via .gitignore)
```

---

## 🚀 Quick Start (Simulation)

Ensure ROS 2 Jazzy is sourced in your environment.

### 1) Build the Workspace
```bash
cd /home/natraj/file
colcon build --symlink-install
source install/setup.bash
```

### 2) Launch the MoveIt 2 Interactive Planner
This launches RViz with the configured robot. You can drag the RGB interactive marker and execute path planning sequences.
```bash
ros2 launch robot_arm_moveit2 demo.launch.py
```

### 3) Launch the Physics Environment (Gazebo)
This spawns the URDF with its `ros2_control` parameters directly inside Gazebo Harmonic, ready to receive `/joint_trajectory` commands.
```bash
ros2 launch robot_arm_gazebo gazebo_rviz.launch.py
```

## Authors
**Maintainer:** Chepuri Natraj
