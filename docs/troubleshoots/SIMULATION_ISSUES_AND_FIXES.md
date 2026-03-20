# Gazebo Harmonic + RViz2 Simulation — Issues and Fixes

**Project:** `robot_description` — 6-DOF Robotic Arm with Gripper  
**Stack:** ROS 2 Jazzy · Gazebo Harmonic (gz-sim 8.10.0) · Physics: DARTsim  
**Workspace:** `/home/natraj/DDS`  
**Date:** March 2, 2026

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Issue 1 — Invalid Inertia Tensors (Physics Error Code 19)](#2-issue-1--invalid-inertia-tensors-physics-error-code-19)
3. [Issue 2 — Mesh URI Resolution Failure (Robot Invisible)](#3-issue-2--mesh-uri-resolution-failure-robot-invisible)
4. [Issue 3 — Unsupported Material Name (Gazebo/Silver)](#4-issue-3--unsupported-material-name-gazebosilver)
5. [Issue 4 — Missing Gazebo Classic Plugin](#5-issue-4--missing-gazebo-classic-plugin)
6. [Issue 5 — Mimic Joint Constraint Not Supported](#6-issue-5--mimic-joint-constraint-not-supported)
7. [Issue 6 — Excessive Debug Log Spam](#7-issue-6--excessive-debug-log-spam)
8. [Issue 7 — RViz2 "Jump Back in Time" Warning](#8-issue-7--rviz2-jump-back-in-time-warning)
9. [Issue 8 — Gripper Continuously Rotating in Gazebo](#9-issue-8--gripper-continuously-rotating-in-gazebo)
10. [Issue 9 — RViz2 TF Transform Errors for Entire Gripper Chain](#10-issue-9--rviz2-tf-transform-errors-for-entire-gripper-chain)
11. [Final Architecture](#11-final-architecture)
12. [File Change Summary](#12-file-change-summary)

---

## 1. System Overview

### Robot Model Statistics

| Attribute | Count |
|---|---|
| Total links | 40 |
| Fixed joints (`type="fixed"`) | 29 |
| Continuous joints (`type="continuous"`) | 6 active |
| Revolute joints (`type="revolute"`) | 4 (gripper fingers) |
| Mesh files (STL) | 40 |
| Gazebo material blocks | ~35 |

### Key Files Modified

| File | Role |
|---|---|
| `launch/sim.launch.py` | Main simulation launch — **created from scratch** |
| `urdf/robot.xacro` | Main URDF — inertia, joint types, dynamics |
| `urdf/robot.gazebo` | Gazebo-specific tags — materials, plugins |

### Launch Pipeline (Final State)

```
robot_state_publisher  ──► publishes /robot_description + /tf (static)
        │
        └── (OnProcessStart + 1s delay)
              └── ros_gz_sim/create ──► spawns robot into Gazebo world
                                              │
gz sim (empty.sdf -r -v1) ─────────────────►│
        │                                     │
        │  JointStatePublisher plugin ────────┴──► /world/empty/model/robot/joint_state
        │
ros_gz_bridge
  ├── /clock           (gz→ROS)   ──► all use_sim_time nodes
  ├── /tf              (gz→ROS)   ──► RViz2 visual transforms
  └── /joint_states    (gz→ROS, remapped) ──► robot_state_publisher ──► TF tree
        │
        └── (6s delay)
              └── rviz2 (view_config.rviz)
```

---

## 2. Issue 1 — Invalid Inertia Tensors (Physics Error Code 19)

### Symptom

```
[Err] [Physics.cc] Error in physics engine:
  Invalid inertia for link [Servo_Horn_v1_1]
  Error Code 19: URDF_INVALID_INERTIA
```
Gazebo reported Error Code 19 for 16 different links immediately at spawn time. The robot was still spawned visually but physics behaved erratically.

### Root Cause

Fusion 360 / SolidWorks URDF exporters set `ixx`, `iyy`, `izz` to `0.0` for low-mass links (servo horns, gripper fingers, connectors, washers) where the exporter could not calculate meaningful inertia. A **positive-definite** inertia tensor is mandatory — all three principal moments must be strictly greater than zero, and the following must hold:

$$I_{xx} \geq 0,\quad I_{yy} \geq 0,\quad I_{zz} \geq 0$$

$$I_{xx} + I_{yy} \geq I_{zz},\quad I_{xx} + I_{zz} \geq I_{yy},\quad I_{yy} + I_{zz} \geq I_{xx}$$

### Affected Links (16 total)

| Link Name | Problem |
|---|---|
| `Servo_Horn_v1_1` | All inertia values = 0 |
| `Servo_Horn_v1__1__1` through `__7__1` | All inertia values = 0 |
| `Gripper_Base_v1_1` | All inertia values = 0 |
| `Gripper_Link_v1_1`, `Gripper_Link_v1__1__1` | All inertia values = 0 |
| `Gripper_Finger_v1_1`, `v1__1__1`, `v1__2__1`, `v1__3__1` | `iyy = 0` |
| `Gripper_Connector_v1_1`, `v1__1__1` | All inertia values = 0 |
| `Gripper_Long-Straight_Washer_*` (×4) | All inertia values = 0 |

### Fix

Replaced all zero inertia values with small positive values proportional to each component's mass. Values used were in the range `1e-7` to `4e-6 kg·m²`.

**Before (robot.xacro):**
```xml
<inertia ixx="0" iyy="0" izz="0" ixy="0" iyz="0" ixz="0"/>
```

**After (robot.xacro):**
```xml
<inertia ixx="1e-07" iyy="2e-07" izz="1e-07" ixy="0.0" iyz="0.0" ixz="0.0"/>
```

### File Modified
- [urdf/robot.xacro](urdf/robot.xacro) — 16 `<inertia>` blocks updated

---

## 3. Issue 2 — Mesh URI Resolution Failure (Robot Invisible)

### Symptom

```
[Err] [SystemPaths.cc] URI [model://robot_description/meshes/base_link.stl] not found
[Wrn] [SubMesh.cc] No mesh was loaded. Generating a unit box.
```

Every link rendered as a plain white box instead of the STL mesh geometry. The robot was present in Gazebo but completely unrecognisable.

### Root Cause

The URDF uses `package://robot_description/meshes/...` URIs (ROS-style), but Gazebo Harmonic internally resolves them as `model://robot_description/meshes/...`. Gazebo uses the `GZ_SIM_RESOURCE_PATH` environment variable to locate model directories. After `colcon build`, the installed package share is at:

```
/home/natraj/DDS/install/robot_description/share/robot_description/
```

For the `model://robot_description` prefix to resolve, Gazebo needs the **parent of the `robot_description` directory** — i.e., `.../share/` — on its resource path.

### Fix

Added `SetEnvironmentVariable` in `sim.launch.py` before any Gazebo process starts:

```python
gz_resource_path = SetEnvironmentVariable(
    name  = 'GZ_SIM_RESOURCE_PATH',
    value = os.path.dirname(pkg_robot),   # .../install/robot_description/share
)
```

### File Modified
- [launch/sim.launch.py](launch/sim.launch.py) — `SetEnvironmentVariable` action added

---

## 4. Issue 3 — Unsupported Material Name (Gazebo/Silver)

### Symptom

```
[Wrn] [Material.cc] Material [Gazebo/Silver] not found.
      Using default material instead.
```

Logged once per link (35+ times). All robot links rendered in Gazebo's default grey instead of the intended metallic silver. This was a cosmetic warning but flooded the log.

### Root Cause

`robot.gazebo` used Gazebo **Classic** (ROS 1 era) Ogre material notation:
```xml
<gazebo reference="base_link">
  <material>Gazebo/Silver</material>
</gazebo>
```

Gazebo Harmonic dropped the Ogre rendering engine and no longer recognises string material names. It requires explicit **RGBA** values in a nested `<visual><material>` block.

### Fix

Replaced all Ogre material references with RGBA format in `robot.gazebo`:

**Before:**
```xml
<gazebo reference="base_link">
  <material>Gazebo/Silver</material>
</gazebo>
```

**After:**
```xml
<gazebo reference="base_link">
  <visual>
    <material>
      <ambient>0.7 0.7 0.7 1</ambient>
      <diffuse>0.7 0.7 0.7 1</diffuse>
      <specular>0.5 0.5 0.5 1</specular>
    </material>
  </visual>
  <mu1>0.2</mu1>
  <mu2>0.2</mu2>
  <selfCollide>true</selfCollide>
</gazebo>
```

Applied to all ~35 links.

### File Modified
- [urdf/robot.gazebo](urdf/robot.gazebo) — all material blocks replaced

---

## 5. Issue 4 — Missing Gazebo Classic Plugin

### Symptom

```
[Err] [SystemPaths.cc] Failed to find plugin [libgazebo_ros_control.so]
```

Fatal error at spawn time; Gazebo could not load the ROS control plugin.

### Root Cause

`robot.gazebo` contained a Gazebo **Classic** plugin block:
```xml
<gazebo>
  <plugin name="gazebo_ros_control" filename="libgazebo_ros_control.so">
    <robotNamespace>/</robotNamespace>
  </plugin>
</gazebo>
```

`libgazebo_ros_control.so` belongs to the `gazebo_ros_pkgs` suite which targets Gazebo Classic (versions 9–11). Gazebo Harmonic uses a completely different plugin API under the `gz::sim::systems` namespace — there is no direct equivalent `.so` drop-in replacement for Harmonic without a full controller manager setup.

### Fix

Removed the entire Classic plugin block from `robot.gazebo`. Gazebo Harmonic operates without this plugin for the purposes of visualization + joint state publishing.

### File Modified
- [urdf/robot.gazebo](urdf/robot.gazebo) — `libgazebo_ros_control.so` plugin block removed

---

## 6. Issue 5 — Mimic Joint Constraint Not Supported

### Symptom

```
[Err] [Physics.cc:1801] Mimic constraint not supported.
      Constraint between [Revolute 39] and [link_6] will be ignored.
```

Repeated for joints `Revolute 39`, `Revolute 40`, `Revolute 41`, `Revolute 44`. The gripper fingers were intended to mirror the main gripper gear joint (`link_6`) but the mimic was silently dropped by the physics engine.

### Root Cause

DARTsim (the default physics backend for Gazebo Harmonic) **does not implement URDF `<mimic>` joint constraints**. The URDF specification allows:
```xml
<mimic joint="link_6" multiplier="1.0" offset="0.0"/>
```
but DARTsim ignores these tags entirely, logging the error above. This is a known DARTsim limitation.

### Affected Joints

| Joint Name | Mimicked Joint | Purpose |
|---|---|---|
| `Revolute 39` | `link_6` | Left gripper link actuated by gear |
| `Revolute 40` | `link_6` | Right gripper link actuated by gear |
| `Revolute 41` | `link_6` | Left gripper finger |
| `Revolute 44` | `link_6` | Right gripper finger |

### Fix

Removed the `<mimic>` tag from all four gripper joints. The joints were left as `continuous` type at this stage (subsequently fixed in Issue 8).

### File Modified
- [urdf/robot.xacro](urdf/robot.xacro) — `<mimic>` elements removed from Revolute 39, 40, 41, 44

---

## 7. Issue 6 — Excessive Debug Log Spam

### Symptom

```
[Dbg] [MeshShape.cc] Mesh construction not implemented for DART.
      Mesh shape will be approximated by its AABB.
```

This message printed **once per mesh collision per simulation step** — thousands of lines per second, filling the terminal and making it impossible to read actual errors.

### Root Cause

Gazebo Harmonic's DARTsim physics engine cannot process STL mesh geometries as collision shapes. Every collision body backed by a mesh triggers this debug message. With 40 links each having a mesh collision, the output was overwhelming.

The default Gazebo verbosity level (`-v4` or unset) includes debug-level (`[Dbg]`) messages.

### Fix

Set Gazebo verbosity to level 1 (`-v1`) in `sim.launch.py`, which suppresses debug and verbose messages, showing only informational (`[Msg]`) and error (`[Err]`) output:

**Before:**
```python
'gz_args': ['-r ', world],
```

**After:**
```python
'gz_args': ['-r -v1 ', world],
```

### Verbosity Level Reference

| Level | Messages shown |
|---|---|
| 0 | None |
| 1 | `[Msg]` and `[Err]` only |
| 2 | + `[Warn]` |
| 3 | + `[Verbose]` |
| 4 | + `[Dbg]` (default) |

### File Modified
- [launch/sim.launch.py](launch/sim.launch.py) — `-v4` → `-v1`

---

## 8. Issue 7 — RViz2 "Jump Back in Time" Warning

### Symptom

```
[rviz2] [WARN] [robot_state_publisher]: Detected a jump back in time.
        Resetting TF buffer.
```

RViz2 started, briefly showed the robot, then reset and showed a blank/broken display. The warning repeated continuously at startup.

### Root Cause

All nodes were configured with `use_sim_time: true`. RViz2 was launched at the **same time** as Gazebo (both in the `LaunchDescription`). RViz2 started with the host system clock (e.g., Unix timestamp `1.77 × 10⁹` seconds), but Gazebo simulation time starts at `t = 0`. When the `/clock` topic began publishing simulation time `0.0`, RViz2's internal TF buffer detected a massive backwards jump in time and reset — clearing all cached transforms.

The sequence causing the problem:

```
t=0s:  RViz2 starts, uses system time (~1.77e9 s)
t=0s:  Gazebo starts, publishes /clock at 0.0 s
t≈0s:  RViz2 subscribes to /clock, receives 0.0 → 
       detects jump of ~1.77e9 seconds → resets TF buffer
```

### Fix

Delayed RViz2 launch by **6 seconds** using `TimerAction`, giving Gazebo time to:
1. Fully start and begin publishing `/clock`
2. Spawn the robot
3. Establish a stable simulation time baseline

```python
rviz2_delayed = TimerAction(period=6.0, actions=[rviz2])
```

Similarly, the spawn action was delayed by 1 second after `robot_state_publisher` starts, ensuring `/robot_description` is being published before `ros_gz_sim create` requests it:

```python
spawn_after_rsp = RegisterEventHandler(
    OnProcessStart(
        target_action = robot_state_publisher,
        on_start      = [TimerAction(period=1.0, actions=[spawn_robot])],
    )
)
```

### File Modified
- [launch/sim.launch.py](launch/sim.launch.py) — `TimerAction(6.0)` for RViz2, `TimerAction(1.0)` + `OnProcessStart` for spawner

---

## 9. Issue 8 — Gripper Continuously Rotating in Gazebo

### Symptom

The gripper assembly (links parented to `Gripper_Base_v1_1`) spun continuously in Gazebo at increasing speed, eventually flying off the robot. The arm joints also sagged downward rapidly under gravity.

### Root Cause

Two compounding factors:

**Factor 1: Mimic removal left joints uncontrolled.**  
After Issue 5 was fixed by removing `<mimic>` tags, joints `Revolute 39/40/41/44` were `continuous` type (no position limits, no upper/lower bound) with no `<dynamics>` element. A `continuous` joint in Gazebo with zero damping and zero friction is a **free revolute joint** — gravity acts on the cantilevered gripper mass, applying torque, and the joint rotates without limit. The angular velocity grows unbounded.

**Factor 2: Arm joints lacked damping.**  
Joints `link_1` through `link_6` (continuous arm joints) had no `<dynamics>` block. Without damping coefficients, the joints could not resist gravity torques and the arm sagged rapidly. Damping provides a restoring force proportional to angular velocity ($\tau_{damping} = -d \cdot \dot{\theta}$), causing oscillations to decay rather than grow.

### Physics Explanation

For a joint with mass $m$, link length $l$, and gravity $g$, the gravitational torque is:
$$\tau_{gravity} = m \cdot g \cdot l \cdot \sin(\theta)$$

Without a controller or damping, the equation of motion is:
$$I\ddot{\theta} = \tau_{gravity}$$

The joint accelerates continuously. With damping $d$:
$$I\ddot{\theta} = \tau_{gravity} - d\dot{\theta}$$

The system reaches terminal velocity and eventually settles (if gravity torque is small enough relative to damping).

### Fix

**Step 1:** Changed gripper joints from `continuous` → `revolute` with position limits and damping:

```xml
<!-- Before -->
<joint name="Revolute 39" type="continuous">
  <origin xyz="0.009526 -0.039853 0.003" rpy="0 0 -0.1"/>
  <parent link="Gripper_Base_v1_1"/>
  <child link="Gripper_Link_v1_1"/>
  <axis xyz="0.0 0.0 -1.0"/>
</joint>

<!-- After -->
<joint name="Revolute 39" type="revolute">
  <origin xyz="0.009526 -0.039853 0.003" rpy="0 0 -0.1"/>
  <parent link="Gripper_Base_v1_1"/>
  <child link="Gripper_Link_v1_1"/>
  <axis xyz="0.0 0.0 -1.0"/>
  <limit lower="-0.5" upper="0.5" effort="1.0" velocity="1.0"/>
  <dynamics damping="0.5" friction="0.1"/>
</joint>
```

Applied identically to `Revolute 40`, `Revolute 41`, and `Revolute 44`.

**Step 2:** Added `<dynamics>` to all six arm joints:

```xml
<!-- Added to link_1 through link_5 -->
<dynamics damping="5.0" friction="0.1"/>

<!-- Added to link_6 (gripper gear drive joint) -->
<dynamics damping="2.0" friction="0.1"/>
```

### Joints Modified

| Joint | Type Change | Limits Added | Damping |
|---|---|---|---|
| `Revolute 39` | `continuous` → `revolute` | ±0.5 rad | 0.5 |
| `Revolute 40` | `continuous` → `revolute` | ±0.5 rad | 0.5 |
| `Revolute 41` | `continuous` → `revolute` | ±0.5 rad | 0.5 |
| `Revolute 44` | `continuous` → `revolute` | ±0.5 rad | 0.5 |
| `link_1` through `link_5` | (unchanged) | — | 5.0 |
| `link_6` | (unchanged) | — | 2.0 |

### File Modified
- [urdf/robot.xacro](urdf/robot.xacro) — 10 joint blocks updated

---

## 10. Issue 9 — RViz2 TF Transform Errors for Entire Gripper Chain

### Symptom

RViz2 `RobotModel` display showed `Status: Error` with the message repeated for 15+ links:

```
No transform from [Gripper_Base_v1_1] to [base_link]
No transform from [Gripper_Connector_v1_1] to [base_link]
No transform from [Gripper_Connector_v1__1__1] to [base_link]
No transform from [Gripper_Finger_v1_1] to [base_link]
No transform from [Gripper_Finger_v1__1__1] to [base_link]
No transform from [Gripper_Finger_v1__2__1] to [base_link]
No transform from [Gripper_Finger_v1__3__1] to [base_link]
No transform from [Gripper_Link_Gear#1_v1_1] to [base_link]
No transform from [Gripper_Link_v1_1] to [base_link]
No transform from [Gripper_Link_v1__1__1] to [base_link]
No transform from [Gripper_Long-Straight_Washer_v1_1] to [base_link]
... (and 4 more washer + bracket links)
```

These are all links in the kinematic chain that passes through **any non-fixed joint** from the root (`base_link`).

### Root Cause

`robot_state_publisher` computes TF transforms for the entire robot tree. For **fixed joints**, it publishes static transforms independently. For **non-fixed joints** (`continuous`, `revolute`, `prismatic`, etc.), it **requires a `/joint_states` message** containing the current angle for each joint in order to compute the transform.

The launch file had no `/joint_states` source. The pipeline was:

```
Gazebo ──► (no bridge) ──► [no /joint_states topic]
                                      │
                          robot_state_publisher receives nothing
                                      │
                          Only static (fixed-joint) TFs published
                                      │
                          All links downstream of link_1 → no TF
```

Since `link_1` is the very first non-fixed joint in the chain from `base_link`, **every single descendant link** — including the entire arm and gripper — had no transform.

> **Important:** The errors showed only gripper links because the arm links (`ServoHorn`, `LongU-TypeServo_Bracket`, etc.) happened to be fixed-joined children that were included in the static TF. But the root problem was universal — all non-fixed joints had no state data.

### Fix

**Step 1:** Added the `JointStatePublisher` system plugin to `robot.gazebo`. This Gazebo Harmonic built-in plugin continuously publishes the actual simulated joint positions/velocities/efforts to a Gazebo topic:

```xml
<!-- robot.gazebo -->
<gazebo>
  <plugin filename="gz-sim-joint-state-publisher-system"
          name="gz::sim::systems::JointStatePublisher">
  </plugin>
</gazebo>
```

The plugin publishes to: `/world/empty/model/robot/joint_state` (type: `gz.msgs.Model`)

**Step 2:** Added a bridge entry in `sim.launch.py` to convert the Gazebo joint state message to a ROS `sensor_msgs/JointState` and remap it to `/joint_states`:

```python
gz_bridge = Node(
    package    = 'ros_gz_bridge',
    executable = 'parameter_bridge',
    arguments  = [
        '/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock',
        '/tf@tf2_msgs/msg/TFMessage[gz.msgs.Pose_V',
        # NEW: joint states bridge
        '/world/empty/model/robot/joint_state@sensor_msgs/msg/JointState[gz.msgs.Model',
    ],
    remappings = [
        ('/world/empty/model/robot/joint_state', '/joint_states'),  # NEW
    ],
    parameters = [{'use_sim_time': use_sim_time}],
)
```

The complete data flow after the fix:

```
Gazebo physics simulation
    │
    └── JointStatePublisher plugin
              │
              ▼
    /world/empty/model/robot/joint_state  (gz.msgs.Model)
              │
              └── ros_gz_bridge (parameter_bridge)
                        │
                        ▼
              /joint_states  (sensor_msgs/JointState)
                        │
                        └── robot_state_publisher
                                  │
                                  ▼
                    /tf + /tf_static  ──► RViz2 TF tree (complete)
```

### Files Modified
- [urdf/robot.gazebo](urdf/robot.gazebo) — `JointStatePublisher` plugin block added
- [launch/sim.launch.py](launch/sim.launch.py) — joint states bridge argument and remapping added

---

## 11. Final Architecture

### Node Graph

```
┌─────────────────────────────────────────────────────────┐
│  ROS 2 (Jazzy)                                          │
│                                                         │
│  robot_state_publisher ◄── /joint_states ◄── bridge ◄─┐│
│        │                                               ││
│        ├── /tf_static (fixed joints)                   ││
│        └── /tf        (moving joints) ──► rviz2        ││
│                                                        ││
│  rviz2 ◄── /clock ◄─────────────────────── bridge ◄──┐││
│         ◄── /tf   ◄─────────────────────── bridge ◄─┐│││
└────────────────────────────────────────────────────────┘│
                          ros_gz_bridge ──────────────────┘
                                 │
┌────────────────────────────────┼────────────────────────┐
│  Gazebo Harmonic               │                        │
│                                │                        │
│  gz_sim (empty.sdf)            │                        │t
│      │                         │                        │
│      └── robot model           │                        │
│            ├── DARTsim physics │                        │
│            ├── JointStatePublisher ──────────────────────┘
│            └── 40 STL meshes (visual only)              │
└─────────────────────────────────────────────────────────┘
```

### Known Remaining Limitations

| Limitation | Cause | Workaround |
|---|---|---|
| Mesh collision shapes approximated as AABB boxes | DARTsim limitation | Use primitive collision shapes (box/cylinder) in URDF collision tags |
| `<mimic>` joints not enforced | DARTsim limitation | Use a position controller / custom plugin |
| Arm joints sag slowly under gravity | No position controller | Add `ros2_control` hardware interface + joint trajectory controller |
| `/tf` bridge drops messages with empty frame IDs | Gazebo `Pose_V` publishes world-frame poses without frame headers | Filter at bridge level or use `gz_ros2_control` |

---

## 12. File Change Summary

### `launch/sim.launch.py` (Created New)

| Change | Reason |
|---|---|
| `SetEnvironmentVariable('GZ_SIM_RESOURCE_PATH')` | Fix mesh URI resolution |
| `gz_args: '-r -v1'` | Suppress `[Dbg]` mesh collision spam |
| `RegisterEventHandler(OnProcessStart)` + `TimerAction(1.0)` | Ensure `/robot_description` published before spawning |
| `TimerAction(6.0)` for RViz2 | Prevent "jump back in time" TF reset |
| `/clock` bridge | Enable `use_sim_time` across all ROS nodes |
| `/tf` bridge | Supply visual transforms to RViz2 |
| `/world/empty/model/robot/joint_state` bridge + remapping | Feed joint states to `robot_state_publisher` for TF tree |

### `urdf/robot.xacro`

| Change | Lines Affected | Reason |
|---|---|---|
| Fixed 16 zero-inertia tensors | ~200 lines across file | Physics Error Code 19 |
| Removed `<mimic>` from Revolute 39/40/41/44 | 4 blocks | DARTsim mimic not supported |
| Added `<dynamics damping="5.0">` to link_1–5 | 5 blocks | Prevent arm sag |
| Added `<dynamics damping="2.0">` to link_6 | 1 block | Prevent gripper gear spin |
| Changed Revolute 39/40/41/44 to `type="revolute"` | 4 blocks | Stop free rotation |
| Added `<limit lower="-0.5" upper="0.5">` to Revolute 39/40/41/44 | 4 blocks | Constrain gripper finger range |
| Added `<dynamics damping="0.5">` to Revolute 39/40/41/44 | 4 blocks | Dampen gripper finger oscillation |

### `urdf/robot.gazebo`

| Change | Reason |
|---|---|
| Replaced all `<material>Gazebo/Silver</material>` with RGBA blocks | Gazebo Harmonic dropped Ogre material support |
| Removed `libgazebo_ros_control.so` plugin | Gazebo Classic plugin, incompatible with Harmonic |
| Added `gz-sim-joint-state-publisher-system` plugin | Publish joint states to Gazebo topic for ROS bridge |

---

*Documentation generated: 2026-03-02*
