#!/bin/bash
# Build and setup autonomous sorting system for real hardware

set -e  # Exit on error

echo "======================================"
echo "Building Autonomous Sorting System"
echo "======================================"

cd ~/file

echo ""
echo "[1/3] Building ROS 2 packages..."
colcon build --packages-select \
    robot_arm_vision \
    robot_arm_moveit2 \
    robot_arm_hardware \
    robot_arm_gesture \
    robot_arm_mode_manager \
    robot_arm_remote \
    --symlink-install \
    --cmake-args -DCMAKE_BUILD_TYPE=Release

echo ""
echo "[2/3] Sourcing install space..."
source ~/file/install/setup.bash

echo ""
echo "[3/3] Verifying installations..."
ros2 pkg list | grep -E "robot_arm_vision|robot_arm_hardware|robot_arm_mode_manager" || (echo "❌ Package not found"; exit 1)

echo ""
echo "======================================"
echo "✅ Build Complete!"
echo "======================================"
echo ""
echo "Next steps:"
echo "1. Configure ESP32-CAM IP in the launch parameters"
echo "2. Run: ros2 launch robot_arm_vision hardware_sorting.launch.py"
echo ""
echo "For more details, see:"
echo "  - docs/AUTONOMOUS_SORTING_QUICKSTART.md"
echo "  - docs/HARDWARE_AUTONOMOUS_SORTING_SETUP.md"
echo ""
