import py_trees
from action_msgs.msg import GoalStatusArray, GoalStatus


class WaitForNavGoalReached(py_trees.behaviour.Behaviour):

    def __init__(self, node):
        super().__init__("WaitForNavGoalReached")
        self.node = node
        self.goal_reached = False

        self.node.create_subscription(
            GoalStatusArray,
            '/navigate_to_pose/_action/status',
            self.status_callback,
            10
        )

    def status_callback(self, msg):
        if not msg.status_list:
            return

        latest_status = msg.status_list[-1].status

        if latest_status == GoalStatus.STATUS_SUCCEEDED:
            self.goal_reached = True

    def update(self):

        if self.goal_reached:
            self.node.get_logger().info("Nav2 Goal Reached.")
            self.goal_reached = False   # reset after consuming
            return py_trees.common.Status.SUCCESS

        return py_trees.common.Status.RUNNING