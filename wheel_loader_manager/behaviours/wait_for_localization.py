import py_trees

class WaitForLocalization(py_trees.behaviour.Behaviour):

    def __init__(self, node):
        super().__init__("WaitForLocalization")
        self.node = node

    def update(self):
        if self.node.localization_ready:
            return py_trees.common.Status.SUCCESS
        else:
            return py_trees.common.Status.RUNNING