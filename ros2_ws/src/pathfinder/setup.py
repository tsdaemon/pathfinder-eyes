from setuptools import find_packages, setup

package_name = 'pathfinder'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/pathfinder/launch', [
            'launch/robot_launch.py',
            'launch/calibrate_launch.py',
            'launch/rmaptab_launch.py',
        ]),
        ('share/pathfinder/camera', [
            'pathfinder/camera/left.yaml',
            'pathfinder/camera/right.yaml',
        ]),
    ],
    install_requires=['setuptools', 'icm20948'],
    zip_safe=True,
    maintainer='anatolii',
    maintainer_email='anatolii.stehnii@gmail.com',
    description='Pathfinder',
    license='MIT',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'imu_node = pathfinder.imu_node:main',
            'camera_node = pathfinder.camera_node:main',
        ],
        'launch': [
            'robot_launch  = pathfinder.launch.robot_launch:generate_launch_description',
            'calibrate_launch = pathfinder.launch.calibrate_launch:generate_launch_description',
            'rmaptab_launch = pathfinder.launch.rmaptab_launch:generate_launch_description',
        ],
    },
)
