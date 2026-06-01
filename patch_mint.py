import sys

with open("gateway_server.py", "r", encoding="utf-8") as f:
    content = f.read()

start_marker = "# --- CLASS: THE SOVEREIGN MINT (SECURED) ---"
end_marker = "MINT = SovereignMint(MINT_SECRET, SITE_URL)"

start_idx = content.find(start_marker)
if start_idx == -1:
    print("Could not find start_marker")
    sys.exit(1)

end_idx = content.find(end_marker, start_idx)
if end_idx == -1:
    print("Could not find end_marker")
    sys.exit(1)

# Include the length of end_marker
end_idx += len(end_marker)

new_class = """# --- CLASS: THE SOVEREIGN MINT (SECURED - SQLite WAL) ---
import sqlite3
import time
import secrets
from pathlib import Path
import json

class SovereignMint:
    def __init__(self, secret, location):
        self.secret = secret
        self.location = location
        self.db_path = DATA_DIR / "mint_history.db"
        self._init_db()

    def _get_db(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._get_db() as conn:
            conn.execute("PRAGMA journal_mode=WAL;")
            conn.execute("PRAGMA synchronous=NORMAL;")
            conn.execute(\"\"\"
                CREATE TABLE IF NOT EXISTS macaroons (
                    id TEXT PRIMARY KEY,
                    remaining_sats INTEGER NOT NULL,
                    expires_at REAL NOT NULL,
                    revoked BOOLEAN DEFAULT 0
                )
            \"\"\")
            conn.commit()

    def create_session(self, amount_sats: int, ttl_seconds: int = 900):
        \"\"\"Mints a new static session macaroon.\"\"\"
        session_id = f"sess_{secrets.token_hex(16)}"
        expires_at = time.time() + ttl_seconds
        
        m = Macaroon(location=self.location, identifier=session_id, key=self.secret)
        
        with self._get_db() as conn:
            conn.execute(
                "INSERT INTO macaroons (id, remaining_sats, expires_at, revoked) VALUES (?, ?, ?, 0)",
                (session_id, amount_sats, expires_at)
            )
            conn.commit()
            
        return m.serialize(), amount_sats

    def verify_and_spend(self, token_str: str, cost: int):
        \"\"\"Verifies session token, deducts cost atomically from SQLite.\"\"\"
        try:
            m = Macaroon.deserialize(token_str)
            m_id = m.identifier
            if isinstance(m_id, bytes):
                m_id = m_id.decode('utf-8')
            
            v = Verifier()
            # We trust the db balance, so we only need to verify the HMAC signature
            if not v.verify(m, self.secret): 
                return False, None, "Invalid Signature"

            with self._get_db() as conn:
                cursor = conn.cursor()
                cursor.execute(\"\"\"
                    UPDATE macaroons 
                    SET remaining_sats = remaining_sats - ? 
                    WHERE id = ? 
                      AND remaining_sats >= ? 
                      AND expires_at > ? 
                      AND revoked = 0
                    RETURNING remaining_sats
                \"\"\", (cost, m_id, cost, time.time()))
                
                row = cursor.fetchone()
                if row:
                    new_balance = row["remaining_sats"]
                    conn.commit()
                    return True, new_balance, "Success"
                
                # If we get here, the update failed. Let's find out why for accurate error reporting.
                cursor.execute("SELECT remaining_sats, expires_at, revoked FROM macaroons WHERE id = ?", (m_id,))
                state = cursor.fetchone()
                if not state:
                    return False, None, "Token/Session not found"
                if state["revoked"]:
                    return False, None, "Token/Session revoked"
                if state["expires_at"] <= time.time():
                    return False, None, "Token/Session expired"
                if state["remaining_sats"] < cost:
                    return False, state["remaining_sats"], "Insufficient Funds"
                    
                return False, None, "Unknown spend error"
        except Exception as e:
            return False, None, f"Token Error: {e}"

MINT = SovereignMint(MINT_SECRET, SITE_URL)"""

new_content = content[:start_idx] + new_class + content[end_idx:]

with open("gateway_server.py", "w", encoding="utf-8") as f:
    f.write(new_content)

print("Successfully patched gateway_server.py")
