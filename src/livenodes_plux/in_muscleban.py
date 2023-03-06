import json
from typing import NamedTuple
from livenodes.producer_blocking import Producer_Blocking
import numpy as np
import time

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

from livenodes_core_nodes.ports import Ports_empty, Ports_data_channels, Port_Data, Port_List_Str, Port_Int, Port_Str

class Ports_out(NamedTuple):
    data: Port_Data = Port_Data("Data")
    channels: Port_List_Str = Port_List_Str("Channel Names")
    battery: Port_Int = Port_Int("Battery")
    status: Port_Str = Port_Str("Status")


class In_muscleban(Producer_Blocking):
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
        "n_bits": 16,
        "name": "Biosignalsplux",
        "emit_at_once": 5
    }

    channel_names = [ "EMG1",
            "ACC_X", "ACC_Y", "ACC_Z", 
            "MAG_X", "MAG_Y", "MAG_Z"]

    def __init__(self,
                 adr,
                 freq,
                 n_bits=16,
                 name="Biosignalsplux",
                 emit_at_once=None,
                 **kwargs):
        super().__init__(name, **kwargs)

        self.adr = adr
        self.freq = freq
        self.n_bits = n_bits
        if emit_at_once is not None:
            self.emit_at_once = emit_at_once
        else:
            # per default make the whole thing update not more than 100 times per second
            self.emit_at_once = max(int(freq / 100.), 1)

        self.device = None

    def _settings(self):
        return {\
            "adr": self.adr,
            "freq": self.freq,
            "n_bits": self.n_bits,
            "emit_at_once": self.emit_at_once
        }

    def _blocking_onstart(self, stop_event):
        """
        Streams the data and calls frame callbacks for each frame.
        """
        self.info(f'Connecting MuscleBan: {self.adr}')
        self.msgs.put_nowait((f'Connecting MuscleBan: {self.adr}', "status", False))
        last_seen = 0 
        buffer = []
        emit_at_once = self.emit_at_once

        def onRawFrame(nSeq, data):
            nonlocal last_seen, stop_event, buffer, emit_at_once
            # nonlocal self
            # array = np.asarray(data).astype(float)
            # for x in range(len(array)):
            #     if x == 0:
            #         # EMG RAW TRANSFER FUNCTION
            #         array[x] = (((array[x] / (np.power(2, self.n_bits)) - 1) - 1 / 2.0) * 2.5) / 1100.0
            #         # EMG ENVELOPED TRANSFER FUNCTION
            #         # out[x] = ((array[x] / (np.power(2, self.n_bits) - 1)) * 2.5) / 1100
            #     if 0 < x < 4:
            #         # ACCELEROMETER TRANSFER FUNCTION
            #         if x == 3:
            #             array[x] = (array[x] - (np.power(2, self.n_bits) / 2.0)) * (8 / (np.power(2, self.n_bits))) - 1
            #         else:
            #             array[x] = (array[x] - (np.power(2, self.n_bits) / 2.0)) * (8 / (np.power(2, self.n_bits)))
            #     else:
            #         # MAGNETOMETER TRANSFER FUNCTION
            #         array[x] = (array[x] - (np.power(2, self.n_bits) / 2.0)) * 0.1
            # # data = tuple(array)
            # data = array

            # d = np.array(data)
            # if nSeq % 1000 == 0:
            #     print(nSeq, d, d.shape)
            if last_seen + 1 < nSeq:
                print(f'Dropped {nSeq - last_seen} frames')
            if nSeq % self.freq * 60 * 2 == 0:
                self.msgs.put_nowait((int(self.device.getBattery()), "battery", False))
            buffer.append(data)
            last_seen = nSeq

            if len(buffer) >= emit_at_once:
                self.msgs.put_nowait((np.array([buffer]) / 2**15 - 1, 'data', True))
                buffer = []
            return stop_event.is_set()

        self.msgs.put_nowait((self.channel_names, "channels", False))
        # print('Lets go twice! ----------------')
        # while not self.stop_event.is_set():
        #     # print('Lets go another time! ----------------')
        #     self.msgs.put_nowait((np.random.rand(1, 1, 7), "data", True))
        #     time.sleep(0.0001)
        #     if np.random.rand() > 0.95:
        #         raise Exception('Lets test this')
        # print('Lets finish! ----------------')


        self.device = NewDevice(self.adr)
        self.msgs.put_nowait((f'Connected MuscleBan: {self.adr}', "status", False))


        # TODO: consider moving the start into the init and assign noop, then here overwrite noop with onRawFrame
        # Idea: connect pretty much as soon as possible, but only pass data once the rest is also ready
        # but: make sure to use the correct threads/processes :D
        self.device.onRawFrame = onRawFrame

        emg_channel_src = plux.Source()
        emg_channel_src.port = 1 # Number of the port used by this channel.
        emg_channel_src.freqDivisor = 1 # Subsampling factor in relation with the freq, i.e., when this value is 
                                        # equal to 1 then the channel collects data at a sampling rate identical to the freq, 
                                        # otherwise, the effective sampling rate for this channel will be freq / freqDivisor
        emg_channel_src.nBits = self.n_bits # Resolution in #bits used by this channel.
        emg_channel_src.chMask = 0x01 # Hexadecimal number defining the number of channels streamed by this port, for example:
                                    # 0x07 ---> 00000111 | Three channels are active.
        # [3xACC + 3xMAG]
        acc_mag_channel_src = plux.Source()
        acc_mag_channel_src.port = 2 # or 11 depending on the muscleBAN hardware version.
        acc_mag_channel_src.freqDivisor = 1
        acc_mag_channel_src.nBits = self.n_bits
        acc_mag_channel_src.chMask = 0x3F # 0x3F to activate the 6 sources (3xACC + 3xMAG) of the Accelerometer and Magnetometer sensors.
        
        # TODO: add try catch if fails with communication port does not exist emit a list of bluetooth signals / mac addresses received
        # Maybe even add a __init__ option to try and reset bluetooth connection to this device if this happens and only if that fails, throw an errro
        self.device.start(self.freq, [emg_channel_src, acc_mag_channel_src])
        
        device_info = self.device.getProperties()
        self.info("Properties: ", json.dumps(device_info))
        
        tmp_msg = f"Looping MuscleBan: {self.adr}\n"
        for key, val in device_info.items():
            tmp_msg += f'\n {key}: {val}'
        self.msgs.put_nowait((tmp_msg, "status", False))
        
        # self.info(f'Battery status for {self.adr}: {self.device.getBattery()}')
        # self.msgs.put_nowait((self.device.getBattery(), "battery", False))

        # # calls self.device.onRawFrame until it returns True
        # try:
        self.device.loop() 
        # except RuntimeError:
        #     self.error('Connection lost, trying to reconnect.')
        #     time.sleep(0.1)
        #     self._blocking_onstart()

        self.device.stop()
        self.device.close()
        self.msgs.put_nowait((f'Stopped and closed MuscleBan: {self.adr}', "status", False))
