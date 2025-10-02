import sys
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, GroupAction, DeclareLaunchArgument, LogInfo
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_xml.launch_description_sources import XMLLaunchDescriptionSource
from launch_ros.actions import Node, SetParameter
from launch_ros.substitutions import FindPackageShare
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution, PythonExpression, TextSubstitution
from launch.conditions import IfCondition


def generate_launch_description():
    robot_model = LaunchConfiguration("robot_model")

    declare_use_namespace_cmd = DeclareLaunchArgument(
        "use_namespace",
        default_value="false",
        description="Whether to apply a namespace to the navigation nodes",
    )

    declare_namespace_cmd = DeclareLaunchArgument(
        "namespace", 
        default_value="", 
        description="Top-level namespace"
    )

    declare_use_sim_time_cmd = DeclareLaunchArgument(
        "use_sim_time",
        default_value="false",
        description="Use simulation (Gazebo) clock if true",
    )

    declare_robot_model_cmd = DeclareLaunchArgument(
        "robot_model",
        default_value="ranger_mini_v3",
        description="ranger_mini_v3",
    )

    SetParameter(
        condition=IfCondition(LaunchConfiguration("use_sim_time")),
        name="use_sim_time",
        value=LaunchConfiguration("use_sim_time"),
    )

    SetParameter(
        condition=IfCondition(LaunchConfiguration("use_namespace")),
        name="namespace",
        value=LaunchConfiguration("namespace"),
    )

    # --------- Robot Base ---------
    robot_base_bringup = GroupAction([
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource([
                PathJoinSubstitution([
                    FindPackageShare("ranger_bringup"),
                    "launch",
                    "ranger_mini_v3.launch.py",
                ])
            ]),
            launch_arguments={
                "port_name": "can0",
                "robot_model": robot_model,
                "odom_frame": "odom",
                "base_frame": "base_link",
                "update_rate": "50",
                "odom_topic_name": "odom",
                "publish_odom_tf": "true",
            }.items(),
        ),
        Node(
            package="tf2_ros",
            executable="static_transform_publisher",
            name="base_footprint_transform_publisher",
            arguments=['--x', '0.0', '--y', '-0.0', '--z', '0.0',
                       '--yaw', '0', '--pitch', '0', '--roll', '0',
                       '--frame-id', 'base_link', '--child-frame-id', 'base_footprint']
        )
    ])

    # --------- Chassis ---------
    chassis_bringup = GroupAction([
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource([
                PathJoinSubstitution([
                    FindPackageShare("invs_bringup"),
                    "launch",
                    "chassis.launch.py",
                ])
            ])
        )
    ])



    laser_transform_publisher = Node(
        package="tf2_ros",
        executable="static_transform_publisher",
        name="hesai_lidar_transform_publisher",
        arguments=['--x', '0.0', '--y', '-0.0', '--z', '0.3',
                   '--yaw', '0', '--pitch', '0', '--roll', '0',
                   '--frame-id', 'base_link', '--child-frame-id', 'base_laser'])
    
    laser_to_hesai_tf = Node(
        package="tf2_ros",
        executable="static_transform_publisher",
        name="laser_to_hesai_tf",
        arguments=['--x', '0.0', '--y', '-0.0', '--z', '0.0',
                   '--yaw', '1.5714', '--pitch', '0', '--roll', '0',
                   '--frame-id', 'base_laser', '--child-frame-id', 'hesai_lidar']
    )

    cloud_to_laser_node = Node(
            package="pointcloud_to_laserscan",
            executable="pointcloud_to_laserscan_node",
            name="pointcloud_to_laserscan_node",
            output="screen",
            parameters=[{
                'target_frame': 'base_laser',
                "range_min": 0.1,
                "range_max": 30.0,
                "scan_time": 0.1,
                "min_height": -0.4,
                "max_height": 0.5,
                "angle_min": -3.14159265,
                "angle_max": 3.14159265,
                "angle_increment": 0.00872664625,
                "inf_epsilon": 1.0,
                "tf_tolerance": 0.03,
            }],
            remappings=[
                ("/cloud_in", "/lidar_points"),
                ("/scan", "/scan"),
            ],
        )

    return LaunchDescription([
        declare_use_namespace_cmd,
        declare_namespace_cmd,
        declare_use_sim_time_cmd,
        declare_robot_model_cmd,
        robot_base_bringup,
        chassis_bringup,
        cloud_to_laser_node,
        laser_transform_publisher,
        laser_to_hesai_tf
    ])
