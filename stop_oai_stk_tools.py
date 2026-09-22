#!/usr/bin/env python3
"""Emergency stop for the runner, bridge, local UE, ping and iperf3.

The normal runner shutdown also stops the remote gNB using its live SSH
connection. If that connection is already gone, stop gNB in its SSH terminal.
"""

from pathlib import Path
import getpass
import shlex
import subprocess
import time

import paramiko
import psutil


THIS_PID = psutil.Process().pid
WINDOWS_NAMES = {
    "run_oai_stk_all.py",
    "run_bridge_forward.py",
    "run_ping_iperf_forward.py",
    "stk_oai_bridge_generic.py",
}
REMOTE_HOST = "192.168.114.16"
REMOTE_USER = "kayokonuc"
IPERF_CONTAINER = "oai-ext-dn"


def stop_remote_gnb() -> None:
    ssh_password = getpass.getpass(
        f"SSH password for {REMOTE_USER}@{REMOTE_HOST} (Enter for SSH key): "
    )
    sudo_password = getpass.getpass("Remote sudo password (Enter = SSH password): ") or ssh_password
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(
            REMOTE_HOST,
            username=REMOTE_USER,
            password=ssh_password or None,
            look_for_keys=True,
            allow_agent=True,
            timeout=15,
            auth_timeout=30,
        )
        command = (
            "pkill -INT -x nr-softmodem 2>/dev/null || true; "
            f"docker exec {shlex.quote(IPERF_CONTAINER)} pkill iperf3 2>/dev/null || true"
        )
        channel = ssh.get_transport().open_session()
        channel.exec_command("sudo -S -p '' sh -lc " + shlex.quote(command))
        channel.sendall((sudo_password + "\n").encode("utf-8"))
        deadline = time.monotonic() + 15
        while not channel.exit_status_ready() and time.monotonic() < deadline:
            time.sleep(0.05)
        if not channel.exit_status_ready():
            raise TimeoutError("remote stop command timed out")
        print("Remote gNB and iperf3 server stopped.")
    finally:
        ssh.close()


def main() -> None:
    for proc in psutil.process_iter(["pid", "cmdline"]):
        if proc.pid == THIS_PID:
            continue
        try:
            command = " ".join(proc.info.get("cmdline") or []).lower()
            if any(name in command for name in WINDOWS_NAMES):
                print(f"Stopping PID {proc.pid}: {Path((proc.info.get('cmdline') or [''])[0]).name}")
                proc.terminate()
                try:
                    proc.wait(3)
                except psutil.TimeoutExpired:
                    proc.kill()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    subprocess.run(
        [
            "wsl.exe", "-d", "Ubuntu-22.04", "-u", "root", "--",
            "bash", "--noprofile", "--norc", "-lc",
            "pkill -INT -x nr-uesoftmodem 2>/dev/null || true; "
            "pkill -INT -x ping 2>/dev/null || true; "
            "pkill -INT -x iperf3 2>/dev/null || true; "
            "sleep 2; "
            "pkill -KILL -x nr-uesoftmodem 2>/dev/null || true; "
            "ip link delete oaitun_ue1 2>/dev/null || true; "
            "while ip rule del table 9999 2>/dev/null; do :; done; "
            "ip route flush table 9999 2>/dev/null || true",
        ],
        check=False,
    )
    print("Windows forwarders, STK bridge, local UE, ping and iperf3 stopped.")
    print("oaitun_ue1 and OAI policy-routing table 9999 were cleared.")
    try:
        stop_remote_gnb()
    except Exception as exc:
        print(f"Could not stop remote gNB automatically: {exc}")
        print("Press Ctrl-C in the remote gNB SSH terminal instead.")


if __name__ == "__main__":
    main()
