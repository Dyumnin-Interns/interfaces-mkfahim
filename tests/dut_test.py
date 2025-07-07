import os
from random import randint
import cocotb
from cocotb.triggers import FallingEdge, NextTimeStep, Timer, RisingEdge, ReadOnly
from cocotb_bus.drivers import BusDriver
from cocotb_bus.monitors import BusMonitor
from cocotb_coverage.coverage import CoverCross, CoverPoint, coverage_db


# Data Containers


class WriteTransaction:
    def __init__(self, address: int, data: int, enable: int = 1):
        self.address = address
        self.data = data
        self.enable = enable


class ReadTransaction:
    def __init__(self, address: int, enable: int = 1):
        self.address = address
        self.enable = enable


# Scoreboard

class Scoreboard:
    def __init__(self):
        self.expected = []

    def push(self, value):
        self.expected.append(value)

    def check(self, actual_value):
        expected = self.expected.pop()
        print(f"Expected: {expected}, Actual: {actual_value}")
        assert actual_value == expected, "Scoreboard check failed!"


# Coverage


@CoverPoint("top.write_address", xf=lambda x, y: x, bins=[4, 5])
@CoverPoint("top.write_data", xf=lambda x, y: y, bins=[0, 1])
@CoverCross("top.cross.write_comb", items=["top.write_address", "top.write_data"])
def cover_write_combination(address, data):
    pass


@CoverPoint("top.read_address", xf=lambda x: x, bins=[0, 1, 2, 3])
def cover_read_address(address):
    pass


@CoverPoint("top.port.w.current", xf=lambda x: x['current'],
            bins=['Write_Idle', 'Write_RDY', 'Write_Txn'])
@CoverPoint("top.port.w.previous", xf=lambda x: x['previous'],
            bins=['Write_Idle', 'Write_RDY', 'Write_Txn'])
@CoverCross("top.cross.write_port", items=["top.port.w.previous", "top.port.w.current"])
def cover_write_port(txn):
    print("Write port transition:", txn)


@CoverPoint("top.port.r.current", xf=lambda x: x['current'],
            bins=['Read_Idle', 'Read_RDY', 'Read_Txn'])
@CoverPoint("top.port.r.previous", xf=lambda x: x['previous'],
            bins=['Read_Idle', 'Read_RDY', 'Read_Txn'])
@CoverCross("top.cross.read_port", items=["top.port.r.previous", "top.port.r.current"])
def cover_read_port(txn):
    print("Read port transition:", txn)


# Drivers and Monitors

class WriteDriverAgent(BusDriver):
    _signals = ["write_rdy", "write_en", "write_data", "write_address"]

    def __init__(self, dut, name, clk):
        super().__init__(dut, name, clk)
        self.clk = clk
        self.bus.write_en.value = 0

    async def _driver_send(self, txn, sync=True):
        if self.bus.write_rdy.value != 1:
            await RisingEdge(self.bus.write_rdy)
        self.bus.write_en.value = 1
        self.bus.write_address.value = txn.address
        self.bus.write_data.value = txn.data
        await ReadOnly()
        await RisingEdge(self.clk)
        await NextTimeStep()
        self.bus.write_en.value = 0


class ReadDriverAgent(BusDriver):
    _signals = ["read_rdy", "read_en", "read_data", "read_address"]

    def __init__(self, dut, name, clk):
        super().__init__(dut, name, clk)
        self.bus.read_en.value = 0
        self.clk = clk

    async def _driver_send(self, txn, sync=True):
        if self.bus.read_rdy.value != 1:
            await RisingEdge(self.bus.read_rdy)
        self.bus.read_en.value = 1
        self.bus.read_address.value = txn.address
        await ReadOnly()
        await RisingEdge(self.clk)
        await NextTimeStep()
        self.bus.read_en.value = 0


class OutputMonitorAgent(BusDriver):
    _signals = ["read_rdy", "read_en", "read_data", "read_address"]

    def __init__(self, dut, name, clk, callback):
        super().__init__(dut, name, clk)
        self.clk = clk
        self.callback = callback
        self.bus.read_en.value = 0

    async def _driver_send(self, value, sync=True):
        while True:
            if self.bus.read_rdy.value != 1:
                await RisingEdge(self.bus.read_rdy)
            await ReadOnly()
            self.callback(int(self.bus.read_data.value))
            await RisingEdge(self.clk)
            await NextTimeStep()


class ReadMonitor(BusMonitor):
    _signals = ["read_rdy", "read_en", "read_address", "read_data"]

    async def _monitor_recv(self):
        phase_map = {0: 'Read_Idle', 1: 'Read_RDY', 3: 'Read_Txn'}
        prev = phase_map[0]
        while True:
            await FallingEdge(self.clock)
            await ReadOnly()
            txn_code = (self.bus.read_en.value << 1) | self.bus.read_rdy.value
            self._recv({'previous': prev, 'current': phase_map[txn_code]})
            prev = phase_map[txn_code]


class WriteMonitor(BusMonitor):
    _signals = ["write_rdy", "write_en", "write_address", "write_data"]

    async def _monitor_recv(self):
        phase_map = {0: 'Write_Idle', 1: 'Write_RDY', 3: 'Write_Txn'}
        prev = phase_map[0]
        while True:
            await FallingEdge(self.clock)
            await ReadOnly()
            txn_code = (self.bus.write_en.value << 1) | self.bus.write_rdy.value
            self._recv({'previous': prev, 'current': phase_map[txn_code]})
            prev = phase_map[txn_code]


# Main Test Function

@cocotb.test()
async def main_testbench(dut):
    sb = Scoreboard()
    write_agent = WriteDriverAgent(dut, "", dut.CLK)
    read_agent = ReadDriverAgent(dut, "", dut.CLK)
    OutputMonitorAgent(dut, "", dut.CLK, sb.check)
    WriteMonitor(dut, '', dut.CLK, callback=cover_write_port)
    ReadMonitor(dut, '', dut.CLK, callback=cover_read_port)

    # Reset
    dut.RST_N.value = 1
    await Timer(20, units="ns")
    dut.RST_N.value = 0
    await Timer(20, units="ns")
    await RisingEdge(dut.CLK)
    dut.RST_N.value = 1

    for _ in range(200):
        w_data = randint(0, 1)
        w_addr = randint(4, 5)
        r_addr = randint(0, 3)

        write_txn = WriteTransaction(w_addr, w_data)
        read_txn = ReadTransaction(r_addr)

        write_agent.append(write_txn)
        read_agent.append(read_txn)
        sb.push(w_data)

        cover_write_combination(w_addr, w_data)
        cover_read_address(r_addr)

    await Timer(1000, units="ns")
    coverage_db.report_coverage(cocotb.log.info, bins=True)
    output_path = os.getenv("RESULT_PATH", "./")
    coverage_db.export_to_xml(filename=os.path.join(output_path, "coverage.xml"))
