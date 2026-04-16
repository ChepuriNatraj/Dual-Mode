# SYSTEM ARCHITECTURE

## High-Level System Flow
The proposed architecture is compartmentalized into perception, planning, and execution tiers, interconnected via the ROS 2 middleware layer. The system functions in two mutually exclusive regimes designated as Autonomous Mode and Teleoperation Mode, governed by a central state machine. The transition between these modes is achieved through explicit MQTT triggers or ROS 2 service calls.

## ROS 2 Node Architecture
The system leverages a decentralized node topology utilizing ROS 2 Data Distribution Service (DDS). The primary nodes include:
1. `vision_processing_node`: Ingests camera streams and publishes spatial coordinates of target objects via YOLOv8.
2. `gesture_capture_node`: Computes human hand landmarks utilizing MediaPipe and publishes target joint angles.
3. `mode_manager_node`: The centralized state machine that multiplexes incoming commands (vision vs. gesture) based on the active operational state.
4. `moveit_trajectory_node`: Subscribes to target poses/angles, computes numerical Inverse Kinematics, and publishes `JointTrajectory` messages.
5. `hardware_interface_node`: Subscribes to trajectories, translating them into serial/I2C protocols executable by the edge microcontrollers.

## Data Pipelines (Vision, Gesture, MQTT)
1. **Vision Pipeline:** RGB data → YOLOv8 Inference → Bounding Box/Centroid Extraction → Depth Mapping (Coordinate Transform) → TF2 Broadcast → MoveIt Pose Goal.
2. **Gesture Pipeline:** RGB data → MediaPipe Hand Tracking → Vector Angle Computation → Low-Pass Filtering → Joint Space Mapping → MoveIt Joint Goal.
3. **Telemetry/MQTT Pipeline:** ESP32 diagnostics (current draw, joint positions, mode status) → MQTT Broker → ROS 2 `diagnostic_updater` → User Interface.

[FIGURE 4: ROS 2 Node Graph (rqt_graph) detailing the publish/subscribe relationships between the vision, gesture, planning, and hardware nodes.]

[FIGURE 5: Data pipeline flowchart showing the transformation of raw sensor data into final PWM signals.]