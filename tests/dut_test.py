import cocotb
from cocotb.triggers import Timer, RisingEdge, FallingEdge, ReadOnly, NextTimeStep
from cocotb_bus.drivers import BusDriver
from cocotb_bus.monitors import BusMonitor
from cocotb_coverage.coverage import CoverCross, CoverPoint, coverage_db
import os

# Scoreboard function
def sb_fn(actual_value):
    global expected_value
    actual = actual_value.integer
    expected = expected_value.pop(0)
    assert actual == expected, f"TEST FAILED, expected={expected}, actual={actual}"

# Coverage functions
@CoverPoint("top.a", xf=lambda x, y: x, bins=[0, 1])
@CoverPoint("top.b", xf=lambda x, y: y, bins=[0, 1])
@CoverCross("top.cross.ab", items=["top.a", "top.b"])
def ab_cover(a, b):
    pass

@CoverPoint("top.prot.a.current", xf=lambda x: x['current'], bins=['Idle', 'RDY', 'Txn'])
@CoverPoint("top.prot.a.previous", xf=lambda x: x['previous'], bins=['Idle', 'RDY', 'Txn'])
@CoverCross("top.cross.a_prot.cross", items=["top.prot.a.current", "top.prot.a.previous"])
def a_prot_cover(txn):
    pass

@cocotb.test()
async def dut_test(dut):
    global expected_value

    # Input sequences and expected output
    a = (0, 0, 1, 1)
    b = (0, 1, 0, 1)
    expected_value = [0, 1, 1, 1]

    # Apply reset
    dut.RST_N.value = 1
    await Timer(6, 'ns')
    dut.RST_N.value = 0
    await Timer(1, 'ns')
    await RisingEdge(dut.CLK)
    dut.RST_N.value = 1
    await Timer(1, 'ns')

    # Instantiate drivers and monitor once
    adrv = WriteDriver(dut, 'write', dut.CLK, address=4)
    bdrv = WriteDriver(dut, 'write', dut.CLK, address=5)
    rdrv = ReadDriver(dut, 'read', dut.CLK, sb_callback=sb_fn)
    IO_Monitor(dut, 'write', dut.CLK, callback=a_prot_cover)

    for i in range(4):
        # Write a[i] to address 4
        await adrv._driver_send(a[i])
        await Timer(6, 'ns')

        # Trigger read at address 0
        dut.read_address.value = 0
        if dut.read_data.value != 1:
            await RisingEdge(dut.read_data)
        await Timer(6, 'ns')

        # Write b[i] to address 5
        await bdrv._driver_send(b[i])
        await Timer(6, 'ns')

        # Collect coverage
        ab_cover(a[i], b[i])

        # Trigger read at address 1
        dut.read_address.value = 1
        if dut.read_data.value != 1:
            await RisingEdge(dut.read_data)
        await Timer(6, 'ns')

        # Perform read and check with scoreboard
        await rdrv._driver_send(None)
        await Timer(6, 'ns')

    # Report and export coverage
    coverage_db.report_coverage(cocotb.log.info, bins=True)
    coverage_file = os.path.join(os.getenv('RESULT_PATH', "./"), 'coverage.xml')
    coverage_db.export_to_xml(filename=coverage_file)

# Bus drivers
class WriteDriver(BusDriver):
    _signals = ['address', 'rdy', 'en', 'data']

    def __init__(self, dut, name, clk, address):
        super().__init__(dut, name, clk)
        self.bus.en.value = 0
        self.clk = clk
        self.bus.address.value = address

    async def _driver_send(self, value, sync=True):
        if self.bus.rdy.value != 1:
            await RisingEdge(self.bus.rdy)
        self.bus.en.value = 1
        self.bus.data.value = value
        await ReadOnly()
        await RisingEdge(self.clk)
        await NextTimeStep()
        self.bus.en.value = 0
        await NextTimeStep()

class ReadDriver(BusDriver):
    _signals = ['address', 'rdy', 'en', 'data']

    def __init__(self, dut, name, clk, sb_callback):
        super().__init__(dut, name, clk)
        self.bus.en.value = 0
        self.clk = clk
        self.callback = sb_callback

    async def _driver_send(self, value, sync=True):
        if self.bus.rdy.value != 1:
            await RisingEdge(self.bus.rdy)
        self.bus.address.value = 2
        if self.bus.data.value != 1:
            await RisingEdge(self.bus.data)
        await Timer(6, 'ns')
        self.bus.en.value = 1
        self.bus.address.value = 3
        await ReadOnly()
        self.callback(self.bus.data.value)
        await RisingEdge(self.clk)
        await NextTimeStep()
        self.bus.en.value = 0

# Bus monitor
class IO_Monitor(BusMonitor):
    _signals = ['address', 'rdy', 'en', 'data']

    async def _monitor_recv(self):
        fallingedge = FallingEdge(self.clock)
        rdonly = ReadOnly()
        phases = {
            0: 'Idle',
            1: 'RDY',
            3: 'Txn'
        }
        prev = 'Idle'
        while True:
            await fallingedge
            await rdonly
            txn = (int(self.bus.en.value) << 1) | int(self.bus.rdy.value)
            self._recv({'previous': prev, 'current': phases[txn]})
            prev = phases[txn]
