#!/usr/bin/env python3
import argparse
import json
import os
import subprocess
import sys
import pathlib

SESSION_FILE = ".pwn_cli_session.json"

def load_google_example():
    """Load session config to be set to the google ctf example"""
    google_example_path = pathlib.Path(__file__).resolve().parent/'google-example'
    binary = google_example_path/"google_challenge"
    gdbscript = google_example_path/"google_gdbscript"
    exploit_file = google_example_path/"google_exploit.py"

    clear_session()
    session_config = {
    "binary": str(binary),
    "exploit_file": str(exploit_file),
    "gdbscript": str(gdbscript)
    }   


    save_session(session_config)

def load_session():
    """Load session config from file if it exists."""
    if os.path.exists(SESSION_FILE):
        try:
            with open(SESSION_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"[-] Warning: could not load session file: {e}")
            return {}
    return {}


def init_default(filepath : pathlib.Path):
    """Initialize default files"""
    defaults_path = pathlib.Path(__file__).resolve().parent/'defaults'
    filepath = pathlib.Path(filepath)
    default_exploit_content = None
    default_gdbscript = None
    with open(defaults_path/"default_exploit.py", "r") as file:
        default_exploit_content = file.read()
    with open(defaults_path/'default_gdbscript', 'r') as file:
        default_gdbscript = file.read()

    with open(filepath/'exploit.py', "w") as file:
        file.write(default_exploit_content)
    with open(filepath/'gdbscript', 'w') as file:
        file.write(default_gdbscript)

    

def save_session(config):
    """Save session config to file."""
    try:
        with open(SESSION_FILE, 'w') as f:
            json.dump(config, f, indent=2)
    except Exception as e:
        print(f"[-] Warning: could not save session file: {e}")

def clear_session():
    """Delete the session file."""
    if os.path.exists(SESSION_FILE):
        os.remove(SESSION_FILE)
        print(f"[+] Session cleared: {SESSION_FILE} deleted.")
    else:
        print(f"[*] No session file to clear.")

def parse_args():
    parser = argparse.ArgumentParser(
        description="Launch pwn_cli.py with a selected target binary."
    )

    parser.add_argument(
        "binary",
        nargs="?",
        help="Path to the target binary to analyze and exploit.",
    )
    parser.add_argument(
        "--binary",
        dest="binary_arg",
        help="Path to the target binary to analyze and exploit.",
    )
    
    parser.add_argument(
        "--init",
        nargs='?',
        default=None,
        help="Create files"
    )

    parser.add_argument(
        "--exploit-file",
        default= None,
        help="Exploit file to load inside pwn_cli.py (default: exploit.py).",
    )
    parser.add_argument(
        "--gdbscript",
        default= None,
        help="GDB script file path to pass to pwn_cli.py (default: gdbscript).",
    )

  
    parser.add_argument(
        "--clear-session",
        action="store_true",
        help="Clear the session file and exit.",
    )
    parser.add_argument(
        "--python",
        default=sys.executable,
        help="Python interpreter to use when launching pwn_cli.py.",
    )
    parser.add_argument(
        "--pwn-cli",
        default=pathlib.Path(__file__).resolve().parent/'pwn_cli.py',
        help="Path to the pwn_cli.py entrypoint script.",
    )
    parser.add_argument(
    "--google_example",
    action="store_true",
    help="Launch setting the session enviroment to the one I used to solve the secure-vault google ctf challenge",
    )

    return parser


def ensure_tmux_session(session_name="pwn_cli"):
    """Ensure a tmux session exists; create it if needed."""
    result = subprocess.run(
        ["tmux", "has-session", "-t", session_name],
        capture_output=True,
    )
    if result.returncode != 0:
        print(f"[*] Creating tmux session '{session_name}'...")
        subprocess.run(["tmux", "new-session", "-d", "-s", session_name])


if __name__ == "__main__":
    logo_path = pathlib.Path(__file__).resolve().parent/'logo'
    with open(logo_path, 'r') as file:
        logo = file.read()
        print(logo)


    parser = parse_args()
    args = parser.parse_args()

    if args.init is not None or "--init" in sys.argv:
            # Default to current directory "." if --init was passed without a path
            init_path = args.init if args.init else "."
            base_path = pathlib.Path(init_path)
            
            exploit_exists = (base_path / "exploit.py").exists()
            gdb_exists = (base_path / "gdbscript").exists()
            if exploit_exists or gdb_exists:
                print(f"[-] Exploit and gdbscript files already exist at {base_path.resolve()}! Delete them before creating new ones")
                sys.exit(1)

            init_default(base_path)
            print(f"[+] Default exploit.py and gdbscript files created at {base_path.resolve()}!")
            sys.exit(0)



    # Handle --clear-session and exit
    if args.clear_session:
        clear_session()
        sys.exit(0)

    # Load session file if it exists
    if args.google_example:
        load_google_example()

    session = load_session()

    # Merge CLI args with session defaults (CLI args override)
    binary = args.binary_arg or args.binary or session.get("binary")
    exploit_file = args.exploit_file or session.get("exploit_file", "exploit.py")

    gdbscript = args.gdbscript or session.get("gdbscript", "gdbscript")

    # Validate binary
    if not binary:
        parser.error("A target binary path must be provided as a positional argument, via --binary, or saved in session.")

    binary = os.path.abspath(binary)
    exploit_file = os.path.abspath(exploit_file)
    gdbscript = os.path.abspath(gdbscript)
    pwn_cli = os.path.abspath(args.pwn_cli)

    if not os.path.exists(binary):
        parser.error(f"Target binary not found: {binary}")

    if not os.path.isfile(pwn_cli):
        parser.error(f"pwn_cli.py not found at: {pwn_cli}")

    # Save session config
    session_config = {
        "binary": str(binary),
        "exploit_file": str(exploit_file),
        "gdbscript": str(gdbscript),
    }
    save_session(session_config)

    # Ensure tmux is available and session exists
    ensure_tmux_session()

    # Pass session config to pwn_cli.py via environment
    env = os.environ.copy()
    env["PWN_CLI_SESSION_FILE"] = os.path.abspath(SESSION_FILE)

    cmd = [args.python, pwn_cli]

    print(f"[*] Launching pwn_cli.py with target binary: {binary}")
    print(f"[*] Using exploit file: {exploit_file}")

    # Launch pwn_cli.py inside the tmux session
    subprocess.run(["tmux", "new-window", "-t", "pwn_cli", "-c", os.getcwd()] + cmd, env=env)
    
    # Attach to the tmux session so the user sees it
    result = subprocess.run(["tmux", "attach-session", "-t", "pwn_cli"])
    sys.exit(result.returncode)
