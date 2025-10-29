Write-Host "Building Docker images..." -ForegroundColor Green

Set-Location "c:\Rudra\College\SEM VII\MAP\Practicals\Practical10"

docker build -t webapp:latest ./web_service
docker build -t dbapp:latest ./db_service

Write-Host "`nInitializing Docker Swarm..." -ForegroundColor Green
docker swarm init

Write-Host "`nDeploying stack..." -ForegroundColor Green
docker stack deploy -c docker-compose-swarm.yml iris-app

Write-Host "`nWaiting for services to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

Write-Host "`nServices:" -ForegroundColor Green
docker service ls

Write-Host "`nService details:" -ForegroundColor Green
docker service ps iris-app_webapp
docker service ps iris-app_dbapp

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Deployment complete!" -ForegroundColor Green
Write-Host "Web UI: http://localhost:5000" -ForegroundColor Yellow
Write-Host "Visualizer: http://localhost:8080" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
