import re

with open('/home/natraj/file/src/robot_arm_description/urdf/robotic_arm.xacro', 'r') as f:
    content = f.read()

# Fix the broken formatting
for i in range(1, 6):
    pattern = rf'<joint name="link_{i}" type="<limit lower="-3.14159" upper="3.14159" effort="100.0" velocity="1.0"/>\n  ">'
    replacement = rf'<joint name="link_{i}" type="revolute">\n  <limit lower="-3.14159" upper="3.14159" effort="100.0" velocity="1.0"/>'
    content = re.sub(pattern, replacement, content, flags=re.DOTALL)

with open('/home/natraj/file/src/robot_arm_description/urdf/robotic_arm.xacro', 'w') as f:
    f.write(content)

print("Restored joints.")
