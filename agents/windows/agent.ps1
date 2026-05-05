#Requires -Version 5.1
<#
.SYNOPSIS
    NetBot Windows Agent - Network Monitoring & Control Agent
.DESCRIPTION
    Runs as a Windows Service, reports system metrics to NetBot,
    and accepts commands for AD, DNS, DHCP management.
.NOTES
    Run as Administrator. Requires RSAT tools for AD/DNS/DHCP management.
    Install: .\agent.ps1 -Install -BotServer "http://BOTSERVER:8080" -Token "YOURTOKEN"
#>

param(
    [string]$BotServer   = $env:NETBOT_SERVER,
    [string]$Token       = $env:NETBOT_TOKEN,
    [string]$ListenPort  = "7845",
    [switch]$Install,
    [switch]$Uninstall,
    [switch]$Debug
)

$AgentVersion = "1.0.0"
$ServiceName  = "NetBotAgent"

# ── Logging ───────────────────────────────────────────────────────────────────

$LogPath = "C:\NetBot\agent.log"
New-Item -ItemType Directory -Force -Path "C:\NetBot" | Out-Null

function Write-Log {
    param([string]$Level = "INFO", [string]$Message)
    $ts  = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $line = "[$ts] [$Level] $Message"
    Add-Content -Path $LogPath -Value $line
    if ($Debug) { Write-Host $line }
}

# ── Install / Uninstall ───────────────────────────────────────────────────────

if ($Uninstall) {
    Stop-Service $ServiceName -ErrorAction SilentlyContinue
    sc.exe delete $ServiceName
    Write-Host "NetBot Agent service removed."
    exit 0
}

if ($Install) {
    if (-not $BotServer -or -not $Token) {
        Write-Error "Provide -BotServer and -Token when installing."
        exit 1
    }
    # Save config
    $cfg = @{ BotServer = $BotServer; Token = $Token; ListenPort = $ListenPort }
    $cfg | ConvertTo-Json | Set-Content "C:\NetBot\config.json"

    # Create scheduled task or NSSM service
    $scriptPath = $MyInvocation.MyCommand.Path
    $action  = New-ScheduledTaskAction -Execute "powershell.exe" `
                   -Argument "-NonInteractive -WindowStyle Hidden -File `"$scriptPath`" -BotServer `"$BotServer`" -Token `"$Token`""
    $trigger = New-ScheduledTaskTrigger -AtStartup
    $principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -RunLevel Highest
    Register-ScheduledTask -TaskName $ServiceName -Action $action -Trigger $trigger `
        -Principal $principal -Force
    Start-ScheduledTask -TaskName $ServiceName
    Write-Host "✅ NetBot Agent installed and started."
    Write-Host "   Listening on port $ListenPort, reporting to $BotServer"
    exit 0
}

# ── Load Config ───────────────────────────────────────────────────────────────

if (-not $BotServer -and (Test-Path "C:\NetBot\config.json")) {
    $cfg = Get-Content "C:\NetBot\config.json" | ConvertFrom-Json
    $BotServer  = $cfg.BotServer
    $Token      = $cfg.Token
    $ListenPort = $cfg.ListenPort
}

if (-not $BotServer) {
    Write-Error "BotServer not configured. Run with -Install first."
    exit 1
}

Write-Log "INFO" "NetBot Agent v$AgentVersion starting. Server: $BotServer, Port: $ListenPort"

# ── Detect Installed Roles ────────────────────────────────────────────────────

function Get-InstalledRoles {
    $roles = @()
    try {
        $features = Get-WindowsFeature | Where-Object { $_.Installed -and $_.FeatureType -eq "Role" }
        foreach ($f in $features) {
            switch ($f.Name) {
                "AD-Domain-Services" { $roles += "AD" }
                "DNS"                { $roles += "DNS" }
                "DHCP"               { $roles += "DHCP" }
                "Web-Server"         { $roles += "IIS" }
                "FileAndStorage-Services" { $roles += "FileServer" }
                "Hyper-V"            { $roles += "HyperV" }
            }
        }
    } catch { $roles = @("Unknown") }
    return $roles
}

