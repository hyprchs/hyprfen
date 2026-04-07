from __future__ import annotations


def popcount(x: int) -> int:
    return x.bit_count()


def pext(value: int, mask: int) -> int:
    """Software implementation of BMI2 PEXT.

    Extracts the bits of ``value`` selected by ``mask`` and packs them into the
    low bits of the return value in increasing source-bit order.
    """
    out = 0
    out_bit = 1
    while mask:
        lsb = mask & -mask
        if value & lsb:
            out |= out_bit
        mask ^= lsb
        out_bit <<= 1
    return out


def pdep(value: int, mask: int) -> int:
    """Software implementation of BMI2 PDEP.

    Deposits the low bits of ``value`` into the bit positions selected by
    ``mask`` in increasing mask-bit order.
    """
    out = 0
    in_bit = 1
    while mask:
        lsb = mask & -mask
        if value & in_bit:
            out |= lsb
        mask ^= lsb
        in_bit <<= 1
    return out
