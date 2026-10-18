# Start a server in a separate, paused, owned Renode instance first:
# machine StartGdbServer 3333
# Invoke: arm-none-eabi-gdb matching.elf -batch -x inspect.gdb
set pagination off
set confirm off
target remote localhost:3333
info registers
bt
disconnect
