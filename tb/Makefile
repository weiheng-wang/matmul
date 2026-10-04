SIM ?= icarus
TOPLEVEL_LANG ?= verilog
TOP ?= systolic_mm
VERILOG_SOURCES += $(PWD)/../rtl/pe.sv $(PWD)/../rtl/systolic_mm.sv
COCOTB_TOPLEVEL = $(TOP)
COCOTB_TEST_MODULES = test_$(TOP)
SIM_BUILD = sim_build/$(TOP)
include $(shell cocotb-config --makefiles)/Makefile.sim