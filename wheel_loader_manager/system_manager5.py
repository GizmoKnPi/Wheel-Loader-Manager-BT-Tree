import rclpy
from rclpy.node import Node
import py_trees
import py_trees_ros
from geometry_msgs.msg import PoseWithCovarianceStamped

# Standard Behaviours
from wheel_loader_manager.behaviours.wait_for_localization import WaitForLocalization
from wheel_loader_manager.behaviours.enable_tracker import EnableTracker
from wheel_loader_manager.behaviours.align_with_pile import AlignWithPile
from wheel_loader_manager.behaviours.disable_tracker import DisableTracker
from wheel_loader_manager.behaviours.start_rocking import StartRocking
from wheel_loader_manager.behaviours.wait_for_scan_time import WaitForScanTime
from wheel_loader_manager.behaviours.save_cloud import SaveCloud
from wheel_loader_manager.behaviours.process_cloud import ProcessCloud
from wheel_loader_manager.behaviours.control_bucket import ControlBucket
from wheel_loader_manager.behaviours.blind_drive import BlindDrive
from wheel_loader_manager.behaviours.wait_for_nav_goal_reached import WaitForNavGoalReached
from wheel_loader_manager.behaviours.wait_for_time import WaitForTime
from wheel_loader_manager.behaviours.hatch_open_reverse_blind_drive import HatchOpenReverseBlindDrive

# 🚀 The New Pre-Flight Nodes
from wheel_loader_manager.behaviours.record_nav_goal import RecordNavGoal
from wheel_loader_manager.behaviours.drive_to_recorded_goal import DriveToRecordedGoal

class SystemManager5(Node):
    def __init__(self):
        super().__init__('system_manager5')

        self.declare_parameters(namespace='', parameters=[
            ('hatch_open_time', 5.0),
            ('hatch_close_time', 5.0)
        ])

        self.localization_ready = False
        self.create_subscription(PoseWithCovarianceStamped, '/amcl_pose', self.amcl_callback, 10)

        # ---- 1. PRE-FLIGHT CHECKLIST (Runs Once) ----
        wait_loc = WaitForLocalization(self)
        
        # This will save to self.pile_target and self.dump_target
        record_pile = RecordNavGoal(name="RecordPileLocation", node=self, pose_attribute_name='pile_target', color='orange')
        record_dump = RecordNavGoal(name="RecordDumpLocation", node=self, pose_attribute_name='dump_target', color='blue')
        
        setup_sequence = py_trees.composites.Sequence("SetupPhase", memory=True)
        setup_sequence.add_children([wait_loc, record_pile, record_dump])

        # ---- 2. THE DRIVING CYCLE (Runs Infinitely) ----
        drive_to_pile = DriveToRecordedGoal(name="DriveToPile", node=self, pose_attribute_name='pile_target')
        enable_tracker = EnableTracker(self)
        align = AlignWithPile(self)
        disable_tracker = DisableTracker(self)
        creep_forward = HatchOpenReverseBlindDrive(name="CreepForward", node=self, distance=0.35) 
            
        start_rock = StartRocking(self)
        wait_scan = WaitForScanTime(20.0)
        save_cloud = SaveCloud(self)
        process_cloud = ProcessCloud(self) 
        
        wait_nav_standoff = WaitForNavGoalReached(self, name="WaitNavStandoff") 
        bucket_down = ControlBucket(name="BucketDown", node=self, command='R', expected_state='RESET')
        drive_in = BlindDrive(name="DriveIn", node=self, direction=1.0)
        bucket_up = ControlBucket(name="BucketUp", node=self, command='B', expected_state='SCOOP')
        drive_out = BlindDrive(name="DriveOut", node=self, direction=-1.0)

        drive_to_dump = DriveToRecordedGoal(name="DriveToDump", node=self, pose_attribute_name='dump_target')
        open_hatch = ControlBucket(name="OpenHatch", node=self, command='O', expected_state=None)
        wait_open = WaitForTime(name="WaitOpen", node=self, param_name='hatch_open_time')
        drive_back_dump = HatchOpenReverseBlindDrive(name="DriveBackDump", node=self, distance=-0.2)
        close_hatch = ControlBucket(name="CloseHatch", node=self, command='C', expected_state=None)
        wait_close = WaitForTime(name="WaitClose", node=self, param_name='hatch_close_time')
        nav_mode = ControlBucket(name="NavMode", node=self, command='N', expected_state='NAV')

        scoop_dump_cycle = py_trees.composites.Sequence("ScoopDumpCycle", memory=True)
        scoop_dump_cycle.add_children([
            drive_to_pile, enable_tracker, align, disable_tracker, creep_forward,
            start_rock, wait_scan, save_cloud, process_cloud,
            wait_nav_standoff, bucket_down, drive_in, bucket_up, drive_out,
            drive_to_dump, open_hatch, wait_open, drive_back_dump, close_hatch, wait_close, nav_mode
        ])

        # ---- 3. THE MASTER TREE ----
        master_sequence = py_trees.composites.Sequence("MasterSequence", memory=True)
        master_sequence.add_children([setup_sequence, scoop_dump_cycle])

        self.tree = py_trees_ros.trees.BehaviourTree(master_sequence)
        self.tree.setup(timeout=15)
        self.create_timer(0.1, self.tick_tree)

    def amcl_callback(self, msg):
        self.localization_ready = True

    def tick_tree(self):
        self.tree.tick()
        
        # When the scoop_dump_cycle succeeds, we ONLY reset that cycle, not the setup sequence!
        if self.tree.root.children[1].status == py_trees.common.Status.SUCCESS:
            self.get_logger().info("=== SHIFT COMPLETE! DRIVING BACK TO PILE ===")
            self.tree.root.children[1].stop(py_trees.common.Status.INVALID)
            
        elif self.tree.root.status == py_trees.common.Status.FAILURE:
            self.get_logger().error("=== PILE EMPTY OR MISSION FAILED. SHUTTING DOWN. ===")

def main(args=None):
    rclpy.init(args=args)
    node = SystemManager5()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()