$ErrorActionPreference='Stop'
$projectRoot=$PSScriptRoot
$frontendRoot=Join-Path $projectRoot 'frontend'
$runRoot=Join-Path $projectRoot '.run'
New-Item -ItemType Directory -Path $runRoot -Force | Out-Null
$websiteUrl='http://127.0.0.1:4317'
$buildRoot=Join-Path $frontendRoot 'out'
$processFile=Join-Path $runRoot 'processes.json'
$backendRoot=Join-Path $projectRoot 'backend'

function Start-WocBackend {
 $listener=Get-NetTCPConnection -LocalPort 8317 -State Listen -ErrorAction SilentlyContinue|Select-Object -First 1
 if($listener){
  $existingApi=Get-CimInstance Win32_Process -Filter "ProcessId = $($listener.OwningProcess)" -ErrorAction SilentlyContinue
  if(-not $existingApi -or -not $existingApi.CommandLine -or $existingApi.CommandLine.IndexOf($backendRoot,[StringComparison]::OrdinalIgnoreCase) -lt 0 -or $existingApi.CommandLine -notmatch 'manage\.py.*runserver'){throw 'Port 8317 is used by another application.'}
 }else{
  $api=Start-Process -FilePath (Join-Path $backendRoot '.venv/Scripts/python.exe') -ArgumentList @('manage.py','runserver','127.0.0.1:8317','--noreload') -WorkingDirectory $backendRoot -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $runRoot 'backend.log') -RedirectStandardError (Join-Path $runRoot 'backend-error.log')
 }
 for($check=0;$check -lt 20;$check++){
  try{
   $health=Invoke-WebRequest -UseBasicParsing -Uri 'http://127.0.0.1:8317/api/health/' -TimeoutSec 2
   if($health.StatusCode -eq 200){return (Get-NetTCPConnection -LocalPort 8317 -State Listen|Select-Object -First 1).OwningProcess}
  }catch{}
  Start-Sleep -Milliseconds 200
 }
 throw 'Backend did not become ready. Check .run/backend-error.log.'
}

$backendProcessId=Start-WocBackend

function Get-WocListener {
 $listener=Get-NetTCPConnection -LocalPort 4317 -State Listen -ErrorAction SilentlyContinue|Select-Object -First 1
 if(-not $listener){return $null}
 $serverProcess=Get-CimInstance Win32_Process -Filter "ProcessId = $($listener.OwningProcess)" -ErrorAction SilentlyContinue
 $commandLine=if($serverProcess){[string]$serverProcess.CommandLine}else{''}
 $isStatic=$commandLine.IndexOf($buildRoot,[StringComparison]::OrdinalIgnoreCase) -ge 0 -and $commandLine -match '-m\s+http\.server\s+4317\b'
 $isNext=$commandLine.IndexOf($frontendRoot,[StringComparison]::OrdinalIgnoreCase) -ge 0 -and $commandLine -match '(?i)next[\\/]|next-server|next\s+dev'
 return [pscustomobject]@{ProcessId=$listener.OwningProcess;IsWoc=($isStatic -or $isNext)}
}

function Test-WocWebsite {
 try{return (Invoke-WebRequest -Uri "$websiteUrl/" -UseBasicParsing -MaximumRedirection 0 -TimeoutSec 2).StatusCode -eq 200}
 catch{return $false}
}

$existing=Get-WocListener
if($existing){
 if(-not $existing.IsWoc){throw 'Port 4317 is used by another application. WOC did not stop or replace it.'}
 if(-not (Test-WocWebsite)){throw 'The existing WOC server is not responding successfully. Stop it and retry.'}
 @{frontend=$existing.ProcessId;backend=$backendProcessId}|ConvertTo-Json|Set-Content -LiteralPath $processFile
 Write-Output "WOC is already running. Reusing $websiteUrl"
 exit 0
}

if(-not (Test-Path -LiteralPath (Join-Path $buildRoot 'index.html'))){throw 'Run npm run build inside frontend first.'}
$pythonPath=(Get-Command python.exe).Source
$webProcess=Start-Process -FilePath $pythonPath -ArgumentList @('-m','http.server','4317','--bind','127.0.0.1','--directory',('"'+$buildRoot+'"')) -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $runRoot 'frontend.log') -RedirectStandardError (Join-Path $runRoot 'frontend-error.log')
@{frontend=$webProcess.Id;backend=$backendProcessId}|ConvertTo-Json|Set-Content -LiteralPath $processFile
for($attempt=0;$attempt -lt 30;$attempt++){
 $ready=Get-WocListener
 if($ready -and $ready.IsWoc -and (Test-WocWebsite)){
  @{frontend=$ready.ProcessId;backend=$backendProcessId}|ConvertTo-Json|Set-Content -LiteralPath $processFile
  Write-Output "WOC website: $websiteUrl"
  exit 0
 }
 Start-Sleep -Milliseconds 200
}
throw 'WOC did not become ready. Check .run/frontend-error.log before retrying.'
