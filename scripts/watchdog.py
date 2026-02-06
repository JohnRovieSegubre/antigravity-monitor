import subprocess
import time
import logging
import sys
from pathlib import Path

# Config
WORKSPACE_DIR = Path(r"c:\Users\rovie segubre\.gemini\antigravity\playground\obsidian-trifid")
MONITOR_SCRIPT = WORKSPACE_DIR / "scripts" / "antigravity_monitor.py"

logging.basicConfig(level=logging.INFO, format='%(asctime)s [WATCHDOG] %(message)s')

def wake_up_alert(message):
    ps_script = f"""
    Add-Type -AssemblyName System.Windows.Forms
    Start-Sleep -Milliseconds 1000
    [System.Windows.Forms.SendKeys]::SendWait('%{{TAB}}')
    Start-Sleep -Milliseconds 500
    [System.Windows.Forms.SendKeys]::SendWait('{message}')
    [System.Windows.Forms.SendKeys]::SendWait('{{ENTER}}')
    """
    try:
        subprocess.run(["powershell", "-Command", ps_script], check=True)
    except:
        pass

def run_monitor():
    while True:
        logging.info("Starting Monitor V2...")
        
        # Start the process
        process = subprocess.Popen([sys.executable, str(MONITOR_SCRIPT)], cwd=WORKSPACE_DIR)
        
        # Wait for it to finish (crash)
        exit_code = process.wait()
        
        logging.warning(f"Monitor exited with code {exit_code}")
        
        if exit_code != 0:
            logging.error("Detected CRASH. Triggering Alert...")
            wake_up_alert(f"⚠️ SYSTEM ALERT: Monitor crashed (Code {exit_code}). Retrying in 5s...")
        else:
            logging.info("Monitor exited normally (User stop?). Restarting anyway...")
            
        time.sleep(5)

if __name__ == "__main__":
    try:
        run_monitor()
    except KeyboardInterrupt:
        logging.info("Watchdog killed.")
