import py_trees
from std_srvs.srv import Trigger


class StartRocking(py_trees.behaviour.Behaviour):

    def __init__(self, node):
        super().__init__("StartRocking")

        self.node = node
        self.client = node.create_client(Trigger, "/start_rocking")

        self.future = None

    def initialise(self):
        self.future = None

    def update(self):

        if not self.client.service_is_ready():
            self.node.get_logger().info("[BT] Waiting for start_rocking...")
            return py_trees.common.Status.RUNNING

        # Call service once
        if self.future is None:

            req = Trigger.Request()
            self.future = self.client.call_async(req)

            self.node.get_logger().info("[BT] Start rocking request sent")
            return py_trees.common.Status.RUNNING

        # Wait for service response
        if not self.future.done():
            return py_trees.common.Status.RUNNING

        response = self.future.result()

        if response.success:
            self.node.get_logger().info("[BT] Servo rocking started")
            return py_trees.common.Status.SUCCESS

        self.node.get_logger().error("[BT] Start rocking failed")
        return py_trees.common.Status.FAILURE