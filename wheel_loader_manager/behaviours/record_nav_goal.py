import py_trees
from geometry_msgs.msg import PoseStamped
from visualization_msgs.msg import Marker

class RecordNavGoal(py_trees.behaviour.Behaviour):
    def __init__(self, name, node, pose_attribute_name, color):
        super().__init__(name)
        self.node = node
        self.pose_attribute_name = pose_attribute_name
        self.color = color # 'orange' or 'blue'
        self.got_pose = False

        self.sub = self.node.create_subscription(PoseStamped, '/setup_goal_pose', self.pose_cb, 10)
        self.marker_pub = self.node.create_publisher(Marker, '/saved_nav_markers', 10)

    def pose_cb(self, msg):
        # Only accept a click if THIS specific node is currently active in the tree
        if self.status == py_trees.common.Status.RUNNING and not self.got_pose:
            # Save the coordinate into the main SystemManager node
            setattr(self.node, self.pose_attribute_name, msg)
            self.got_pose = True
            self.publish_marker(msg)
            self.node.get_logger().info(f"[{self.name}] Target acquired and saved as '{self.pose_attribute_name}'!")

    def initialise(self):
        # 🚀 THE FIX: Check if the main brain already has this sticky note!
        if getattr(self.node, self.pose_attribute_name, None) is not None:
            self.got_pose = True
            # Skip the log, we already have the coordinates!
        else:
            self.got_pose = False
            self.node.get_logger().info(f"[{self.name}] Waiting for RViz click on /setup_goal_pose...")
            
    def update(self):
        if self.got_pose:
            return py_trees.common.Status.SUCCESS
        return py_trees.common.Status.RUNNING

    def publish_marker(self, pose_msg):
        m = Marker()
        m.header.frame_id = "map"
        m.header.stamp = self.node.get_clock().now().to_msg()
        m.ns = self.name
        m.id = 0
        m.type = Marker.ARROW
        m.action = Marker.ADD
        m.pose = pose_msg.pose
        m.scale.x = 0.6; m.scale.y = 0.15; m.scale.z = 0.15
        
        if self.color == 'orange':
            m.color.r = 1.0; m.color.g = 0.5; m.color.b = 0.0; m.color.a = 0.8 
        else:
            m.color.r = 0.0; m.color.g = 0.5; m.color.b = 1.0; m.color.a = 0.8 
        self.marker_pub.publish(m)