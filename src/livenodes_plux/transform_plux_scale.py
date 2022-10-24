import numpy as np

from livenodes.node import Node

from livenodes_core_nodes.ports import Ports_data

class Transform_plux_scale(Node):
    ports_in = Ports_data()
    ports_out = Ports_data()

    category = "Transform"
    description = ""

    def _should_process(self, data=None, **kwargs):
        return data is not None

    def process(self, data, **kwargs):
        res = (np.array(data) - 2**15) / 2**16
        return self.ret(data=res)
