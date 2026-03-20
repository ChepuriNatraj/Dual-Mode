#!/bin/bash
# Helper script to launch MoveIt2 Setup Assistant for our specific Robotic Arm configuration

echo "=========================================================="
echo "          Launching MoveIt 2 Setup Assistant              "
echo "=========================================================="
echo ""
echo "IMPORTANT REMINDER FOR THIS SPECIFIC ROBOT:"
echo "1. When loading the URDF, make sure it pulls the Xacro from:"
echo "   src/robot_arm_description/urdf/robotic_arm.xacro"
echo ""
echo "2. PLANNING GROUPS:"
echo "   - Create 'arm' group with links: link_1 -> link_6"
echo "   - Create 'gripper' group focused only on link_6 as the active parent"
echo ""
echo "3. *** PASSIVE JOINTS (CRITICAL FIX FOR THE MIMIC ISSUE) ***:"
echo "   - Go to 'Passive Joints' tab"
echo "   - MUST check the following joints so MoveIt ignores them:"
echo "     * link_10"
echo "     * link_11"
echo "     * link_12"
echo "     * link_13"
echo "   - Why? Because Gazebo Harmonic physics will mechanically drive these!"
echo ""
echo "4. ROS 2 CONTROLLERS:"
echo "   - Make sure you specify standard JointTrajectoryControllers for the active groups."
echo ""
echo "=========================================================="

source /opt/ros/jazzy/setup.bash
source install/setup.bash
ros2 run moveit_setup_assistant moveit_setup_assistant
