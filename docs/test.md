To prove the rigorous engineering behind this thesis and validate the system for defense/demonstration, you must conduct the following specific tests:

The 50-Cycle Autonomous Sorting Stress Test: Run the fully autonomous pick-and-place loop continuously for 50 uninterrupted cycles on the physical hardware. This proves IK stability, handles edge configurations, and validates camera calibration consistency under physical vibration.
Mode Preemption Integrity Test: While the arm is in the middle of executing an autonomous sorting trajectory, dynamically switch to "Remote Gesture" mode. The system must seamlessly cancel the MoveIt trajectory and transition to following the new command without violent hardware jerks (Velocity/Acceleration boundary validation).
Network-Severance Fallback Test (Safety Profiling): During active MQTT remote teleoperation, physically sever the network connection. Measure the latency it takes for the mode manager to detect the timeout, halt the ROS 2 controller, and safely drop to the home configuration.
End-to-End Latency Benchmark: Quantify the exact millisecond delay from a hand gesture being captured by a mobile browser -> HiveMQ backend -> mqtt_bridge_node -> ros2_control C++ plugin -> ESP32 command-to-PWM execution. Academic standards expect this profile to be documented (target ideally <150 ms for seamless human-in-the-loop compliance).
4. Percentage Pending
Codebase & Control Integration: ~90–95% Complete.
Pending Implementation: ~5–10% Remaining.

### ✅ Final Consolidated Updates Applied (Docs-Only)

The following updates are now explicitly reflected in this docs file:

- Architecture consistency is set to **ESP32-only actuation path** (`ros2_control -> ESP32 -> PCA9685 -> servos`), with no Arduino Mega as primary controller.
- Remote teleoperation is documented as **GitHub-hosted web deployment + HiveMQ MQTT** browser control flow.
- Results-level addition for deployment is included with practical operator outcomes.
- Web controller feature validation is included: dual modes (joystick/camera), 6-DOF mapping, live telemetry, tuning controls, MQTT session status, reset, haptics, and PWA behavior.
- Methodology correction text and System Architecture correction text are included and aligned to the current implementation.

### 🔴 Missing Points & Discrepancies to Fix in the Report

1. **Remote Teleoperation & GitHub Pages Web UI:** 
   * **In the Report:** The System Architecture claims MQTT is used for ESP32 telemetry. 
   * **Current System:** The repository (`robot_arm_remote`) actually handles global remote internet teleoperation using a web interface hosted on **GitHub Pages**, executing MediaPipe.js in the browser and streaming joint commands over **HiveMQ MQTT**. This is a major highlight that needs more emphasis.

2. **Vision Feed Source:**
   * **In the Report:** The methodology states "An RGB camera feed is processed using OpenCV...". 
   * **Current System:** The `robot_arm_vision` package consumes a wireless camera stream for OpenCV preprocessing and inference.

3. **State Machine / Mode Manager Node:**
   * The repository has a dedicated package for this (`robot_arm_mode_manager`). The report should emphasize that the safety timeouts (e.g., aborting to HOME if the internet MQTT connection drops for 3 seconds) are implemented in this dedicated central node.

4. **Missing Images/Figures:** 
   * Across the report documents, there are plain text placeholders (e.g., `[FIGURE 11: Bar chart...]`). Ensure the actual image markdown links (e.g., `![Bar Chart](./images/fig11.png)`) are inserted before final generation.

---

### 📝 Proofreading & Suggested Corrections

**4_SYSTEM_ARCHITECTURE.md (Correction on Nodes and MQTT)**
> **ROS 2 Node Architecture**
> 1. `vision_processing_node`: Ingests wireless camera streams and publishes spatial coordinates of target objects via YOLOv8.
> 2. `gesture_capture_node` & `mqtt_bridge_node`: Computes human hand landmarks utilizing MediaPipe. This is achieved locally or via a **GitHub Pages Web UI** deployed on mobile devices, transmitting joint configurations globally to the ESP32 via **HiveMQ MQTT**.
> 3. `mode_manager_node`: The centralized state machine that multiplexes incoming commands (vision vs. gesture) and enforces safety timeouts (e.g., stopping the arm if the MQTT connection drops).
> 4. `moveit_trajectory_node`: Subscribes to target poses/angles, computes Inverse Kinematics via KDL, and publishes `JointTrajectory` messages.
> 5. `hardware_interface_node`: A custom `ros2_control` C++ interface that serializes trajectories into protocol commands executable by the **ESP32**.

