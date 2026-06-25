#!/usr/bin/env python3
import argparse
import json
import os
import subprocess
import sys

SESSION_FILE = ".pwn_cli_session.json"

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
        "--exploit-file",
        default="exploit.py",
        help="Exploit file to load inside pwn_cli.py (default: exploit.py).",
    )
    parser.add_argument(
        "--gdbscript",
        default="gdbscript",
        help="GDB script file path to pass to pwn_cli.py (default: gdbscript).",
    )
    parser.add_argument(
        "--logo",
        default="logo",
        help="Logo file path to pass to pwn_cli.py (default: logo).",
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
        default="pwn_cli.py",
        help="Path to the pwn_cli.py entrypoint script.",
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
    
    with open('logo', 'r') as file:
        logo = file.read()
        print(logo)

    parser = parse_args()
    args = parser.parse_args()

    # Handle --clear-session and exit
    if args.clear_session:
        clear_session()
        sys.exit(0)

    # Load session file if it exists
    session = load_session()

    # Merge CLI args with session defaults (CLI args override)
    binary = args.binary or args.binary_arg or session.get("binary")
    exploit_file = args.exploit_file or session.get("exploit_file", "exploit.py")
    gdbscript = args.gdbscript or session.get("gdbscript", "gdbscript")
    logo_file = args.logo or session.get("logo", "logo")

    # Validate binary
    if not binary:
        parser.error("A target binary path must be provided as a positional argument, via --binary, or saved in session.")

    binary = os.path.abspath(binary)
    exploit_file = os.path.abspath(exploit_file)
    gdbscript = os.path.abspath(gdbscript)
    logo_file = os.path.abspath(logo_file)
    pwn_cli = os.path.abspath(args.pwn_cli)

    if not os.path.exists(binary):
        parser.error(f"Target binary not found: {binary}")

    if not os.path.isfile(pwn_cli):
        parser.error(f"pwn_cli.py not found at: {pwn_cli}")

    # Save session config
    session_config = {
        "binary": binary,
        "exploit_file": exploit_file,
        "gdbscript": gdbscript,
        "logo": logo_file,
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
