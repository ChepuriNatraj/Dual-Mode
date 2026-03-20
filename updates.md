* 6-DOF custom robotic arm designed in Fusion 360 and exported to URDF.
* Operating Environment: ROS 2 Jazzy, Gazebo Harmonic, Linux.
* Current Issue: Gripper mimic joints act individually in MoveIt 2 Setup Assistant and conflict with Gazebo Harmonic physics engine.
* Planned Resolution: Define mimic fingers as "Passive Joints" in MoveIt 2 and only include the active driver joint in the planning group.
* Planned Resolution: Adjust `ros2_control` hardware interfaces to only send commands to the active joint and update Gazebo configurations to handle mimic visual states/physics.
* Completed Task: Set up a dedicated `robot_arm_gazebo` package with Launch files (Gazebo + RViz).
* Resolved Issue: Fixed classic Gazebo plugins `libgazebo_ros_control.so` to modern `gz_ros2_control-system` for Harmonic.
* Resolved Issue: Exported `GZ_SIM_RESOURCE_PATH` to resolve `model://` URI mesh not found errors.
* Resolved Issue: Changed Gazebo Harmonic physics engine to `gz-physics-bullet-featherstone-plugin` to correctly support URDF `<mimic>` joints (Dart engine lacks mimic support).
* Resolved Issue: Fixed mesh loading in Gazebo by converting `package://` URIs to `model://` in `robotic_arm.xacro` and correctly exporting the workspace install path.
* Completed Task: Modernized `<ros2_control>` tags in `robotic_arm.trans`, successfully isolating passive mimic joints from active driver joints.
* Discovered Issue: Gazebo throws warnings for legacy Ogre `Gazebo/Silver` materials. Not a fatal error (Harmonic uses defaults), but good to note.
* Resolved Issue: MoveIt 2 demo threw a parsing error (`'NoneType' object is not subscriptable`) because `config/initial_positions.yaml` was empty.
* Completed Task: Wrote a base `initial_positions.yaml` file so the MoveIt 2 Setup Assistant correctly parses `ros2_control.xacro`. 
* Next Task: Implement real `controllers.yaml` integration with Gazebo if required, mapping the physical trajectory bounds.
## Latest Progress: MoveIt 2 Tuning and Fixes
- Fixed MoveIt `joint_limits.yaml` to override 0.0 velocity/acceleration values, enabling Time-Optimal Trajectory planning.
- Fixed `moveit_controllers.yaml` to include correct `action_ns: follow_joint_trajectory` namespaces.
- Prevented 5-DOF IK Singularity issues by enabling `position_only_ik: True` in `kinematics.yaml`.
- Solved ground collision bug by teaching the addition of virtual Scene Objects in RViz.
- Status: Fully working MoveIt + ROS2 + Gazebo Harmonic pipeline!

