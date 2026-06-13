import unittest

from main import RISC_V

# funct3 / funct7 selectors for R-type ALU ops
F3 = {
    "ADD": 0b000, "SUB": 0b000, "SLT": 0b010, "SLTU": 0b011,
    "XOR": 0b100, "OR": 0b110, "AND": 0b111,
    "SRL": 0b101, "SRA": 0b101, "SLL": 0b001,
}
F7 = {
    "ADD": 0b0000000, "SUB": 0b0100000, "SLT": 0b0000000, "SLTU": 0b0000000,
    "XOR": 0b0000000, "OR": 0b0000000, "AND": 0b0000000,
    "SRL": 0b0000000, "SRA": 0b0100000, "SLL": 0b0000000,
}


def encode_r(op, rd, rs1, rs2):
    """Encode an R-type instruction word for the given mnemonic."""
    opcode = 0b0110011  # OP_REG
    return (
        (F7[op] << 25)
        | (rs2 << 20)
        | (rs1 << 15)
        | (F3[op] << 12)
        | (rd << 7)
        | opcode
    )


def run_op(op, a, b, rd=3, rs1=1, rs2=2):
    """Load a, b into rs1, rs2; execute op; return the value written to rd."""
    cpu = RISC_V()
    cpu.registers[rs1] = a & 0xFFFFFFFF
    cpu.registers[rs2] = b & 0xFFFFFFFF
    cpu.decode_instruction(encode_r(op, rd, rs1, rs2))
    return cpu.registers[rd]


# funct3 selectors for I-type (OP-IMM) ops
F3_I = {"ADDI": 0b000, "SLTI": 0b010, "SLTIU": 0b011,
        "XORI": 0b100, "ORI": 0b110, "ANDI": 0b111,
        "SLLI": 0b001, "SRLI": 0b101, "SRAI": 0b101}
# funct7 (imm[11:5]) selectors for the shift-immediate ops
F7_I = {"SLLI": 0b0000000, "SRLI": 0b0000000, "SRAI": 0b0100000}


def encode_i(op, rd, rs1, imm):
    """Encode an I-type (OP-IMM) instruction word for the given mnemonic."""
    opcode = 0b0010011  # OP_IMM
    return (
        ((imm & 0xFFF) << 20)  # 12-bit immediate, two's complement
        | (rs1 << 15)
        | (F3_I[op] << 12)
        | (rd << 7)
        | opcode
    )


def encode_shift_i(op, rd, rs1, shamt):
    """Encode a shift-immediate (SLLI/SRLI/SRAI) instruction word."""
    opcode = 0b0010011  # OP_IMM
    return (
        (F7_I[op] << 25)
        | ((shamt & 0x1F) << 20)
        | (rs1 << 15)
        | (F3_I[op] << 12)
        | (rd << 7)
        | opcode
    )


# opcodes for U-type ops
OPCODE_U = {"LUI": 0b0110111, "AUIPC": 0b0010111}


def encode_u(op, rd, imm20):
    """Encode a U-type instruction word. imm20 is the 20-bit upper immediate."""
    return ((imm20 & 0xFFFFF) << 12) | (rd << 7) | OPCODE_U[op]


def run_u(op, imm20, pc=0, rd=3):
    """Execute a U-type op at the given pc; return the value written to rd."""
    cpu = RISC_V()
    cpu.pc = pc
    cpu.decode_instruction(encode_u(op, rd, imm20))
    return cpu.registers[rd]


# funct3 selectors for B-type (branch) ops
F3_B = {"BEQ": 0b000, "BNE": 0b001, "BLT": 0b100,
        "BGE": 0b101, "BLTU": 0b110, "BGEU": 0b111}


def encode_b(op, rs1, rs2, imm):
    """Encode a B-type branch instruction. imm is the signed byte offset."""
    opcode = 0b1100011  # OP_BRANCH
    imm &= 0x1FFF  # 13-bit two's complement; bit 0 is dropped on encode
    return (
        (((imm >> 12) & 0x1) << 31)   # imm[12]
        | (((imm >> 5) & 0x3F) << 25)  # imm[10:5]
        | (rs2 << 20)
        | (rs1 << 15)
        | (F3_B[op] << 12)
        | (((imm >> 1) & 0xF) << 8)    # imm[4:1]
        | (((imm >> 11) & 0x1) << 7)   # imm[11]
        | opcode
    )


