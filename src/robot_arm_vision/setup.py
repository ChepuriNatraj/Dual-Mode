from setuptools import find_packages, setup

package_name = 'robot_arm_vision'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/launch', [
            'launch/sorting.launch.py',
            'launch/hardware_sorting.launch.py'
        ]),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='natraj',
    maintainer_email='chepurinatraj2005@gmail.com',
    description='TODO: Package description',
    license='TODO: License declaration',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'vision_node = robot_arm_vision.vision_node:main',
            'sorting_planner_node = robot_arm_vision.sorting_planner_node:main',
            'esp32_camera_bridge = robot_arm_vision.esp32_camera_bridge:main'
        ],
    },
)