# Session 6: Bridging MoveIt 2 and Gazebo Harmonic

## Context
The robotic arm system's simulation phase (Phase 0/1) was reaching completion. While MoveIt 2 successfully generated paths using fake hardware in RViz, and Gazebo Harmonic could spawn the URDF model, the two layers were completely disconnected. Gazebo couldn't control the arm based on MoveIt trajectories.

## Identified Issues & Troubleshooting

### 1. The Sagging Robot Base
**Issue:** When launching the robot in Gazebo, the arm's base would physically tilt over or detach from the ground.
**Root Cause:** MoveIt defined a `Virtual Joint` to connect `base_link` to the `world_frame`. While RViz respects virtual joints, Gazebo's physics engine completely ignores them. Consequently, gravity pulled the unbalanced base downwards in the simulator. 
**Solution:** Hardcoded a static `world` link and a `fixed` joint directly into the actual `src/robot_arm_description/urdf/robotic_arm.xacro`. The Gazebo world physically bolts the model upright. 

### 2. MoveIt Controllers vs Gazebo Controllers Fighting / Multi-Spawn Bug
**Issue:** Attempting to spawn controllers crashed, often accompanied by duplicate `robotic_arm_0` entries in Gazebo and `Failed to configure controller` errors. 
**Root Cause:**
- Hanging background simulation processes retained old model iterations in memory. 
- The URDF requested `gz_ros2_control::GazeboRos2ControlPlugin` which is deprecated in Gazebo Harmonic. It failed silently, the Controller Manager aborted, and spawners timed out.
**Solution:**
- Modified `robotic_arm.gazebo` to specify the modern `gz_ros2_control::GazeboSimROS2ControlPlugin`.
- Enforced clean process destruction between runs (`killall -9 gz ros2 rviz2 ruby`).

### 3. RViz "Robot Model Not Found" Flickering and Crashing
**Issue:** The TF tree continuously bounced, RViz displayed errors about the robot model disappearing, and RViz frequently crashed or froze entirely while Gazebo ran smoothly. 
**Root Cause:** Zombie `ros_gz_bridge` processes and massive time-clock mismatches. 
- When shutting down previous launch files abruptly, the simulation parameter bridge often failed to terminate fully.
- This resulted in multiple ghost bridges simultaneously fighting to publish the `/clock` topic over DDS.
- RViz and MoveIt received completely chaotic time jumps (e.g. bouncing from epoch 5 to 110, then back to 45). The `tf2_buffer` flooded with `Detected jump back in time` warnings, eventually crashing the RViz render threads entirely.
**Solution:** 
- Nuke all hanging network bridges brutally with `killall -9 parameter_bridge ruby gz rviz2 move_group robot_state_publisher spawner`.
- Updated `src/robot_arm_gazebo/config/controllers.yaml` parameters explicitly enforcing `use_sim_time: true` inside the Controller Manager. 
- Configured a custom combined launch script (`moveit_gazebo.launch.py`) that boots components asynchronously on a delay, guaranteeing the unified `sim_time` clock establishes dominance before MoveIt subscribes to TF data.

## Final Resolution
The system is now fully integrated and stable. The `moveit_gazebo.launch.py` script correctly passes the `use_fake_hardware:=false` arguments down the pipeline, boots up Gazebo Harmonic, spawns the physical controller models, and delays MoveIt precisely until `tf2` and `joint_states` stabilize. RViz now accurately matches the Gazebo simulation without time drift and correctly routes `follow_joint_trajectory` commands down into the simulated robot. 
