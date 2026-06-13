# riscv-sim

A small **RV32I** instruction-set simulator written in pure Python. It decodes and
executes the base 32-bit RISC-V integer instruction set, runs real binaries produced
by a standard toolchain (LLVM/clang), and ships with a thorough unit-test suite.

No dependencies — just the Python standard library.

## Features

- Full **RV32I** base integer instruction set:
  - **Register/register (R-type):** `ADD` `SUB` `SLL` `SLT` `SLTU` `XOR` `SRL` `SRA` `OR` `AND`
  - **Register/immediate (I-type):** `ADDI` `SLTI` `SLTIU` `XORI` `ORI` `ANDI` `SLLI` `SRLI` `SRAI`
  - **Upper immediate (U-type):** `LUI` `AUIPC`
  - **Branches (B-type):** `BEQ` `BNE` `BLT` `BGE` `BLTU` `BGEU`
  - **Jumps:** `JAL` `JALR`
  - **Loads (I-type):** `LB` `LH` `LW` `LBU` `LHU`
  - **Stores (S-type):** `SB` `SH` `SW`
  - **System / fence:** `ECALL` `EBREAK` `FENCE`
- Correct 32-bit semantics: two's-complement wraparound, signed vs. unsigned
  comparisons, sign-/zero-extension on sub-word loads, little-endian memory.
- `x0` hardwired to zero, 1 MB of byte-addressable memory.
- A fetch–decode–execute loop that runs flat program images until `ECALL`/`EBREAK`.
- 130+ unit tests covering every instruction, including edge cases.

## Requirements

- **Python 3.11+** (uses `int.from_bytes`/`to_bytes` with default byte order).
- To build your own programs: a RISC-V–capable toolchain. On macOS with Homebrew:
  ```bash
  brew install llvm lld
  ```

## Quick start

Run the included Fibonacci example:

```bash
python3 -c "from main import RISC_V; \
  c = RISC_V(); c.load(open('examples/fib.bin','rb').read()); \
  print(c.run()); print('fib(10) =', c.registers[10])"
```

```
EBREAK
fib(10) = 55
```

## Usage

```python
from main import RISC_V

cpu = RISC_V()                       # use RISC_V(debug=True) to trace instructions
cpu.load(open("prog.bin", "rb").read())   # load a flat binary at address 0
reason = cpu.run()                   # runs until ECALL/EBREAK; returns the reason
print(reason)                        # -> "ECALL" or "EBREAK"
print(cpu.registers)                 # inspect the register file
```

### API

| Member | Description |
|--------|-------------|
| `RISC_V(debug=False)` | Construct a CPU. `debug=True` prints each instruction as it runs. |
| `cpu.load(data, addr=0)` | Copy a flat program image into memory and set `pc`. |
| `cpu.run()` | Fetch–decode–execute until halted; returns `"ECALL"` / `"EBREAK"`. |
| `cpu.decode_instruction(instr)` | Execute a single 32-bit instruction word. |
| `cpu.registers` | The 32-entry register file (`x0`–`x31`). |
| `cpu.pc` | The program counter. |
| `cpu.memory` | 1 MB `bytearray` of system memory. |

## Building a program from assembly

Write RV32I assembly (see [`examples/fib.s`](examples/fib.s)), then compile it to a
flat binary. Programs are loaded at address `0`, and execution starts at `pc = 0`, so
the entry point must be first. End programs with `ebreak` to halt the simulator.

```bash
LLVM=/opt/homebrew/opt/llvm/bin
$LLVM/clang --target=riscv32 -march=rv32i -nostdlib \
  -fuse-ld=/opt/homebrew/opt/lld/bin/ld.lld \
  -Wl,--image-base=0 -Wl,-Ttext=0 -Wl,-e,_start examples/fib.s -o examples/fib.elf
$LLVM/llvm-objcopy -O binary examples/fib.elf examples/fib.bin
```

The pipeline: assembly → ELF (`clang`) → flat binary (`objcopy`) → loaded into memory.
`objcopy -O binary` strips the ELF metadata, leaving just the raw instruction bytes
that `cpu.load()` expects.

## Running the tests

```bash
python3 -m unittest test_alu -v
```

The suite hand-encodes each instruction (R/I/S/B/U/J formats), executes it, and
checks the resulting registers, memory, or PC — including store→load round-trips and
signed/unsigned edge cases.

## Project layout

| File | Purpose |
|------|---------|
| `main.py` | The simulator: instruction decode/execute, memory, and the run loop. |
| `test_alu.py` | Unit tests and instruction encoders for every RV32I instruction. |
| `examples/fib.s` | Example program: iterative Fibonacci. |
| `examples/prog.s` | Example program: a minimal add. |

## Not (yet) implemented

- Extensions beyond base integer: **M** (mul/div), **A** (atomics), **C** (compressed), floating point.
- ELF loading (only flat binaries), CSRs, traps/interrupts, and a real syscall ABI
  (`ECALL`/`EBREAK` currently just halt the machine).
