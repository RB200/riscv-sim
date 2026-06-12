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
                    self.registers[rd] = a + b
                    print("add")
                    pass
                elif funct7 == 0b100000:
                    self.registers[rd] = a - b
                    print("sub")
                    pass
            
            elif funct3 == 0b001:
                # SLL
                    
                self.registers[rd] = (a << (b & 0x1F)) & 0xFFFFFFFF
                print("SLL")

            elif funct3 == 0b010:  # SLT (signed)
                self.registers[rd] = 1 if to_signed(a) < to_signed(b) else 0

            elif funct3 == 0b011:  # SLTU (unsigned)
                if a == x0 and b != 0: # edge case as per sec 2.4.2 of spec
                    self.registers[rd] = 1
                self.registers[rd] = 1 if a < b else 0
            
            elif funct3 == 0b100:
                self.registers[rd] = a ^ b
                print("XOR")
            
            elif funct3 == 0b101:
                shamt = b & 0x1F    # shift amount = low 5 bits of rs2
                if funct7 == 0:
                    # SRL
                    self.registers[rd] = (a >> shamt) & 0xFFFFFFFF
                    print("SRL")
                elif funct7 == 0b0100000:
                    # SRA
                    self.registers[rd] = (to_signed(a) >> shamt) & 0xFFFFFFFF
                    print("SRA")
                    
            elif funct3 == 0b110:
                # OR
                self.registers[rd] = a | b
                print("OR")
            
            elif funct3 == 0b111:
                self.registers[rd] = a & b
                # AND
                print("AND")
            