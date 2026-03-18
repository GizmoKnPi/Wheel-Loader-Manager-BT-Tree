import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    # Point directly to the config file in your package
    config_file = os.path.join(
        get_package_share_directory('wheel_loader_manager'),
        'config',
        'manager_params.yaml'
    )

    manager_node = Node(
        package='wheel_loader_manager',
        executable='system_manager', # Make sure this matches your setup.py entry point
        name='system_manager',
        parameters=[config_file],
        output='screen'
    )

    return LaunchDescription([
        manager_node
    ])