from enum import Enum

from amaranth import *


class Opcode(Enum):
    HALT   = 0x00
    NOP    = 0x01
    REI    = 0x02
    BPT    = 0x03
    RET    = 0x04
    RSB    = 0x05
    LDPCTX = 0x06
    SVPCTX = 0x07
    CVTPS  = 0x08
    CVTSP  = 0x09
    INDEX  = 0x0a
    CRC    = 0x0b
    PROBER = 0x0c
    PROBEW = 0x0d
    INSQUE = 0x0e
    REMQUE = 0x0f
    BSBB   = 0x10
    BRB    = 0x11
    BNEQ   = 0x12
    BEQL   = 0x13
    BGTR   = 0x14
    BLEQ   = 0x15
    JSB    = 0x16
    JMP    = 0x17
    BGEQ   = 0x18
    BLSS   = 0x19
    BGTRU  = 0x1a
    BLEQU  = 0x1b
    BVC    = 0x1c
    BVS    = 0x1d
    BGEQU  = 0x1e
    BLSSU  = 0x1f

    ADDB2  = 0x80
    ADDB3  = 0x81

    ADDW2  = 0xa0
    ADDW3  = 0xa1

    ADDL2  = 0xc0
    ADDL3  = 0xc1

    # Extended opcode bytes, for convenience.
    EXOPFD = 0xfd
    EXOPFE = 0xfe
    EXOPFF = 0xff

    @staticmethod
    def _data():
        # Opcode: (operand kind, data type)
        # where operand kinds is a string of:
        # - effective "a"ddress
        # - "b"ranch displacement
        # - "m"odified operand
        # - "r"ead operand
        # - effective address "v" (I don't know the difference between this and a)
        # - "w"ritten operand
        # data type is a string of:
        # - "b"yte
        # - "w"ord
        # - "l"ongword
        # - "q"uadword
        return {
            Opcode.ADDB2: ("rm", "bb"),
            Opcode.ADDB3: ("rrw", "bbb"),
            Opcode.ADDW2: ("rm", "ww"),
            Opcode.ADDW3: ("rrw", "www"),
            Opcode.ADDL2: ("rm", "ll"),
            Opcode.ADDL3: ("rrw", "lll"),
        }

    @staticmethod
    def zero_op_insns():
        return [opcode for opcode, data in Opcode._data() if len(data[0]) == 0]

    @staticmethod
    def one_op_insns():
        return [opcode for opcode, data in Opcode._data() if len(data[0]) == 1]

    @staticmethod
    def two_op_insns():
        return [opcode for opcode, data in Opcode._data() if len(data[0]) == 2]

    @staticmethod
    def three_op_insns():
        return [opcode for opcode, data in Opcode._data() if len(data[0]) == 3]

    @staticmethod
    def four_op_insns():
        return [opcode for opcode, data in Opcode._data() if len(data[0]) == 4]

    @staticmethod
    def five_op_insns():
        return [opcode for opcode, data in Opcode._data() if len(data[0]) == 5]

    @staticmethod
    def six_op_insns():
        return [opcode for opcode, data in Opcode._data() if len(data[0]) == 6]


class OpcodeOperandCount(Elaboratable):
    def __init__(self):
        self.i_opcode = Signal(16)
        self.o_count  = Signal(range(6))

    def elaborate(self, platform):
        m = Module()

        with m.Switch(self.i_opcode):
            with m.Case(Opcode.zero_op_insns()):
                m.d.comb += self.o_count.eq(0)
            with m.Case(Opcode.one_op_insns()):
                m.d.comb += self.o_count.eq(1)
            with m.Case(Opcode.two_op_insns()):
                m.d.comb += self.o_count.eq(2)
            with m.Case(Opcode.three_op_insns()):
                m.d.comb += self.o_count.eq(3)
            with m.Case(Opcode.four_op_insns()):
                m.d.comb += self.o_count.eq(4)
            with m.Case(Opcode.five_op_insns()):
                m.d.comb += self.o_count.eq(5)
            with m.Case(Opcode.six_op_insns()):
                m.d.comb += self.o_count.eq(6)
            with m.Default():
                m.d.comb += self.o_count.eq(0)

        return m


# Assumptions:
# - register file is 32-entry, not 16
# - outputs to a 3-input, 2-output micro-op

class VaxDecoder(Elaboratable):
    def __init__(self):
        # Input data for the decoder; little endian.
        self.i_data = Signal(48)

        # Current data address
        self.o_addr = Signal(32)

    def elaborate(self, platform):
        m = Module()

        opcode = Signal(Opcode)

        operand = Signal(48) # 48 bits holds longword displacement indexed.
        operand_valid_bytes = Signal(6)

        with m.FSM():
            with m.State("START"):
                # For now this only looks at the very first operand.
                # For increased performance one would want to examine as much of the instruction as possible.

                with m.If(self.i_data[:8].matches(Opcode.EXOPFD, Opcode.EXOPFE, Opcode.EXOPFF)):
                    m.d.sync += opcode.eq(self.i_data[:16])
                    m.d.comb += [
                        operand.eq(self.i_data),
                        operand_valid_bytes.eq(0b111100),
                    ]
                with m.Else():
                    m.d.sync += opcode.eq(self.i_data[:8])
                    m.d.comb += [
                        operand.eq(self.i_data),
                        operand_valid_bytes.eq(0b111110),
                    ]

        return m