"""
Helper script to terminate any APIx FastAPI and Streamlit services running on ports 8000 and 8501.
"""

import psutil
import time

TARGET_PORTS = (8000, 8501)

def stop_services():
    print("=" * 60)
    print("Stopping APIx Services (Ports 8000 & 8501)")
    print("=" * 60)

    terminated_pids = set()

    for conn in psutil.net_connections(kind='inet'):
        if conn.laddr and conn.laddr.port in TARGET_PORTS and conn.pid:
            if conn.pid not in terminated_pids and conn.pid > 0:
                try:
                    proc = psutil.Process(conn.pid)
                    print(f"[*] Stopping {proc.name()} (PID: {conn.pid}) on port {conn.laddr.port}...")
                    for child in proc.children(recursive=True):
                        child.kill()
                    proc.kill()
                    terminated_pids.add(conn.pid)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass

    if terminated_pids:
        time.sleep(1)
        print(f"[OK] Successfully terminated {len(terminated_pids)} process(es). Ports are now free.")
    else:
        print("[INFO] No active services found on ports 8000 or 8501. Already stopped.")

if __name__ == "__main__":
    stop_services()
