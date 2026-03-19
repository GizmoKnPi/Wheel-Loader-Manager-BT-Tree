import py_trees
import rclpy
from rclpy.action import ActionClient
from geometry_msgs.msg import PoseStamped
from nav2_msgs.action import NavigateToPose
from visualization_msgs.msg import Marker # 🚀 IMPORTED FOR RVIZ HOLOGRAMS

class ReusableNavGoal(py_trees.behaviour.Behaviour):
    def __init__(self, name, node, topic_name='/goal_pose'):
        super().__init__(name)
        self.node = node
        self.topic_name = topic_name
        self.saved_pose = None
        self.goal_handle = None
        self.nav_done = False
        self.nav_success = False

        self.nav_client = ActionClient(self.node, NavigateToPose, 'navigate_to_pose')
        self.pose_sub = self.node.create_subscription(PoseStamped, self.topic_name, self.pose_cb, 10)

        # 🚀 Create the RViz Marker Publisher and a 1-second refresh timer
        self.marker_pub = self.node.create_publisher(Marker, '/saved_nav_markers', 10)
        self.marker_timer = self.node.create_timer(1.0, self.publish_marker)

    def publish_marker(self):
        # Only draw the hologram if we actually have a saved coordinate!
        if self.saved_pose is not None:
            m = Marker()
            m.header.frame_id = "map"
            m.header.stamp = self.node.get_clock().now().to_msg()
            m.ns = self.name # Keeps the Pile and Dump arrows separate
            m.id = 0
            m.type = Marker.ARROW
            m.action = Marker.ADD
            m.pose = self.saved_pose.pose

            # Make the arrow massive so it's easy to see (60cm long)
            m.scale.x = 0.6
            m.scale.y = 0.15
            m.scale.z = 0.15

            # Color code them so you never get confused
            if "Pile" in self.name:
                # Orange for the Woodchip Pile
                m.color.r = 1.0; m.color.g = 0.5; m.color.b = 0.0; m.color.a = 0.8 
            else:
                # Blue for the Dump Site
                m.color.r = 0.0; m.color.g = 0.5; m.color.b = 1.0; m.color.a = 0.8 

            self.marker_pub.publish(m)

    def pose_cb(self, msg):
        # Only accept a click if we don't already have one saved!
        if self.status == py_trees.common.Status.RUNNING and self.saved_pose is None:
            self.saved_pose = msg
            self.node.get_logger().info(f"[{self.name}] RViz coordinate locked into memory!")

    def initialise(self):
        # Reset the Nav2 states so it can drive again, but keep the saved memory!
        self.goal_handle = None
        self.nav_done = False
        self.nav_success = False

        if self.saved_pose is None:
            self.node.get_logger().info(f"[{self.name}] Waiting for FIRST RViz click on {self.topic_name}...")
        else:
            self.node.get_logger().info(f"[{self.name}] Reusing memorized coordinate. Driving...")

    def update(self):
        # 1. Wait for the first click
        if self.saved_pose is None:
            return py_trees.common.Status.RUNNING

        # 2. Fire the Nav2 Goal using the saved memory
        if self.goal_handle is None:
            if not self.nav_client.wait_for_server(timeout_sec=1.0):
                self.node.get_logger().error(f"[{self.name}] Nav2 action server missing!")
                return py_trees.common.Status.FAILURE

            goal_msg = NavigateToPose.Goal()
            goal_msg.pose = self.saved_pose
            send_goal_future = self.nav_client.send_goal_async(goal_msg)
            send_goal_future.add_done_callback(self.goal_response_cb)
            self.goal_handle = "PENDING"
            return py_trees.common.Status.RUNNING

        # 3. Wait to arrive
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