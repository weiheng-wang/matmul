"""Convert between matrices and the flat buses of systolic_mm."""
import numpy as np


def pack(m, width):
    """Pack a square matrix of signed integers into one integer.

    Entry [i][j] goes in slot i*n + j, and each slot is `width` bits.
    """
    n = len(m)
    mask = (1 << width) - 1                 # `width` ones in a row
    value = 0
    for i in range(n):
        for j in range(n):
            bits = int(m[i][j]) & mask      # two's complement bit pattern of the entry
            value |= bits << ((i * n + j) * width)
    return value


def unpack(value, n, width):
    """Split one integer into an n x n NumPy array of signed integers."""
    mask = (1 << width) - 1
    out = np.zeros((n, n), dtype=np.int64)
    for i in range(n):
        for j in range(n):
            bits = (value >> ((i * n + j) * width)) & mask
            if bits >= 1 << (width - 1):    # top bit set, so the number is negative
                bits -= 1 << width
            out[i][j] = bits
    return out


if __name__ == "__main__":
    assert pack([[1, 2], [3, 4]], 8) == 0x04030201
    assert pack([[-1, 0], [0, 0]], 8) == 0xFF
    assert pack([[-128, 127], [0, -1]], 8) == 0xFF007F80
    assert unpack(0xFF007F80, 2, 8).tolist() == [[-128, 127], [0, -1]]
    assert unpack(0x30000, 2, 18).tolist() == [[-65536, 0], [0, 0]]
    rng = np.random.default_rng(0)
    for _ in range(200):
        x = rng.integers(-128, 128, size=(4, 4))
        y = unpack(pack(x, 8), 4, 8)
        assert np.array_equal(x, y)
    print("helpers ok")