# Clean URDF Restructuring & Joint State Fix

**Project:** `robot_arm_description` — Clean 6-DOF Robot Arm  
**Previous Package:** `robot_description` (original CAD export, 40 links)  
**Stack:** ROS 2 Jazzy · Gazebo Harmonic (gz-sim 8.10.0) · DARTsim  
**Workspace:** `/home/natraj/DDS`  
**Date:** March 2, 2026

---

## Table of Contents

1. [Why This Was Done](#1-why-this-was-done)
2. [What Changed — TF Tree Before vs After](#2-what-changed--tf-tree-before-vs-after)
3. [Link Merging Details](#3-link-merging-details)
4. [How the Transform Math Works](#4-how-the-transform-math-works)
5. [New Joint Configuration](#5-new-joint-configuration)
6. [Issue 10 — Joint State Publisher Not Working](#6-issue-10--joint-state-publisher-not-working)
7. [Issue 11 — Empty frame_id on /joint_states](#7-issue-11--empty-frame_id-on-joint_states)
8. [New Package File Reference](#8-new-package-file-reference)
9. [How to Launch](#9-how-to-launch)

---

## 1. Why This Was Done

The original `robot_description` URDF was auto-exported from CAD (SolidWorks → Onshape → URDF).
Every individual CAD component became its own URDF link, connected by fixed joints:

- **40 links** total for what is physically a 6-DOF arm
- **29 fixed joints** connecting parts that never move relative to each other
- **11 actuated joints** (the real ones)

This created a **messy TF tree** with dozens of unnecessary frames, making it:
- Hard to set up MoveIt2 (planning groups become confusing)
- Hard to debug (TF tree is unreadable)
- Inefficient (robot_state_publisher publishes 40 transforms instead of 12)

### The Solution: Option 3 + Option 4 Combined

- **Option 3:** Build a clean new URDF from scratch with proper link groupings
- **Option 4:** Merge all fixed-joint CAD parts into single logical links

Result: A new package `robot_arm_description` with **12 links** and **11 joints** (only **1 fixed**).

---

## 2. What Changed — TF Tree Before vs After

### BEFORE — `robot_description` (40 links)

```
base_link
├── Rigid_1 → base_link2_1
│   └── Rigid_2 → ServoBracket_1
│       └── Rigid_3 → ServoMotor1_1
│           └── link_1 → Servo_Horn_v1_1
│               └── rigid_5 → Servo_Bracket2_1
│                   └── rigid_6 → ServoMotor2_1
│                       └── link_2 → ServoHorn1_1
│                           └── rigid_8 → LongU-TypeServo_Bracket_1
│                               └── rigid_9 → Long_U-Type_Servo_Bracket2_1
│                                   └── rigid_10 → Servo_Horn_v1__1__1
│                                       └── link_3 → Servo_Motor_v1_1
│                                           └── ... (9 more fixed joints)
│                                               └── link_4 → ...
│                                                   └── ... (more chains)
... (40 links, impossible to read)
```

### AFTER — `robot_arm_description` (12 links)

```
base_link
└── [revolute] joint_1 → link_1
    └── [revolute] joint_2 → link_2
        └── [revolute] joint_3 → link_3
            └── [revolute] joint_4 → link_4
                └── [revolute] joint_5 → link_5
                    └── [fixed] gripper_base_joint → gripper_base
                        ├── [revolute] gripper_drive_joint → gripper_gear
                        ├── [revolute] gripper_right_inner_joint → gripper_right_link
                        │   └── [revolute] gripper_right_finger_joint → gripper_right_finger
                        └── [revolute] gripper_left_inner_joint → gripper_left_link
                            └── [revolute] gripper_left_finger_joint → gripper_left_finger
```

| Metric | Before | After |
|---|---|---|
| Links | 40 | 12 |
| Joints | 40 | 11 |
| Fixed joints | 29 | 1 |
| Actuated joints | 11 | 10 |

---

## 3. Link Merging Details

Each new link merges multiple CAD parts that were originally connected by fixed joints.
All original STL meshes are kept — each merged link has **multiple `<visual>` blocks** (one per original part) with a shared offset so they render in the correct global position.

### Merge Table

| New Clean Link | Original CAD Parts Merged | # Meshes | Total Mass |
|---|---|---|---|
| `base_link` | `base_link` + `base_link2_1` + `ServoBracket_1` + `ServoMotor1_1` | 4 | 0.583 kg |
| `link_1` | `Servo_Horn_v1_1` + `Servo_Bracket2_1` + `ServoMotor2_1` | 3 | 0.301 kg |
| `link_2` | `ServoHorn1_1` + `LongU-TypeServo_Bracket_1` + `Long_U-Type_Servo_Bracket2_1` + `Servo_Horn_v1__1__1` | 4 | 0.143 kg |
| `link_3` | `Servo_Motor_v1_1` + `Multifunctional_Servo_Bracket_v1_1` + `L-Type_Servo_Bracket_v1_1` + `Servo_Horn_v1__2__1` + `rod_1` + `Servo_Horn_v1__3__1` + `L-Type_Servo_Bracket_v1__1__1` + `Multifunctional_Servo_Bracket_v1__1__1` + `Servo_Motor_v1__1__1` | 9 | 0.691 kg |
| `link_4` | `Servo_Horn_v1__6__1` + `Long_U-Type_Servo_Bracket_v1_1` + `Servo_Motor_v1__2__1` | 3 | 0.324 kg |
| `link_5` | `Servo_Horn_v1__5__1` + `Gripper_Connector_v1_1` + `Gripper_Connector_v1__1__1` | 3 | 0.013 kg |
| `gripper_base` | `Gripper_Base_v1_1` + 4× Long-Straight Washers + `Servo_Motor_v1__3__1` + `Servo_Horn_v1__7__1` | 7 | 0.296 kg |
| `gripper_gear` | `gripper_link_gear1_v1_1` | 1 | 0.015 kg |
| `gripper_right_link` | `Gripper_Link_v1_1` | 1 | 0.003 kg |
| `gripper_left_link` | `Gripper_Link_v1__1__1` | 1 | 0.003 kg |
| `gripper_right_finger` | `Gripper_Finger_v1__2__1` + `Gripper_Finger_v1__3__1` | 2 | 0.023 kg |
| `gripper_left_finger` | `Gripper_Finger_v1_1` + `Gripper_Finger_v1__1__1` | 2 | 0.023 kg |

---

## 4. How the Transform Math Works

### The Problem

All 43 STL mesh files were exported in the **global assembly coordinate frame** (millimeters).
When we merge parts, we need each mesh's `<visual>` `<origin>` to place it correctly relative
to the new link's joint frame.

### The Method

1. **Trace the fixed-joint chain** from `base_link` to each actuated joint
2. **Sum all the xyz translations** (all fixed joints had `rpy="0 0 0"`, so pure translation)
3. The **cumulative translation** at each joint = that joint's position in the global frame
4. Each mesh's visual origin = **negative of that cumulative translation** (shifting global-frame mesh into joint-local frame)

### Computed Cumulative Transforms

| Joint | Cumulative XYZ (meters) | Fixed Joints Summed |
|---|---|---|
| `joint_1` (base→link_1) | -0.002898, -0.010056, 0.077211 | Rigid_1 + Rigid_2 + Rigid_3 + link_1 |
| `joint_2` (base→link_2) | 0.030702, -0.020056, 0.090956 | + rigid_5 + rigid_6 + link_2 |
| `joint_3` (base→link_3) | 0.030702, -0.020054, 0.201449 | + rigid_8 + rigid_9 + rigid_10 + link_3 |
| `joint_4` (base→link_4) | 0.030703, -0.152546, 0.201449 | + rigid_12..20 + link_4 |
| `joint_5` (base→link_5) | -0.004297, -0.223293, 0.201450 | + rigid_29 + rigid_23 + link_5 |
| `gripper_base` (base→grip) | -0.009297, -0.229038, 0.199950 | + rigid_26 + rigid_27 |

### Visual Origin Formula

For each mesh in a merged link:
```
visual_origin_xyz = -(cumulative_transform_at_link_frame)
```

Example: All meshes in `link_3` use `origin xyz="-0.030702 0.020054 -0.201449"` — this shifts
each globally-positioned STL back into `link_3`'s local coordinate frame.

### Verification

All 6 checkpoint transforms were verified against the original URDF's visual origins.
Error = 0.000000 for all checks. The math is exact.

---

## 5. New Joint Configuration

All actuated joints changed from `continuous` to `revolute` with proper limits, damping, and friction:

| Joint | Type | Axis | Limits (rad) | Damping | Purpose |
|---|---|---|---|---|---|
| `joint_1` | revolute | Z | ±2.618 (±150°) | 5.0 | Base rotation |
| `joint_2` | revolute | X | ±1.571 (±90°) | 5.0 | Shoulder |
| `joint_3` | revolute | -X | ±1.571 (±90°) | 5.0 | Elbow |
| `joint_4` | revolute | X | ±2.618 (±150°) | 5.0 | Forearm rotation |
| `joint_5` | revolute | -Y | ±1.571 (±90°) | 5.0 | Wrist |
| `gripper_drive_joint` | revolute | -Z | ±1.571 (±90°) | 2.0 | Gripper gear drive |
| `gripper_right_inner_joint` | revolute | -Z | ±0.5 (±29°) | 0.5 | Right linkage arm |
| `gripper_left_inner_joint` | revolute | -Z | ±0.5 (±29°) | 0.5 | Left linkage arm |
| `gripper_right_finger_joint` | revolute | Z | ±0.5 (±29°) | 0.5 | Right finger |
| `gripper_left_finger_joint` | revolute | Z | ±0.5 (±29°) | 0.5 | Left finger |
| `gripper_base_joint` | **fixed** | — | — | — | Wrist to gripper mount |

---

## 6. Issue 10 — Joint State Publisher Not Working

### Symptom

After creating the clean `robot_arm_description` package, the Gazebo `JointStatePublisher` plugin
listed explicit `<joint_name>` tags. No `/joint_states` data was published. Robot appeared in
Gazebo but RViz2 showed it stuck in zero-pose.

### Root Cause

In Gazebo Harmonic, the `JointStatePublisher` plugin uses **scoped joint names** internally
(e.g., `robot_arm::joint_1`). When you list plain names like `<joint_name>joint_1</joint_name>`,
they don't match the scoped names and the plugin **silently publishes nothing**.

### Fix

Remove all explicit `<joint_name>` tags. With no names specified, the plugin automatically
publishes **ALL joints** in the model:

```xml
<!-- BEFORE (broken — names don't match scoped form) -->
<plugin filename="gz-sim-joint-state-publisher-system"
        name="gz::sim::systems::JointStatePublisher">
  <joint_name>joint_1</joint_name>
  <joint_name>joint_2</joint_name>
  ...
</plugin>

<!-- AFTER (works — publishes all joints automatically) -->
<plugin filename="gz-sim-joint-state-publisher-system"
        name="gz::sim::systems::JointStatePublisher">
</plugin>
```

**File changed:** `src/robot_arm_description/urdf/gazebo.xacro`

---

## 7. Issue 11 — Empty frame_id on /joint_states

### Symptom

After fixing Issue 10, `/joint_states` messages were being published (verified with `ros2 topic echo`),
but RViz2 still showed the robot in zero-pose. The console was flooded with:

```
[rviz2] Message Filter dropping message: frame '' at time 21.190
        for reason 'the frame id of the message is empty'
```

This repeated ~30 times/second, once per Gazebo physics step.

### Root Cause

The `ros_gz_bridge` converts Gazebo's `gz.msgs.Model` → ROS2 `sensor_msgs/msg/JointState`.
However, the Gazebo message **does not contain a frame_id field**, so the bridge sets
`header.frame_id = ''` (empty string).

In ROS2 Jazzy, RViz2's `RobotModel` display passes incoming `/joint_states` through a
`tf2::MessageFilter`. This filter **requires a non-empty `frame_id`** to look up the TF
transform, and silently drops any message with `frame_id = ''`.

The `robot_state_publisher` still receives the joint states (it doesn't use a MessageFilter),
so TF transforms ARE being published correctly. But RViz2's own internal joint state display
drops every message.

### Data Flow (broken)

```
Gazebo JointStatePublisher plugin
  ↓ gz.msgs.Model (no frame_id concept)
ros_gz_bridge (parameter_bridge)
  ↓ sensor_msgs/JointState (frame_id = '')   ← PROBLEM
/joint_states topic
  ↓
robot_state_publisher → /tf (works fine, ignores frame_id)
RViz2 RobotModel → MessageFilter drops message (frame_id empty) ← BROKEN
```

### Fix — Joint State Relay Node

Created a lightweight Python relay node that:
1. Subscribes to `/joint_states_gz` (the raw bridge output with empty frame_id)
2. Sets `header.frame_id = 'base_link'`
3. Republishes to `/joint_states`

### Data Flow (fixed)

```
Gazebo JointStatePublisher plugin
  ↓ gz.msgs.Model
ros_gz_bridge
  ↓ sensor_msgs/JointState (frame_id = '')
/joint_states_gz topic                          ← renamed raw topic
  ↓
joint_state_relay.py (sets frame_id = 'base_link')
  ↓ sensor_msgs/JointState (frame_id = 'base_link')  ← FIXED
/joint_states topic
  ↓
robot_state_publisher → /tf ✓
RViz2 RobotModel → MessageFilter accepts ✓
```

### Files Changed

| File | Change |
|---|---|
| `config/bridge.yaml` | Changed ROS topic from `/joint_states` → `/joint_states_gz` |
| `scripts/joint_state_relay.py` | **New file** — relay node that stamps `frame_id` |
| `launch/sim.launch.py` | Added `joint_state_relay` node to launch |
| `CMakeLists.txt` | Added `install(PROGRAMS scripts/joint_state_relay.py ...)` |

### Why `base_link` as frame_id?

The `frame_id` on `JointState` messages is largely unused by `robot_state_publisher` —
it only looks at `name[]`, `position[]`, `velocity[]`, and `effort[]`. But the tf2
MessageFilter needs *some* valid frame to do a lookup. `base_link` is the root frame
of the robot, always exists in the TF tree, and its transform to itself is identity —
making the lookup trivial and costless.

---

## 8. New Package File Reference

```
src/robot_arm_description/
├── CMakeLists.txt                      ← build config, installs scripts
├── package.xml                         ← ROS2 package manifest
├── urdf/
│   ├── robot.urdf.xacro               ← clean 12-link URDF (main file)
│   ├── materials.xacro                ← RViz material color definitions
│   └── gazebo.xacro                   ← Gazebo RGBA materials + JointStatePublisher plugin
├── meshes/                            ← 43 STL files (copied from robot_description)
├── config/
│   ├── bridge.yaml                    ← ros_gz_bridge topic mapping config
│   └── view_config.rviz              ← RViz2 display configuration
├── launch/
│   ├── sim.launch.py                  ← Gazebo Harmonic + RViz2 simulation
│   └── display.launch.py             ← RViz2 + joint_state_publisher_gui (no Gazebo)
└── scripts/
    └── joint_state_relay.py           ← stamps frame_id on joint states from Gazebo
```

---

## 9. How to Launch

### Full Simulation (Gazebo + RViz2)

```bash
cd /home/natraj/DDS
source install/setup.bash
ros2 launch robot_arm_description sim.launch.py
```

### RViz2 Only (with joint slider GUI, no physics)

```bash
ros2 launch robot_arm_description display.launch.py
```

### Verify Joint States Are Flowing

```bash
# Check the topic exists and has a publisher
ros2 topic info /joint_states

# Echo one message — frame_id should say 'base_link'
ros2 topic echo /joint_states --once

# Check TF tree
ros2 run tf2_tools view_frames
```

### Expected Healthy Output

```
header:
  stamp: {sec: XX, nanosec: XXXXXXXXX}
  frame_id: 'base_link'          ← must NOT be empty
name: [joint_1, joint_2, joint_3, joint_4, joint_5,
       gripper_drive_joint, gripper_left_inner_joint, ...]
position: [0.0, 0.0, ...]
```

---

*Documentation generated: 2026-03-02*
