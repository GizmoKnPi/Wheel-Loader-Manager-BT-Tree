import py_trees
import rclpy
from geometry_msgs.msg import Twist
import time

class HatchOpenReverseBlindDrive(py_trees.behaviour.Behaviour):
    def __init__(self, name, node, distance):
        super().__init__(name)
        self.node = node
        self.target_distance = distance
        self.cmd_pub = self.node.create_publisher(Twist, '/cmd_vel', 10)
        
        # Set speed based on direction
        self.speed = 0.15 if self.target_distance > 0 else -0.20
        
        # Calculate how many seconds we need to drive
        if self.speed != 0:
            self.duration = abs(self.target_distance / self.speed)
        else:
            self.duration = 0.0
            
        self.start_time = None

    def initialise(self):
        self.start_time = time.time()
        self.node.get_logger().info(f"[{self.name}] Reversing {self.target_distance}m for {self.duration:.2f} seconds...")

    def update(self):
        elapsed = time.time() - self.start_time
        cmd = Twist()
        
        if elapsed < self.duration:
            cmd.linear.x = self.speed
            self.cmd_pub.publish(cmd)
            return py_trees.common.Status.RUNNING
        else:
            # Slam the brakes
            cmd.linear.x = 0.0
            self.cmd_pub.publish(cmd)
            self.node.get_logger().info(f"[{self.name}] Fixed drive complete.")
            return py_trees.common.Status.SUCCESS

    def terminate(self, new_status):
        # Safety catch: if the tree is killed or interrupted, stop the motors
        cmd = Twist()
        cmd.linear.x = 0.0
        self.cmd_pub.publish(cmd)