# RESULT & ANALYSIS

## Latency Analysis (Gesture vs. MQTT vs. Autonomous)
Comprehensive timing analyses were conducted to isolate systemic bottlenecks. 
- **Autonomous Mode:** The primary latency constraint observed is the visual inference phase. YOLOv8l inference operates at approximately 45 ms per frame. The subsequent MoveIt2 trajectory generation averages 120 ms. Total end-to-end latency for autonomous grasping initialization is measured at ~170 ms.
- **Gesture Mode:** MediaPipe processing incurs ~25 ms latency. The transmission via MQTT to the ESP32, bypassing MoveIt trajectory planning, requires ~15 ms. Total end-to-end latency for human-in-the-loop control averages 45 ms, presenting a highly responsive, real-time feel to the human operator.

## Accuracy of Object Detection
The vision pipeline's robustness was evaluated over 500 discrete trials involving standardized test geometries. Bounding box intersection-over-union (IoU) scores averaged 0.88 in standard lighting. Translation of the 2D centroid to 3D grasping coordinates exhibited a Mean Absolute Error (MAE) of 4.2 mm, well within the tolerance required for the compliant gripper design.

## System Responsiveness
Control loop stability was verified by commanding step responses to individual joints. The theoretical `ros2_control` update rate was maintained steadily at 100 Hz. The mechanical response time of the servos, accounting for internal PID settling and inertia, was documented at approximately 0.15 seconds to achieve 90% of the target step magnitude. 

## Bottlenecks (CPU, GPU, Network)
Analysis indicates that the GPU utilization peaks at 85% during YOLOv8 inference. Network latency becomes a secondary bottleneck when operating the MQTT broker over a generic 2.4 GHz Wi-Fi infrastructure; packet jitter under heavy network load occasionally exceeds 30 ms. The CPU (host machine) remains nominally utilized (< 40%) primarily handling ROS 2 DDS overhead and MoveIt node computations.

[FIGURE 10: Graph showing End-to-End Latency comparison between Autonomous and Teleoperated modes across 100 trials.]

[FIGURE 11: Bar chart detailing CPU vs GPU resource utilization during the different operational states of the robotic arm.]