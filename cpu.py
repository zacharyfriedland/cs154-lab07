# Zach Friedland
# Homework Buddy: Peter Brede
import pyrtl

rf = pyrtl.MemBlock(bitwidth=32, addrwidth=5, name = 'rf', asynchronous=True, max_read_ports=3, max_write_ports=None)
i_mem = pyrtl.MemBlock(bitwidth=32, addrwidth=32, name = 'i_mem')
d_mem = pyrtl.MemBlock(bitwidth=32, addrwidth=32, name = 'd_mem', asynchronous=True)

# Declare one 32-bit data input: instr
instr = pyrtl.WireVector(bitwidth=32, name='instr')
PC = pyrtl.Register(bitwidth=32)

bMux = pyrtl.WireVector(bitwidth=32, name='bMux')
PC.next <<= bMux

instr <<= i_mem[PC]



# initialize wire vectors
op = pyrtl.WireVector(bitwidth=6, name='op')
rs = pyrtl.WireVector(bitwidth=5, name='rs')
rt = pyrtl.WireVector(bitwidth=5, name='rt')
rd = pyrtl.WireVector(bitwidth=5, name='rd')
sh = pyrtl.WireVector(bitwidth=5, name='sh')
func = pyrtl.WireVector(bitwidth=6, name='func')
alu_out = pyrtl.WireVector(bitwidth=32, name='alu_out')
imm = pyrtl.WireVector(bitwidth=16, name='imm')

# INSTRUCTION DECODE LOGIC
op <<= instr[26:32]
rs <<= instr[21:26]
rt <<= instr[16:21]
rd <<= instr[11:16]
sh <<= instr[6:11]
func <<= instr[0:6]
imm <<= instr[0:16]

# set wires
data0 = pyrtl.WireVector(bitwidth=32, name='data0')
data1 = pyrtl.WireVector(bitwidth=32, name='data1')
alu_in = pyrtl.WireVector(bitwidth=32, name='alu_in')
writeToReg = pyrtl.WireVector(bitwidth=32, name='writeToReg')
branch = pyrtl.WireVector(bitwidth=32, name='branch')
zeroExt = pyrtl.WireVector(bitwidth=1, name='zeroExt')

data0 <<= rf[rs]
data1 <<= rf[rt]



# set control wire
control = pyrtl.WireVector(bitwidth=10, name='control')
with pyrtl.conditional_assignment:
   # R-Types
   with op == 0x00:
      # add
      with func == 0x20:
         control |= 0x280
      # and
      with func == 0x24:
         control |= 0x281
      # slt
      with func == 0x2A:
         control |= 0x282
   # lui
   with op == 0x0F:
      control |= 0x0A5
   # addi
   with op == 0x08:
      control |= 0x0A0
   # ori
   with op == 0x0D:
      control |= 0x0C4
   # lw
   with op == 0x23:
      control |= 0x0A8
   # sw
   with op == 0x2B:
      control |= 0x030
   # beq
   with op == 0x04:
      control |= 0x103


rf[0] <<= pyrtl.Const(0)
rf[rt] <<= pyrtl.MemBlock.EnabledWrite(writeToReg, enable=control[7] & ~control[9])
rf[rd] <<= pyrtl.MemBlock.EnabledWrite(writeToReg, enable=control[7] & control[9])


# alu_in assignment to go along with data0
with pyrtl.conditional_assignment:
   with control[5:7] == 0:
      alu_in |= data1
   with control[5:7] == 1:
      alu_in |= imm.sign_extended(32)
   with control[5:7] == 2:
      alu_in |= imm.zero_extended(32)

with pyrtl.conditional_assignment:
   # add
   with control[0:3] == 0:
      alu_out |= pyrtl.corecircuits.signed_add(data0, alu_in)
   # and
   with control[0:3] == 1:
      alu_out |= data0 & alu_in
   # slt
   with control[0:3] == 2:
      alu_out |= pyrtl.corecircuits.signed_lt(data0, alu_in)
   # beq
   with control[0:3] == 3:
      with data0 == alu_in:
         zeroExt |= 1
      with pyrtl.otherwise:
         zeroExt|= 0
   # ori
   with control[0:3] == 4:
      alu_out |= data0 | alu_in
   # lui
   with control[0:3] == 5:
      alu_out |= pyrtl.corecircuits.shift_left_logical(alu_in, pyrtl.Const(16))


# memory
d_mem[alu_out] <<= pyrtl.MemBlock.EnabledWrite(rf[rt], enable=control[4])
with pyrtl.conditional_assignment:
   with control[3] == 0:
      writeToReg |= alu_out
   with control[3] == 1:
      writeToReg|= d_mem[alu_out]

# branching
branch <<= pyrtl.corecircuits.signed_add(PC + 0x1, imm.sign_extended(32))
with pyrtl.conditional_assignment:
   with control[8] & zeroExt:
      bMux |= branch
   with pyrtl.otherwise:
      bMux |= PC + 0x1

if __name__ == '__main__':

   """

   Here is how you can test your code.
   This is very similar to how the autograder will test your code too.

   1. Write a MIPS program. It can do anything as long as it tests the
      instructions you want to test.

   2. Assemble your MIPS program to convert it to machine code. Save
      this machine code to the "i_mem_init.txt" file.
      You do NOT want to use QtSPIM for this because QtSPIM sometimes
      assembles with errors. One assembler you can use is the following:

      https://alanhogan.com/asu/assembler.php

   3. Initialize your i_mem (instruction memory).

   4. Run your simulation for N cycles. Your program may run for an unknown
      number of cycles, so you may want to pick a large number for N so you
      can be sure that the program has "finished" its business logic.

   5. Test the values in the register file and memory to make sure they are
      what you expect them to be.

   6. (Optional) Debug. If your code didn't produce the values you thought
      they should, then you may want to call sim.render_trace() on a small
      number of cycles to see what's wrong. You can also inspect the memory
      and register file after every cycle if you wish.

   Some debugging tips:

      - Make sure your assembly program does what you think it does! You
         might want to run it in a simulator somewhere else (SPIM, etc)
         before debugging your PyRTL code.

      - Test incrementally. If your code doesn't work on the first try,
         test each instruction one at a time.

      - Make use of the render_trace() functionality. You can use this to
         print all named wires and registers, which is extremely helpful
         for knowing when values are wrong.

      - Test only a few cycles at a time. This way, you don't have a huge
         500 cycle trace to go through!

   """
   

   # Start a simulation trace
   sim_trace = pyrtl.SimulationTrace()

   # Initialize the i_mem with your instructions.
   i_mem_init = {}
   with open('i_mem_init.txt', 'r') as fin:
      i = 0
      for line in fin.readlines():
         i_mem_init[i] = int(line, 16)
         i += 1

   sim = pyrtl.Simulation(tracer=sim_trace, memory_value_map={
      i_mem : i_mem_init
   })

   # Run for an arbitrarily large number of cycles.
   for cycle in range(500):
      sim.step({})

   # Use render_trace() to debug if your code doesn't work.
   # sim_trace.render_trace()

   # You can also print out the register file or memory like so if you want to debug:
   print(sim.inspect_mem(d_mem))
   print(sim.inspect_mem(rf))

   # Perform some sanity checks to see if your program worked correctly
   # assert(sim.inspect_mem(d_mem)[0] == 10)
   # assert(sim.inspect_mem(rf)[8] == 10)    # $v0 = rf[8]
   print('Passed!')
