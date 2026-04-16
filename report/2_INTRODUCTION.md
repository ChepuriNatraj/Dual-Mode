# INTRODUCTION

## Overview
The integration of robotic manipulators into semi-structured and dynamic environments necessitates a departure from rigid, pre-programmed operational paradigms. This report details the development of a dual-mode robotic arm system that combines autonomous computer-vision-based capabilities with human-in-the-loop remote teleoperation. The system is synthesized utilizing ROS 2, Gazebo simulation, MoveIt2 for motion planning, and edge-level microcontrollers for actuation.

## Problem Statement
Current robotic manipulation systems typically operate in either fully autonomous or strictly manual teleoperation modes. Fully autonomous systems lack the adaptability required for novel or irregular tasks, while purely manual systems induce high cognitive loads on operators and suffer from reduced efficiency in repetitive scenarios. Furthermore, integrating these two paradigms into a unified, low-latency framework utilizing off-the-shelf hardware and open-source middleware remains a significant challenge.

## Motivation
The primary motivation for this research is to bridge the gap between deterministic automation and human cognitive adaptability. By developing a system that can autonomously sort objects under nominal conditions—yet seamlessly yield control to a human operator via intuitive gesture commands during edge cases—a higher degree of operational resilience can be achieved. This paradigm is highly applicable in fields such as hazardous material handling, flexible manufacturing, and remote assembly.

## Objectives
1. To design and simulate a functional 6-DOF (Degrees of Freedom) robotic arm in Gazebo using URDF modeling.
2. To implement a dual-mode control architecture in ROS 2 integrating discrete operational states: Autonomous Vision and Human-in-the-Loop Gesture.
3. To develop a robust visual processing pipeline utilizing YOLOv8 for spatial object localization and grasping.
4. To engineer a low-latency gesture mapping system using MediaPipe to accurately translate operator hand kinematics into manipulator joint angles.
5. To orchestrate hardware-level communication between the central ROS 2 computational node and the ESP32/PCA9685 actuation layer.
6. To quantify the system's performance metrics, explicitly focusing on end-to-end latency, positional accuracy, and computational bottlenecks.

[FIGURE 2: Concept diagram illustrating the transition between autonomous sorting and human-guided teleoperation, highlighting the environmental triggers.]