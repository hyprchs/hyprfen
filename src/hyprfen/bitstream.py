from __future__ import annotations


class BitWriter:
    __slots__ = ("_value", "_nbits")

    def __init__(self) -> None:
        self._value = 0
        self._nbits = 0

    @property
    def nbits(self) -> int:
        return self._nbits

    def write_bits(self, value: int, nbits: int) -> None:
        if nbits < 0:
            raise ValueError("nbits must be non-negative")
        if nbits == 0:
            return
        if value < 0:
            raise ValueError("value must be non-negative")
        if value >> nbits:
            raise ValueError(f"value {value} does not fit in {nbits} bits")
        self._value |= value << self._nbits
        self._nbits += nbits

    def write_bool(self, value: bool) -> None:
        self.write_bits(1 if value else 0, 1)

    def write_varuint(self, value: int) -> None:
        if value < 0:
            raise ValueError("value must be non-negative")
        while True:
            byte = value & 0x7F
            value >>= 7
            if value:
                self.write_bits(byte | 0x80, 8)
            else:
                self.write_bits(byte, 8)
                break

    def to_bytes(self) -> bytes:
        return self._value.to_bytes((self._nbits + 7) // 8, "little")


class BitReader:
    __slots__ = ("_value", "_nbits", "_offset")

    def __init__(self, data: bytes) -> None:
        self._value = int.from_bytes(data, "little")
        self._nbits = len(data) * 8
        self._offset = 0

    @property
    def offset(self) -> int:
        return self._offset

    @property
    def nbits(self) -> int:
        return self._nbits

    def remaining_bits(self) -> int:
        return self._nbits - self._offset

    def read_bits(self, nbits: int) -> int:
        if nbits < 0:
            raise ValueError("nbits must be non-negative")
        if self._offset + nbits > self._nbits:
            raise ValueError("not enough bits remaining in stream")
        if nbits == 0:
            return 0
        mask = (1 << nbits) - 1
        value = (self._value >> self._offset) & mask
        self._offset += nbits
        return value

    def read_bool(self) -> bool:
        return bool(self.read_bits(1))

    def read_varuint(self) -> int:
        shift = 0
        value = 0
        while True:
            byte = self.read_bits(8)
            value |= (byte & 0x7F) << shift
            if (byte & 0x80) == 0:
                return value
            shift += 7
            if shift > 63:
                raise ValueError("varuint is too large or malformed")
