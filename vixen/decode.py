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

    ADDP4  = 0x20
    ADDP6  = 0x21
    SUBP4  = 0x22
    SUBP6  = 0x23
    CVTPT  = 0x24
    MULP   = 0x25
    CVTTP  = 0x26
    DIVP   = 0x27
    MOVC3  = 0x28
    CMPC3  = 0x29
    SCANC  = 0x2a
    SPANC  = 0x2b
    MOVC5  = 0x2c
    CMPC5  = 0x2d
    MOVTC  = 0x2e
    MOVTUC = 0x2f

    BSBW   = 0x30
    BRW    = 0x31
    CVTWL  = 0x32
    CVTWB  = 0x33
    MOVP   = 0x34
    CMPP3  = 0x35
    CVTPL  = 0x36
    CMPP4  = 0x37
    EDITPC = 0x38
    MATCHC = 0x39
    LOCC   = 0x3a
    SKPC   = 0x3b
    MOVZWL = 0x3c
    ACBW   = 0x3d
    MOVAW  = 0x3e
    PUSHAW = 0x3f

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
            # 0x00 (misc)
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
            # 0x10 (branches/jumps)
            Opcode.BSBB:   ("b", "b"),
            Opcode.BRB:    ("b", "b"),
            Opcode.BNEQ:   ("b", "b"),
            Opcode.BEQL:   ("b", "b"),
            Opcode.BGTR:   ("b", "b"),
            Opcode.BLEQ:   ("b", "b"),
            Opcode.JSB:    ("a", "b"),
            Opcode.JMP:    ("a", "b"),
            Opcode.BGEQ:   ("b", "b"),
            Opcode.BLSS:   ("b", "b"),
            Opcode.BGTRU:  ("b", "b"),
            Opcode.BLEQU:  ("b", "b"),
            Opcode.BVC:    ("b", "b"),
            Opcode.BVS:    ("b", "b"),
            Opcode.BGEQU:  ("b", "b"),
            Opcode.BLSSU:  ("b", "b"),
            # 0x20 (packed decimal)
            Opcode.ADDP4:  ("rara", "wbwb"),
            Opcode.ADDP6:  ("rarara", "wbwbwb"),
            Opcode.SUBP4:  ("rara", "wbwb"),
            Opcode.SUBP6:  ("rarara", "wbwbwb"),
            # 0x30 (packed decimal and conversions)
            Opcode.BSBW:   ("b", "w"),
            Opcode.BRW:    ("b", "w"),
            Opcode.CVTWL:  ("rw", "wl"),
            Opcode.CVTWB:  ("rw", "wb"),
            Opcode.MOVP:   ("raa", "wbb"),
            Opcode.CMPP3:  ("raa", "wbb"),
            Opcode.CVTPL:  ("raw", "wbl"),
            Opcode.CMPP4:  ("rara", "wbwb"),
            Opcode.EDITPC: ("raaa", "wbbb"),
            Opcode.MATCHC: ("rara", "wbwb"),
            Opcode.LOCC:   ("rra", "bwb"),
            Opcode.SKPC:   ("rra", "bwb"),
            Opcode.MOVZWL: ("rw", "wl"),
            Opcode.ACBW:   ("rrmb", "wwww"),
            Opcode.MOVAW:  ("aw", "wl"),
            Opcode.PUSHAW: ("a", "w"),
            # 0x80 (byte math)
            Opcode.ADDB2:  ("rm", "bb"),
            Opcode.ADDB3:  ("rrw", "bbb"),
            # 0xa0 (word math)
            Opcode.ADDW2:  ("rm", "ww"),
            Opcode.ADDW3:  ("rrw", "www"),
            # 0xc0 (longword math)
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