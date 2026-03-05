import py_trees

class ManualOverride(py_trees.behaviour.Behaviour):

    def __init__(self, node):
        super().__init__("ManualOverride")
        self.node = node

    def update(self):
        if self.node.teleop_active:
            self.node.get_logger().info("Manual Override Active")
            return py_trees.common.Status.SUCCESS
        else:
            return py_trees.common.Status.FAILURE