from typing import NamedTuple
import numpy as np

from livenodes.producer_blocking import Producer_Blocking
from livenodes_core_nodes.ports import Ports_empty, Port_Data, Port_List_Str, Port_Str

from . import plux

class NewDevice(plux.SignalsDev):
    """
    Stub for a Plux based device.
    The onRawFrame should be overwritten
    """

    def __init__(self, address):
        plux.MemoryDev.__init__(address)
        self.onRawFrame = lambda _: None

    # From the doc/examples:
    #
    # https://github.com/biosignalsplux/python-samples/blob/master/MultipleDeviceThreadingExample.py
    # Supported channel number codes:
    # {1 channel - 0x01, 2 channels - 0x03, 3 channels - 0x07
    # 4 channels - 0x0F, 5 channels - 0x1F, 6 channels - 0x3F
    # 7 channels - 0x7F, 8 channels - 0xFF}
    # Maximum acquisition frequencies for number of channels:
    # 1 channel - 8000, 2 channels - 5000, 3 channels - 4000
    # 4 channels - 3000, 5 channels - 3000, 6 channels - 2000
    # 7 channels - 2000, 8 channels - 2000

    # DEBUG NOTE:
    # It seems to work best when activating the plux hub and shortly after starting the pipline in qt interface
    # (which is weird) as on command line the timing is not important at all...

class Ports_out(NamedTuple):
    data: Port_Data = Port_Data("Data")
    channels: Port_List_Str = Port_List_Str("Channel Names")
    status: Port_Str = Port_Str("Status")

class In_biosignalsplux(Producer_Blocking):
    """
    Feeds data frames from a biosiagnal plux based device into the pipeline.

    Examples for biosignal plux devices are: biosignalplux hup and muscleban (for RIoT and Bitalino please have a look at in_riot.py)

    Requires the plux libaray.
    """

    ports_in = Ports_empty()
    ports_out = Ports_out()

    category = "Data Source"
    description = ""

    example_init = {
        "adr": "mac address",
        "freq": 100,
        "channel_names": ["Channel 1"],
        "n_bits": 16,
        "name": "Biosignalsplux",
    }

    def __init__(self,
                 adr,
                 freq,
                 channel_names=[],
                 n_bits=16,
                 name="Biosignalsplux",
                 **kwargs):
        super().__init__(name, **kwargs)

        self.adr = adr
        self.freq = freq
        self.n_bits = n_bits
        self.channel_names = channel_names

        self.device = None

    def _settings(self):
        return {\
            "adr": self.adr,
            "freq": self.freq,
            "n_bits": self.n_bits,
            "channel_names": self.channel_names
        }

    def _blocking_onstart(self, stop_event):
        """
        Streams the data and calls frame callbacks for each frame.
        """
        self.info(f'Connecting BiosignalsPluxHub: {self.adr}')
        self.msgs.put_nowait((f'Connecting BiosignalsPluxHub: {self.adr}', "status", False))

        last_seen = 0 
        buffer = []
        emit_at_once = self.emit_at_once

        def onRawFrame(nSeq, data):
            nonlocal last_seen, stop_event, buffer, emit_at_once

            if last_seen + 1 < nSeq:
                print(f'Dropped {nSeq - last_seen} frames')
            buffer.append(list(data))
            last_seen = nSeq

            if len(buffer) >= emit_at_once:
                self.msgs.put_nowait((np.array([buffer]) / 2**15 - 1, 'data', True))
                buffer = []
            return stop_event.is_set()
        
        self.msgs.put_nowait((self.channel_names, "channels", False))

        self.device = NewDevice(self.adr)
        self.device.frequency = self.freq

        self.msgs.put_nowait((f'Connected BiosignalsPluxHub: {self.adr}', "status", False))

        # TODO: consider moving the start into the init and assign noop, then here overwrite noop with onRawFrame
        # Idea: connect pretty much as soon as possible, but only pass data once the rest is also ready
        # but: make sure to use the correct threads/processes :D
        self.device.onRawFrame = onRawFrame
        # self.device.start(self.device.frequency, 0x01, 16)
        # convert len of channel_names to bit mask for start (see top, or: https://github.com/biosignalsplux/python-samples/blob/master/MultipleDeviceThreadingExample.py)
        self.device.start(self.device.frequency,
                          2**len(self.channel_names) - 1, self.n_bits)
        self.device.loop(
        )  # calls self.device.onRawFrame until it returns True

        self.device.stop()
        self.device.close()
        self.msgs.put_nowait((f'Stopped and closed BiosignalsPluxHub: {self.adr}', "status", False))