$InstalledRoles = Get-InstalledRoles
Write-Log "INFO" "Detected roles: $($InstalledRoles -join ', ')"

# ── Metric Collection ─────────────────────────────────────────────────────────

function Get-SystemMetrics {
    $cpu    = [math]::Round((Get-WmiObject Win32_Processor | Measure-Object -Property LoadPercentage -Average).Average, 1)
    $os     = Get-WmiObject Win32_OperatingSystem
    $memTotal = [math]::Round($os.TotalVisibleMemorySize / 1MB, 2)
    $memFree  = [math]::Round($os.FreePhysicalMemory / 1MB, 2)
    $memPct   = [math]::Round((($memTotal - $memFree) / $memTotal) * 100, 1)

    $disks = Get-WmiObject Win32_LogicalDisk -Filter "DriveType=3" | ForEach-Object {
        @{
            Drive   = $_.DeviceID
            TotalGB = [math]::Round($_.Size / 1GB, 1)
            FreeGB  = [math]::Round($_.FreeSpace / 1GB, 1)
            UsedPct = [math]::Round((($_.Size - $_.FreeSpace) / $_.Size) * 100, 1)
        }
    }

    $maxDiskPct = ($disks | Measure-Object -Property UsedPct -Maximum).Maximum

    return @{
        cpu     = $cpu
        memory  = $memPct
        disk    = $maxDiskPct
        disks   = $disks
        uptime  = (Get-Date) - (Get-CimInstance Win32_OperatingSystem).LastBootUpTime | ForEach-Object { "$($_.Days)d $($_.Hours)h $($_.Minutes)m" }
    }
}

function Get-AgentInfo {
    $metrics = Get-SystemMetrics
    return @{
        agent    = "netbot"
        hostname = $env:COMPUTERNAME
        os       = "windows"
        version  = $AgentVersion
        roles    = $InstalledRoles
        cpu      = $metrics.cpu
        memory   = $metrics.memory
        disk     = $metrics.disk
        uptime   = $metrics.uptime[0]
    }
}

# ── AD Management ─────────────────────────────────────────────────────────────

