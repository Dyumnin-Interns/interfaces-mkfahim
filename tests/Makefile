SIM ?= icarus
TOPLEVEL_LANG ?= verilog
VERILOG_SOURCES += $(PWD)/wrappers/dut_test.v
VERILOG_SOURCES += $(PWD)/../hdl/dut.v
VERILOG_SOURCES += $(PWD)/../hdl/FIFO1.v
VERILOG_SOURCES += $(PWD)/../hdl/FIFO2.v

# 'sim' defines a Makefile target, and when running `make sim`, the commands under it will be executed.
sim:
	rm -rf sim_build
	$(MAKE) MODULE=dut_test TOPLEVEL=dut_test

# Importing Cocotb’s standard simulation Makefile, so this Makefile uses Cocotb’s build system and simulator interface.
include $(shell cocotb-config --makefiles)/Makefile.sim
