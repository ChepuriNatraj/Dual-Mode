# Project Progress Tracking

## Completed Tasks
* [x] Analyzed the initial `robot_arm_description` URDF and workspace.
* [x] Identified MoveIt 2 and Gazebo Harmonic integration issues related to `<mimic>` joints.
* [x] Created `updates.md` to document the strategy and set up `robot_arm_gazebo` package.
* [x] Created `gazebo.launch.py` and `gazebo_rviz.launch.py` to spawn the robot in Gazebo Harmonic.
* [x] Solved missing mesh errors by exporting `GZ_SIM_RESOURCE_PATH`.
* [x] Solved mimic joint capabilities in Gazebo by specifying `--physics-engine gz-physics-bullet-featherstone-plugin` in launch files.
* [x] Replaced legacy ROS 1 `libgazebo_ros_control.so` and `<transmission>` tags with ROS 2 `<ros2_control>` tags and `gz_ros2_control-system`.
* [x] Generated a complete MoveIt 2 configuration package (`robot_arm_moveit2`).
* [x] Added manually created `initial_positions.yaml` dummy values to prevent MoveIt Setup Assistant Xacro `NoneType` errors.
* [x] Tracked down and safely overrode MoveIt's trajectory generation limits (fixed `max_velocity` boundaries from 0.0 to 1.0).
* [x] Mapped `action_ns: follow_joint_trajectory` on MoveIt controllers so execution properly reaches the correct action servers locally.
* [x] Enabled 5-DOF structural IK by injecting `position_only_ik: True` into `kinematics.yaml`, solving Interactive Marker snap-back singularities. 
* [x] Handled floor crashing issues by demonstrating how to use "Scene Objects" in RViz for virtual collision boxes.
* [x] Created a comprehensive breakdown guide of debugging cases in `MoveIt_Simulation_Troubleshooting.md`.
* [x] Firmly rooted the robotic arm to the Gazebo environment by injecting a `<link name="world"/>` fix directly to `base_link` inside `robotic_arm.xacro`.
* [x] Upgraded `robotic_arm.gazebo` to use modern `gz_ros2_control::GazeboSimROS2ControlPlugin`.
* [x] Connected MoveIt 2 to Gazebo Harmonic by explicitly providing a `use_fake_hardware:=false` mapping inside `moveit_gazebo.launch.py`.
* [x] Fixed RViz timer mismatch flickering and TF jumps by configuring `use_sim_time: true` across all Controller Managers and Launch parameters.

## Current Issues & Roadblocks
* [ ] **Ogre Material Warnings:** The legacy material "Gazebo/Silver" generates warnings in Gazebo Harmonic. This isn't fatal as it falls back to default, but eventually, standard modern PBR materials should be applied.

## Next Steps
* [ ] Proceed to Phase 2: Integrate MediaPipe live tracking directly into MoveIt 2's action server to control the simulation dynamically from the webcam.
