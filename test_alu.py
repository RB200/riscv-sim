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
        "XORI": 0b100, "ORI": 0b110, "ANDI": 0b111}


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


if __name__ == "__main__":
    unittest.main()
