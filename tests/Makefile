SIM ?= icarus
TOPLEVEL_LANG ?= verilog
VERILOG_SOURCES += $(PWD)/../hdl/or_gate.v
VERILOG_SOURCES += $(PWD)/wrappers/or_test.v
VERILOG_SOURCES += $(PWD)/wrappers/dut_test.v
VERILOG_SOURCES += $(PWD)/../hdl/dut.v
VERILOG_SOURCES += $(PWD)/../hdl/FIFO1.v
VERILOG_SOURCES += $(PWD)/../hdl/FIFO2.v

all: or dut

or:
# Setting the top-level module and testbench module for simulation
	rm -rf sim_build
	$(MAKE) MODULE=or_test TOPLEVEL=or_test
dut:
# Setting the top-level module and testbench module for simulation
	rm -rf sim_build
	$(MAKE) MODULE=dut_test TOPLEVEL=dut_test 
include $(shell cocotb-config --makefiles)/Makefile.sim
