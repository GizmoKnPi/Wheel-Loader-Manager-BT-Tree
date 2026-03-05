import py_trees
from std_msgs.msg import Bool


class DisableTracker(py_trees.behaviour.Behaviour):

    def __init__(self, node):
        super().__init__("DisableTracker")
        self.node = node
        self.pub = node.create_publisher(Bool, "/woodchip_tracker/enable", 10)
        self.sent = False

    def initialise(self):
        self.sent = False

    def update(self):

        if not self.sent:
            msg = Bool()
            msg.data = False
            self.pub.publish(msg)

            self.node.get_logger().info("[BT] Woodchip tracker DISABLED")
            self.sent = True

        return py_trees.common.Status.SUCCESS