def run_branch(op, a, b, imm, pc=0x1000, rs1=1, rs2=2):
    """Set pc and rs1/rs2; execute branch; return the resulting pc."""
    cpu = RISC_V()
    cpu.pc = pc
    cpu.registers[rs1] = a & 0xFFFFFFFF
    cpu.registers[rs2] = b & 0xFFFFFFFF
    cpu.decode_instruction(encode_b(op, rs1, rs2, imm))
    return cpu.pc


def encode_jal(rd, imm):
    """Encode a JAL (J-type) instruction. imm is the signed byte offset."""
    opcode = 0b1101111  # OP_JAL
    imm &= 0x1FFFFF  # 21-bit two's complement; bit 0 is dropped on encode
    return (
        (((imm >> 20) & 0x1) << 31)    # imm[20]
        | (((imm >> 1) & 0x3FF) << 21)  # imm[10:1]
        | (((imm >> 11) & 0x1) << 20)   # imm[11]
        | (((imm >> 12) & 0xFF) << 12)  # imm[19:12]
        | (rd << 7)
        | opcode
    )


def run_jal(imm, pc=0x1000, rd=1):
    """Execute JAL at the given pc; return (resulting pc, link register value)."""
    cpu = RISC_V()
    cpu.pc = pc
    cpu.decode_instruction(encode_jal(rd, imm))
    return cpu.pc, cpu.registers[rd]


def encode_jalr(rd, rs1, imm):
    """Encode a JALR (I-type) instruction. imm is the signed 12-bit offset."""
    opcode = 0b1100111  # OP_JALR, funct3 = 000
    return (((imm & 0xFFF) << 20) | (rs1 << 15) | (rd << 7) | opcode)


def run_jalr(base, imm, pc=0x1000, rd=1, rs1=2):
    """Set rs1=base; execute JALR at pc; return (resulting pc, link value)."""
    cpu = RISC_V()
    cpu.pc = pc
    cpu.registers[rs1] = base & 0xFFFFFFFF
    cpu.decode_instruction(encode_jalr(rd, rs1, imm))
    return cpu.pc, cpu.registers[rd]


def run_shift_imm(op, a, shamt, rd=3, rs1=1):
    """Load a into rs1; execute shift-immediate op; return value written to rd."""
    cpu = RISC_V()
    cpu.registers[rs1] = a & 0xFFFFFFFF
    cpu.decode_instruction(encode_shift_i(op, rd, rs1, shamt))
    return cpu.registers[rd]


def run_imm(op, a, imm, rd=3, rs1=1):
    """Load a into rs1; execute op with immediate imm; return value written to rd."""
    cpu = RISC_V()
    cpu.registers[rs1] = a & 0xFFFFFFFF
    cpu.decode_instruction(encode_i(op, rd, rs1, imm))
    return cpu.registers[rd]


