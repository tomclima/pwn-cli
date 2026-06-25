#!/usr/bin/env python3
import argparse
import os
import subprocess
import sys


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
        "--no-gdb",
        action="store_true",
        help="Disable automatic gdb attachment in pwn_cli.py.",
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

    args = parser.parse_args()
    binary = args.binary or args.binary_arg
    if not binary:
        parser.error("A target binary path must be provided as a positional argument or via --binary.")

    args.binary = os.path.abspath(binary)
    args.exploit_file = os.path.abspath(args.exploit_file)
    args.gdbscript = os.path.abspath(args.gdbscript)
    args.logo = os.path.abspath(args.logo)
    args.pwn_cli = os.path.abspath(args.pwn_cli)

    if not os.path.exists(args.binary):
        parser.error(f"Target binary not found: {args.binary}")

    if not os.path.isfile(args.pwn_cli):
        parser.error(f"pwn_cli.py not found at: {args.pwn_cli}")

    return args


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
    args = parse_args()

    # Ensure tmux is available and session exists
    ensure_tmux_session()

    env = os.environ.copy()
    env["PWN_CLI_TARGET_BINARY"] = args.binary
    env["PWN_CLI_EXPLOIT_FILE"] = args.exploit_file
    env["PWN_CLI_GDBSCRIPT"] = args.gdbscript
    env["PWN_CLI_LOGO"] = args.logo
    if args.no_gdb:
        env["PWN_CLI_NO_GDB"] = "1"

    cmd = [args.python, args.pwn_cli]

    print(f"[*] Launching pwn_cli.py with target binary: {args.binary}")
    print(f"[*] Using exploit file: {args.exploit_file}")

    # Launch pwn_cli.py inside the tmux session
    subprocess.run(["tmux", "new-window", "-t", "pwn_cli", "-c", os.getcwd()] + cmd, env=env)
    
    # Attach to the tmux session so the user sees it
    result = subprocess.run(["tmux", "attach-session", "-t", "pwn_cli"])
    sys.exit(result.returncode)
