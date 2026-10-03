import cocotb
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge


@cocotb.test()
async def accumulates(dut):
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())

    # reset: hold rst high for two cycles
    dut.rst.value = 1
    dut.clr.value = 0
    dut.en.value = 0
    dut.a_in.value = 0
    dut.b_in.value = 0
    await FallingEdge(dut.clk)
    await FallingEdge(dut.clk)

    # release reset and enable the cell
    dut.rst.value = 0
    dut.en.value = 1


    # first pair: 3 x 4
    dut.a_in.value = 3
    dut.b_in.value = 4
    await FallingEdge(dut.clk)
    assert dut.acc.value.to_signed() == 12 # 3 x 4 = 12
    assert dut.a_out.value.to_signed() == 3
    assert dut.b_out.value.to_signed() == 4


    # second pair: -2 x 5
    dut.a_in.value = -2
    dut.b_in.value = 5
    await FallingEdge(dut.clk)
    assert dut.acc.value.to_signed() == 2 # 12 + (-2 x 5) = 2
    assert dut.a_out.value.to_signed() == -2
    assert dut.b_out.value.to_signed() == 5


    dut.en.value = 0 # testing enable signal works

    # third pair: 9 x 7
    dut.a_in.value = 9
    dut.b_in.value = 7
    await FallingEdge(dut.clk)
    assert dut.acc.value.to_signed() == 2 # should not change
    assert dut.a_out.value.to_signed() == -2
    assert dut.b_out.value.to_signed() == 5


    dut.clr.value = 1 # testing clear signal works

    await FallingEdge(dut.clk)
    assert dut.acc.value.to_signed() == 0
    assert dut.a_out.value.to_signed() == 0
    assert dut.b_out.value.to_signed() == 0


    dut.clr.value = 0
    dut.en.value = 1

    # fourth pair: -128 x -128, testing extreme case
    dut.a_in.value = -128
    dut.b_in.value = -128
    await FallingEdge(dut.clk)
    assert dut.acc.value.to_signed() == 16384 # (-128) x (-128) = 16384
    assert dut.a_out.value.to_signed() == -128
    assert dut.b_out.value.to_signed() == -128