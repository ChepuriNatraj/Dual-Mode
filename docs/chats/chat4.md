# Chat 4 — gesture_arm_demo: Live Hand Gesture → Robotic Arm (Session 4, March 9 2026)

---

**User:** understand the progress of the project that we are currently working right now, understand the directory and I need you to implement something for me

**GitHub Copilot:** *[Read PROGRESS.md, listed src/ directory, read launch files and URDF joint definitions]*

Project state summary:
- Phase 0 + 0b complete (URDF, Gazebo Harmonic, RViz2 all working)
- Pre-phase complete (MediaPipe landmarks working from webcam)
- Phase 1 at 40% (MoveIt2 installed, demo.launch.py runs, Setup Assistant not done)
- Phase 2 at 30% (landmarks extracted, gesture_node.py not written yet)
- Phases 3–5 not started

Asked what to implement — gesture_node, MoveIt2 config, Mode Manager, or other.

---

**User:** so the objective is to be able to move the robotic arm using hand signs that we are showing, and make it possible to move it around. Right now I know MoveIt2 is not properly setup but I just want to experiment something — create a separate package for this demonstration where by moving my hand the robot should follow my hands.

**GitHub Copilot:** *[Checked URDF joint names, limits, and existing launch files. Created a full standalone package.]*

Created new package: `src/gesture_arm_demo/`

**Files created:**
- `package.xml` — ROS2 ament_python package manifest
- `setup.py` — includes launch/ files in install
- `setup.cfg`
- `gesture_arm_demo/__init__.py`
- `gesture_arm_demo/gesture_node.py` — Main node (webcam → MediaPipe → joint angles → /joint_states)
- `launch/demo.launch.py` — Launches RSP + gesture_node + RViz2
- `launch/gesture_demo.rviz` — Clean RViz2 config with correct ROS2 plugin names

**Architecture:**
```
Webcam → MediaPipe HandLandmarker → 21 landmarks → _compute_joints() → EMA filter → JointState → /joint_states → robot_state_publisher → TF → RViz2
```

**Hand → Joint mapping:**
| Movement | Joint |
|---|---|
| Hand left ↔ right | link_1 — base |
| Hand up ↕ down | link_2 — shoulder |
| Palm lean angle | link_3 — elbow |
| Index finger direction | link_4 — wrist pitch |
| Knuckle row tilt | link_5 — wrist roll |
| Thumb–index pinch | link_6 — gripper |

Build command used: `colcon build --packages-select gesture_arm_demo` — succeeded.

---

**User:** *[Ran the launch file — got two errors:]*
1. `AttributeError: module 'mediapipe' has no attribute 'solutions'`
2. RViz2 errors: `rviz/Grid`, `rviz/RobotModel`, `rviz/Orbit` plugin not found

**GitHub Copilot:** *[Inspected existing working hand_landmarker.py — confirmed it uses tasks API not solutions API. Fixed both bugs.]*

**Bug 1 — MediaPipe API:**
The installed MediaPipe version (0.10+) removed `mp.solutions`. The gesture_node was rewritten to use the same `mediapipe.tasks` API as the working `hand_landmarker.py`:
```python
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision as mp_vision
landmarker = mp_vision.HandLandmarker.create_from_options(options)
results = landmarker.detect(mp_image)
hand_lm = results.hand_landmarks[0]  # already a list of 21 NormalizedLandmark
```
Reuses the `hand_landmarker.task` model file already at `src/hand gesture/hand_landmarker.task`.

**Bug 2 — RViz2 plugins:**
The old `urdf.rviz` used ROS1-style plugin class names (`rviz/Grid`, `rviz/Orbit`, etc.).
Created `launch/gesture_demo.rviz` with correct ROS2 names:
- `rviz_default_plugins/Grid`
- `rviz_default_plugins/RobotModel`
- `rviz_default_plugins/TF`
- `rviz_default_plugins/Orbit`

Rebuild succeeded. Both issues resolved.

---

**User:** it is working great, now update it in the progress and also save this chat, explain the code and help me understand the working of this project

**GitHub Copilot:** *[Updated PROGRESS.md, saved this chat as chat4.md, and provided full explanation below.]*

---

## Full Code & Project Explanation

### How the entire system works (data flow)

```
Your Hand
   │
   ▼
[Webcam] ──OpenCV──▶ BGR frame at 30fps
   │
   ▼
[gesture_node.py]
   ├─ cv2.flip()           — mirror image
   ├─ cvtColor BGR→RGB
   ├─ mp.Image wrapper
   ├─ HandLandmarker.detect()  ◀── hand_landmarker.task (ML model)
   │      └─ 21 NormalizedLandmark {x,y,z}  ∈ [0,1]
   ├─ _compute_joints()   — pure geometry math
   ├─ _ema_update()       — smoothing filter
   └─ JointState.publish() → /joint_states
         │
         ▼
[robot_state_publisher node]
   └─ reads /joint_states
   └─ broadcasts TF: world→base_link→link_1→...→gripper
         │
         ▼
[RViz2]
   └─ RobotModel display subscribes to /robot_description
   └─ TF display shows the transform tree
   └─ Robot renders with joints at the angles you published
```

