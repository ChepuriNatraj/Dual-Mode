# Chat Session 2 — Hardware Architecture, Camera Decisions & Component Procurement
**Date:** March 7, 2026
**Scope:** Hardware audit, camera placement architecture, wiring validation, component shopping, and camera module evaluation
    
---

## 1. Session Overview

This session focused entirely on the **hardware side** of the Dual-Mode Vision-Guided Robotic Arm project. No code was written. The key outcomes were:

- Final camera architecture locked (3-camera setup)
- Servo drooping behaviour understood and mitigated
- Complete shopping list finalised with live product links
- Wiring diagram validated for PSU → PCA9685 → ESP8266
- OV7670 camera module evaluated and rejected

---

## 2. Topics Discussed

### 2.1 Servo Drooping Under Load (MG996R)

**Problem raised:** MG996R servos were observed to droop/fall under load after the arm was positioned.

**Root cause analysis:**
- MG996R is open-loop — no internal position encoder or feedback
- If PWM signal is removed or goes idle, the servo releases its hold completely
- Under gravity load (especially at full horizontal extension), cumulative torque exceeds the rated 10 kg·cm stall torque

**Mitigations decided:**
| Mitigation | Reasoning |
|---|---|
| Always send hold PWM (never idle the signal) | Servo holds position only when receiving active signal |
| Keep workspace within 15 cm of base | Reduces moment arm, reduces required torque |
| Solid 5V / 10A PSU (no USB power) | PSU brownout causes servo jitter and positional drift |
| Avoid full horizontal extension in workspace design | Worst-case torque scenario for shoulder joint |

**Conclusion:** Drooping is a design constraint, not a fault. Work within servo limits.

---

### 2.2 IMU Module — MPU6050

**Decision:** Add MPU6050 to the wrist link for Phase 5 hardware deployment.

**Purpose:**
- Detect cumulative drift in wrist/end-effector orientation
- Cross-validate servo position estimates
- Used for drift correction, not full closed-loop control

**Specs confirmed:**
- I2C address: `0x68` (default, ADO pin low)
- Shares the same I2C bus as PCA9685 (no conflict — different addresses)
- Mounts physically on the wrist link of the arm
- Source: indianhobbycenter.com — ₹199

---

### 2.3 Camera Architecture — Final Decision

**The conflict:** User's phone was originally planned for both fixed overhead camera (YOLOv8) AND as the remote MQTT operator device.

**Resolution reached:** These are two completely different roles:
- User's phone = **always fixed overhead**, mounted on a stand above the workspace
- Remote operators = **their own phones**, accessing the ngrok web app URL from anywhere

**Final 3-Camera Architecture:**

| Camera | Mount | Purpose | Technology |
|---|---|---|---|
| User's phone | Fixed overhead stand | YOLOv8 object detection | IP Webcam app → MJPEG stream → `cv2.VideoCapture("http://...")` |
| Laptop webcam | Laptop lid | LOCAL MediaPipe gesture control | `usb_cam` ROS2 node |
| Any remote phone | Anywhere in world | REMOTE MQTT gesture control | Browser → MediaPipe.js → MQTT |

**Why phone beats ESP32-CAM for fixed overhead:**

| Criterion | Phone (IP Webcam) | ESP32-CAM |
|---|---|---|
| Resolution | 1080p+ | 640×480 max |
| Setup | Install app, share URL | Flash firmware, configure WiFi |
| Cost | ₹0 (already owned) | ~₹400 |
| ROS2 integration | `cv2.VideoCapture` (2 lines) | Custom driver needed |
| Reliability | Proven MJPEG streaming | Known stability issues |

**Winner: Phone (IP Webcam app) — zero cost, higher quality, easier integration.**

---

### 2.4 OV7670 Camera Module — Evaluated and Rejected

**Question:** Can OV7670 be used in this project?

**Analysis:**

| Issue | Detail |
|---|---|
| No USB / network output | Raw parallel bus (D0–D7 + PCLK/VSYNC/HREF) — requires MCU to read; getting frames to ROS2 is a custom engineering problem |
| Resolution cap | 640×480 VGA max — YOLOv8 accuracy drops significantly vs 1080p |
| No JPEG compression | Raw RGB frame ≈ 900 KB; streaming over serial is unusably slow |
| Complex wiring | 10+ GPIO lines with strict timing — notoriously unreliable even on Arduino |
| No ROS2 driver | No `usb_cam` or standard package supports it — full custom driver needed |

