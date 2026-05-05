#Requires -RunAsAdministrator
<#
.SYNOPSIS
    NetBot Windows Agent Installer
.DESCRIPTION
    Downloads and installs the NetBot agent as a scheduled task.
    Run this on any Windows Server you want to monitor.
.EXAMPLE
    .\install.ps1 -BotServer "http://192.168.1.100:8080" -BotToken "your_secret_token"
#>
param(
    [Parameter(Mandatory=$true)]  [string]$BotServer,
    [Parameter(Mandatory=$true)]  [string]$BotToken,
    [string]$InstallPath = "C:\NetBot",
    [int]   $Port        = 7845
)

$ErrorActionPreference = "Stop"

function Write-Step { param($msg) Write-Host "  [+] $msg" -ForegroundColor Cyan }
function Write-OK   { param($msg) Write-Host "  [✓] $msg" -ForegroundColor Green }
function Write-Fail { param($msg) Write-Host "  [✗] $msg" -ForegroundColor Red; exit 1 }

Write-Host ""
Write-Host "╔══════════════════════════════════════════╗" -ForegroundColor Blue
Write-Host "║    NetBot Windows Agent Installer        ║" -ForegroundColor Blue
Write-Host "╚══════════════════════════════════════════╝" -ForegroundColor Blue
Write-Host ""

# Check PowerShell version
if ($PSVersionTable.PSVersion.Major -lt 5) {
    Write-Fail "PowerShell 5.1+ required."
}

# Create install directory
Write-Step "Creating install directory: $InstallPath"
New-Item -ItemType Directory -Force -Path $InstallPath | Out-Null
Write-OK "Directory ready"

# Download agent
Write-Step "Downloading agent from $BotServer..."
try {
    Invoke-WebRequest -Uri "$BotServer/agent/download/windows" -OutFile "$InstallPath\agent.ps1" -UseBasicParsing
    Write-OK "Agent downloaded"
} catch {
    Write-Fail "Could not download agent: $_"
}

# Save config
Write-Step "Saving configuration..."
@{
    BotServer   = $BotServer
    BotToken    = $BotToken
    Port        = $Port
    InstallPath = $InstallPath
} | ConvertTo-Json | Set-Content "$InstallPath\config.json" -Force
Write-OK "Config saved"

# Open firewall port
Write-Step "Opening firewall port $Port..."
$ruleName = "NetBot Agent"
try {
    Remove-NetFirewallRule -DisplayName $ruleName -ErrorAction SilentlyContinue
    New-NetFirewallRule -DisplayName $ruleName -Direction Inbound -Protocol TCP -LocalPort $Port -Action Allow | Out-Null
    Write-OK "Firewall rule created"
} catch {
    Write-Host "  [!] Could not create firewall rule: $_" -ForegroundColor Yellow
}

# Create scheduled task
Write-Step "Creating scheduled task..."
$taskName = "NetBotAgent"
$action   = New-ScheduledTaskAction `
    -Execute "powershell.exe" `
    -Argument "-NonInteractive -WindowStyle Hidden -ExecutionPolicy Bypass -File `"$InstallPath\agent.ps1`" -BotServer `"$BotServer`" -Token `"$BotToken`" -ListenPort `"$Port`""
$trigger    = New-ScheduledTaskTrigger -AtStartup
$settings   = New-ScheduledTaskSettingsSet -ExecutionTimeLimit (New-TimeSpan -Days 365) -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1)
$principal  = New-ScheduledTaskPrincipal -UserId "SYSTEM" -RunLevel Highest

try {
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction SilentlyContinue
    Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger `
        -Settings $settings -Principal $principal -Force | Out-Null
    Start-ScheduledTask -TaskName $taskName
    Write-OK "Scheduled task created and started"
} catch {
    Write-Fail "Could not create scheduled task: $_"
}

# Wait and verify
Write-Step "Verifying agent is running..."
Start-Sleep -Seconds 3
try {
    $response = Invoke-WebRequest -Uri "http://localhost:$Port/health" -UseBasicParsing -TimeoutSec 5
    if ($response.StatusCode -eq 200) {
        Write-OK "Agent health check passed!"
    }
} catch {
    Write-Host "  [!] Agent may not be responding yet. Check: Get-ScheduledTask -TaskName '$taskName'" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "╔══════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║         Installation Complete!            ║" -ForegroundColor Green
Write-Host "╚══════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""
Write-Host "  Computer:  $env:COMPUTERNAME"
Write-Host "  Agent URL: http://$(hostname):$Port"
Write-Host "  Bot Server: $BotServer"
Write-Host ""
Write-Host "  To check status: Get-ScheduledTask -TaskName '$taskName'"
Write-Host "  To view logs:    Get-Content $InstallPath\agent.log -Tail 50"
Write-Host ""
