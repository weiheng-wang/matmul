import cocotb
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge

DW = 8


def sizes(dut):
    n = int(dut.N.value)                   # read the parameter from the design
    aw = 2 * DW + (n - 1).bit_length()     # same as 2*DW + $clog2(N)
    steps = 3 * n - 2
    return n, aw, steps


async def reset(dut):
    """Start the clock and hold rst for two edges with every input at 0."""
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    dut.rst.value = 1
    dut.start.value = 0
    dut.a_flat.value = 0
    dut.b_flat.value = 0
    await FallingEdge(dut.clk)
    await FallingEdge(dut.clk)
    dut.rst.value = 0


@cocotb.test()
async def widths(dut):
    """Check that the flattened input and output arrays have the expected widths."""
    n, aw, steps = sizes(dut)
    assert len(dut.a_flat) == n * n * DW
    assert len(dut.b_flat) == n * n * DW
    assert len(dut.c_flat) == n * n * aw


@cocotb.test()
async def control_timeline(dut):
    """Check that the control for the array works."""
    n, aw, steps = sizes(dut)
    await reset(dut)
    assert dut.busy.value == 0
    assert dut.done.value == 0

    dut.start.value = 1
    for t in range(steps):
        await FallingEdge(dut.clk)         # while busy: busy is high, done is low, t counts up
        dut.start.value = 0
        assert dut.busy.value == 1
        assert dut.done.value == 0
        assert dut.t.value == t

    await FallingEdge(dut.clk)             # finished: busy is low, done is high
    assert dut.busy.value == 0
    assert dut.done.value == 1

    await FallingEdge(dut.clk)             # done lasts one cycle, busy is low, done is low
    assert dut.busy.value == 0
    assert dut.done.value == 0


@cocotb.test()
async def start_held_high(dut):
    n, aw, steps = sizes(dut)
    await reset(dut)

    dut.start.value = 1                    # never lowered in this test
    for t in range(steps):                 # ignored while busy: t never restarts
        await FallingEdge(dut.clk)
        assert dut.busy.value == 1
        assert dut.done.value == 0
        assert dut.t.value == t

    await FallingEdge(dut.clk)             # finished: busy is low, done is high
    assert dut.busy.value == 0
    assert dut.done.value == 1

    await FallingEdge(dut.clk)              # start is still high and busy was low, so go is high: this edge begins a new run
    assert dut.busy.value == 1
    assert dut.done.value == 0
    assert dut.t.value == 0