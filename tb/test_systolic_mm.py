import cocotb
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge
import numpy as np
from mm_helpers import pack, unpack

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


async def multiply(dut, a, b):
    """Run one product. Returns C as a NumPy array, and the number of edges it took."""
    n, aw, steps = sizes(dut)
    dut.a_flat.value = pack(a, DW)
    dut.b_flat.value = pack(b, DW)
    dut.start.value = 1
    await FallingEdge(dut.clk)             # the starting edge has happened
    dut.start.value = 0
    dut.a_flat.value = 0                   # the design has its own copies now
    dut.b_flat.value = 0

    edges = 0
    while dut.done.value != 1:             # wait for done, counting edges
        await FallingEdge(dut.clk)
        edges += 1
        assert edges <= 10 * steps, "done never went high"
    return unpack(int(dut.c_flat.value), n, aw), edges


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

    await FallingEdge(dut.clk)             # start is still high and busy was low, so go is high: this edge begins a new run
    assert dut.busy.value == 1
    assert dut.done.value == 0
    assert dut.t.value == 0


@cocotb.test()
async def capture(dut):
    await reset(dut)

    dut.a_flat.value = 0x04030201          # A = [[1, 2], [3, 4]]
    dut.b_flat.value = 0x08070605          # B = [[5, 6], [7, 8]]
    dut.start.value = 1
    await FallingEdge(dut.clk)             # copies are taken
    assert dut.a_r.value == 0x04030201
    assert dut.b_r.value == 0x08070605

    dut.a_flat.value = 0                   # change the inputs
    dut.b_flat.value = 0
    await FallingEdge(dut.clk)
    await FallingEdge(dut.clk)
    assert dut.a_r.value == 0x04030201     # busy is high, so the copies do not change
    assert dut.b_r.value == 0x08070605


@cocotb.test()
async def feeds(dut):
    n, aw, steps = sizes(dut)
    if n != 2:
        dut._log.info("skipped: the expected values below are for N = 2")
        return
    await reset(dut)

    dut.a_flat.value = 0x04030201          # A = [[1, 2], [3, 4]]
    dut.b_flat.value = 0x08070605          # B = [[5, 6], [7, 8]]
    dut.start.value = 1

    rows = [(1, 0), (2, 3), (0, 4), (0, 0)]   # (row 0, row 1) after edges 1 to 4
    cols = [(5, 0), (7, 6), (0, 8), (0, 0)]   # (column 0, column 1)
    for row, col in zip(rows, cols):
        await FallingEdge(dut.clk)
        dut.start.value = 0
        assert dut.a_feed[0].value.to_signed() == row[0]
        assert dut.a_feed[1].value.to_signed() == row[1]
        assert dut.b_feed[0].value.to_signed() == col[0]
        assert dut.b_feed[1].value.to_signed() == col[1]

    await FallingEdge(dut.clk)             # finished: nothing is fed
    assert dut.a_feed[0].value == 0 and dut.a_feed[1].value == 0
    assert dut.b_feed[0].value == 0 and dut.b_feed[1].value == 0

@cocotb.test()
async def product(dut):
    n, aw, steps = sizes(dut)
    if n != 2:
        dut._log.info("skipped: the expected values below are for N = 2")
        return
    await reset(dut)

    dut.a_flat.value = 0x04030201          # A = [[1, 2], [3, 4]]
    dut.b_flat.value = 0x08070605          # B = [[5, 6], [7, 8]]
    dut.start.value = 1
    await FallingEdge(dut.clk)             # edge 1
    dut.start.value = 0
    for _ in range(steps):                 # edges 2 to 5
        await FallingEdge(dut.clk)
    assert dut.done.value == 1

    c = int(dut.c_flat.value)              # the whole 68-bit bus as one integer
    mask = (1 << aw) - 1                   # aw ones in a row: keeps one 17-bit slot
    got = [(c >> (aw * slot)) & mask for slot in range(4)]
    assert got == [19, 22, 43, 50]         # C = [[19, 22], [43, 50]]


@cocotb.test()
async def random_products(dut):
    n, aw, steps = sizes(dut)
    await reset(dut)

    rng = np.random.default_rng(0)
    for _ in range(1000):
        a = rng.integers(-128, 128, size=(n, n))
        b = rng.integers(-128, 128, size=(n, n))
        c_expected = a @ b
        c_got, edges = await multiply(dut, a, b)
        assert edges == steps, f"expected {steps} edges, got {edges}"
        assert np.array_equal(c_expected, c_got), (
            f"A=\n{a}\nB=\n{b}\nexpected\n{c_expected}\ngot\n{c_got}"
        )


@cocotb.test()
async def corner_cases(dut):
    n, aw, steps = sizes(dut)
    await reset(dut)

    lo = np.full((n, n), -128)             # every entry is the most negative value
    hi = np.full((n, n), 127)              # every entry is the most positive value
    zero = np.zeros((n, n), dtype=int)
    eye = np.eye(n, dtype=int)             # the identity matrix
    rng = np.random.default_rng(1)
    m = rng.integers(-128, 128, size=(n, n))

    pairs = [(lo, lo), (lo, hi), (hi, hi), (zero, m), (eye, m), (m, eye)]
    for a, b in pairs:
        c_expected = a @ b
        c_got, edges = await multiply(dut, a, b)
        assert edges == steps, f"expected {steps} edges, got {edges}"
        assert np.array_equal(c_expected, c_got), (
            f"A=\n{a}\nB=\n{b}\nexpected\n{c_expected}\ngot\n{c_got}"
        )