class TestADD(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(run_op("ADD", 2, 3), 5)

    def test_with_zero(self):
        self.assertEqual(run_op("ADD", 0, 7), 7)

    def test_negative_operand(self):
        # (-1) + 1 == 0  (using 32-bit two's complement input)
        self.assertEqual(run_op("ADD", -1, 1) & 0xFFFFFFFF, 0)


class TestSUB(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(run_op("SUB", 10, 3), 7)

    def test_zero_result(self):
        self.assertEqual(run_op("SUB", 5, 5), 0)

    def test_negative_result(self):
        # 3 - 5 == -2  -> 0xFFFFFFFE in 32-bit two's complement
        self.assertEqual(run_op("SUB", 3, 5) & 0xFFFFFFFF, 0xFFFFFFFE)


class TestSLT(unittest.TestCase):
    def test_less_than(self):
        self.assertEqual(run_op("SLT", 1, 2), 1)

    def test_not_less_than(self):
        self.assertEqual(run_op("SLT", 2, 1), 0)

    def test_equal(self):
        self.assertEqual(run_op("SLT", 4, 4), 0)

    def test_signed_negative_less_than_positive(self):
        # -1 < 1 should be true under signed comparison
        self.assertEqual(run_op("SLT", -1, 1), 1)


class TestSLTU(unittest.TestCase):
    def test_less_than(self):
        self.assertEqual(run_op("SLTU", 1, 2), 1)

    def test_not_less_than(self):
        self.assertEqual(run_op("SLTU", 2, 1), 0)

    def test_unsigned_large_not_less_than(self):
        # -1 as unsigned is 0xFFFFFFFF, which is NOT < 1
        self.assertEqual(run_op("SLTU", -1, 1), 0)


class TestXOR(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(run_op("XOR", 0b1100, 0b1010), 0b0110)

    def test_identical_operands_zero(self):
        self.assertEqual(run_op("XOR", 0xABCD, 0xABCD), 0)

    def test_with_zero_identity(self):
        self.assertEqual(run_op("XOR", 0x1234, 0), 0x1234)


class TestOR(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(run_op("OR", 0b1100, 0b1010), 0b1110)

    def test_with_zero_identity(self):
        self.assertEqual(run_op("OR", 0x1234, 0), 0x1234)

    def test_all_ones(self):
        self.assertEqual(run_op("OR", 0xFFFFFFFF, 0x0F0F0F0F), 0xFFFFFFFF)


class TestAND(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(run_op("AND", 0b1100, 0b1010), 0b1000)

    def test_with_zero_clears(self):
        self.assertEqual(run_op("AND", 0x1234, 0), 0)

    def test_mask(self):
        self.assertEqual(run_op("AND", 0xABCD, 0x00FF), 0x00CD)


class TestSRL(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(run_op("SRL", 0b1000, 2), 0b0010)

    def test_zero_fills_top(self):
        # logical shift: sign bit is NOT preserved, top fills with 0
        self.assertEqual(run_op("SRL", 0x80000000, 4), 0x08000000)

    def test_shift_amount_masked_to_5_bits(self):
        # shamt uses only low 5 bits, so 32 wraps to 0 (no shift)
        self.assertEqual(run_op("SRL", 0x1234, 32), 0x1234)

    def test_shift_by_zero(self):
        self.assertEqual(run_op("SRL", 0xDEAD, 0), 0xDEAD)


class TestSRA(unittest.TestCase):
    def test_positive_same_as_logical(self):
        self.assertEqual(run_op("SRA", 0b1000, 2), 0b0010)

    def test_negative_sign_extends(self):
        # -8 >> 1 == -4  -> 0xFFFFFFFC in 32-bit two's complement
        self.assertEqual(run_op("SRA", -8, 1) & 0xFFFFFFFF, 0xFFFFFFFC)

    def test_all_ones_stays_all_ones(self):
        # 0xFFFFFFFF is -1; arithmetic shift of -1 is still -1
        self.assertEqual(run_op("SRA", 0xFFFFFFFF, 8), 0xFFFFFFFF)

    def test_shift_amount_masked_to_5_bits(self):
        self.assertEqual(run_op("SRA", 0x1234, 32), 0x1234)


class TestSLL(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(run_op("SLL", 0b0001, 4), 0b10000)

    def test_shift_into_top_bit(self):
        self.assertEqual(run_op("SLL", 0x1, 31), 0x80000000)

    def test_overflow_truncates(self):
        # bit shifted past bit 31 is dropped, not clamped
        self.assertEqual(run_op("SLL", 0x80000000, 1), 0x0)

    def test_shift_amount_masked_to_5_bits(self):
        # shamt uses only low 5 bits, so 32 wraps to 0 (no shift)
        self.assertEqual(run_op("SLL", 0x1234, 32), 0x1234)

    def test_shift_by_zero(self):
        self.assertEqual(run_op("SLL", 0xDEAD, 0), 0xDEAD)


class TestADDI(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(run_imm("ADDI", 2, 3), 5)

    def test_negative_immediate(self):
        self.assertEqual(run_imm("ADDI", 10, -1), 9)

    def test_negative_immediate_wraps(self):
        # 0 + (-1) -> 0xFFFFFFFF in 32-bit two's complement
        self.assertEqual(run_imm("ADDI", 0, -1), 0xFFFFFFFF)

    def test_immediate_zero(self):
        self.assertEqual(run_imm("ADDI", 0x1234, 0), 0x1234)


class TestSLTI(unittest.TestCase):
    def test_less_than(self):
        self.assertEqual(run_imm("SLTI", 1, 2), 1)

    def test_not_less_than(self):
        self.assertEqual(run_imm("SLTI", 2, 1), 0)

    def test_signed_register_less_than(self):
        # reg holds 0xFFFFFFFF (= -1 signed); -1 < 0 is true
        self.assertEqual(run_imm("SLTI", 0xFFFFFFFF, 0), 1)

    def test_signed_negative_immediate(self):
        # 5 < -1 is false under signed comparison
        self.assertEqual(run_imm("SLTI", 5, -1), 0)


class TestSLTIU(unittest.TestCase):
    def test_less_than(self):
        self.assertEqual(run_imm("SLTIU", 1, 2), 1)

    def test_not_less_than(self):
        self.assertEqual(run_imm("SLTIU", 2, 1), 0)

    def test_large_unsigned_not_less_than(self):
        # reg holds 0xFFFFFFFF (max unsigned); NOT < 1 under unsigned compare
        self.assertEqual(run_imm("SLTIU", 0xFFFFFFFF, 1), 0)

    def test_sign_extended_immediate_compared_unsigned(self):
        # imm -1 sign-extends to 0xFFFFFFFF; 5 < 0xFFFFFFFF is true
        self.assertEqual(run_imm("SLTIU", 5, -1), 1)


class TestXORI(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(run_imm("XORI", 0b1100, 0b1010), 0b0110)

    def test_with_zero_identity(self):
        self.assertEqual(run_imm("XORI", 0x1234, 0), 0x1234)

    def test_not_idiom(self):
        # xori rd, rs1, -1 is bitwise NOT: ~0 -> 0xFFFFFFFF
        self.assertEqual(run_imm("XORI", 0, -1), 0xFFFFFFFF)
        self.assertEqual(run_imm("XORI", 0x0F0F0F0F, -1), 0xF0F0F0F0)


class TestORI(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(run_imm("ORI", 0b1100, 0b1010), 0b1110)

    def test_with_zero_identity(self):
        self.assertEqual(run_imm("ORI", 0x1234, 0), 0x1234)

    def test_negative_immediate_sets_high_bits(self):
        # imm -1 sign-extends to 0xFFFFFFFF; OR sets every bit
        self.assertEqual(run_imm("ORI", 0x1234, -1), 0xFFFFFFFF)


class TestANDI(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(run_imm("ANDI", 0b1100, 0b1010), 0b1000)

    def test_with_zero_clears(self):
        self.assertEqual(run_imm("ANDI", 0x1234, 0), 0)

    def test_negative_immediate_preserves(self):
        # imm -1 sign-extends to 0xFFFFFFFF; AND is identity
        self.assertEqual(run_imm("ANDI", 0xABCD, -1), 0xABCD)

    def test_low_byte_mask(self):
        self.assertEqual(run_imm("ANDI", 0xABCD, 0xFF), 0xCD)


class TestSLLI(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(run_shift_imm("SLLI", 0b0001, 4), 0b10000)

    def test_shift_into_top_bit(self):
        self.assertEqual(run_shift_imm("SLLI", 0x1, 31), 0x80000000)

    def test_overflow_truncates(self):
        self.assertEqual(run_shift_imm("SLLI", 0x80000000, 1), 0x0)

    def test_shift_by_zero(self):
        self.assertEqual(run_shift_imm("SLLI", 0xDEAD, 0), 0xDEAD)


class TestSRLI(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(run_shift_imm("SRLI", 0b1000, 2), 0b0010)

    def test_zero_fills_top(self):
        # logical shift: sign bit NOT preserved
        self.assertEqual(run_shift_imm("SRLI", 0x80000000, 4), 0x08000000)

    def test_shift_by_zero(self):
        self.assertEqual(run_shift_imm("SRLI", 0xDEAD, 0), 0xDEAD)


class TestSRAI(unittest.TestCase):
    def test_positive_same_as_logical(self):
        self.assertEqual(run_shift_imm("SRAI", 0b1000, 2), 0b0010)

    def test_negative_sign_extends(self):
        # -8 >> 1 == -4 -> 0xFFFFFFFC
        self.assertEqual(run_shift_imm("SRAI", 0xFFFFFFF8, 1), 0xFFFFFFFC)

    def test_all_ones_stays_all_ones(self):
        # 0xFFFFFFFF is -1; arithmetic shift of -1 is still -1
        self.assertEqual(run_shift_imm("SRAI", 0xFFFFFFFF, 8), 0xFFFFFFFF)


class TestLUI(unittest.TestCase):
    def test_basic(self):
        # imm goes into the upper 20 bits; low 12 bits are zero
        self.assertEqual(run_u("LUI", 0x12345), 0x12345000)

    def test_zero(self):
        self.assertEqual(run_u("LUI", 0x00000), 0x0)

    def test_top_bit_set(self):
        # LUI does not sign-extend; it just places the bits
        self.assertEqual(run_u("LUI", 0xFFFFF), 0xFFFFF000)


class TestAUIPC(unittest.TestCase):
    def test_adds_to_pc(self):
        self.assertEqual(run_u("AUIPC", 0x1, pc=0x1000), 0x1000 + 0x1000)

    def test_pc_zero_same_as_lui(self):
        self.assertEqual(run_u("AUIPC", 0x12345, pc=0), 0x12345000)

    def test_wraps_to_32_bits(self):
        # 0xFFFFF000 + 0x2000 overflows 32 bits and wraps
        self.assertEqual(run_u("AUIPC", 0xFFFFF, pc=0x2000), 0x1000)


PC = 0x1000  # base pc used by run_branch


class TestBEQ(unittest.TestCase):
    def test_taken(self):
        self.assertEqual(run_branch("BEQ", 5, 5, 0x40), PC + 0x40)

    def test_not_taken(self):
        self.assertEqual(run_branch("BEQ", 5, 6, 0x40), PC + 4)


class TestBNE(unittest.TestCase):
    def test_taken(self):
        self.assertEqual(run_branch("BNE", 5, 6, 0x40), PC + 0x40)

    def test_not_taken(self):
        self.assertEqual(run_branch("BNE", 5, 5, 0x40), PC + 4)


class TestBLT(unittest.TestCase):
    def test_taken(self):
        self.assertEqual(run_branch("BLT", 1, 2, 0x40), PC + 0x40)

    def test_not_taken_equal(self):
        self.assertEqual(run_branch("BLT", 2, 2, 0x40), PC + 4)

    def test_signed_negative_less_than_positive(self):
        # -1 < 1 under signed comparison -> taken
        self.assertEqual(run_branch("BLT", -1, 1, 0x40), PC + 0x40)


class TestBGE(unittest.TestCase):
    def test_taken_greater(self):
        self.assertEqual(run_branch("BGE", 2, 1, 0x40), PC + 0x40)

    def test_taken_equal(self):
        # >= must branch when equal
        self.assertEqual(run_branch("BGE", 2, 2, 0x40), PC + 0x40)

    def test_not_taken(self):
        self.assertEqual(run_branch("BGE", 1, 2, 0x40), PC + 4)


class TestBLTU(unittest.TestCase):
    def test_taken(self):
        self.assertEqual(run_branch("BLTU", 1, 2, 0x40), PC + 0x40)

    def test_large_unsigned_not_less(self):
        # 0xFFFFFFFF is max unsigned, NOT < 1 -> not taken
        self.assertEqual(run_branch("BLTU", 0xFFFFFFFF, 1, 0x40), PC + 4)


class TestBGEU(unittest.TestCase):
    def test_taken_equal(self):
        self.assertEqual(run_branch("BGEU", 5, 5, 0x40), PC + 0x40)

    def test_large_unsigned_taken(self):
        # 0xFFFFFFFF >= 1 unsigned -> taken
        self.assertEqual(run_branch("BGEU", 0xFFFFFFFF, 1, 0x40), PC + 0x40)

    def test_not_taken(self):
        self.assertEqual(run_branch("BGEU", 1, 2, 0x40), PC + 4)


class TestBranchOffset(unittest.TestCase):
    def test_backward_negative_offset(self):
        # taken branch with negative offset jumps backward (loop case)
        self.assertEqual(run_branch("BEQ", 5, 5, -0x20), PC - 0x20)

    def test_offset_is_even(self):
        # smallest nonzero offset is 2 (bit 0 always 0)
        self.assertEqual(run_branch("BEQ", 5, 5, 2), PC + 2)


class TestJAL(unittest.TestCase):
    def test_forward_jump(self):
        pc, _ = run_jal(0x40, pc=0x1000)
        self.assertEqual(pc, 0x1000 + 0x40)

    def test_link_is_pc_plus_4(self):
        _, link = run_jal(0x40, pc=0x1000)
        self.assertEqual(link, 0x1000 + 4)

    def test_backward_jump(self):
        pc, link = run_jal(-0x20, pc=0x1000)
        self.assertEqual(pc, 0x1000 - 0x20)
        self.assertEqual(link, 0x1000 + 4)

    def test_discard_link_with_x0(self):
        # jal x0, offset is a plain jump; x0 must stay 0
        cpu = RISC_V()
        cpu.pc = 0x1000
        cpu.decode_instruction(encode_jal(0, 0x40))
        self.assertEqual(cpu.pc, 0x1000 + 0x40)
        self.assertEqual(cpu.registers[0], 0)

    def test_large_offset(self):
        # exercises the imm[19:12] field of the scrambled immediate
        pc, _ = run_jal(0x1F000, pc=0x1000)
        self.assertEqual(pc, 0x1000 + 0x1F000)


class TestJALR(unittest.TestCase):
    def test_jump_to_register_target(self):
        # target = rs1 + imm
        pc, _ = run_jalr(0x2000, 0x40, pc=0x1000)
        self.assertEqual(pc, 0x2040)

    def test_link_is_pc_plus_4(self):
        _, link = run_jalr(0x2000, 0x40, pc=0x1000)
        self.assertEqual(link, 0x1000 + 4)

    def test_negative_immediate(self):
        pc, _ = run_jalr(0x2000, -0x10, pc=0x1000)
        self.assertEqual(pc, 0x2000 - 0x10)

    def test_lsb_is_cleared(self):
        # rs1 + imm produces an odd address; JALR forces it even
        pc, _ = run_jalr(0x2001, 0, pc=0x1000)
        self.assertEqual(pc, 0x2000)

    def test_rd_equals_rs1(self):
        # jalr x1, x1, 0 : must read rs1's old value before overwriting it
        cpu = RISC_V()
        cpu.pc = 0x1000
        cpu.registers[1] = 0x2000
        cpu.decode_instruction(encode_jalr(1, 1, 0x40))
        self.assertEqual(cpu.pc, 0x2040)       # used old rs1, not the new link
        self.assertEqual(cpu.registers[1], 0x1004)  # link written after

    def test_ret_idiom_discards_link(self):
        # jalr x0, ra, 0 is `ret`; x0 stays 0, pc jumps to ra
        cpu = RISC_V()
        cpu.pc = 0x1000
        cpu.registers[2] = 0x500   # ra in rs1=2
        cpu.decode_instruction(encode_jalr(0, 2, 0))
        self.assertEqual(cpu.pc, 0x500)
        self.assertEqual(cpu.registers[0], 0)


class TestX0Hardwired(unittest.TestCase):
    def test_alu_write_to_x0_ignored(self):
        # add x0, x1, x2 must not change x0
        cpu = RISC_V()
        cpu.registers[1] = 5
        cpu.registers[2] = 7
        cpu.decode_instruction(encode_r("ADD", 0, 1, 2))
        self.assertEqual(cpu.registers[0], 0)

    def test_addi_write_to_x0_ignored(self):
        cpu = RISC_V()
        cpu.decode_instruction(encode_i("ADDI", 0, 1, 42))
        self.assertEqual(cpu.registers[0], 0)


if __name__ == "__main__":
    unittest.main()