**Verdict: Rejected.** The OV7670 is a microcontroller learning module. It is architecturally incompatible with a ROS2 + YOLOv8 pipeline. Phone + laptop webcam architecture is superior in every dimension.

---

## 3. Component Shopping List (Finalised)

### 3.1 From indianhobbycenter.com (Verified Live Links)

| Component | Link | Price | Purpose |
|---|---|---|---|
| MPU6050 6-axis IMU | https://www.indianhobbycenter.com/products/mpu6050-6-axis-accelerometer-and-gyroscope-sensor | ₹199 | Wrist drift correction |
| MB102 830-point Breadboard | https://www.indianhobbycenter.com/products/mb102-830-points-solderless-prototype-pcb-breadboard | ₹75 | Prototyping connections |
| 400-point Breadboard | https://www.indianhobbycenter.com/products/small-breadboard-400-pin-copper | ₹55 | Secondary prototyping |

> **Note:** Jumper wires (40-pin Dupont packs) were NOT found on indianhobbycenter.com. Source from Amazon.in or Robu.in — search "40 pin dupont jumper wire male female" (~₹80–120).

### 3.2 Hardware Already On Hand

| Component | Status |
|---|---|
| 6-DOF Metal Servo Arm Kit | ✅ Received |
| 6× MG996R Servo | ✅ Received |
| ESP8266 NodeMCU | ✅ Received |
| PCA9685 16-channel Servo Driver | ✅ Received |
| 5V / 10A PSU | ✅ Received |
| 1080p Webcam | ✅ Received |
| DC Power Jack Female (2-pin screw terminal) | ✅ Being purchased |

### 3.3 Final Remaining Items (Non-Electronic)

| Item | Why Needed | Source |
|---|---|---|
| Micro-USB cable | Flashing firmware to ESP8266 | Any store / already owned |
| 2 mm flathead screwdriver | **Critical** — tightening PCA9685 screw terminal block (V+/GND) | Hardware store |
| Electrical tape / heat shrink | Insulating bare PSU wire joints | Hardware store |
| Zip ties | Cable management on arm | Any store |
| Stable base / clamp for arm | Prevent arm from tipping under load | Workshop / custom |
| Phone stand / clamp | Mount phone overhead above workspace | Amazon ~₹150–300 |

**Confirmed NOT needed:**
- Pull-up resistors for I2C → already on PCA9685 and MPU6050 boards
- Logic level converter → ESP8266 is 3.3V, PCA9685 accepts 3.3V on VCC/SDA/SCL
- Extra capacitors → only needed if PSU rail shows oscilloscope noise
- Additional MCU → ESP8266 is sufficient for this architecture

---

## 4. Wiring Architecture (Validated)

### 4.1 Power Domain Separation (Critical)

```
SERVO POWER DOMAIN:
PSU (5V rail) ──→ DC Jack Female (barrel) ──→ Screw Terminal
                                              ├─ Red wire  → PCA9685 V+
                                              └─ Black wire → PCA9685 GND

LOGIC POWER DOMAIN:
ESP8266 3.3V ──→ PCA9685 VCC  (only powers the IC logic, NOT servos)
ESP8266 GND  ──→ PCA9685 GND  (MANDATORY — common ground reference)
```

> **Critical rule:** VCC and V+ on PCA9685 are separate pins. VCC = logic (3.3V from ESP8266). V+ = servo power (5V from PSU). Never connect PSU directly to VCC.

### 4.2 I2C Bus Connections

```
ESP8266 D1 (GPIO5) ──→ PCA9685 SCL
ESP8266 D2 (GPIO4) ──→ PCA9685 SDA

MPU6050 SCL ──→ same SCL line (address 0x68)
MPU6050 SDA ──→ same SDA line
MPU6050 VCC ──→ ESP8266 3.3V
MPU6050 GND ──→ Common GND
```

### 4.3 Wire Gauge

| Connection | Wire Gauge |
|---|---|
| PSU → PCA9685 V+/GND (servo power) | 20–22 AWG |
| ESP8266 → PCA9685 VCC/GND (logic) | 24–26 AWG (any thin wire) |
| I2C lines (SCL/SDA) | 24–26 AWG |

### 4.4 DC Power Jack Female Connector (Screw Terminal Type)

**Confirmation:** DC Power Jack Female with 2-pin PBT screw terminal is the **correct connector** for connecting the PSU barrel output to the PCA9685 power input.

- Centre pin = positive (V+) → red wire → PCA9685 V+
- Outer sleeve = negative (GND) → black wire → PCA9685 GND
- Screw down firmly with 2 mm flathead screwdriver

