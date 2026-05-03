source ~/file/install/setup.bash
ros2 launch robot_arm_hardware hardware_gesture.launch.py serial_port:=/dev/ttyUSB0 camera_index:=0 enable_gesture:=true

sudo chmod a+rw /dev/ttyUSB0