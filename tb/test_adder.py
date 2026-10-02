import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles


@cocotb.test()
async def adds(dut):
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    dut.a.value = 3
    dut.b.value = 4
    await ClockCycles(dut.clk, 3)
    assert int(dut.sum.value) == 7