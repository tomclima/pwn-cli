# pwn_cli

pwn_cli is a lightweight helper for working through binary exploitation challenges with pwntools, GDB, and a Python-based REPL.

It helps you:
- launch a target binary in a tmux session,
- attach GDB automatically,
- load an exploit script dynamically,
- bootstrap starter files for a new challenge,
- and optionally use the bundled Google example setup.

## Features

- Create starter files with `--init`
- Launch a binary with a saved session config
- Load `exploit.py` dynamically inside the REPL
- Use helpers such as `restart()` and `read_exploit()`
- Try the included Google example with `--google_example`

## Requirements

Install the following before using the tool:

- Python 3
- pwntools
- ptpython
- tmux
- gdb

Install Python dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Quick start

### 1. Create starter files

```bash
python3 main.py --init .
```

This will create:
- `exploit.py`
- `gdbscript`

### 2. Launch a binary

```bash
python3 main.py /path/to/your/binary
```

You can also provide the binary explicitly with:

```bash
python3 main.py --binary /path/to/your/binary
```

### 3. Use the bundled Google example

```bash
python3 main.py --google_example
```

This configures the session to use the sample files in the `google-example/` directory.

## Usage

### Main launcher

The main entrypoint is `main.py`.

Common options:

```bash
python3 main.py [binary]
python3 main.py --binary /path/to/binary
python3 main.py --exploit-file /path/to/exploit.py
python3 main.py --gdbscript /path/to/gdbscript
python3 main.py --clear-session
python3 main.py --google_example
```

### REPL helpers

Once the session starts, you will enter a Python REPL with access to:

- `io` — the live pwntools GDB connection
- `restart()` — restart the session in a new tmux window
- `read_exploit()` — reload the exploit script from disk

## Project layout

```text
.
├── defaults/
│   ├── default_exploit.py
│   └── default_gdbscript
├── google-example/
│   ├── google_challenge
│   ├── google_exploit.py
│   └── google_gdbscript
├── main.py
├── pwn_cli.py
├── requirements.txt
└── logo
```

## Notes

- The launcher stores session information in `.pwn_cli_session.json`.
- `main.py` uses tmux to create a managed session and then launches the interactive REPL.
- The exploit file is loaded dynamically, so you can update it without restarting the whole workflow manually.
