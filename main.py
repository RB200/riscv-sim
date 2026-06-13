memory = bytearray(1024 * 1024)

# opcodes
OP_LUI    = 0b0110111
OP_AUIPC  = 0b0010111
OP_JAL    = 0b1101111
OP_JALR   = 0b1100111
OP_BRANCH = 0b1100011
OP_LOAD   = 0b0000011
OP_STORE  = 0b0100011
OP_IMM    = 0b0010011
OP_REG    = 0b0110011
OP_FENCE  = 0b0001111
OP_SYSTEM = 0b1110011

x0 = 0
def to_signed(val, bits=32):
    if val & (1 << (bits - 1)):
        return val - (1 << bits)
    return val
class RISC_V:
    def __init__(self):
        self.pc = 0
        self.registers = [0] * 32

    def write_reg(self, rd, val):
        if rd != 0:                              # x0 is hardwired to zero
            self.registers[rd] = val & 0xFFFFFFFF  # store as 32-bit unsigned

    def decode_instruction(self, instr):
        opcode = instr & 0x7F

        if opcode == OP_REG:
            funct3 = (instr >> 12) & 0x07
            funct7 = (instr >> 25) & 0x7F
            rs1 = (instr >> 15) & 0x1F
            rs2 = (instr >> 20) & 0x1F
            rd = (instr >> 7) & 0x1F


            a = self.registers[rs1]
            b = self.registers[rs2]

            if funct3 == 0b000:
                if funct7 == 0:
                    self.write_reg(rd, a + b)
                    print("add")
                elif funct7 == 0b100000:
                    self.write_reg(rd, a - b)
                    print("sub")

            elif funct3 == 0b001:
                # SLL
                self.write_reg(rd, a << (b & 0x1F))
                print("SLL")

            elif funct3 == 0b010:  # SLT (signed)
                self.write_reg(rd, 1 if to_signed(a) < to_signed(b) else 0)

            elif funct3 == 0b011:  # SLTU (unsigned)
                self.write_reg(rd, 1 if a < b else 0)

            elif funct3 == 0b100:
                self.write_reg(rd, a ^ b)
                print("XOR")

            elif funct3 == 0b101:
                shamt = b & 0x1F    # shift amount = low 5 bits of rs2
                if funct7 == 0:
                    # SRL
                    self.write_reg(rd, a >> shamt)
                    print("SRL")
                elif funct7 == 0b0100000:
                    # SRA
                    self.write_reg(rd, to_signed(a) >> shamt)
                    print("SRA")

            elif funct3 == 0b110:
                # OR
                self.write_reg(rd, a | b)
                print("OR")

            elif funct3 == 0b111:
                # AND
                self.write_reg(rd, a & b)
                print("AND")

        elif opcode == OP_IMM:
            imm = to_signed((instr >> 20) & 0xFFF, 12) # sign-extend 12-bit immediate value
            rs1 = (instr >> 15) & 0x1F
            funct3 = (instr >> 12) & 0x07
            funct7 = (instr >> 25) & 0x7F
            shamt = (instr >> 20) & 0x1F
            rd = (instr >> 7) & 0x1F

            a = self.registers[rs1]

            if funct3 == 0b000:
                # ADDI
                self.write_reg(rd, a + imm)
                print("ADDI")

            elif funct3 == 0b010:
                # SLTI
                self.write_reg(rd, 1 if to_signed(a) < imm else 0)
                print("SLTI")

            elif funct3 == 0b011:
                # SLTIU
                self.write_reg(rd, 1 if a < (imm & 0xFFFFFFFF) else 0)
                print("SLTIU")

            elif funct3 == 0b100:
                # XORI
                self.write_reg(rd, a ^ imm)
                print("XORI")

            elif funct3 == 0b110:
                # ORI
                self.write_reg(rd, a | imm)
                print("ORI")

            elif funct3 == 0b111:
                # ANDI
                self.write_reg(rd, a & imm)
                print("ANDI")

            elif funct3 == 0b001:
                # SLLI
                self.write_reg(rd, a << shamt)
                print("SLLI")

            elif funct3 == 0b101:
                if funct7 == 0:
                    # SRLI
                    self.write_reg(rd, a >> shamt)
                    print("SRLI")
                elif funct7 == 0b0100000:
                    # SRAI
                    self.write_reg(rd, to_signed(a) >> shamt)
                    print("SRAI")

        elif opcode == OP_LUI:
            imm = instr & 0xFFFFF000
            rd = (instr >> 7) & 0x1F

            self.write_reg(rd, imm)

        elif opcode == OP_AUIPC:
            imm = instr & 0xFFFFF000
            rd = (instr >> 7) & 0x1F
            self.write_reg(rd, self.pc + imm)

        elif opcode == OP_BRANCH:
            imm = (
                ((instr >> 31) & 0x1)  << 12 |   # imm[12]  <- sign bit
                ((instr >> 7)  & 0x1)  << 11 |   # imm[11]
                ((instr >> 25) & 0x3F) << 5  |   # imm[10:5]
                ((instr >> 8)  & 0xF)  << 1      # imm[4:1]
            )                                     # imm[0] is always 0
            imm = to_signed(imm, 13)
            rs2 = (instr >> 20) & 0x1F
            rs1 = (instr >> 15) & 0x1F
            funct3 = (instr >> 12) & 0x07

            a = self.registers[rs1]
            b = self.registers[rs2]

            taken = False
            if funct3 == 0:
                # BEQ
                taken = (a == b)
            elif funct3 == 0b001:
                # BNE
                taken = (a != b)
            elif funct3 == 0b100:
                # BLT
                taken = (to_signed(a) < to_signed(b))
            elif funct3 == 0b101:
                # BGE
                taken = (to_signed(a) >= to_signed(b))
            elif funct3 == 0b110:
                # BLTU
                taken = (a < b)
            elif funct3 == 0b111:
                # BGEU
                taken = (a >= b)

            if taken:
                self.pc = (self.pc + imm) & 0xFFFFFFFF   # jump
            else:
                self.pc = (self.pc + 4) & 0xFFFFFFFF      # fall through

        elif opcode == OP_JAL:
            imm = (
                ((instr >> 31) & 0x1)   << 20 |   # imm[20]  <- sign bit
                ((instr >> 12) & 0xFF)  << 12 |   # imm[19:12]
                ((instr >> 20) & 0x1)   << 11 |   # imm[11]
                ((instr >> 21) & 0x3FF) << 1      # imm[10:1]
            )                                      # imm[0] = 0
            imm = to_signed(imm, 21)
            rd = (instr >> 7) & 0x1F

            self.write_reg(rd, self.pc + 4)       # link: save return address
            self.pc = (self.pc + imm) & 0xFFFFFFFF
