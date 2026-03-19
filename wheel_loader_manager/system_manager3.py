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
from wheel_loader_manager.behaviours.control_bucket import ControlBucket
from wheel_loader_manager.behaviours.blind_drive import BlindDrive

# 🚀 NEW PHASE IMPORTS
from wheel_loader_manager.behaviours.wait_for_dump_goal import WaitForDumpGoal
from wheel_loader_manager.behaviours.wait_for_time import WaitForTime
from wheel_loader_manager.behaviours.hatch_open_reverse_blind_drive import HatchOpenReverseBlindDrive

class SystemManager3(Node):

    def __init__(self):
        super().__init__('system_manager3')

        # ---- DECLARE PARAMETERS ----
        self.declare_parameters(namespace='', parameters=[
            ('hatch_open_time', 5.0),
            ('hatch_close_time', 5.0)
        ])

        # ---- STATE FLAGS ----
        self.last_teleop_time = None
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
        auto_sequence = py_trees.composites.Sequence(
            name="AutoMission",
            memory=True
        )

        auto_once = py_trees.decorators.OneShot(
            name="RunOnce",
            child=auto_sequence,
            policy=py_trees.common.OneShotPolicy.ON_COMPLETION
        )

        # 1. Existing Phase: Arrive, Align, and Scan
        wait_loc = WaitForLocalization(self)
        wait_nav_initial = WaitForNavGoalReached(self) 
        enable_tracker = EnableTracker(self)
        align = AlignWithPile(self)
        disable_tracker = DisableTracker(self)
        start_rock = StartRocking(self)
        wait_scan = WaitForScanTime(20.0)
        save_cloud = SaveCloud(self)
        process_cloud = ProcessCloud(self) 

        # 2. Existing Phase: Final Approach and Scoop
        wait_nav_standoff = WaitForNavGoalReached(self) 
        bucket_down = ControlBucket(name="BucketDown", node=self, command='R', expected_state='RESET')
        drive_in = BlindDrive(name="DriveIn", node=self, direction=1.0)
        bucket_up = ControlBucket(name="BucketUp", node=self, command='B', expected_state='SCOOP')
        drive_out = BlindDrive(name="DriveOut", node=self, direction=-1.0)

        # 3. 🚀 NEW PHASE: The Dump Sequence
        wait_dump_goal = WaitForDumpGoal(self) 
        open_hatch = ControlBucket(name="OpenHatch", node=self, command='O', expected_state='HATCH_OPEN')
        wait_open = WaitForTime(name="WaitOpen", node=self, param_name='hatch_open_time')
        drive_back_dump = HatchOpenReverseBlindDrive(name="DriveBackDump", node=self, distance=-0.2)
        close_hatch = ControlBucket(name="CloseHatch", node=self, command='C', expected_state='HATCH_CLOSED')
        wait_close = WaitForTime(name="WaitClose", node=self, param_name='hatch_close_time')
        
        # NOTE: Change 'N' below if your ESP32 uses a different character for travel/nav mode
        nav_mode = ControlBucket(name="NavMode", node=self, command='N', expected_state='NAV_MODE')

        # ---- ADD TO SEQUENCE ----
        auto_sequence.add_children([
            # Phase 1
            wait_loc,
            wait_nav_initial,
            enable_tracker,
            align,
            disable_tracker,
            start_rock,
            wait_scan,
            save_cloud,
            process_cloud,
            
            # Phase 2
            wait_nav_standoff, 
            bucket_down,
            drive_in,
            bucket_up,
            drive_out,
            
            # Phase 3
            wait_dump_goal, 
            open_hatch,
            wait_open,
            drive_back_dump,
            close_hatch,
            wait_close,
            nav_mode
        ])

        self.tree = py_trees_ros.trees.BehaviourTree(auto_once)
        self.tree.setup(timeout=15)

        self.create_timer(0.1, self.tick_tree)

    def teleop_callback(self, msg):
        import time
        if abs(msg.linear.x) > 0.01 or abs(msg.angular.z) > 0.01:
            self.last_teleop_time = time.time()

    def teleop_active(self):
        import time
        if self.last_teleop_time is None:
            return False
        return (time.time() - self.last_teleop_time) < 1.0

    def amcl_callback(self, msg):
        self.localization_ready = True

    def tick_tree(self):
        self.tree.tick()

def main(args=None):
    rclpy.init(args=args)
    node = SystemManager3()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()