---

### gesture_node.py — section by section

#### 1. Constants
```python
JOINTS = ['link_1', 'link_2', ..., 'link_13']   # must match URDF exactly
LIMITS = {'link_1': (-3.14, 3.14), ...}          # copy of URDF <limit> values
EMA_ALPHA = 0.3                                   # smoothing strength
```
The joint names MUST be identical to those in `robotic_arm.xacro` — that's how `robot_state_publisher` knows which TF joint to move.

#### 2. `__init__` — startup
```python
self._pub = self.create_publisher(JointState, '/joint_states', 10)
```
Creates the ROS2 topic publisher. `/joint_states` is the standard topic that `robot_state_publisher` listens to.

```python
self._landmarker = mp_vision.HandLandmarker.create_from_options(options)
```
Loads the TFLite ML model that does the actual hand detection (the `.task` file = a packaged ML model + preprocessing).

```python
self.create_timer(1.0 / 30.0, self._timer_cb)
```
Fires `_timer_cb` 30 times per second — this is the main loop.

#### 3. `_timer_cb` — the main loop (runs 30×/s)
```python
ret, frame = self._cap.read()              # grab frame from webcam
frame = cv2.flip(frame, 1)                 # mirror it
rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
results = self._landmarker.detect(mp_image) # run the ML model
```
The ML model outputs `results.hand_landmarks` — a list of hands, each with 21 landmarks.

```python
hand_lm = results.hand_landmarks[0]        # first hand found
new_joints = self._compute_joints(hand_lm) # geometry math
self._ema_update(new_joints)               # smooth
self._publish()                             # send to ROS2
```

#### 4. `_compute_joints` — the geometry brain
Each landmark is `(x, y)` where `(0,0)` = top-left, `(1,1)` = bottom-right of the camera frame.

**link_1 (base yaw):** Linear remap of wrist X position
```python
j1 = remap(wrist.x, 0.0, 1.0,  +π, -π)
# hand at left edge  → +π (arm turned left)
# hand at right edge → -π (arm turned right)
```

**link_2 (shoulder):** Linear remap of wrist Y position
```python
j2 = remap(wrist.y, 0.05, 0.95,  +π/2, -π/2)
# y=0 = top of frame → +π/2 (arm raised)
# y=1 = bottom       → -π/2 (arm lowered)
```

**link_3 (elbow):** Angle of the vector from wrist to middle knuckle
```python
j3 = atan2(dx, -dy)   # dy negated because image Y is downward
# palm leaned forward → positive angle
# palm leaned back    → negative angle
```

**link_4 (wrist pitch):** Angle of index MCP → index TIP vector
```python
j4 = atan2(dx, -dy)
# index pointing up   → 0
# index pointing down → ±π/2
```

**link_5 (wrist roll):** Tilt of the knuckle row (pinky_MCP → index_MCP)
```python
j5 = atan2(-dy, dx)
# hand flat horizontal → 0
# hand rotated/rolled  → ±π/2
```

**link_6 (gripper):** Euclidean distance between thumb tip and index tip
```python
pinch = hypot(thumb.x - index.x, thumb.y - index.y)
gripper = remap(pinch, 0.03, 0.35,  -0.5, +0.5)
# fully pinched (0.03) → -0.5 (closed)
# fully open    (0.35) → +0.5 (open)
```

#### 5. EMA filter — why it matters
Raw landmark coordinates jitter frame-to-frame even without moving your hand (ML model noise). Without smoothing the robot would vibrate constantly.

$$\text{smoothed}[t] = \alpha \cdot \text{new}[t] + (1-\alpha) \cdot \text{smoothed}[t-1]$$

With α=0.3: heavily weights the history → slow, smooth motion. Raising α toward 1.0 → faster response but more jitter.

#### 6. JointState message
```python
msg.name     = ['link_1', 'link_2', ...]    # which joints
msg.position = [j1, j2, j3, j4, j5, ...]   # radians
```
`robot_state_publisher` receives this, updates its internal joint state, recomputes forward kinematics (FK), and broadcasts `/tf` transforms for every link. RViz2 reads those transforms, looks up the mesh for each link, and draws the robot in the correct pose.

---

### Why no MoveIt2 or Gazebo is needed for this demo

| Component | Role | Needed here? |
|---|---|---|
| Gazebo | Physics simulation, collision, sensor simulation | ❌ No |
| MoveIt2 | Inverse kinematics, collision-aware path planning | ❌ No |
| `robot_state_publisher` | FK only — given joint angles, compute TF | ✅ Yes |
| RViz2 | Visualise TF tree as a 3D robot | ✅ Yes |
| `gesture_node` | Source of joint angles | ✅ Yes |

This demo is "FK-only" — you supply the joint angles directly, RSP does the forward kinematics, RViz2 shows the result. No physics, no planning needed.

When Phase 1 (MoveIt2 setup) is complete, the gesture_node will be upgraded to publish `JointTrajectory` messages to the controller instead of raw `JointState` — that will make the real arm (and Gazebo physics sim) follow the commands.

---

*End of Chat 4*
