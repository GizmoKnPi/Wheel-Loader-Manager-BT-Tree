import py_trees
from action_msgs.msg import GoalStatusArray, GoalStatus

class WaitForNavGoalReached(py_trees.behaviour.Behaviour):
    # 🚀 THE MAGIC FIX: A class-level variable shared by ALL instances of this node!
    _last_succeeded_goal_id = None 

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

        latest_goal = msg.status_list[-1]
        latest_status = latest_goal.status
        
        # Extract the unique ID of the current Nav2 goal
        current_goal_id = bytes(latest_goal.goal_info.goal_id.uuid).hex()

        if latest_status == GoalStatus.STATUS_SUCCEEDED:
            # If this is a brand new successful goal we haven't seen before...
            if current_goal_id != WaitForNavGoalReached._last_succeeded_goal_id:
                self.goal_reached = True
                
                # Record it globally so no other wait nodes get tricked by it!
                WaitForNavGoalReached._last_succeeded_goal_id = current_goal_id

    def initialise(self):
        # We purposely do NOT wipe memory here anymore! 
        # This protects the node if you interrupt it with the joystick.
        self.node.get_logger().info(f"[{self.name}] Armed. Watching for Nav2 arrival...")

    def update(self):
        if self.goal_reached:
            self.node.get_logger().info(f"[{self.name}] Nav2 Goal Reached!")
            self.goal_reached = False # Reset local flag so this node can be reused
            return py_trees.common.Status.SUCCESS

        return py_trees.common.Status.RUNNING