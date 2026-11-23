$ErrorActionPreference='Stop'
$projectRoot=$PSScriptRoot
$frontendRoot=Join-Path $projectRoot 'frontend'
$backendRoot=Join-Path $projectRoot 'backend'
$runRoot=Join-Path $projectRoot '.run'
New-Item -ItemType Directory -Path $runRoot -Force | Out-Null
if(-not (Test-Path -LiteralPath (Join-Path $frontendRoot 'out/index.html'))){throw 'Run npm run build inside frontend first.'}
foreach($port in @(4317,8317)){
 if(Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue){throw "Port $port is already in use. Stop the existing WOC servers with stop-woc.ps1, or use the running URL."}
}
$pythonPath=(Get-Command python.exe).Source
$webProcess=Start-Process -FilePath $pythonPath -ArgumentList @('-m','http.server','4317','--bind','127.0.0.1','--directory',('"'+(Join-Path $frontendRoot 'out')+'"')) -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $runRoot 'frontend.log') -RedirectStandardError (Join-Path $runRoot 'frontend-error.log')
$apiProcess=Start-Process -FilePath (Join-Path $backendRoot '.venv/Scripts/python.exe') -ArgumentList @((Join-Path $backendRoot 'manage.py'),'runserver','127.0.0.1:8317','--noreload') -WorkingDirectory $backendRoot -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $runRoot 'backend.log') -RedirectStandardError (Join-Path $runRoot 'backend-error.log')
@{frontend=$webProcess.Id;backend=$apiProcess.Id}|ConvertTo-Json|Set-Content -LiteralPath (Join-Path $runRoot 'processes.json')
Write-Output 'WOC website: http://127.0.0.1:4317'
Write-Output 'WOC API: http://127.0.0.1:8317/api/health/'
