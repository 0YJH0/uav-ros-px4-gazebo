import os

from glob import glob

from setuptools import find_packages
from setuptools import setup


package_name = 'uav_learning'


setup(

    name=package_name,

    version='0.0.0',

    packages=find_packages(
        exclude=['test']
    ),

    data_files=[

        (
            'share/ament_index/resource_index/packages',
            [
                'resource/' + package_name
            ],
        ),

        (
            'share/' + package_name,
            [
                'package.xml'
            ],
        ),

        (
            os.path.join(
                'share',
                package_name,
                'launch',
            ),
            glob(
                'launch/*.launch.py'
            ),
        ),

    ],

    install_requires=[
        'setuptools'
    ],

    zip_safe=True,

    maintainer='yjh',

    maintainer_email='yjh@todo.todo',

    description=(
        'ROS 2 UAV autonomous perception, '
        'PX4 Offboard control and Gazebo mission simulation.'
    ),

    license='Apache-2.0',

    tests_require=[
        'pytest'
    ],

    entry_points={

        'console_scripts': [

            'status_publisher = '
            'uav_learning.status_publisher:main',

            'status_subscriber = '
            'uav_learning.status_subscriber:main',

            'uav_state_publisher = '
            'uav_learning.uav_state_publisher:main',

            'uav_state_monitor = '
            'uav_learning.uav_state_monitor:main',

            'uav_mode_server = '
            'uav_learning.uav_mode_server:main',

            'uav_mode_client = '
            'uav_learning.uav_mode_client:main',

            'fly_to_altitude_server = '
            'uav_learning.fly_to_altitude_server:main',

            'fly_to_altitude_client = '
            'uav_learning.fly_to_altitude_client:main',

            'px4_offboard_controller = '
            'uav_learning.px4_offboard_controller:main',

            'perception_node = '
            'uav_learning.perception_node:main',

            'benchmark_logger = '
            'uav_learning.benchmark_logger:main',

            'batch_benchmark_runner = '
            'uav_learning.batch_benchmark:main',

        ],
    },
)
