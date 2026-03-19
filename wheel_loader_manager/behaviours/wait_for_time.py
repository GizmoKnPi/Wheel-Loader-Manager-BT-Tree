import py_trees
import rclpy
import time

class WaitForTime(py_trees.behaviour.Behaviour):
    def __init__(self, name, node, param_name):
        super().__init__(name)
        self.node = node
        self.param_name = param_name
        self.delay_seconds = 5.0  # Fallback default
        self.start_time = None

    def initialise(self):
        # 1. Fetch the freshest parameter value right as the timer starts
        try:
            self.delay_seconds = self.node.get_parameter(self.param_name).value
        except rclpy.exceptions.ParameterNotDeclaredException:
            self.node.get_logger().warn(
                f"[{self.name}] Param '{self.param_name}' not declared! Using default {self.delay_seconds}s."
            )
        
        self.start_time = time.time()
        self.node.get_logger().info(f"[{self.name}] Timer started for {self.delay_seconds} seconds.")

    def update(self):
        elapsed = time.time() - self.start_time
        
        if elapsed < self.delay_seconds:
            return py_trees.common.Status.RUNNING
        else:
            self.node.get_logger().info(f"[{self.name}] Timer complete.")
            return py_trees.common.Status.SUCCESS