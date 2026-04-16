# ADVANTAGES

1. **Operational Versatility:** The dual-mode architecture fundamentally mitigates the risks associated with strictly autonomous systems. Edge cases or algorithmic failures in object recognition can be immediately overridden by a human operator, ensuring continuous operational uptime.
2. **Cost-Effectiveness:** Utilizing markerless pose estimation (MediaPipe) circumvents the requirement for expensive, proprietary haptic feedback suits or teach-pendants traditionally mandated for complex teleoperation. 
3. **Modularity and Scalability:** Constructed entirely within the ROS 2 framework, the system is inherently modular. Neural network models, kinematic planners, and even the mechanical structure can be hot-swapped or upgraded with minimal refactoring of the core middleware.
4. **Hardware Agnosticism:** The abstraction provided by `ros2_control` ensures that the high-level cognitive and planning logic is decoupled from the actual actuator hardware. Transitioning from hobbyist servos to industrial stepper/servo configurations requires only modifications to the C++ hardware interface and ESP32 firmware, leaving the Python perception and planning nodes untouched.
5. **Reduced Operator Cognitive Load:** By mapping human physiological movements directly to the kinematics of the robot arm, spatial translation required by the operator is minimized compared to joystick-based operation.

[FIGURE 12: Diagram showcasing the hardware abstraction layer, illustrating how the same ROS 2 architecture can command both a sub-scale prototype and an industrial counterpart.]