from enum import Enum

from nmigen import *

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

    # Extended opcode bytes, for convenience.
    EXOPFD = 0xfd
    EXOPFE = 0xfe
    EXOPFF = 0xff

    # more to add...
    BUGL   = 0xfdff
    BUGW   = 0xfeff


class OperandDecoder(Elaboratable):
    def __init__(self):
        self.i_data  = Signal(48)
        self.i_valid = Signal(6)
        self.i_oplength = Signal(2)

        self.o_needmore = Signal()
        self.o_immed    = Signal(32)
        self.o_immvalid = Signal()

    def elaborate(self, platform):
        m = Module()

        m.d.comb += [
            self.o_needmore.eq(1),
            self.o_immvalid.eq(0)
        ]

        # What kind of operand is this?
        # TODO: I am not as confident with pattern syntax as I thought I was; this needs checking.
        with m.Switch(self.i_data[0:8]):
            with m.Case("00------"): # literal
                m.d.comb += [
                    self.o_immed.eq(self.i_data[0:6]),
                    self.o_immvalid.eq(1)
                ]
            with m.Case("0100----"): # index mode
                with m.Switch(self.i_data[8:16]):
                    with m.Case("00------"): # literal indexed (forbidden)
                        # TODO: Rightward lean is a bit much, maybe these should be flattened together?
                        pass
                    with m.Case("0100----"): # index indexed (forbidden)
                        pass
                    with m.Case("0101----"): # register indexed (forbidden)
                        pass
                    with m.Case("0110----"): # register deferred indexed
                        pass
                    with m.Case("0111----"): # autodecrement indexed
                        pass
                    with m.Case("10001111"): # immediate indexed (forbidden)
                        pass
                    with m.Case("1000----"): # autoincrement indexed
                        pass
                    with m.Case("10011111"): # absolute indexed
                        pass
                    with m.Case("1001----"): # autoincrement deferred indexed
                        pass
                    with m.Case("1010----"): # byte displacement indexed
                        pass
                    with m.Case("1011----"): # word displacement indexed
                        pass
                    with m.Case("1100----"): # long displacement indexed
                        pass
                    with m.Case("1101----"): # byte displacement deferred indexed
                        pass
                    with m.Case("1110----"): # word displacement deferred indexed
                        pass
                    with m.Case("1111----"): # long displacement deferred indexed
                        pass
            with m.Case("0101----"): # register
                pass
            with m.Case("0110----"): # register deferred
                pass
            with m.Case("0111----"): # autodecrement
                pass
            with m.Case("10001111"): # immediate
                pass
            with m.Case("1000----"): # autoincrement
                pass
            with m.Case("10011111"): # absolute
                pass
            with m.Case("1001----"): # autoincrement deferred
                pass
            with m.Case("1010----"): # byte displacement
                with m.If(self.i_valid[1]):
                    m.d.comb += [
                        self.o_immed.eq(Cat(self.i_data[8:16], Repl(self.i_data[15], 24))),
                        self.o_immvalid.eq(1)
                    ]
            with m.Case("1011----"): # word displacement
                with m.If(self.i_valid[1] & self.i_valid[2]):
                    m.d.comb += [
                        self.o_immed.eq(Cat(self.i_data[8:24], Repl(self.i_data[23], 16))),
                        self.o_immvalid.eq(1)
                    ]
            with m.Case("1100----"): # longword displacement
                pass
            with m.Case("1101----"): # byte displacement deferred
                with m.If(self.i_valid[1]):
                    m.d.comb += [
                        self.o_immed.eq(Cat(self.i_data[8:16], Repl(self.i_data[15], 24))),
                        self.o_immvalid.eq(1)
                    ]
            with m.Case("1110----"): # word displacement deferred
                with m.If(self.i_valid[1] & self.i_valid[2]):
                    m.d.comb += [
                        self.o_immed.eq(Cat(self.i_data[8:24], Repl(self.i_data[23], 16))),
                        self.o_immvalid.eq(1)
                    ]
            with m.Case("1111----"): # longword displacement deferred
                pass

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