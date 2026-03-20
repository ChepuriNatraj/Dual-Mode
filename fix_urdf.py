import re

with open('/home/natraj/file/src/robot_arm_description/urdf/robotic_arm.xacro', 'r') as f:
    lines = f.readlines()

new_lines = []
for i, line in enumerate(lines):
    new_lines.append(line)
    if '<axis' in line:
        # Check if the previous lines were one of our arm joints
        for j in range(1, 6):
            if any(f'name="link_{j}"' in l for l in lines[max(0, i-6):i]):
                if '</joint>' not in lines[i+1] and 'limit' not in lines[i+1] and 'mimic' not in lines[i+1]:
                    new_lines.append('</joint>\n')

with open('/home/natraj/file/src/robot_arm_description/urdf/robotic_arm.xacro', 'w') as f:
    f.write("".join(new_lines))

