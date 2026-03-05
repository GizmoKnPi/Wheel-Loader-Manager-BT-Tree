import py_trees
import time


class WaitForScanTime(py_trees.behaviour.Behaviour):

    def __init__(self, duration=15.0):
        super().__init__("WaitForScanTime")

        self.duration = duration
        self.start_time = None

    def initialise(self):

        self.start_time = time.time()

    def update(self):

        elapsed = time.time() - self.start_time

        if elapsed >= self.duration:

            return py_trees.common.Status.SUCCESS

        return py_trees.common.Status.RUNNING