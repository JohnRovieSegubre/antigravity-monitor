import subprocess
import sys

with open('gateway_server.py', 'rb') as f:
    data = f.read()

cmd = [
    'gcloud.cmd', 'compute', 'ssh', 'rovie_segubre@instance-20260208-234621',
    '--project=super-ai-483717', '--zone=us-central1-c', '--tunnel-through-iap',
    '--command=cat > ~/sovereign/gateway_server.py'
]

print("Uploading...")
p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
out, err = p.communicate(input=data)

if p.returncode == 0:
    print("Upload successful!")
else:
    print(f"Failed: {err.decode('utf-8', errors='ignore')}")
    sys.exit(1)
