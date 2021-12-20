from enum import Enum

from amaranth import *

from decode_operand import OperandDecoder
from util import Length


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
    def _data() -> dict[Enum, tuple[str, str]]:
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
            Opcode.HALT:   ("", ""),
            Opcode.NOP:    ("", ""),
            Opcode.REI:    ("", ""),
            Opcode.BPT:    ("", ""),
            Opcode.RET:    ("", ""),
            Opcode.RSB:    ("", ""),
            Opcode.LDPCTX: ("", ""),
            Opcode.SVPCTX: ("", ""),
            Opcode.CVTPS:  ("rara", "wbwb"),
            Opcode.CVTSP:  ("rara", "wbwb"),
            Opcode.INDEX:  ("rrrrrw", "llllll"),
            Opcode.CRC:    ("arra", "blwb"),
            Opcode.PROBER: ("rra", "bwb"),
            Opcode.PROBEW: ("rra", "bwb"),
            Opcode.INSQUE: ("aa", "bb"),
            Opcode.REMQUE: ("aw", "bl"),

            Opcode.ADDB2:  ("rm", "bb"),
            Opcode.ADDB3:  ("rrw", "bbb"),

            Opcode.ADDW2:  ("rm", "ww"),
            Opcode.ADDW3:  ("rrw", "www"),

            Opcode.ADDL2:  ("rm", "ll"),
            Opcode.ADDL3:  ("rrw", "lll"),
        }

    @staticmethod
    def n_op_insns(operand_count=0):
        return [opcode for opcode, data in Opcode._data().items() if len(data[0]) == operand_count]

    @staticmethod
    def nth_op_byte_insns(operand=0):
        return [opcode for opcode, data in Opcode._data().items() if len(data[1]) > operand and data[1][operand] == "b"]

    @staticmethod
    def nth_op_word_insns(operand=0):
        return [opcode for opcode, data in Opcode._data().items() if len(data[1]) > operand and data[1][operand] == "w"]

    @staticmethod
    def nth_op_long_insns(operand=0):
        return [opcode for opcode, data in Opcode._data().items() if len(data[1]) > operand and data[1][operand] == "l"]


class OpcodeOperandCount(Elaboratable):
    def __init__(self):
        self.i_opcode = Signal(16)
        self.o_count  = Signal(range(6))

    def elaborate(self, platform):
        m = Module()

        with m.Switch(self.i_opcode):
            for operand_count in range(0, 7):
                with m.Case(Opcode.n_op_insns(operand_count)):
                    m.d.comb += self.o_count.eq(operand_count)
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