---

## 5. Architecture Approaches Considered & Decisions Made

### 5.1 Fixed Camera — Approaches Considered

| Approach | Considered | Rejected Reason |
|---|---|---|
| ESP32-CAM module | Yes | Lower resolution, firmware complexity, ~₹400 cost |
| OV7670 raw sensor | Yes | No network output, parallel bus incompatible with ROS2 |
| USB webcam mounted overhead | Yes | Cable management difficult, webcam already used for gesture |
| **Phone (IP Webcam app)** | **Yes** | **CHOSEN — 1080p, free, MJPEG stream, zero integration friction** |

### 5.2 Servo Controller — Approaches Considered

| Approach | Considered | Rejected Reason |
|---|---|---|
| Arduino Mega (original plan) | Yes | USB tether, no wireless, limited for future phases |
| Raspberry Pi direct GPIO | Yes | 3.3V PWM output, RPi GPIO not designed for servo load |
| **ESP8266 + PCA9685** | **Yes** | **CHOSEN — Wi-Fi capable, I2C clean, 16-channel, 5V servo signal** |

### 5.3 Remote Control Infrastructure — Approaches Considered

| Approach | Considered | Rejected Reason |
|---|---|---|
| Direct WebSocket to laptop | Considered | Requires port forwarding, fails behind NAT/firewall |
| WebRTC | Considered | Complex setup, overkill for joint angle streaming |
| Custom TCP server + VPN | Considered | Requires VPN setup, not phone-accessible |
| **MQTT + HiveMQ + ngrok** | **Yes** | **CHOSEN — free, NAT-penetrating, reliable on mobile networks** |

---

## 6. Project Phase Status (as of this session)

| Phase | Description | Status |
|---|---|---|
| Phase 0 | URDF, Gazebo simulation, RViz2 TF tree | ✅ Complete |
| Pre-Phase | MediaPipe hand detection pipeline | ✅ Verified working |
| Phase 1 | MoveIt2 Setup Assistant + SRDF | ⏳ Not started — **immediate next step** |
| Phase 2 | Gesture → arm joint mapping (live simulation) | 🔄 Partial (landmarks work, mapping not written) |
| Phase 3 | YOLOv8 autonomous sorting pipeline | ⏳ Not started |
| Phase 4 | MQTT remote control (Flask + ngrok + HiveMQ) | ⏳ Not started |
| Phase 5 | Hardware deployment (ESP8266 + PCA9685 + MPU6050) | ⏳ Not started |

---

## 7. Immediate Next Actions

1. **Order remaining components:**
   - MPU6050 from indianhobbycenter.com (₹199)
   - 40-pin Dupont jumper wires from Amazon/Robu.in (~₹100)
   - Phone overhead stand (~₹150–300)
   - 2 mm flathead screwdriver

2. **Begin Phase 1 — MoveIt2 Setup:**
   ```bash
   sudo apt install ros-jazzy-moveit
   ros2 launch moveit_setup_assistant setup_assistant.launch.py
   ```
   - Load: `robot_arm_description` URDF
   - Configure planning group: `arm` (joint_1 → joint_5)
   - Configure end-effector: `gripper` (parent: gripper_base link)
   - Generate self-collision matrix (SRDF)
   - Export `robot_arm_moveit_config` package

3. **Test MoveIt2:** Drag interactive marker in RViz2 → Plan and Execute → verify arm moves in simulation

---

## 8. Key Technical Decisions Summary

| Decision | Choice Made | Rationale |
|---|---|---|
| Fixed overhead camera | Phone (IP Webcam app) | Free, 1080p, MJPEG, works with OpenCV directly |
| Remote operator camera | Any phone (browser) | MediaPipe.js runs in browser, no app install needed |
| IMU for drift feedback | MPU6050 on wrist link | Low cost, I2C compatible, shares ESP8266 bus |
| Servo controller | ESP8266 + PCA9685 | Wi-Fi ready, I2C clean, 16 channels |
| Power supply | Dedicated 5V/10A PSU | Prevents brownout; USB/laptop power insufficient |
| ROS middleware | ROS2 Jazzy + Gazebo Harmonic | Ubuntu 24.04 compatible pair, active LTS |
| Motion planning | MoveIt2 + OMPL | Industry standard, collision-aware IK |
| Object detection | YOLOv8 (CUDA) on RTX 3060 | ~15ms inference, >90% accuracy on standard objects |

---

*Session ended with hardware architecture fully resolved. No code changes made. Next session should begin Phase 1 (MoveIt2).*
