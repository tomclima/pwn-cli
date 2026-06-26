#!/usr/bin/env python3
import os
import sys
import json
from pwn import *
import ptpython.repl
import importlib.util

SESSION_FILE = ".pwn_cli_session.json"


def load_session():
    """Load session config from file."""
    session_path = os.environ.get("PWN_CLI_SESSION_FILE", SESSION_FILE)
    if os.path.exists(session_path):
        try:
            with open(session_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"[-] Warning: could not load session file: {e}")
            return {}
    print(f"[-] Error: Session file not found at {session_path}")
    sys.exit(1)

session = load_session()

os.system("clear")

# Load logo from session
logo_path = session.get("logo", "logo")
try:
    with open(logo_path, 'r') as file:
        logo = file.read()
        print(logo)
except Exception as e:
    print(f"[-] Warning: could not load logo from {logo_path}: {e}")

# Load binary from session
binary_path = session.get("binary")
if not binary_path:
    print("[-] Error: No binary path in session.")
    sys.exit(1)

exe = elf.ELF(binary_path)
context.binary = exe
context.terminal = ['tmux', 'splitw', '-h']
context.log_level = 'error' 

# Load gdbscript from session
gdbscript_path = session.get("gdbscript", "gdbscript")
gdbscript = None
try:
    with open(gdbscript_path, 'r') as file:
        gdbscript = file.read()
except Exception as e:
    print(f"[-] Warning: could not load gdbscript from {gdbscript_path}: {e}")

# -------------------------------------------------------------------------
# HELPER FUNCTIONS FOR THE REPL
# -------------------------------------------------------------------------

def r():
    """
    restart() shorthand
    """
    restart()

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
    
def read_exploit(filename=None):
    if filename is None:
        filename = session.get("exploit_file", "exploit.py")

    path = Path(filename).resolve()
    if not path.exists():
        print(f"[-] Error: {filename} not found.")
        return

    try:
        # 1. Create a unique module name or keep overriding 'current_exploit'
        module_name = "current_exploit"

        # 2. Load the file dynamically using importlib
        spec = importlib.util.spec_from_file_location(module_name, str(path))
        if spec is None or spec.loader is None:
            print(f"[-] Error: Could not load spec for {filename}")
            return

        module = importlib.util.module_from_spec(spec)

        # 3. Force update sys.modules so imports within the exploit behave nicely
        sys.modules[module_name] = module

        # 4. Execute the module to populate it
        spec.loader.exec_module(module)

        # 5. Inject the module's functions cleanly into the REPL globals
        # You can either inject the whole module:
        globals()["exploit_mod"] = module
        # Or explicitly grab just the exploit function:
        if hasattr(module, "exploit"):
            globals()["exploit"] = module.exploit
            print(
                f"[+] Successfully loaded/reloaded exploit() from {filename}!"
            )
        else:
            print(f"[-] Warning: {filename} has no exploit() function defined.")

    except Exception as e:
        print(f"[-] Error loading {filename}: {e}")

def repl_startup(repl):
    read_exploit()
    io.send(exploit())

# -------------------------------------------------------------------------
# MAIN EXECUTION
# -------------------------------------------------------------------------

# Start with GDB attached (Mode 1)

io = gdb.debug(exe.path, gdbscript=gdbscript)
print(session)



print("[*] Dropping into Python REPL. 'io' is your live connection object.")
print("[*] Available helpers: restart(), read_exploit()")

# MODE 2: LIVE PYTHON CLI (This freezes the script here and opens a prompt)
# Passing globals() allows the REPL to see restart() and read_exploit()
ptpython.repl.embed(globals(), locals(), configure=repl_startup) 

# MODE 3: RAW INTERACTION (Runs after you exit the Python CLI)
print("[*] Exiting Python CLI. Switching to raw interaction...")
io.interactive()