function Invoke-ADCommand {
    param([string]$Action, [array]$Args)

    if (-not (Get-Module -ListAvailable -Name ActiveDirectory)) {
        return "❌ ActiveDirectory module not available. Install RSAT-AD-PowerShell."
    }
    Import-Module ActiveDirectory -ErrorAction SilentlyContinue

    switch ($Action) {
        "ad_users" {
            $users = Get-ADUser -Filter * -Properties DisplayName, EmailAddress, Enabled, LastLogonDate |
                Select-Object SamAccountName, DisplayName, Enabled, LastLogonDate |
                Sort-Object SamAccountName | Select-Object -First 50
            return ($users | Format-Table -AutoSize | Out-String).Trim()
        }
        "ad_groups" {
            $groups = Get-ADGroup -Filter * | Sort-Object Name | Select-Object -First 50
            return ($groups | Format-Table Name, GroupScope, GroupCategory -AutoSize | Out-String).Trim()
        }
        "ad_create" {
            if ($Args.Count -lt 2) { return "Usage: ad_create <username> <password> [OU]" }
            $user  = $Args[0]; $pass = $Args[1]
            $ou    = if ($Args[2]) { $Args[2] } else { (Get-ADDomain).UsersContainer }
            $secPw = ConvertTo-SecureString $pass -AsPlainText -Force
            New-ADUser -Name $user -SamAccountName $user -AccountPassword $secPw `
                       -Path $ou -Enabled $true -ChangePasswordAtLogon $true
            Write-Log "INFO" "AD user created: $user"
            return "✅ User '$user' created successfully. Must change password at next logon."
        }
        "ad_reset" {
            if ($Args.Count -lt 2) { return "Usage: ad_reset <username> <newpassword>" }
            $user  = $Args[0]; $pass = $Args[1]
            $secPw = ConvertTo-SecureString $pass -AsPlainText -Force
            Set-ADAccountPassword -Identity $user -NewPassword $secPw -Reset
            Set-ADUser -Identity $user -ChangePasswordAtLogon $true
            Write-Log "INFO" "AD password reset: $user"
            return "✅ Password reset for '$user'. User must change password at logon."
        }
        "ad_disable" {
            if ($Args.Count -lt 1) { return "Usage: ad_disable <username>" }
            Disable-ADAccount -Identity $Args[0]
            Write-Log "INFO" "AD user disabled: $($Args[0])"
            return "✅ User '$($Args[0])' disabled."
        }
        "ad_enable" {
            if ($Args.Count -lt 1) { return "Usage: ad_enable <username>" }
            Enable-ADAccount -Identity $Args[0]
            return "✅ User '$($Args[0])' enabled."
        }
        "ad_search" {
            if ($Args.Count -lt 1) { return "Usage: ad_search <name>" }
            $results = Get-ADUser -Filter "Name -like '*$($Args[0])*'" -Properties DisplayName, Enabled |
                Select-Object SamAccountName, DisplayName, Enabled
            return ($results | Format-Table -AutoSize | Out-String).Trim()
        }
        "ad_lockout" {
            $locked = Search-ADAccount -LockedOut | Select-Object Name, SamAccountName, LockedOut
            return ($locked | Format-Table -AutoSize | Out-String).Trim()
        }
        "ad_unlock" {
            if ($Args.Count -lt 1) { return "Usage: ad_unlock <username>" }
            Unlock-ADAccount -Identity $Args[0]
            return "✅ Account '$($Args[0])' unlocked."
        }
        default { return "Unknown AD action: $Action" }
    }
}

# ── DNS Management ────────────────────────────────────────────────────────────

function Invoke-DNSCommand {
    param([string]$Action, [array]$Args)

    if (-not (Get-Module -ListAvailable -Name DnsServer)) {
        return "❌ DnsServer module not available."
    }
    Import-Module DnsServer -ErrorAction SilentlyContinue

    switch ($Action) {
        "dns" {
            $zones = Get-DnsServerZone | Select-Object ZoneName, ZoneType, IsAutoCreated, IsDsIntegrated
            return ($zones | Format-Table -AutoSize | Out-String).Trim()
        }
        "dns_records" {
            $zone = if ($Args[0]) { $Args[0] } else { (Get-DnsServerZone | Where-Object ZoneType -eq "Primary" | Select-Object -First 1).ZoneName }
            $records = Get-DnsServerResourceRecord -ZoneName $zone | Select-Object HostName, RecordType, RecordData |
                Sort-Object RecordType, HostName | Select-Object -First 40
            return "Zone: $zone`n" + ($records | Format-Table -AutoSize | Out-String).Trim()
        }
        "dns_add" {
            # dns_add <zone> <name> <type> <value>
            if ($Args.Count -lt 4) { return "Usage: dns_add <zone> <name> A <ip>" }
            Add-DnsServerResourceRecordA -ZoneName $Args[0] -Name $Args[1] -IPv4Address $Args[3]
            return "✅ DNS record added: $($Args[1]).$($Args[0]) A $($Args[3])"
        }
        default { return "Unknown DNS action: $Action" }
    }
}

# ── DHCP Management ───────────────────────────────────────────────────────────

function Invoke-DHCPCommand {
    param([string]$Action, [array]$Args)

    if (-not (Get-Module -ListAvailable -Name DhcpServer)) {
        return "❌ DhcpServer module not available."
    }
    Import-Module DhcpServer -ErrorAction SilentlyContinue

    switch ($Action) {
        "dhcp" {
            $scopes = Get-DhcpServerv4Scope | Select-Object ScopeId, Name, StartRange, EndRange, SubnetMask, State
            return ($scopes | Format-Table -AutoSize | Out-String).Trim()
        }
        "dhcp_leases" {
            $scope = $Args[0]
            if (-not $scope) {
                $scope = (Get-DhcpServerv4Scope | Select-Object -First 1).ScopeId
            }
            $leases = Get-DhcpServerv4Lease -ScopeId $scope | Select-Object IPAddress, ClientId, HostName, LeaseExpiryTime |
                Sort-Object IPAddress | Select-Object -First 50
            return "DHCP Leases for $scope`n" + ($leases | Format-Table -AutoSize | Out-String).Trim()
        }
        "dhcp_stats" {
            $stats = Get-DhcpServerv4ScopeStatistics
            return ($stats | Format-Table -AutoSize | Out-String).Trim()
        }
        default { return "Unknown DHCP action: $Action" }
    }
}

