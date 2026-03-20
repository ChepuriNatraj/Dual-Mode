import os

color_map = {
    'base_link': 'dark_grey',
    'link_1_1': 'orange',
    'link_2_1': 'orange',
    'link_3_1': 'orange',
    'link_4_1': 'dark_grey',
    'link_5_1': 'dark_grey',
    'Gripper_Link_v1__1__1': 'black',
    'Gripper_Link_v1_1': 'black',
    'GripperFinger_1': 'black',
    'GripperFinger2_1': 'black',
    'Gripper_Link_Gear#1_v1_1': 'black'
}

rgba_map = {
    'orange': '1.0 0.42 0.04 1.0',
    'dark_grey': '0.2 0.2 0.2 1.0',
    'black': '0.05 0.05 0.05 1.0'
}

def update_materials_xacro():
    p = 'src/robot_arm_description/urdf/materials.xacro'
    with open(p, 'w') as f:
        f.write('''<?xml version="1.0" ?>
<robot name="robotic_arm" xmlns:xacro="http://www.ros.org/wiki/xacro" >

<material name="orange">
  <color rgba="1.0 0.42 0.04 1.0"/>
</material>

<material name="dark_grey">
  <color rgba="0.2 0.2 0.2 1.0"/>
</material>

<material name="black">
  <color rgba="0.05 0.05 0.05 1.0"/>
</material>

</robot>''')

def update_urdf():
    p = 'src/robot_arm_description/urdf/robotic_arm.xacro'
    with open(p, 'r') as f:
        lines = f.readlines()
    
    out = []
    current_link = None
    for line in lines:
        if '<link name="' in line:
            current_link = line.split('"')[1]
        
        if '<material name="silver"/>' in line and current_link in color_map:
            line = line.replace('silver', color_map[current_link])
            
        out.append(line)
        
    with open(p, 'w') as f:
        f.writelines(out)

def update_gazebo():
    p = 'src/robot_arm_description/urdf/robotic_arm.gazebo'
    with open(p, 'r') as f:
        lines = f.readlines()
    
    out = []
    current_ref = None
    for line in lines:
        if '<gazebo reference="' in line:
            current_ref = line.split('"')[1]
            
        if '<material>${body_color}</material>' in line and current_ref in color_map:
            color_name = color_map[current_ref]
            rgba = rgba_map[color_name]
            indent = line[:line.find('<')]
            replacement = (
                f'{indent}<visual>\n'
                f'{indent}  <material>\n'
                f'{indent}    <ambient>{rgba}</ambient>\n'
                f'{indent}    <diffuse>{rgba}</diffuse>\n'
                f'{indent}    <specular>0.1 0.1 0.1 1.0</specular>\n'
                f'{indent}  </material>\n'
                f'{indent}</visual>\n'
            )
            out.append(replacement)
            continue
            
        out.append(line)
        
    with open(p, 'w') as f:
        f.writelines(out)

print("Updating files...")
update_materials_xacro()
update_urdf()
update_gazebo()
print("Done.")