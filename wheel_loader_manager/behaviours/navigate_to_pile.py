import py_trees
from nav2_msgs.action import NavigateToPose
from rclpy.action import ActionClient
from geometry_msgs.msg import PoseStamped
from action_msgs.msg import GoalStatus

class NavigateToPile(py_trees.behaviour.Behaviour):

    def __init__(self, node):
        super().__init__("NavigateToPile")
        self.node = node
        self.goal_sent = False
        self.result_future = None
        self.goal_handle = None

        self.client = ActionClient(
            node,
            NavigateToPose,
            'navigate_to_pose'
        )

    def initialise(self):
        self.goal_sent = False

    def update(self):

        # If teleop interrupted, don't cancel goal
        # Let twist_mux handle motion arbitration

        if not self.goal_sent:
            if not self.client.wait_for_server(timeout_sec=1.0):
                self.node.get_logger().info("Waiting for Nav2 action server...")
                return py_trees.common.Status.RUNNING

            goal_msg = NavigateToPose.Goal()
            goal_msg.pose = self.create_goal()

            self.node.get_logger().info("Sending Nav2 Goal...")

            send_goal_future = self.client.send_goal_async(goal_msg)
            send_goal_future.add_done_callback(self.goal_response_callback)

            self.goal_sent = True
            return py_trees.common.Status.RUNNING

        if self.result_future is not None:
            if self.result_future.done():
                result = self.result_future.result()
                if result.status == GoalStatus.STATUS_SUCCEEDED:
                    self.node.get_logger().info("Navigation Succeeded")
                    return py_trees.common.Status.SUCCESS
                else:
                    self.node.get_logger().info("Navigation Failed")
                    return py_trees.common.Status.FAILURE

        return py_trees.common.Status.RUNNING

    def goal_response_callback(self, future):
        self.goal_handle = future.result()
        if not self.goal_handle.accepted:
            self.node.get_logger().info("Goal rejected")
            return
        self.result_future = self.goal_handle.get_result_async()

    def create_goal(self):
        pose = PoseStamped()
        pose.header.frame_id = "map"
        pose.header.stamp = self.node.get_clock().now().to_msg()

        pose.pose.position.x = 2.0   # CHANGE THIS
        pose.pose.position.y = 1.0   # CHANGE THIS
        pose.pose.orientation.w = 1.0

        return pose