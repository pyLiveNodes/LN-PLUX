import numpy as np
from pythonosc.osc_server import BlockingOSCUDPServer, AsyncIOOSCUDPServer, ForkingOSCUDPServer
from pythonosc.dispatcher import Dispatcher
import asyncio
import threading

from livenodes.producer import Producer
from livenodes_core_nodes.ports import Ports_empty, Ports_data_channels


class In_riot(Producer):
    channels = [
        "ACC_X", "ACC_Y", "ACC_Z", "GYRO_X", "GYRO_Y", "GYRO_Z", "MAG_X",
        "MAG_Y", "MAG_Z", "TEMP", "IO", "A1", "A2", "C", "Q1", "Q2", "Q3",
        "Q4", "PITCH", "YAW", "ROLL", "HEAD"
    ]

    ports_in = Ports_empty()
    ports_out = Ports_data_channels()

    category = "Data Source"
    description = ""

    example_init = {
        'name': 'Name',
        "id": 0,
        "listen_ip": '192.168.1.101',
        "listen_port": 9000
    }

    def __init__(self,
                 id=0,
                 name="RIoT",
                 listen_ip='192.168.1.101',
                 listen_port=9000,
                 **kwargs):
        super().__init__(name, **kwargs)

        self.id = id
        self.listen_ip = listen_ip
        self.listen_port = listen_port

        # self._stop_event = threading.Event()

    def _settings(self):
        return {\
            "name": self.name,
            "id": self.id,
            "listen_ip": self.listen_ip,
            "listen_port": self.listen_port,
        }

    # async def collect(self):
    #     factors = np.array([
    #         2 / x for x in [
    #             8, 8, 8, 2, 2, 2, 2, 2, 2, 1, 1, 1, 4095, 4095, 1, 1, 1, 1,
    #             180, 180, 180, 180
    #         ]
    #     ])

    #     def onRawFrame(addr, *data):
    #         # nonlocal factors
    #         # print(addr, data)
    #         # print(np.array(data).shape)
    #         self._emit_data([[np.array(list(data)) * factors]])
    #         # self._emit_data([data])

    #     self.info('Starting server')
    #     disp = Dispatcher()
    #     disp.map(f"/{self.id}/raw", onRawFrame)
    #     server = AsyncIOOSCUDPServer((self.listen_ip, self.listen_port), disp,
    #                                  asyncio.get_event_loop())
    #     transport, protocol = await server.create_serve_endpoint()

    #     self.info('Server started')
    #     self._emit_data(self.channels, channel="Channel Names")

    #     while (not self._stop_event.is_set()):
    #         await asyncio.sleep(0)

    #     self.info("Closing server")
    #     transport.close()
    #     self.info("Server closed")

    # def _onstop(self):
    #     self._stop_event.set()

    def _onstart(self):
        """
        Streams the data and calls frame callbacks for each frame.
        """
        # asyncio.run(self.collect())

        factors = np.array([
            2 / x for x in [
                8, 8, 8, 2, 2, 2, 2, 2, 2, 1, 1, 1, 4095, 4095, 1, 1, 1, 1,
                180, 180, 180, 180
            ]
        ])

        def onRawFrame(addr, *data):
            # nonlocal factors
            # print(addr, data)
            # print(addr, np.array(data).shape)
            self._emit_data([[np.array(list(data)) * factors]])
            self._clock.tick()
            # self._emit_data([data])

        self.info('Starting server')
        disp = Dispatcher()
        disp.map(f"/{self.id}/raw", onRawFrame)

        self._emit_data(self.channels, channel="Channel Names")

        server = BlockingOSCUDPServer((self.listen_ip, self.listen_port), disp)
        # server = ForkingOSCUDPServer((self.listen_ip, self.listen_port), disp)
        self.info('Serving')
        server.serve_forever()  # Blocks forever
        

        # The threading idea works, but returns imediately due to the asyncio calls -> therefore ending the subprocess directly
        # if threading.current_thread() is not threading.main_thread():
        #     # let's create a new eventloop, since we're not in the main thread and thus non is created for us
        #     asyncio.set_event_loop(asyncio.new_event_loop())


        # server = AsyncIOOSCUDPServer((self.listen_ip, self.listen_port), disp, asyncio.get_event_loop())
        # self.info('Serving')
        # server.serve()