import py_trees
from std_msgs.msg import Float32


class AlignWithPile(py_trees.behaviour.Behaviour):

    def __init__(self, node):
        super().__init__("AlignWithPile")

        self.node = node
        self.distance = None

        # same threshold used in tracker
        self.arrival_threshold = 20.0

        node.create_subscription(
            Float32,
            "/woodchip_tracker/bottom_distance",
            self.callback,
            10
        )

    def callback(self, msg):
        self.distance = msg.data

    def update(self):

        if self.distance is None:
            return py_trees.common.Status.RUNNING

        if self.distance <= self.arrival_threshold:

            self.node.get_logger().info("[BT] Alignment Complete")

            return py_trees.common.Status.SUCCESS

        return py_trees.common.Status.RUNNING