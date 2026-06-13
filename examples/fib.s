.section .text
.globl _start
_start:
    li   a0, 10        # n: which Fibonacci number to compute
    li   t0, 0         # prev = fib(0) = 0
    li   t1, 1         # curr = fib(1) = 1
    li   t2, 0         # i = 0

loop:
    bge  t2, a0, done  # if i >= n, stop
    add  t3, t0, t1    # next = prev + curr
    mv   t0, t1        # prev = curr
    mv   t1, t3        # curr = next
    addi t2, t2, 1     # i += 1
    j    loop

done:
    mv   a0, t0        # result = prev = fib(n)  -> a0 (x10)
    ebreak