# ── General System Commands ───────────────────────────────────────────────────

function Invoke-SystemCommand {
    param([string]$Action, [array]$Args)

    switch ($Action) {
        "stats" {
            $m = Get-SystemMetrics
            $out  = "=== System Stats: $env:COMPUTERNAME ===`n"
            $out += "CPU:    $($m.cpu)%`n"
            $out += "Memory: $($m.memory)%`n"
            $out += "Uptime: $($m.uptime)`n`nDisks:`n"
            foreach ($d in $m.disks) {
                $out += "  $($d.Drive) $($d.UsedPct)% used ($($d.FreeGB) GB free of $($d.TotalGB) GB)`n"
            }
            return $out
        }
        "services" {
            $svcs = Get-Service | Where-Object { $_.StartType -ne "Disabled" } |
                Sort-Object Status, DisplayName |
                Select-Object -First 40 |
                Select-Object DisplayName, Status, StartType
            return ($svcs | Format-Table -AutoSize | Out-String).Trim()
        }
        "processes" {
            $procs = Get-Process | Sort-Object CPU -Descending | Select-Object -First 20 |
                Select-Object ProcessName, Id, CPU, WorkingSet
            return ($procs | Format-Table -AutoSize | Out-String).Trim()
        }
        "eventlog" {
            $events = Get-EventLog -LogName System -EntryType Error,Warning -Newest 20 |
                Select-Object TimeGenerated, EntryType, Source, Message
            $out = ""
            foreach ($e in $events) {
                $out += "[$($e.TimeGenerated)] [$($e.EntryType)] $($e.Source)`n"
                $out += "  $($e.Message.Substring(0, [Math]::Min(100, $e.Message.Length)))`n"
            }
            return $out
        }
        "metrics" {
            $m = Get-SystemMetrics
            return @{
                cpu    = $m.cpu
                memory = $m.memory
                disk   = $m.disk
            } | ConvertTo-Json
        }
        "netstat" {
            return (netstat -ano | Select-Object -First 40) -join "`n"
        }
        default { return "Unknown action: $Action" }
    }
}

# ── HMAC Signature Verification ───────────────────────────────────────────────

function Test-Signature {
    param([string]$Timestamp, [string]$Signature, [string]$Body)
    $secret = $Token
    $data   = "${Timestamp}:${Body}"
    $keyBytes  = [System.Text.Encoding]::UTF8.GetBytes($secret)
    $dataBytes = [System.Text.Encoding]::UTF8.GetBytes($data)
    $hmac = New-Object System.Security.Cryptography.HMACSHA256
    $hmac.Key = $keyBytes
    $hash = $hmac.ComputeHash($dataBytes)
    $expected = [BitConverter]::ToString($hash).Replace("-","").ToLower()
    return ($expected -eq $Signature)
}

# ── HTTP Listener ─────────────────────────────────────────────────────────────

