# IMPLEMENTATION

## URDF Modeling
The physical properties of the robotic arm are modeled using the Unified Robot Description Format (URDF). Each link is defined with inertial parameters (mass, center of mass, inertia tensor), visual geometries (STL meshes), and collision geometries (simplified primitives bounding the visual meshes). The joints are defined as revolute, with precise hardware-matched actuator limits (effort, velocity, and positional limits in radians).

## Gazebo Simulation
Prior to hardware deployment, the system is rigorously tested in a physics-accurate Gazebo simulation environment. Plugins such as `gazebo_ros2_control` are integrated to simulate joint actuation dynamics. A virtual camera (utilizing the `gazebo_ros_camera` plugin) is spawned within the simulation to generate synthetic RGB feeds, facilitating the testing of the YOLOv8 and visual mapping pipelines without necessitating physical hardware setup.

## ROS 2 Package Structure
The repository is modularly structured into the following key packages:
- `robotic_arm_description`: Contains URDF, meshes, and launch files for RViz visualization.
- `robotic_arm_moveit_config_v2`: Auto-generated and refined MoveIt configurations, including SRDF, kinematics.yaml, and controller alignments.
- `robot_arm_gazebo`: Worlds, spawning scripts, and physics tuning for simulation.
- `robot_arm_vision`: Python nodes encapsulating OpenCV, YOLOv8 inference, and coordinate transformation logic.
- `robot_arm_gesture`: Python nodes containing MediaPipe dependencies and kinematic translation algorithms.
- `robot_arm_hardware`: The `ros2_control` hardware interface written in C++ for optimized serialization, alongside ESP32 firmware.
- `robot_arm_remote`: MQTT bridges and high-level teleoperation logic.

## Communication Layers
Intra-system communication heavily relies on the FastDDS implementation within ROS 2. Custom message types were defined for specialized gesture telemetry. Hardware-level communication between the host PC and the ESP32 is routed over a dedicated 115200 baud UART connection or via a localized MQTT broker for untethered operation, ensuring low-overhead execution of the PWM commands.

[FIGURE 8: Visual representation of the URDF model rendered in RViz showing coordinate frames (TF) at each joint.]

[FIGURE 9: Architecture diagram detailing the ROS 2 workspace package hierarchy and dependency flow.]