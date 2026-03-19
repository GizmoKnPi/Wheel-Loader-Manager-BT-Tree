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

    def initialise(self):
        # 🚀 THE FIX: Shred the memory from the previous loop!
        # This forces the node to wait for a FRESH 'True' message from the tracker.
        self.is_arrived = False
        self.node.get_logger().info(f"[{self.name}] Waking up for alignment... memory wiped!")

    def update(self):
        # Wait until the tracker explicitly confirms we are centered AND close enough
        if self.is_arrived:
            self.node.get_logger().info("[BT] Alignment Complete - Triggering Scoop!")
            return py_trees.common.Status.SUCCESS

        return py_trees.common.Status.RUNNING