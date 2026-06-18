#!/usr/bin/env python3
import os
import sys
from pwn import *
import ptpython.repl


os.system("clear")

with open('logo', 'r') as file:
    logo = file.read()
    print(logo)



exe = elf.ELF('./vault')
context.binary = exe
context.terminal = ['tmux', 'splitw', '-h']
context.log_level = 'error' 

gdbscript = None
with open('gdbscript', 'r') as file:
    gdbscript = file.read()

# -------------------------------------------------------------------------
# HELPER FUNCTIONS FOR THE REPL
# -------------------------------------------------------------------------

def restart():
    """
    Spawns a new tmux window running this script, then kills all other windows.
    """
    print("[*] Restarting session in a new tmux window...")
    # 1. Spawn a new tmux window running this exact script
    #    (Using sys.argv[0] ensures it works regardless of the filename)
    os.system(f"tmux new-window 'python3 {sys.argv[0]}'")
    os.system("tmux select-window -t :-")
    
    # 2. Kill the current tmux window (which terminates this old session)
    os.system("tmux kill-window")

def read_exploit(filename="exploit.py"):
    """
    Reads exploit.py, extracts the exploit() function, and loads it 
    directly into the current REPL environment.
    """
    if not os.path.exists(filename):
        print(f"[-] Error: {filename} not found.")
        return

    try:
        with open(filename, 'r') as f:
            code = f.read()
        
        # We execute the file's code inside the global context of the REPL.
        # This will inject the `exploit()` function dynamically.
        exec(code, globals())
        print(f"[+] Successfully loaded/reloaded exploit() from {filename}!")
    except Exception as e:
        print(f"[-] Error reading or executing {filename}: {e}")

# -------------------------------------------------------------------------
# MAIN EXECUTION
# -------------------------------------------------------------------------

# Start with GDB attached (Mode 1)

read_exploit()
io = gdb.debug(exe.path, gdbscript=gdbscript)

print("[*] Dropping into Python REPL. 'io' is your live connection object.")
print("[*] Available helpers: restart(), read_exploit()")

# MODE 2: LIVE PYTHON CLI (This freezes the script here and opens a prompt)
# Passing globals() allows the REPL to see restart() and read_exploit()
ptpython.repl.embed(globals(), locals()) 

# MODE 3: RAW INTERACTION (Runs after you exit the Python CLI)
print("[*] Exiting Python CLI. Switching to raw interaction...")
io.interactive()