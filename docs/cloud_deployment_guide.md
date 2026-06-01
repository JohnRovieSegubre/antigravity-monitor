# Sovereign API: Cloud Deployment & Update Guide

> **Server:** `34.55.175.24` (Google Cloud)  
> **GCP Instance:** `instance-20260208-234621`  
> **GCP Project:** `super-ai-483717`  
> **GCP Zone:** `us-central1-c`  
> **User:** `rovie_segubre`  
> **Remote Path:** `~/sovereign`

> [!IMPORTANT]
> **Port 22 is blocked** on this server's external firewall. All SSH/SCP commands must use
> `gcloud compute ssh/scp --tunnel-through-iap` to route through Google's Identity-Aware Proxy.
> Raw `ssh`/`scp` to the IP will timeout.

---

## Quick Reference — What Do I Need to Update?

| What Changed | Update Method | Downtime? |
|---|---|---|
| Blog posts only | [Scenario A](#scenario-a-blog-updates-only) | ❌ None |
| Landing page (`index.html`, CSS) | [Scenario B](#scenario-b-landing-page-updates) | ❌ None |
| Gateway code (`gateway_server.py`) | [Scenario C](#scenario-c-gateway-code-updates) | ⚡ ~10 seconds |
| `.env` / secrets | [Scenario D](#scenario-d-environment-variable-changes) | ⚡ ~10 seconds |
| NGINX config | [Scenario E](#scenario-e-nginx-config-changes) | ⚡ ~5 seconds |
| Full deployment (first time or major) | [Scenario F](#scenario-f-full-deployment) | ⏱️ ~2 minutes |

---

## Prerequisites

```powershell
# Test connection via IAP tunnel
echo y | gcloud compute ssh rovie_segubre@instance-20260208-234621 --project=super-ai-483717 --zone=us-central1-c --tunnel-through-iap --command="echo CONNECTION_OK"
```

If this fails, ensure:
1. `gcloud` CLI is installed and authenticated (`gcloud auth login`)
2. The IAP API is enabled on the project
3. Your GCP account has `IAP-secured Tunnel User` role

---

## Helper Variables

To avoid repeating long arguments, set these at the start of your session:

```powershell
$GCP_INSTANCE = "instance-20260208-234621"
$GCP_PROJECT  = "super-ai-483717"
$GCP_ZONE     = "us-central1-c"
$GCP_USER     = "rovie_segubre"
```

Then use them like:
```powershell
echo y | gcloud compute ssh ${GCP_USER}@${GCP_INSTANCE} --project=$GCP_PROJECT --zone=$GCP_ZONE --tunnel-through-iap --command="echo OK"
```

---

## Scenario A: Blog Updates Only

No server restart needed. Blog files are static HTML served by NGINX.

```powershell
# 1. Build the blog locally
python build_blog.py

# 2. Upload the blogs directory
echo y | gcloud compute scp --recurse landing\blogs rovie_segubre@instance-20260208-234621:/home/rovie_segubre/sovereign/landing/ --project=super-ai-483717 --zone=us-central1-c --tunnel-through-iap

# 3. Fix permissions (prevents 403 errors)
echo y | gcloud compute ssh rovie_segubre@instance-20260208-234621 --project=super-ai-483717 --zone=us-central1-c --tunnel-through-iap --command="chmod -R 755 ~/sovereign/landing/blogs/"
```

> ⚠️ **Always set permissions after upload.** `gcloud compute scp` can create directories with restrictive permissions that NGINX can't read (403 error).

---

## Scenario B: Landing Page Updates

For changes to `landing/index.html`, `landing/skill.md`, `landing/llm.txt`, or other static files:

```powershell
# Upload a specific file
echo y | gcloud compute scp landing\index.html rovie_segubre@instance-20260208-234621:/home/rovie_segubre/sovereign/landing/index.html --project=super-ai-483717 --zone=us-central1-c --tunnel-through-iap

# Or upload the entire landing folder
echo y | gcloud compute scp --recurse landing\* rovie_segubre@instance-20260208-234621:/home/rovie_segubre/sovereign/landing/ --project=super-ai-483717 --zone=us-central1-c --tunnel-through-iap

# Fix permissions
echo y | gcloud compute ssh rovie_segubre@instance-20260208-234621 --project=super-ai-483717 --zone=us-central1-c --tunnel-through-iap --command="chmod -R 755 ~/sovereign/landing/"
```

Changes are live immediately — no restart needed.

---

## Scenario C: Gateway Code Updates

For changes to `gateway_server.py`, `api_key_registry.py`, `polygon_watcher.py`, or other Python backend files.

### Step 1: Upload the changed file(s)
```powershell
echo y | gcloud compute scp gateway_server.py rovie_segubre@instance-20260208-234621:/home/rovie_segubre/sovereign/ --project=super-ai-483717 --zone=us-central1-c --tunnel-through-iap
```

### Step 2: Rebuild and restart the gateway container
```powershell
echo y | gcloud compute ssh rovie_segubre@instance-20260208-234621 --project=super-ai-483717 --zone=us-central1-c --tunnel-through-iap --command="cd ~/sovereign && sudo docker-compose up -d --build gateway"
```

### If `docker-compose` fails with `KeyError: 'ContainerConfig'`
This is a known bug. Use the manual fallback:

```powershell
echo y | gcloud compute ssh rovie_segubre@instance-20260208-234621 --project=super-ai-483717 --zone=us-central1-c --tunnel-through-iap --command="cd ~/sovereign && sudo docker stop sovereign_gateway && sudo docker rm sovereign_gateway && sudo docker build -t sovereign_gateway . && sudo docker run -d --name sovereign_gateway -p 8000:8000 --env-file .env --network sovereign_default -v ./data:/app/.agent sovereign_gateway python -u gateway_server.py"
```

> ⚠️ **Critical:** Always use `docker-compose` or include `--network sovereign_default` and volumes. Without them, the gateway can't access SQLite (crash) and NGINX can't reach the gateway ("WARMING UP" error).

### Step 3: Verify
```powershell
echo y | gcloud compute ssh rovie_segubre@instance-20260208-234621 --project=super-ai-483717 --zone=us-central1-c --tunnel-through-iap --command="sudo docker logs sovereign_gateway --tail 5"
```
Look for: `Uvicorn running on http://0.0.0.0:8000`

---

## Scenario D: Environment Variable Changes

The `.env` file on the server contains secrets: `MINT_SECRET`, `OPENROUTER_API_KEY`, `X402_WALLET_ADDRESS`, etc.

```powershell
# Upload local .env
echo y | gcloud compute scp .env rovie_segubre@instance-20260208-234621:/home/rovie_segubre/sovereign/.env --project=super-ai-483717 --zone=us-central1-c --tunnel-through-iap
```

After editing, restart the gateway to pick up the new values:
```powershell
echo y | gcloud compute ssh rovie_segubre@instance-20260208-234621 --project=super-ai-483717 --zone=us-central1-c --tunnel-through-iap --command="cd ~/sovereign && sudo docker-compose restart gateway"
```

---

## Scenario E: NGINX Config Changes

```powershell
# Upload the updated config
echo y | gcloud compute scp nginx.conf rovie_segubre@instance-20260208-234621:/home/rovie_segubre/sovereign/nginx.conf --project=super-ai-483717 --zone=us-central1-c --tunnel-through-iap

# Restart only NGINX (no gateway restart needed)
echo y | gcloud compute ssh rovie_segubre@instance-20260208-234621 --project=super-ai-483717 --zone=us-central1-c --tunnel-through-iap --command="sudo docker restart sovereign_nginx"
```

---

## Scenario F: Full Deployment

For major updates or first-time setup. This stops everything, uploads all files, and rebuilds.

> ⚠️ The legacy `deploy_to_cloud.ps1` script uses raw `scp`/`ssh` and **will not work** with the current firewall configuration. Use the manual steps below instead.

```powershell
# 1. Stop all containers
echo y | gcloud compute ssh rovie_segubre@instance-20260208-234621 --project=super-ai-483717 --zone=us-central1-c --tunnel-through-iap --command="cd ~/sovereign && sudo docker-compose down"

# 2. Upload all source files
$files = @("gateway_server.py", "api_key_registry.py", "autonomous_core.py", "docker-compose.yml", "Dockerfile", "requirements.txt", "polygon_watcher.py", "llm.txt", "nginx.conf", ".env")
foreach ($file in $files) {
    if (Test-Path $file) {
        echo y | gcloud compute scp $file rovie_segubre@instance-20260208-234621:/home/rovie_segubre/sovereign/ --project=super-ai-483717 --zone=us-central1-c --tunnel-through-iap
    }
}

# 3. Upload SDK and Landing
echo y | gcloud compute scp --recurse sdk rovie_segubre@instance-20260208-234621:/home/rovie_segubre/sovereign/ --project=super-ai-483717 --zone=us-central1-c --tunnel-through-iap
echo y | gcloud compute scp --recurse landing rovie_segubre@instance-20260208-234621:/home/rovie_segubre/sovereign/ --project=super-ai-483717 --zone=us-central1-c --tunnel-through-iap

# 4. Fix permissions
echo y | gcloud compute ssh rovie_segubre@instance-20260208-234621 --project=super-ai-483717 --zone=us-central1-c --tunnel-through-iap --command="chmod -R 755 ~/sovereign/landing/"

# 5. Rebuild and start
echo y | gcloud compute ssh rovie_segubre@instance-20260208-234621 --project=super-ai-483717 --zone=us-central1-c --tunnel-through-iap --command="cd ~/sovereign && sudo docker-compose up -d --build"
```

---

## Architecture Overview

```
Internet → NGINX (:80) → Gateway (:8000) → OpenRouter

                ┌─────────────────┐
Client ────────►│  sovereign_nginx │  (port 80)
                │  serves: landing/ │
                └────────┬────────┘
                         │ proxy_pass (api.sovereign-api.com)
                         ▼
                ┌─────────────────┐
                │sovereign_gateway│  (port 8000, internal)
                │ gateway_server.py│
                └────────┬────────┘
                         │ calls OpenRouter, manages Macaroons
                         │
                ┌────────┴────────┐
                │ polygon_cashier │  (no port, internal)
                │ polygon_watcher │  watches Base for USDC deposits
                └─────────────────┘
```

### Docker Containers

| Container | Purpose | Port |
|---|---|---|
| `sovereign_nginx` | Serves landing page, proxies API requests | 80 (public) |
| `sovereign_gateway` | FastAPI gateway — auth, routing, billing | 8000 (internal) |
| `polygon_cashier` | Watches Base blockchain for USDC deposits | None |

### Volumes

| Mount | Purpose |
|---|---|
| `./data:/app/.agent` | SQLite databases (Macaroons, API keys) — **never delete** |
| `./.env:/app/.env:ro` | Gateway reads environment variables |
| `./nginx.conf:/etc/nginx/nginx.conf:ro` | NGINX configuration |
| `./landing:/usr/share/nginx/html:ro` | Landing page + blog static files |

---

## Troubleshooting

### SSH connection timeout (raw ssh/scp)
**Cause:** Port 22 is blocked on the GCP firewall.  
**Fix:** Use `gcloud compute ssh/scp --tunnel-through-iap` instead of raw SSH. See all scenarios above.

### "403 Forbidden" on blog pages
**Cause:** `scp`/`gcloud compute scp` creates directories with restrictive permissions.  
**Fix:**
```powershell
echo y | gcloud compute ssh rovie_segubre@instance-20260208-234621 --project=super-ai-483717 --zone=us-central1-c --tunnel-through-iap --command="chmod -R 755 ~/sovereign/landing/blogs/"
```

### "WARMING UP" or gateway unreachable
**Cause:** Gateway container crashed (usually missing volumes or SQLite access).  
**Fix:**
```powershell
# Check logs
echo y | gcloud compute ssh rovie_segubre@instance-20260208-234621 --project=super-ai-483717 --zone=us-central1-c --tunnel-through-iap --command="sudo docker logs sovereign_gateway --tail 20"

# Restart with docker-compose (ensures correct volumes)
echo y | gcloud compute ssh rovie_segubre@instance-20260208-234621 --project=super-ai-483717 --zone=us-central1-c --tunnel-through-iap --command="cd ~/sovereign && sudo docker-compose down && sudo docker-compose up -d --build"
```

### `KeyError: 'ContainerConfig'` during docker-compose
**Cause:** Stale container metadata from a previous manual `docker run`.  
**Fix:**
```powershell
echo y | gcloud compute ssh rovie_segubre@instance-20260208-234621 --project=super-ai-483717 --zone=us-central1-c --tunnel-through-iap --command="sudo docker stop sovereign_gateway sovereign_nginx polygon_cashier 2>/dev/null; sudo docker rm sovereign_gateway sovereign_nginx polygon_cashier 2>/dev/null; sudo docker network rm sovereign_default 2>/dev/null; cd ~/sovereign && sudo docker-compose up -d --build"
```

### Plink host key prompt (Windows)
**Cause:** `gcloud compute ssh` on Windows uses PuTTY's `plink`, which prompts to cache the host key.  
**Fix:** Prefix the command with `echo y |` to auto-accept the key prompt.
