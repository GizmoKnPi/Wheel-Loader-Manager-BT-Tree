import py_trees
from std_msgs.msg import Bool

class AlignWithPile(py_trees.behaviour.Behaviour):

    def __init__(self, node):
        super().__init__("AlignWithPile")

        self.node = node
        self.is_arrived = False

        self.node.create_subscription(
            Bool,
            "/woodchip_tracker/arrived",
            self.callback,
            10
        )

    def callback(self, msg):
        self.is_arrived = msg.data

    def update(self):
        # Wait until the tracker explicitly confirms we are centered AND close enough
        if self.is_arrived:
            self.node.get_logger().info("[BT] Alignment Complete - Triggering Scoop!")
            return py_trees.common.Status.SUCCESS

        return py_trees.common.Status.RUNNING