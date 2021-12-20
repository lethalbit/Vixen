from amaranth import *

from util import Length

class OperandDecoder(Elaboratable):
    def __init__(self):
        self.i_data     = Signal(6*8)
        self.i_valid    = Signal()
        self.i_operidx  = Signal(6, reset=1)
        self.i_operlen1 = Signal(Length)
        self.i_operlen2 = Signal(Length)
        self.i_operlen3 = Signal(Length)
        self.i_operlen4 = Signal(Length)
        self.i_operlen5 = Signal(Length)
        self.i_operlen6 = Signal(Length)

        self.o_deferred = Signal()
        self.o_legalop  = Signal()
        self.o_immed    = Signal(32)
        self.o_immvalid = Signal()
        self.o_length   = Signal(6)
        self.o_nextidx  = Signal(6)

    def elaborate(self, platform):
        m = Module()

        is_indexed  = self.i_data[4:8] == 0x4

        op_offset   = Mux(is_indexed, 8, 0)
        imm_offset  = Mux(is_indexed, 16, 8)

        opcode_nibble = self.i_data.bit_select(op_offset+4, 4)
        opcode_byte   = self.i_data.bit_select(op_offset, 8)

        is_literal           = self.i_data[6:8]   == 0b00
        is_literal_indexed   = self.i_data[14:16] == 0b00
        is_index_indexed     = self.i_data[12:16] == 0x4
        is_register          = self.i_data[4:8]   == 0x5
        is_register_indexed  = self.i_data[12:16] == 0x5
        is_register_deferred = opcode_nibble      == 0x6
        is_autodec           = opcode_nibble      == 0x7
        is_autoinc           = opcode_nibble      == 0x8
        is_immediate         = self.i_data[0:8]   == 0x8F
        is_immediate_indexed = self.i_data[8:16]  == 0x8F
        is_autoinc_deferred  = opcode_nibble      == 0x9
        is_absolute          = opcode_byte        == 0x9F
        is_bytedisp          = opcode_nibble      == 0xA
        is_worddisp          = opcode_nibble      == 0xB
        is_longdisp          = opcode_nibble      == 0xC
        is_bytedisp_deferred = opcode_nibble      == 0xD
        is_worddisp_deferred = opcode_nibble      == 0xE
        is_longdisp_deferred = opcode_nibble      == 0xF

        oplength = Signal(Length)
        operlens = [self.i_operlen1, self.i_operlen2, self.i_operlen3, self.i_operlen4, self.i_operlen5, self.i_operlen6]
        for i, operlen in enumerate(operlens):
            with m.If(self.i_operidx[i]):
                m.d.comb += oplength.eq(operlen)

        literal_imm   = self.i_data[0:6] # indexed literal is illegal, so no shift needed
        autoinc_imm   = Mux(oplength == Length.BYTE, 1, Mux(oplength == Length.WORD, 2, Mux(oplength == Length.LONG, 4, 8)))
        autodec_imm   = -autoinc_imm
        immediate_imm = Mux(oplength == Length.BYTE, self.i_data[8:16], Mux(oplength == Length.WORD, self.i_data[8:24], self.i_data[8:40]))
        absolute_imm  = self.i_data.bit_select(imm_offset, 32)
        bytedisp_imm  = Cat(self.i_data.bit_select(imm_offset, 8), Repl(self.i_data.bit_select(imm_offset + 7, 1), 24))
        worddisp_imm  = Cat(self.i_data.bit_select(imm_offset, 16), Repl(self.i_data.bit_select(imm_offset + 15, 1), 16))
        longdisp_imm  = absolute_imm

        is_one_byte           = (~is_indexed) & (is_literal | is_register | is_register_deferred | is_autodec | is_autoinc | is_autoinc_deferred)
        is_one_byte_indexed   = is_indexed & (is_literal | is_register | is_register_deferred | is_autodec | is_autoinc | is_autoinc_deferred)
        is_two_byte           = is_one_byte_indexed | ((oplength == Length.BYTE) & is_immediate) | ((~is_indexed) & (is_bytedisp | is_bytedisp_deferred))
        is_two_byte_indexed   = is_indexed & (is_bytedisp | is_bytedisp_deferred)
        is_three_byte         = is_two_byte_indexed | ((oplength == Length.WORD) & is_immediate) | ((~is_indexed) & (is_worddisp | is_worddisp_deferred))
        is_three_byte_indexed = is_indexed & (is_worddisp | is_worddisp_deferred)
        is_four_byte          = is_three_byte_indexed
        is_five_byte          = (~is_indexed) & (((oplength == Length.LONG) & is_immediate) | is_absolute | is_longdisp | is_longdisp_deferred)
        is_five_byte_indexed  = is_indexed & (is_absolute | is_longdisp | is_longdisp_deferred)
        is_six_byte           = is_five_byte_indexed

        m.d.comb += [
            self.o_deferred.eq(is_register_deferred | is_autoinc_deferred | is_bytedisp_deferred | is_worddisp_deferred | is_longdisp_deferred),
            self.o_legalop.eq((~is_indexed) | (~(is_literal_indexed | is_index_indexed | is_register_indexed | is_immediate_indexed))),
            self.o_immvalid.eq(~(is_register | is_register_deferred))
        ]

        # Immediate routing
        with m.If(is_literal):
            m.d.comb += self.o_immed.eq(literal_imm)
        with m.Elif(is_autodec):
            m.d.comb += self.o_immed.eq(autodec_imm)
        with m.Elif(is_immediate):
            m.d.comb += self.o_immed.eq(immediate_imm)
        with m.Elif(is_absolute):
            m.d.comb += self.o_immed.eq(absolute_imm)
        with m.Elif(is_autoinc | is_autoinc_deferred):
            m.d.comb += self.o_immed.eq(autoinc_imm)
        with m.Elif(is_bytedisp | is_bytedisp_deferred):
            m.d.comb += self.o_immed.eq(bytedisp_imm)
        with m.Elif(is_worddisp | is_worddisp_deferred):
            m.d.comb += self.o_immed.eq(worddisp_imm)
        with m.Elif(is_longdisp | is_longdisp_deferred):
            m.d.comb += self.o_immed.eq(longdisp_imm)

        # Size routing
        with m.If(self.i_valid):
            with m.If(is_one_byte):
                m.d.comb += self.o_length.eq(1 << 0)
            with m.Elif(is_two_byte):
                m.d.comb += self.o_length.eq(1 << 1)
            with m.Elif(is_three_byte):
                m.d.comb += self.o_length.eq(1 << 2)
            with m.Elif(is_four_byte):
                m.d.comb += self.o_length.eq(1 << 3)
            with m.Elif(is_five_byte):
                m.d.comb += self.o_length.eq(1 << 4)
            with m.Else(): # equivalent to m.Elif(is_six_byte)
                m.d.comb += self.o_length.eq(1 << 5)

        # Operand index routing
        m.d.comb += self.o_nextidx.eq(self.i_operidx.rotate_left(1))

        return m

if __name__ == "__main__":
    from amaranth.back import verilog

    opdec = OperandDecoder()
    ports = [
        opdec.i_data, opdec.i_valid, opdec.i_operlen1, opdec.i_operlen2, opdec.i_operlen3, opdec.i_operlen4, opdec.i_operlen5, opdec.i_operlen6,
        opdec.o_deferred, opdec.o_legalop, opdec.o_immed, opdec.o_immvalid, opdec.o_length
    ]

    print(verilog.convert(opdec, ports=ports))
