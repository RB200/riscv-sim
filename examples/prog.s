.section .text
.globl _start
_start:
    li   a0, 5         # x10 = 5
    li   a1, 7         # x11 = 7
    add  a2, a0, a1    # x12 = 12
    ebreak

