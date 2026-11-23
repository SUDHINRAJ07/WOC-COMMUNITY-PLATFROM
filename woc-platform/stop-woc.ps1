$ErrorActionPreference='Stop'
$processFile=Join-Path $PSScriptRoot '.run/processes.json'
if(-not(Test-Path -LiteralPath $processFile)){Write-Output 'No project-owned server record found.';exit}
$ownedProcesses=Get-Content -LiteralPath $processFile -Raw|ConvertFrom-Json
foreach($processId in @($ownedProcesses.frontend,$ownedProcesses.backend)){
 $serverProcess=Get-CimInstance Win32_Process -Filter "ProcessId = $processId" -ErrorAction SilentlyContinue
 if($serverProcess -and $serverProcess.CommandLine -and $serverProcess.CommandLine.Contains($PSScriptRoot)){
  Stop-Process -Id $processId -ErrorAction SilentlyContinue
 }elseif($serverProcess){Write-Warning "Skipped PID $processId because its command does not belong to this project."}
}
Write-Output 'Stopped recorded WOC server processes.'
