# METHODOLOGY

## Vision Pipeline (OpenCV + YOLOv8)
The autonomous sorting capability is predicated on a real-time visual recognition pipeline. An RGB camera feed is processed using OpenCV and subsequently fed into a pre-trained YOLOv8 neural network. The network isolates specific target classes (e.g., specific sorting objects). The 2D bounding box centroids are extracted and projected into a 3D coordinate space using camera intrinsic parameters and depth estimation techniques. These spatial coordinates are broadcast to the ROS 2 TF2 (Transform) tree, enabling the motion planner to define target end-effector poses relative to the robot's base link.

## Gesture Mapping (MediaPipe → Joint Angles)
Human-in-the-loop control is facilitated by MediaPipe’s hand landmark detection. Specific phalanx vectors are calculated from the derived 3D landmark coordinates. The respective angles between these vectors (e.g., index finger flexion, wrist rotation) are mapped linearly to the allowable joint limits of the robotic arm. A Savitzky-Golay filter is applied to the raw angular data to attenuate high-frequency noise inherent in markerless tracking, ensuring smooth manipulator actuation.

## Mode Manager Logic (State Machine)
To prevent command collision, a multiplexing mode manager is implemented. 
- **State A (Autonomous):** The gesture node is paused. The system polls the vision node for target coordinates, formulates a grasp plan, executes the trajectory, and returns to a home position.
- **State B (Teleoperation):** The vision node is deprecated. The system enables high-frequency streaming of joint targets from the gesture node directly to the low-level controller, bypassing complex trajectory generation to minimize latency.

## Motion Planning (MoveIt2 IK)
For autonomous operations, MoveIt2 is utilized. The kinematic chain is defined within a SRDF (Semantic Robot Description Format) file. The KDL (Kinematics and Dynamics Library) plugin is used as the underlying numerical IK solver. Obstacle avoidance is handled dynamically by updating the MoveIt planning scene with collision objects detected by the vision system.

## Control Execution (ros2_control → ESP32 → PCA9685)
The computed trajectories are consumed by a custom `ros2_control` hardware interface. This interface serializes the desired joint states and transmits them to an ESP32 microcontroller via a secure connection (Serial or MQTT). The ESP32 parses these commands and utilizes the I2C protocol to interface with a PCA9685 16-channel PWM driver. The PCA9685 generates the precise duty cycles required to actuate the respective servomotors to the target angles.

[FIGURE 6: Kinematic mapping diagram illustrating how MediaPipe hand landmarks correspond to specific physical joints on the robotic arm.]

[FIGURE 7: Finite State Machine (FSM) diagram of the Mode Manager logic.]