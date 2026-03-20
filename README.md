# Dual-Mode Vision-Guided Robotic Arm

Design and development of a 6-DOF robotic arm that supports:

- Autonomous vision-based object sorting
- Local gesture teleoperation
- Remote internet-based gesture control
- Automatic mode switching between AUTO, LOCAL, and REMOTE

Current platform:

- Ubuntu 24.04 LTS
- ROS 2 Jazzy
- Gazebo Harmonic
- MoveIt 2

## Current Project Status

Simulation and core motion planning are working, with vision and remote-control phases in progress.

- URDF migration and simulation debugging: complete
- Gazebo Harmonic launch pipeline: working
- MoveIt 2 setup and planning: mostly working
- Gesture demo prototype: working in RViz
- Vision sorting, MQTT remote mode, and hardware interface: pending

Detailed progress lives in:

- PROGRESS.md
- REMAINING_STEPS.md
- MoveIt_Simulation_Troubleshooting.md

## Repository Structure

```text
.
├── src/
│   ├── robot_arm_description/      # URDF/Xacro, meshes, base launch files
│   ├── robot_arm_gazebo/           # Gazebo Harmonic launch + controllers
│   └── robot_arm_moveit2/          # MoveIt2 config and launch files
├── PROGRESS.md
├── REMAINING_STEPS.md
├── MoveIt_Simulation_Troubleshooting.md
├── run_moveit_setup.sh
└── scripts and helper notes
```

## Quick Start

### 1) Build

```bash
cd /home/natraj/file
source /opt/ros/jazzy/setup.bash
colcon build --symlink-install
source install/setup.bash
```

### 2) Launch MoveIt Demo

```bash
ros2 launch robot_arm_moveit2 demo.launch.py
```

### 3) Launch Gazebo + RViz Pipeline

```bash
ros2 launch robot_arm_gazebo gazebo_rviz.launch.py
```

## Next Milestones

- Finalize controller bridge so MoveIt execution drives Gazebo arm motion directly
- Add OpenCV + YOLOv8 perception pipeline for autonomous sorting
- Integrate MediaPipe gesture control into controller trajectory flow
- Add MQTT bridge for remote phone control
- Implement robust mode manager and safety timeouts

## Notes

- This repository currently includes development notes and troubleshooting docs used during active implementation.
- Build artifacts are excluded via .gitignore.

## Author

Maintainer: Natraj
