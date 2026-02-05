import os
import time
import shutil
import logging
from pathlib import Path
import subprocess

# --- Configuration ---
WORKSPACE_DIR = Path(r"c:\Users\rovie segubre\.gemini\antigravity\playground\obsidian-trifid")
INBOX_DIR = WORKSPACE_DIR / ".agent" / "inbox"
COMPLETED_DIR = INBOX_DIR / "completed"
FAILED_DIR = INBOX_DIR / "failed"
LOGS_DIR = INBOX_DIR / "logs"

POLL_INTERVAL = 5  # Seconds

# --- Logging Setup ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(LOGS_DIR / "monitor.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)

def wake_up_antigravity(message):
    """
    Injects a message into the active window using PowerShell SendKeys.
    This simulates the user typing to wake up the AI.
    """
    logging.info(f"Configuring Wake-On-Lan: '{message}'")
    
    # PowerShell script to type keys
    # We use a slight delay to ensure the window captures it if focused.
    # Note: The user MUST have the chat window focused for this to work perfectly.
    ps_script = f"""
    Add-Type -AssemblyName System.Windows.Forms
    Start-Sleep -Milliseconds 1000
    # Try to switch back to the previous window (Alt+Tab)
    [System.Windows.Forms.SendKeys]::SendWait('%{{TAB}}')
    Start-Sleep -Milliseconds 500
    [System.Windows.Forms.SendKeys]::SendWait('{message}')
    [System.Windows.Forms.SendKeys]::SendWait('{{ENTER}}')
    """
    
    try:
        subprocess.run(["powershell", "-Command", ps_script], check=True)
        logging.info("Keystrokes sent successfully.")
    except Exception as e:
        logging.error(f"Failed to send keys: {e}")

def process_task(task_file):
    logging.info(f"New task detected: {task_file.name}")
    
    try:
        # 1. Read the task
        with open(task_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        logging.info(f"Content: {content[:100]}...")
        
        # 2. Invoke Antigravity (Execution Mode)
        if content.startswith("EXEC:"):
            command = content.replace("EXEC:", "").strip()
            logging.info(f"Executing command: {command}")
            
            # Run the command
            result = subprocess.run(command, shell=True, capture_output=True, text=True, cwd=WORKSPACE_DIR)
            
            # Create a receipt with output
            result_file = INBOX_DIR / f"{task_file.stem}_RESULT.md"
            with open(result_file, 'w', encoding='utf-8') as rf:
                rf.write(f"# Task Result: {task_file.name}\n\n")
                rf.write(f"Executed at: {time.ctime()}\n\n")
                rf.write("## Console Output:\n")
                rf.write(f"```text\n{result.stdout}\n```\n")
                if result.stderr:
                    rf.write("## Errors:\n")
                    rf.write(f"```text\n{result.stderr}\n```\n")
            
            logging.info(f"Execution finished. Exit code: {result.returncode}")
            
            # WAKE UP THE AGENT
            wake_up_antigravity(f"Monitor: Task {task_file.name} complete. Exit code {result.returncode}.")
        else:
            # Receipt Mode (Fallback)
            result_file = INBOX_DIR / f"{task_file.stem}_RESULT.md"
            with open(result_file, 'w', encoding='utf-8') as rf:
                rf.write(f"# Task Received: {task_file.name}\n\n")
                rf.write(f"Antigravity is in receipt mode for this file at {time.ctime()}\n\n")
                rf.write("## Status: QUEUED\n")
                rf.write("To execute this immediately, start the file with `EXEC:`")

        # 3. Archive
        shutil.move(str(task_file), str(COMPLETED_DIR / task_file.name))
        logging.info(f"Task archived to completed.")

    except Exception as e:
        logging.error(f"Failed to process {task_file.name}: {e}")
        shutil.move(str(task_file), str(FAILED_DIR / task_file.name))

def main():
    logging.info("Antigravity Inbox Monitor Started.")
    logging.info(f"Watching: {INBOX_DIR}")
    
    # Ensure dirs exist (just in case)
    for d in [COMPLETED_DIR, FAILED_DIR, LOGS_DIR]:
        d.mkdir(parents=True, exist_ok=True)

    try:
        while True:
            # Look for .md or .txt files
            tasks = list(INBOX_DIR.glob("*.md")) + list(INBOX_DIR.glob("*.txt"))
            
            for task in tasks:
                if task.stem.endswith("_RESULT"):
                    continue
                process_task(task)
            
            time.sleep(POLL_INTERVAL)
    except KeyboardInterrupt:
        logging.info("🛑 Monitor stopped by user.")

if __name__ == "__main__":
    main()
