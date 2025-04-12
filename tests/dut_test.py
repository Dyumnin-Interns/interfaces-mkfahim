import cocotb
from cocotb.triggers import Timer, RisingEdge, FallingEdge, ReadOnly, NextTimeStep
from cocotb_bus.driver import BusDriver



def sb_fn(actual_value):
    global expected_value
    assert actual_value == expected_value.pop(0), "Scoreboard Matching Failed"


@cocotb.test()
async def dut_test(dut):
    global expected_value
    a= (0, 0, 1, 1)
    b= (0, 1, 0, 1)
    expected_value=[0,1,1,1]
    dut.RST_N.value=1
    await Timer(6, 'ns')
    dut.RST_N.value=0
    await Timer(1, 'ns')
    await RisingEdge(dut.CLK)
    dut.RST_N.value=1
    await Timer(1,'ns')
    for i in range(4):
        adrv=WriteDriver(dut,'write',dut.CLK,4)
        adrv.append(a[i])
        await Timer(6,'ns')
        dut.read_address.value=0
        if dut.read_data.value!=1:
            await RisingEdge(dut.read_data)
        await Timer(6,'ns')
        bdrv=WriteDriver(dut,'write',dut.CLK,5)
        bdrv.append(b[i])
        await Timer(6,'ns')
        ab_cover(a[i], b[i])
        dut.read_address.value=1
        if dut.read_data.value!=1:
            await RisingEdge(dut.read_data)
        await Timer(6,'ns')
        ReadDriver(dut,'read',dut.CLK,sb_fn)
        await Timer(6,'ns')

    coverage_db.report_coverage(cocotb.log.info, bins=True)
    coverage_file=os.path.join( os.getenv('RESULT_PATH', "./"), 'coverage.xml')
    coverage_db.export_to_xml(filename=coverage_file)
        
class InputDriver(BusDriver):
    _signals=['address', 'rdy', 'en', 'data']
    def __init__(self, dut, name, clk, address):
        BusDriver.__init__(self, dut, name, clk)
        self.bus.en.value=0
        self.clk = clk
        self.bus.address.value = address
        
    async def _driver_send(self,value,sync=True):
        if self.bus.rdy.value!=1:
            await RisingEdge(self.bus.rdy)
        self.bus.en.value=1
        self.bus.data.value=value
        await ReadOnly()
        await RisingEdge(self.clk)
        self.bus.en.value=0
        await NextTimeStep()
        
class OutputDriver(BusDriver):
    _signals=['address', 'rdy', 'en', 'data']

    def __init__(self, dut, name, clk, sb_callback):
        BusDriver.__init__(self, dut, name, clk)
        self.bus.en.value=0
        self.clk = clk
        self.callback = sb_callback
    
    async def _driver_send(self,value,sync=True):
        if self.bus.rdy.value!=1:
            await RisingEdge(self.bus.rdy)
        self.bus.address.value=2
        if self.bus.data.value!=1:
            await RisingEdge(self.bus.data)
        await Timer(6,'ns')
        self.bus.en.value=1
        self.bus.address.value=3
        await ReadOnly()
        self.callback(self.bus.data.value)
        await RisingEdge(self.clk)
        await NextTimeStep()
        self.bus.en.value=0 

        

 

            
            
