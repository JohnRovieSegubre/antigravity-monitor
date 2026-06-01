from eth_account import Account
import os
from dotenv import load_dotenv

load_dotenv("sovereign-openclaw/.env")
pk = os.getenv("AGENT_PRIVATE_KEY")
if pk:
    acc = Account.from_key(pk)
    print(f"Agent Address: {acc.address}")
else:
    print("No PK found")
