import py_trees
import rclpy
from geometry_msgs.msg import Twist
from std_msgs.msg import Float32
import time

class BlindDrive(py_trees.behaviour.Behaviour):
    def __init__(self, name, node, direction=1.0):
        """
        :param direction: 1.0 for Forward (into the pile), -1.0 for Reverse (backing out)
        """
        super().__init__(name)
        self.node = node
        self.direction = direction

        # Declare parameters (won't throw an error if already declared by the main node)
        if not self.node.has_parameter('blind_drive_speed'):
            self.node.declare_parameter('blind_drive_speed', 0.05)
        if not self.node.has_parameter('standoff_distance'):
            self.node.declare_parameter('standoff_distance', 0.35)

        self.cmd_pub = self.node.create_publisher(Twist, '/cmd_vel', 10)
        
        # Subscribe to the depth calculated by SmartWiper
        self.latest_depth = 0.0
        self.depth_sub = self.node.create_subscription(
            Float32, '/scoop_depth', self.depth_callback, 10)

        self.start_time = 0.0
        self.target_duration = 0.0
        self.is_driving = False

    def depth_callback(self, msg):
        # Always keep the most recent depth measurement in memory
        self.latest_depth = msg.data

    def initialise(self):
        """Runs once when this node becomes ACTIVE."""
        speed = self.node.get_parameter('blind_drive_speed').value
        standoff = self.node.get_parameter('standoff_distance').value
        
        # Total distance to drive = empty space + physical pile depth
        total_distance = standoff + self.latest_depth
        
        # Calculate time: Time = Distance / Speed
        if speed > 0:
            self.target_duration = total_distance / speed
        else:
            self.target_duration = 0.0
            self.node.get_logger().error(f"[{self.name}] Speed is zero! Cannot calculate time.")

        self.start_time = time.time()
        self.is_driving = True
        
        dir_str = "FORWARD" if self.direction > 0 else "REVERSE"
        self.node.get_logger().info(
            f"[{self.name}] Blind Drive {dir_str}: Dist={total_distance:.2f}m, "
            f"Speed={speed:.2f}m/s, Time={self.target_duration:.1f}s"
        )

    def update(self):
        """Runs every tick while ACTIVE."""
        if not self.is_driving:
            return py_trees.common.Status.FAILURE

        elapsed_time = time.time() - self.start_time

        if elapsed_time < self.target_duration:
            # We are still driving. Publish the velocity command.
            twist = Twist()
            speed = self.node.get_parameter('blind_drive_speed').value
            twist.linear.x = speed * self.direction
            self.cmd_pub.publish(twist)
            return py_trees.common.Status.RUNNING
        else:
            # Timer is up. STOP the robot.
            self.stop_robot()
            self.node.get_logger().info(f"[{self.name}] Drive complete. Robot stopped.")
            self.is_driving = False
            return py_trees.common.Status.SUCCESS

    def terminate(self, new_status):
        """Runs when the node finishes naturally, or if it is interrupted (e.g. by manual override)."""
        if self.is_driving:
            self.stop_robot()
            self.is_driving = False
        self.node.get_logger().info(f"[{self.name}] Terminated with status: {new_status}")

    def stop_robot(self):
        """Helper to safely stop the motors."""
        twist = Twist()
        twist.linear.x = 0.0
        twist.angular.z = 0.0
        self.cmd_pub.publish(twist)