import py_trees
import rclpy
from rclpy.action import ActionClient
from geometry_msgs.msg import PoseStamped
from nav2_msgs.action import NavigateToPose

class WaitForDumpGoal(py_trees.behaviour.Behaviour):
    def __init__(self, node, name="WaitForDumpGoal"):
        super().__init__(name)
        self.node = node
        self.goal_received = False
        self.target_pose = None
        self.nav_client = ActionClient(self.node, NavigateToPose, 'navigate_to_pose')
        self.goal_handle = None
        self.nav_done = False
        self.nav_success = False

        # Listen to RViz clicks
        self.pose_sub = self.node.create_subscription(
            PoseStamped,
            '/goal_pose',
            self.pose_cb,
            10
        )

    def pose_cb(self, msg):
        # Only accept the RViz click if the tree is actually at this step!
        if self.status == py_trees.common.Status.RUNNING and not self.goal_received:
            self.target_pose = msg
            self.goal_received = True
            self.node.get_logger().info(f"[{self.name}] Dump site goal received from RViz! Sending to Nav2...")

    def update(self):
        # 1. Wait for human to click RViz
        if not self.goal_received:
            self.node.get_logger().info(f"[{self.name}] WAITING... Please click '2D Goal Pose' in RViz for the dump site.", throttle_duration_sec=3.0)
            return py_trees.common.Status.RUNNING

        # 2. Fire the goal to Nav2
        if self.goal_received and self.goal_handle is None:
            if not self.nav_client.wait_for_server(timeout_sec=1.0):
                self.node.get_logger().error("Nav2 action server not available!")
                return py_trees.common.Status.FAILURE

            goal_msg = NavigateToPose.Goal()
            goal_msg.pose = self.target_pose
            
            send_goal_future = self.nav_client.send_goal_async(goal_msg)
            send_goal_future.add_done_callback(self.goal_response_cb)
            self.goal_handle = "PENDING" 
            return py_trees.common.Status.RUNNING

        # 3. Wait for Nav2 to finish driving
        if self.nav_done:
            if self.nav_success:
                self.node.get_logger().info(f"[{self.name}] Arrived at dump site!")
                return py_trees.common.Status.SUCCESS
            else:
                self.node.get_logger().error(f"[{self.name}] Failed to reach dump site. Aborting.")
                return py_trees.common.Status.FAILURE

        return py_trees.common.Status.RUNNING

    def goal_response_cb(self, future):
        goal_handle = future.result()
        if not goal_handle.accepted:
            self.node.get_logger().error("Nav2 rejected dump goal.")
            self.nav_done = True
            self.nav_success = False
            return
        self.goal_handle = goal_handle
        get_result_future = goal_handle.get_result_async()
        get_result_future.add_done_callback(self.get_result_cb)

    def get_result_cb(self, future):
        status = future.result().status
        if status == 4: # 4 is SUCCEEDED in ROS 2 Action Status
            self.nav_success = True
        else:
            self.nav_success = False
        self.nav_done = True