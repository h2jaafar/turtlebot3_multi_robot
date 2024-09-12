#!/usr/bin/env python3
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Authors: Arshad Mehmood

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, RegisterEventHandler
from launch.substitutions import LaunchConfiguration
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
from launch.event_handlers import OnProcessExit
from launch.conditions import IfCondition


def generate_launch_description():
    ld = LaunchDescription()

    TURTLEBOT3_MODEL = "burger"
    enable_drive = LaunchConfiguration("enable_drive", default="true")
    declare_enable_drive = DeclareLaunchArgument(
        name="enable_drive", default_value="true", description="Enable robot drive node"
    )

    turtlebot3_multi_robot = get_package_share_directory("turtlebot3_multi_robot")
    launch_file_dir = os.path.join(turtlebot3_multi_robot, "launch")

    world = os.path.join(
        turtlebot3_multi_robot, "worlds", "multi_empty_world.world"
    )

    urdf_file_name = "turtlebot3_" + TURTLEBOT3_MODEL + ".urdf"
    print("urdf_file_name : {}".format(urdf_file_name))

    urdf = os.path.join(
        turtlebot3_multi_robot, "urdf", urdf_file_name
    )

    gzserver_cmd = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(get_package_share_directory("gazebo_ros"), "launch", "gzserver.launch.py")
        ),
        launch_arguments={"world": world}.items(),
    )

    gzclient_cmd = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(get_package_share_directory("gazebo_ros"), "launch", "gzclient.launch.py")
        ),
    )

    ld.add_action(declare_enable_drive)
    ld.add_action(gzserver_cmd)
    ld.add_action(gzclient_cmd)

    robot_counter = 1
    ROWS = 2
    COLS = 2

    x = -ROWS
    y = -COLS
    last_action = None
    remappings = [("/tf", "tf"), ("/tf_static", "tf_static")]

    for i in range(COLS):
        x = -ROWS
        for j in range(ROWS):
            namespace = "B" + "{:02}".format(robot_counter)
            # name = "turtlebot" + str(i) + "_" + str(j)
            name = namespace
            robot_counter += 1

            turtlebot_state_publisher = Node(
                package="robot_state_publisher",
                namespace=namespace,
                executable="robot_state_publisher",
                output="screen",
                parameters=[{"use_sim_time": False,
                             "publish_frequency": 10.0}],
                remappings=remappings,
                arguments=[urdf],
            )

            spawn_turtlebot3_burger = Node(
                package="gazebo_ros",
                executable="spawn_entity.py",
                arguments=[
                    "-file",
                    os.path.join(turtlebot3_multi_robot,'models', 'turtlebot3_' + TURTLEBOT3_MODEL, 'model.sdf'),
                    "-entity",
                    name,
                    "-robot_namespace",
                    namespace,
                    "-x",
                    str(x),
                    "-y",
                    str(y),
                    "-z",
                    "0.01",
                    "-Y",
                    "3.14159",
                    "-unpause",
                ],
                output="screen",
            )

            x += 2.0

            if last_action is None:
                ld.add_action(turtlebot_state_publisher)
                ld.add_action(spawn_turtlebot3_burger)
            else:
                spawn_turtlebot3_event = RegisterEventHandler(
                    event_handler=OnProcessExit(
                        target_action=last_action,
                        on_exit=[spawn_turtlebot3_burger,
                                 turtlebot_state_publisher],
                    )
                )
                ld.add_action(spawn_turtlebot3_event)

            last_action = spawn_turtlebot3_burger

        y += 2.0

    return ld
