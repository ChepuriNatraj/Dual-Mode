# CONCLUSION

This project successfully engineered and validated a dual-mode robotic manipulator framework within the ROS 2 ecosystem. By synthesizing an autonomous object-sorting pipeline powered by YOLOv8 and an intuitive human-in-the-loop teleoperation mode utilizing MediaPipe gesture mapping, the inherent limitations of rigid automation and traditional manual control were effectively circumnavigated.

The system's modular architecture, leveraging standard abstractions such as `ros2_control` and MoveIt2 alongside edge-level micro-controllers (ESP32/PCA9685), proved highly successful in creating a unified control environment. Analysis of the implementation demonstrated clear operational advantages: the autonomous mode offered precise repetitional accuracy for structured tasks, while the sub-50ms latency in the gesture-driven teleoperation mode ensured seamless operator intervention during complex edge-case scenarios. 

While certain limitations persist regarding the lack of haptic feedback and susceptibility to visual occlusion, the fundamental architecture establishes a robust foundation for flexible manufacturing paradigms. Future integrations of RGB-D spatial processing and localized Edge AI inference are positioned to further elevate this system from a prototype methodology to a viable, industrial-grade solution capable of navigating dynamic, unstructured environments.

[FIGURE 15: Final physical prototype of the dual-mode robotic arm grasping an object, symbolizing the project synthesis.]