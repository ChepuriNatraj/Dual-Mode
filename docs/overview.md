The main purpose of the project is to create a 6-DOF robotic arm system that bridges the gap between fully autonomous operation and manual human control. By default, the robot uses computer vision and AI to detect, classify, and sort objects completely on its own. However, a human can instantly take control of the arm using hand gestures—either locally via a webcam or remotely from a smartphone anywhere in the world—without needing to press any buttons or use a physical UI. 

Here is a comprehensive README file for your project:

# Design & Development of a Dual-Mode Vision-Guided Robotic Arm

## Project Overview
This project builds a unified robotic system capable of seamless, automatic mode-switching between autonomous sorting and human-in-the-loop manipulation. Most industrial arms operate in fixed modes, requiring physical intervention to switch from automated to manual control. This system solves that problem by allowing context-aware, completely hands-free mode switching. The robot will automatically sort items on a conveyor, but if a human raises their hand to the camera, the robot immediately hands over manual control. 

## Operating Modes
The system is managed by a central Mode Manager node that seamlessly transitions between three active modes:
*   **AUTONOMOUS:** The default state where a camera detects objects, YOLOv8 classifies them, and MoveIt2 handles the inverse kinematics to pick and sort the objects.
*   **LOCAL GESTURE:** Triggered instantly when a hand is detected in the local webcam, using MediaPipe to map 21 hand landmarks to the arm's 6 joint angles so it mirrors the human's movement in real-time.
*   **REMOTE GESTURE:** Triggered by incoming MQTT commands, allowing an operator to control the arm from a mobile phone browser anywhere in the world.

## Technology Stack
The software and hardware stack is built around modern robotics frameworks and AI libraries:
*   **Core Infrastructure:** Ubuntu 24.04 LTS, ROS2 Jazzy Jalisco, and ros2_control.
*   **Simulation & Motion Planning:** Gazebo Harmonic and MoveIt2.
*   **Vision & AI:** OpenCV for color detection, YOLOv8 (with PyTorch and CUDA 12.1) for object classification, and MediaPipe for hand tracking.
*   **Remote Control:** MQTT via HiveMQ Cloud, Python Flask, and ngrok for internet tunneling.
*   **Hardware Control (Physical Phase):** Esp8266 communicating via serial link to a PCA9685 16-channel I2C servo driver.

there are different phases in this project, first is to implement the local teleoperation using the computer vision near the robot after having a clear and good understanding of the project we will proced with the remote control over MQTT


* **Caution:** : the components used in the project might vary based on the senario and budject, right now the above stack and the hardware is fixed