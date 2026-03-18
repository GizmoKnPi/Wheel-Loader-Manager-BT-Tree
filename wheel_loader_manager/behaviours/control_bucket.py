import py_trees
import rclpy
from std_msgs.msg import String

class ControlBucket(py_trees.behaviour.Behaviour):
    def __init__(self, name, node, command, expected_state):
        """
        :param command: The character to send (e.g., 'R', 'B', 'N')
        :param expected_state: The string to wait for (e.g., 'RESET', 'SCOOP', 'NAV')
        """
        super().__init__(name)
        self.node = node
        self.command = command
        self.expected_state = expected_state

        self.current_bucket_state = "UNKNOWN"
        self.command_sent = False

        # Subscriber to listen to the bucket's current position
        self.state_sub = self.node.create_subscription(
            String,
            '/bucket_position',
            self.state_callback,
            10
        )

        # Publisher to send the command character to the servo_driver
        self.cmd_pub = self.node.create_publisher(
            String,
            '/bucket_command',
            10
        )

    def state_callback(self, msg):
        self.current_bucket_state = msg.data

    def initialise(self):
        """Runs once each time the node is ticked from an IDLE state."""
        self.command_sent = False
        self.node.get_logger().info(f"[{self.name}] Initialized. Target state: {self.expected_state}")

    def update(self):
        """Runs every tick."""
        
        # 1. Send the command if we haven't already
        if not self.command_sent:
            msg = String()
            msg.data = self.command
            self.cmd_pub.publish(msg)
            self.command_sent = True
            self.node.get_logger().info(f"[{self.name}] Sent command '{self.command}'. Waiting for '{self.expected_state}'...")
            return py_trees.common.Status.RUNNING

        # 2. Wait for the ESP32 to confirm the bucket reached the position
        if self.current_bucket_state == self.expected_state:
            self.node.get_logger().info(f"[{self.name}] Success! Bucket is in {self.expected_state} position.")
            return py_trees.common.Status.SUCCESS
        
        # 3. Still waiting
        return py_trees.common.Status.RUNNING

    def terminate(self, new_status):
        """Runs when the node finishes or is interrupted."""
        self.node.get_logger().info(f"[{self.name}] Terminated with status {new_status}")