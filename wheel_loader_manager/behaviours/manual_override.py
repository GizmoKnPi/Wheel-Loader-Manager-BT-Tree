import py_trees

class ManualOverride(py_trees.behaviour.Behaviour):

    def __init__(self, node):
        super().__init__("ManualOverride")
        self.node = node

    def update(self):

        if self.node.teleop_active():
            self.node.get_logger().info("Manual Override Active", throttle_duration_sec=2)
            return py_trees.common.Status.SUCCESS

        return py_trees.common.Status.FAILURE