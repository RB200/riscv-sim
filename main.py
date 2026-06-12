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

class RISC_V:
    def __init__(self):
        self.pc = 0
        self.registers = [0] * 32
        
    def decode_instruction(self, instr):
        opcode = instr & 0x7F 
        
        if opcode == OP_REG:
            funct3 = (instr >> 12) & 0x07
            funct7 = (instr >> 25) & 0x7F
            if funct3 == 0:
                if funct7 == 0:
                    # add
                    print("add")
                    pass
                elif funct7 == 32:
                    # sub
                    print("sub")
                    pass
            

r = RISC_V()
sub = 0b01000000000000000000000000110011
add = 0b00000000000000000000000000110011
r.decode_instruction(sub)
r.decode_instruction(add)
