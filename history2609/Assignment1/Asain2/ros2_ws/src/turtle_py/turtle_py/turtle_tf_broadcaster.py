import math

import rclpy
from rclpy.node import Node

from geometry_msgs.msg import TransformStamped
from turtlesim.msg import Pose
from tf2_ros import TransformBroadcaster


class TurtleTFBroadcaster(Node):

    def __init__(self):
        super().__init__('turtle_tf_broadcaster')

        self.tf_broadcaster = TransformBroadcaster(self)

        self.subscription = self.create_subscription(
            Pose,
            '/turtle1/pose',
            self.pose_callback,
            10
        )

    def pose_callback(self, msg):
        transform = TransformStamped()

        # 현재 시간
        transform.header.stamp = self.get_clock().now().to_msg()

        # 좌표계 관계: world → turtle1
        transform.header.frame_id = 'world'
        transform.child_frame_id = 'turtle1'

        # 위치
        transform.transform.translation.x = msg.x
        transform.transform.translation.y = msg.y
        transform.transform.translation.z = 0.0

        # theta → quaternion
        transform.transform.rotation.x = 0.0
        transform.transform.rotation.y = 0.0
        transform.transform.rotation.z = math.sin(msg.theta / 2.0)
        transform.transform.rotation.w = math.cos(msg.theta / 2.0)

        # TF 발행
        self.tf_broadcaster.sendTransform(transform)


def main(args=None):
    rclpy.init(args=args)

    node = TurtleTFBroadcaster()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
