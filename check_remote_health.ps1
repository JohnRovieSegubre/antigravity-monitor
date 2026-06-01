# check_remote_health.ps1
$SERVER_IP = "34.55.175.24"
$USER = "rovie_segubre"
$REMOTE_PATH = "~/sovereign"

if (Test-Path "$HOME\.ssh\id_ed25519") { $SSH_KEY = "$HOME\.ssh\id_ed25519" }
elseif (Test-Path "$HOME\.ssh\id_rsa") { $SSH_KEY = "$HOME\.ssh\id_rsa" }
else { Write-Error "No SSH key found"; exit 1 }

Write-Host ">>> Checking Remote Health..." -ForegroundColor Cyan

Write-Host "--- Docker Container Status ---" -ForegroundColor Yellow
ssh -i $SSH_KEY $USER@$SERVER_IP "cd $REMOTE_PATH && sudo docker-compose ps"

Write-Host "--- Gateway Logs (Last 20 lines) ---" -ForegroundColor Yellow
ssh -i $SSH_KEY $USER@$SERVER_IP "cd $REMOTE_PATH && sudo docker-compose logs --tail=20 gateway"

Write-Host "--- Nginx Logs (Last 20 lines) ---" -ForegroundColor Yellow
ssh -i $SSH_KEY $USER@$SERVER_IP "cd $REMOTE_PATH && sudo docker-compose logs --tail=20 nginx"

Write-Host "--- Remote Directory Structure ---" -ForegroundColor Yellow
ssh -i $SSH_KEY $USER@$SERVER_IP "ls -la $REMOTE_PATH && ls -la $REMOTE_PATH/landing"

Write-Host "--- Nginx Internal View ---" -ForegroundColor Yellow
ssh -i $SSH_KEY $USER@$SERVER_IP "sudo docker exec sovereign_nginx ls -la /usr/share/nginx/html"

Write-Host ">>> Diagnostic Done."
