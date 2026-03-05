import rclpy
from rclpy.node import Node
import py_trees
import py_trees_ros

from geometry_msgs.msg import Twist
from geometry_msgs.msg import PoseWithCovarianceStamped

from wheel_loader_manager.behaviours.manual_override import ManualOverride
from wheel_loader_manager.behaviours.wait_for_localization import WaitForLocalization
from wheel_loader_manager.behaviours.navigate_to_pile import NavigateToPile
from wheel_loader_manager.behaviours.wait_for_nav_goal_reached import WaitForNavGoalReached
from wheel_loader_manager.behaviours.enable_tracker import EnableTracker
from wheel_loader_manager.behaviours.align_with_pile import AlignWithPile
from wheel_loader_manager.behaviours.disable_tracker import DisableTracker
from wheel_loader_manager.behaviours.start_rocking import StartRocking
from wheel_loader_manager.behaviours.wait_for_scan_time import WaitForScanTime
from wheel_loader_manager.behaviours.save_cloud import SaveCloud
from wheel_loader_manager.behaviours.process_cloud import ProcessCloud

class SystemManager(Node):

    def __init__(self):
        super().__init__('system_manager')

        # ---- STATE FLAGS ----
        self.teleop_active = False
        self.localization_ready = False

        # ---- SUBSCRIPTIONS ----
        self.create_subscription(
            Twist,
            '/cmd_vel_keyboard',
            self.teleop_callback,
            10
        )

        self.create_subscription(
            PoseWithCovarianceStamped,
            '/amcl_pose',
            self.amcl_callback,
            10
        )

        # ---- BUILD TREE ----
        manual = ManualOverride(self)
        auto_sequence = py_trees.composites.Sequence(
            name="AutoMission",
            memory=True
        )

        auto_once = py_trees.decorators.OneShot(
        name="RunOnce",
        child=auto_sequence,
        policy=py_trees.common.OneShotPolicy.ON_COMPLETION
        )

        wait_loc = WaitForLocalization(self)
        
        wait_nav = WaitForNavGoalReached(self)
        enable_tracker = EnableTracker(self)
        align = AlignWithPile(self)
        disable_tracker = DisableTracker(self)
        start_rock = StartRocking(self)
        wait_scan = WaitForScanTime(20.0)
        save_cloud = SaveCloud(self)
        process_cloud = ProcessCloud(self)

        auto_sequence.add_children([
            wait_loc,
            wait_nav,
            enable_tracker,
            align,
            disable_tracker,
            start_rock,
            wait_scan,
            save_cloud,
            process_cloud
        ]) 

        root = py_trees.composites.Selector(
            name="Root",
            memory=False
        )
        root.add_children([manual, auto_once])

        self.tree = py_trees_ros.trees.BehaviourTree(root)
        self.tree.setup(timeout=15)

        self.create_timer(0.1, self.tick_tree)

    def teleop_callback(self, msg):
        if abs(msg.linear.x) > 0.01 or abs(msg.angular.z) > 0.01:
            self.teleop_active = True
        else:
            self.teleop_active = False

    def amcl_callback(self, msg):
        self.localization_ready = True

    def tick_tree(self):
        self.tree.tick()


def main(args=None):
    rclpy.init(args=args)
    node = SystemManager()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()