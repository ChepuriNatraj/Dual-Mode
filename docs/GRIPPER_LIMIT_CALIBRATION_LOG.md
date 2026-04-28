# Gripper Limit Calibration Log

Purpose: record safe open and close limits for the gripper servo so future control, MoveIt mapping, and autonomous grasping stay inside tested mechanical bounds.

Date: April 25, 2026
Tester: Natraj
Hardware:
- Servo model:
- Driver: PCA9685 (channel ____)
- Controller: ESP32
- Supply voltage/current:

## 1) Pre-check
- Horn tightened and linkage free: [ ]
- No binding by hand rotation around neutral: [ ]
- Common ground between ESP32, PCA9685, servo PSU: [ ]

## 2) Direct PCA9685 Angle Sweep (hardware-only)
Use test sketch:
- src/robot_arm_hardware/firmware/tests/test_02_single_servo_pca9685/test_02_single_servo_pca9685.ino

Suggested manual sweep sequence:
0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 110, 120, 130, 140

Record observations:
| Angle (deg) | Movement OK | Noise/Click | Mechanical Stress | Notes |
|---|---|---|---|---|
| 0 | Yes | No | No | Fully open |
| 10 |  |  |  |  |
| 20 |  |  |  |  |
| 30 |  |  |  |  |
| 40 |  |  |  |  |
| 50 | Yes | No | Low | Almost fully closed |
| 60 | Yes | Low | Medium | Maximum close position observed |
| 70 |  |  |  |  |
| 80 |  |  |  |  |
| 90 |  |  |  |  |
| 100 |  |  |  |  |
| 110 |  |  |  |  |
| 120 |  |  |  |  |
| 130 |  |  |  |  |
| 140 |  |  |  |  |

## 3) Chosen Safe Limits
- Safe close angle (deg): 50
- Safe open angle (deg): 0
- Keep-out margin (deg): 5
- Final operating range used in firmware: 0 to 60 hard clamp, 0 to 50 recommended operation

## 4) ROS/MoveIt Mapping Check
Run gripper topic sweep in radians and map to physical result.

Record test points:
| ROS rad command | Observed deg (approx) | Behavior (open/close) | Acceptable |
|---|---|---|---|
| -1.0 |  |  |  |
| -0.5 |  |  |  |
| 0.0 |  |  |  |
| 0.5 |  |  |  |
| 1.0 |  |  |  |

## 5) Final Constants To Update
- In firmware conversion:
  - gripper_offset_deg =
  - gripper_invert = true/false
  - gripper_min_deg =
  - gripper_max_deg =
- In ROS controller limits:
  - link_6 lower =
  - link_6 upper =

## 6) Sign-off
- Verified 20 continuous open/close cycles with no binding: [ ]
- Verified same behavior from ROS command path: [ ]
- Ready for autonomous grasp testing: [ ]

## Important Integration Note
- If the ESP32 is flashed with any test sketch from `firmware/tests/`, ROS2 `robot_arm_hardware` motion commands may not move the arm because test sketches do not parse the full 6-joint comma protocol.
- Before full bring-up, flash production firmware from `src/robot_arm_hardware/firmware/`.
- During ROS control tests, use calibrated gripper range only: open `0.0`, close `-0.8727`, hard ceiling `-1.0472`.
