import unittest

from main import RISC_V

# funct3 / funct7 selectors for R-type ALU ops
F3 = {
    "ADD": 0b000, "SUB": 0b000, "SLT": 0b010, "SLTU": 0b011,
    "XOR": 0b100, "OR": 0b110, "AND": 0b111,
}
F7 = {
    "ADD": 0b0000000, "SUB": 0b0100000, "SLT": 0b0000000, "SLTU": 0b0000000,
    "XOR": 0b0000000, "OR": 0b0000000, "AND": 0b0000000,
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


if __name__ == "__main__":
    unittest.main()