function Start-HttpListener {
    $listener = New-Object System.Net.HttpListener
    $listener.Prefixes.Add("http://+:$ListenPort/")
    $listener.Start()
    Write-Log "INFO" "HTTP listener started on port $ListenPort"

    # Register with bot server
    Register-WithBot

    while ($listener.IsListening) {
        try {
            $context  = $listener.GetContext()
            $request  = $context.Request
            $response = $context.Response

            $path   = $request.Url.AbsolutePath
            $method = $request.HttpMethod

            Write-Log "DEBUG" "$method $path"

            # /info endpoint — no auth required (discovery)
            if ($path -eq "/info" -and $method -eq "GET") {
                $info = Get-AgentInfo | ConvertTo-Json
                $buf  = [System.Text.Encoding]::UTF8.GetBytes($info)
                $response.ContentType   = "application/json"
                $response.ContentLength64 = $buf.Length
                $response.OutputStream.Write($buf, 0, $buf.Length)
                $response.Close()
                continue
            }

            # /command endpoint — HMAC auth required
            if ($path -eq "/command" -and $method -eq "POST") {
                $body = New-Object System.IO.StreamReader($request.InputStream)
                $bodyStr = $body.ReadToEnd()
                $ts  = $request.Headers["X-Timestamp"]
                $sig = $request.Headers["X-Signature"]

                if (-not (Test-Signature $ts $sig $bodyStr)) {
                    $response.StatusCode = 401
                    $response.Close()
                    Write-Log "WARN" "Rejected request with invalid signature"
                    continue
                }

                $cmd    = $bodyStr | ConvertFrom-Json
                $action = $cmd.action
                $args   = @($cmd.args)

                Write-Log "INFO" "Command: $action ($($args -join ' '))"

                $result = switch -Regex ($action) {
                    "^ad_"     { Invoke-ADCommand   $action $args }
                    "^dns"     { Invoke-DNSCommand   $action $args }
                    "^dhcp"    { Invoke-DHCPCommand  $action $args }
                    "^metrics$"{ Invoke-SystemCommand $action $args }
                    default    { Invoke-SystemCommand $action $args }
                }

                # If result is JSON (from metrics), wrap it differently
                $responseObj = if ($action -eq "metrics") {
                    @{ metrics = ($result | ConvertFrom-Json) } | ConvertTo-Json
                } else {
                    @{ result = $result } | ConvertTo-Json
                }

                $buf = [System.Text.Encoding]::UTF8.GetBytes($responseObj)
                $response.ContentType     = "application/json"
                $response.ContentLength64 = $buf.Length
                $response.OutputStream.Write($buf, 0, $buf.Length)
                $response.Close()
                continue
            }

            # Health check
            if ($path -eq "/health") {
                $buf = [System.Text.Encoding]::UTF8.GetBytes('{"status":"ok"}')
                $response.ContentType = "application/json"
                $response.OutputStream.Write($buf, 0, $buf.Length)
                $response.Close()
                continue
            }

            $response.StatusCode = 404
            $response.Close()

        } catch {
            Write-Log "ERROR" "Listener error: $_"
        }
    }
}

function Register-WithBot {
    if (-not $BotServer) { return }
    try {
        $info = Get-AgentInfo
        $info["url"] = "http://$($env:COMPUTERNAME):$ListenPort"
        # Try both hostname and IP
        try {
            $ip = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.InterfaceAlias -notlike "*Loopback*" } | Select-Object -First 1).IPAddress
            $info["url"] = "http://${ip}:${ListenPort}"
            $info["ip"]  = $ip
        } catch {}
        $body = $info | ConvertTo-Json
        Invoke-RestMethod -Uri "$BotServer/agent/register" -Method POST `
            -Body $body -ContentType "application/json" -TimeoutSec 10
        Write-Log "INFO" "Registered with bot server at $BotServer"
    } catch {
        Write-Log "WARN" "Could not register with bot server: $_"
    }
}

# ── Entry Point ───────────────────────────────────────────────────────────────

Write-Log "INFO" "Starting NetBot Windows Agent v$AgentVersion"
Write-Log "INFO" "Computer: $env:COMPUTERNAME | Roles: $($InstalledRoles -join ', ')"

# Start heartbeat in background
$heartbeatJob = Start-Job -ScriptBlock {
    param($Server, $AgentPath, $Port, $Token)
    while ($true) {
        Start-Sleep -Seconds 25
        try {
            # Re-register to update metrics
            . $AgentPath
        } catch {}
    }
} -ArgumentList $BotServer, $MyInvocation.MyCommand.Path, $ListenPort, $Token

Start-HttpListener
