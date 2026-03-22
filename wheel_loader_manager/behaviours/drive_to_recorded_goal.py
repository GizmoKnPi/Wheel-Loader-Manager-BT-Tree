import py_trees
from rclpy.action import ActionClient
from nav2_msgs.action import NavigateToPose

class DriveToRecordedGoal(py_trees.behaviour.Behaviour):
    def __init__(self, name, node, pose_attribute_name):
        super().__init__(name)
        self.node = node
        self.pose_attribute_name = pose_attribute_name
        
        self.goal_handle = None
        self.nav_done = False
        self.nav_success = False
        self.nav_client = ActionClient(self.node, NavigateToPose, 'navigate_to_pose')

    def initialise(self):
        self.goal_handle = None
        self.nav_done = False
        self.nav_success = False
        self.node.get_logger().info(f"[{self.name}] Retrieving '{self.pose_attribute_name}' from memory. Driving...")

    def update(self):
        if self.goal_handle is None:
            if not self.nav_client.wait_for_server(timeout_sec=1.0):
                self.node.get_logger().error(f"[{self.name}] Nav2 action server missing!")
                return py_trees.common.Status.FAILURE

            # Read the target from the main node's memory!
            target_pose = getattr(self.node, self.pose_attribute_name, None)
            if target_pose is None:
                self.node.get_logger().error(f"[{self.name}] ERROR: Target coordinate was never saved!")
                return py_trees.common.Status.FAILURE

            goal_msg = NavigateToPose.Goal()
            goal_msg.pose = target_pose
            send_goal_future = self.nav_client.send_goal_async(goal_msg)
            send_goal_future.add_done_callback(self.goal_response_cb)
            self.goal_handle = "PENDING"
            return py_trees.common.Status.RUNNING

        if self.nav_done:
            if self.nav_success:
                self.node.get_logger().info(f"[{self.name}] Destination Reached!")
                return py_trees.common.Status.SUCCESS
            else:
                return py_trees.common.Status.FAILURE

        return py_trees.common.Status.RUNNING

    def goal_response_cb(self, future):
        goal_handle = future.result()
        if not goal_handle.accepted:
            self.nav_done = True; self.nav_success = False
            return
        self.goal_handle = goal_handle
        get_result_future = goal_handle.get_result_async()
        get_result_future.add_done_callback(self.get_result_cb)

    def get_result_cb(self, future):
        self.nav_success = (future.result().status == 4)
        self.nav_done = True