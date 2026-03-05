import py_trees
from std_srvs.srv import Trigger


class ProcessCloud(py_trees.behaviour.Behaviour):

    def __init__(self, node):
        super().__init__("ProcessCloud")

        self.node = node
        self.client = node.create_client(Trigger, "/process_scan")

        self.future = None

    def initialise(self):
        self.future = None

    def update(self):

        if not self.client.service_is_ready():
            self.node.get_logger().warn("[BT] process_scan service not available")
            return py_trees.common.Status.RUNNING

        if self.future is None:

            req = Trigger.Request()
            self.future = self.client.call_async(req)

            self.node.get_logger().info("[BT] Processing Cloud")

            return py_trees.common.Status.RUNNING

        if not self.future.done():
            return py_trees.common.Status.RUNNING

        response = self.future.result()

        if response.success:
            self.node.get_logger().info("[BT] Cloud Processed")
            return py_trees.common.Status.SUCCESS
        else:
            self.node.get_logger().error("[BT] Cloud Processing Failed")
            return py_trees.common.Status.FAILURE