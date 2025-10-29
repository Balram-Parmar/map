Write-Host "Removing stack and cleaning up..." -ForegroundColor Green

docker stack rm iris-app

Write-Host "`nWaiting for services to stop..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

Write-Host "`nLeaving swarm mode..." -ForegroundColor Green
docker swarm leave --force

Write-Host "`nCleaning up images (optional)..." -ForegroundColor Yellow
$cleanup = Read-Host "Remove images? (y/n)"
if ($cleanup -eq 'y') {
    docker rmi webapp:latest
    docker rmi dbapp:latest
}

Write-Host "`nCleanup complete!" -ForegroundColor Green