**5_METHODOLOGY.md (Correction on Hardware Implementation Detail)**
> **Control Execution (ros2_control → ESP32 → PCA9685)**
> The computed trajectories are consumed by a custom `ros2_control` hardware interface. This interface serializes the desired joint states and transmits them to the **ESP32**. The ESP32 parses these commands and utilizes the I2C protocol to interface with a PCA9685 16-channel PWM driver. The PCA9685 generates the precise duty cycles required to actuate the physical servomotors to target angles.

### 🖼️ Required Images & Figures Checklist

To complete the report, the following figures must be generated or captured and placed into an `images/` directory. Each placeholder in the report should be replaced with the corresponding markdown image link (e.g., `![Figure 2 Description](./images/figure_02.png)`).

- [ ] **FIGURE 2:** Concept diagram illustrating the transition between autonomous sorting and human-guided teleoperation, highlighting the environmental triggers.
- [ ] **FIGURE 3:** Comparative timeline and architectural evolution of teleoperation interfaces vs. autonomous visual grasping frameworks.
- [ ] **FIGURE 4:** ROS 2 Node Graph (`rqt_graph`) detailing the publish/subscribe relationships between the vision, gesture, planning, and hardware nodes.
- [ ] **FIGURE 5:** Data pipeline flowchart showing the transformation of raw sensor data into final PWM signals on the ESP32.
- [ ] **FIGURE 6:** Kinematic mapping diagram illustrating how MediaPipe hand landmarks correspond to specific physical joints on the robotic arm.
- [ ] **FIGURE 7:** Finite State Machine (FSM) diagram of the Mode Manager logic.
- [ ] **FIGURE 8:** Visual representation of the URDF model rendered in RViz showing coordinate frames (TF) at each joint.
- [ ] **FIGURE 9:** Architecture diagram detailing the ROS 2 workspace package hierarchy and dependency flow.
- [ ] **FIGURE 10:** Graph showing End-to-End Latency comparison between Autonomous and Teleoperated modes across 100 trials.
- [ ] **FIGURE 11:** Bar chart detailing CPU vs GPU resource utilization during the different operational states of the robotic arm.
- [ ] **FIGURE 12:** Diagram showcasing the hardware abstraction layer, illustrating how the same ROS 2 architecture can command both a sub-scale prototype and an industrial counterpart.
- [ ] **FIGURE 13:** Example visual frame illustrating a failed YOLOv8 detection (e.g., due to occlusion or shadowing).
- [ ] **FIGURE 14:** Conceptual layout for an Edge-AI upgraded architecture featuring a decentralized processing topology with Jetson Nano / Coral Edge TPU integration.
- [ ] **FIGURE 15:** Final physical prototype of the dual-mode robotic arm grasping an object, symbolizing the project synthesis.

### ✅ Results Addendum: GitHub Deployment and Webpage Feature Validation

To strengthen the Results chapter, explicitly include deployment outcomes and operator-facing capabilities from the live web controller.

**GitHub Deployment Result (Remote Teleoperation Availability):**
- The web controller is deployable through GitHub-hosted static delivery and supports browser-first teleoperation without a native app dependency.
- Cross-device operation is validated through responsive layout rules for both desktop and mobile viewport widths.
- The browser client publishes teleoperation state to HiveMQ over MQTT WebSockets (`qos=0`) at an adjustable control loop rate.

**Webpage Features Validated from the Current Controller Implementation:**
- Dual operating tabs: **Joystick Mode** and **Camera Mode**.
- Full 6-DOF control mapping: dual virtual joysticks for J1-J4, dedicated controls for J5 roll and J6 gripper.
- Live telemetry cards for all six joints (degree display updates in real time).
- Runtime tuning controls: joystick speed, deadzone, camera smoothing, and publish rate (5-20 Hz).
- MQTT session controls with online/offline status chip and connect/disconnect actions.
- Browser camera pipeline with MediaPipe hand tracking and canvas landmark overlay.
- Pose reset command and haptic feedback support on compatible mobile devices.
- Progressive Web App capability: install prompt handling and service-worker registration.

**Recommended Results Wording for Thesis Chapter 5:**
The remote control interface was successfully operationalized as a browser-delivered teleoperation console, enabling hardware-agnostic operator access from mobile and desktop devices. The deployed interface supports dual interaction paradigms (joystick and camera-hand-tracking modes), full 6-DOF command generation, real-time joint telemetry, and online parameter tuning for control sensitivity and smoothing. MQTT connectivity and publish status are surfaced directly in the interface, and PWA support enables installable usage patterns. These outcomes demonstrate that the project's internet teleoperation subsystem is not only functionally correct but also operator-usable under practical field conditions.
