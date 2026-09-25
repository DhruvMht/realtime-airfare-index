"""
Startup script to launch both APIx FastAPI REST API and Streamlit Dashboard concurrently.
Includes pre-flight port checks to automatically clear stale processes and prevent [WinError 10048].
"""

import subprocess
import sys
import os
import time
import psutil

TARGET_PORTS = (8000, 8501)

def kill_stale_processes_on_ports(ports):
    """Cleanly terminates any lingering processes bound to target ports."""
    terminated = False
    for conn in psutil.net_connections(kind='inet'):
        if conn.laddr and conn.laddr.port in ports and conn.pid:
            if conn.pid > 0 and conn.pid != os.getpid():
                try:
                    proc = psutil.Process(conn.pid)
                    print(f"[*] Port {conn.laddr.port} in use by PID {conn.pid} ({proc.name()}). Freeing port...")
                    for child in proc.children(recursive=True):
                        child.kill()
                    proc.kill()
                    terminated = True
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
    if terminated:
        time.sleep(1.5)
        print("[OK] Stale processes terminated. Ports are free.")

def kill_proc_tree(proc):
    """Terminates a subprocess and all of its spawned children on Windows."""
    if proc is None:
        return
    try:
        parent = psutil.Process(proc.pid)
        for child in parent.children(recursive=True):
            try:
                child.kill()
            except psutil.NoSuchProcess:
                pass
        parent.kill()
    except psutil.NoSuchProcess:
        pass

def main():
    print("=" * 70)
    print("Starting APIx Services (FastAPI + Streamlit)")
    print("=" * 70)

    # Pre-flight check: ensure ports 8000 and 8501 are free
    kill_stale_processes_on_ports(TARGET_PORTS)

    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    python_exe = sys.executable

    # 1. Start FastAPI REST Server
    print("[*] Launching FastAPI REST API on http://127.0.0.1:8000...")
    api_cmd = [python_exe, "-m", "uvicorn", "apix.api.server:app", "--host", "127.0.0.1", "--port", "8000"]
    api_proc = subprocess.Popen(api_cmd, cwd=project_root)

    time.sleep(2)

    # 2. Start Streamlit Dashboard
    print("[*] Launching Streamlit Dashboard on http://localhost:8501...")
    dash_cmd = [python_exe, "-m", "streamlit", "run", "apix/dashboard/app.py", "--server.port", "8501"]
    dash_proc = subprocess.Popen(dash_cmd, cwd=project_root)

    print("\n" + "=" * 70)
    print("[OK] All APIx Services launched successfully:")
    print("     - Web Dashboard : http://localhost:8501")
    print("     - OpenAPI / Docs: http://127.0.0.1:8000/docs")
    print("     - Health Check  : http://127.0.0.1:8000/api/v1/health")
    print("=" * 70)
    print("\nPress Ctrl+C to terminate all services cleanly.\n")

    try:
        api_proc.wait()
        dash_proc.wait()
    except KeyboardInterrupt:
        print("\nStopping APIx services...")
        kill_proc_tree(api_proc)
        kill_proc_tree(dash_proc)
        print("[OK] All services stopped cleanly.")

if __name__ == "__main__":
    main()
