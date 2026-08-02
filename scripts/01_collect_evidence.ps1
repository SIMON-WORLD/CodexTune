<#
CodexTune - 01_collect_evidence.ps1
Read-only diagnostic collector. Does not modify any data.
Writes an evidence package (JSON) under $OutDir/<timestamp>/.

Optional parameters:
  -ProjectRoot <path>  additionally count skills under <path>\.agents\skills
  -IncludeExtended     collect sessions size, disk free, OneDrive memory,
                       proxy environment, loopback exemption, and config summary

Evidence JSON contains local machine paths; treat it as private and never
commit it to the repository.
#>
param(
    [string]$OutDir = "reports",
    [string]$ProjectRoot = "",
    [switch]$IncludeExtended
)
$ErrorActionPreference = "Continue"
$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$dir = Join-Path $OutDir $stamp
New-Item -ItemType Directory -Path $dir -Force | Out-Null
$report = [ordered]@{}

# 1. Timestamp and related processes
$report.collected_at = (Get-Date -Format "yyyy-MM-dd HH:mm:ss")
$report.codex_processes = @(Get-Process | Where-Object { $_.ProcessName -match 'ChatGPT|codex|node_repl|uvx' } | Select-Object ProcessName, Id, @{N='MemMB';E={[math]::Round($_.WorkingSet64/1MB,0)}}, StartTime)

# 2. Skill roots (read-only)
$skillRoots = @(
    "$env:USERPROFILE\.codex\skills",
    "$env:USERPROFILE\.agents\skills"
)
if ($ProjectRoot) {
    $skillRoots += (Join-Path $ProjectRoot '.agents\skills')
}
$skills = @()
foreach ($r in $skillRoots) {
    if (Test-Path -LiteralPath $r) {
        $md = @(Get-ChildItem -LiteralPath $r -Filter 'SKILL.md' -File -Recurse -Force -ErrorAction SilentlyContinue)
        $skills += [pscustomobject]@{ root = $r; skill_count = $md.Count }
    }
}
$report.skills = $skills

# 3. Plugin staging directories and cached plugin skills
$pluginDirs = @(
    "$env:USERPROFILE\.codex\.tmp\plugins\plugins",
    "$env:USERPROFILE\.codex\plugins\cache"
)
$plugins = @()
foreach ($p in $pluginDirs) {
    if (Test-Path -LiteralPath $p) {
        $dirs = @(Get-ChildItem -LiteralPath $p -Directory -Force -ErrorAction SilentlyContinue)
        $pluginSkills = $null
        if ($p -like '*\plugins\cache*') {
            $pluginSkills = @(Get-ChildItem -LiteralPath $p -Filter 'SKILL.md' -File -Recurse -Force -ErrorAction SilentlyContinue).Count
        }
        $plugins += [pscustomobject]@{ path = $p; plugin_dir_count = $dirs.Count; skill_count = $pluginSkills }
    }
}
$report.plugins = $plugins

# 4. Key database sizes
$dbFiles = @(
    "$env:USERPROFILE\.codex\logs_2.sqlite",
    "$env:USERPROFILE\.codex\state_5.sqlite",
    "$env:USERPROFILE\.codex\session_index.jsonl"
)
$dbs = @()
foreach ($f in $dbFiles) {
    if (Test-Path -LiteralPath $f) {
        $dbs += [pscustomobject]@{ path = $f; size_mb = [math]::Round((Get-Item -LiteralPath $f).Length/1MB, 2) }
    }
}
$report.databases = $dbs

# 5. MCP config audit (flag refresh / latest / install patterns)
$cfg = Join-Path $env:USERPROFILE '.codex\config.toml'
if (Test-Path -LiteralPath $cfg) {
    $lines = Get-Content -LiteralPath $cfg
    $mcp = @()
    $current = $null
    foreach ($line in $lines) {
        if ($line -match '^\[mcp_servers\.([^\]]+)\]') {
            $current = $Matches[1]
        } elseif ($line -match 'refresh|@latest|pip install|npm install') {
            $mcp += [pscustomobject]@{ server = $current; suspicious_line = $line.Trim() }
        }
    }
    $report.mcp_suspicious = $mcp
    $report.config_toml_mcp_server_count = @($lines | Where-Object { $_ -match '^\[mcp_servers\.' }).Count
}

# 6. Extended evidence (optional)
if ($IncludeExtended) {
    $ext = [ordered]@{}
    $ext.sessions = @()
    $sessionRoots = @(
        "$env:USERPROFILE\.codex\sessions",
        "$env:USERPROFILE\.codex\archived_sessions"
    )
    foreach ($s in $sessionRoots) {
        if (Test-Path -LiteralPath $s) {
            $files = @(Get-ChildItem -LiteralPath $s -File -Recurse -Force -ErrorAction SilentlyContinue)
            $totalMB = [math]::Round((($files | Measure-Object Length -Sum).Sum)/1MB, 2)
            $ext.sessions += [pscustomobject]@{ path = $s; file_count = $files.Count; total_mb = $totalMB }
        }
    }
    if (Test-Path -LiteralPath "$env:USERPROFILE\.codex\sessions") {
        $ext.largest_sessions = @(Get-ChildItem -LiteralPath "$env:USERPROFILE\.codex\sessions" -File -Recurse -Force -ErrorAction SilentlyContinue |
            Sort-Object Length -Descending | Select-Object -First 5 FullName, @{N='SizeMB';E={[math]::Round($_.Length/1MB,2)}})
    }
    $ext.c_drive_free_gb = [math]::Round((Get-PSDrive C).Free/1GB, 2)
    $ext.one_drive = @(Get-Process -Name 'OneDrive.Sync.Service' -ErrorAction SilentlyContinue |
        Select-Object ProcessName, Id, @{N='MemMB';E={[math]::Round($_.WorkingSet64/1MB,0)}})
    $ext.proxy_env = [ordered]@{
        HTTP_PROXY = $env:HTTP_PROXY
        HTTPS_PROXY = $env:HTTPS_PROXY
        ALL_PROXY = $env:ALL_PROXY
    }
    $ext.loopback_exempt = @()
    try {
        $ext.loopback_exempt = @(CheckNetIsolation LoopbackExempt -s 2>&1 | Select-Object -First 20)
    } catch {
        $ext.loopback_exempt = @("CheckNetIsolation error: $($_.Exception.Message)")
    }
    $report.extended = $ext
}

# 7. Write evidence package
$json = $report | ConvertTo-Json -Depth 8
$jsonPath = Join-Path $dir 'evidence.json'
Set-Content -LiteralPath $jsonPath -Value $json -Encoding utf8
Write-Output ("Evidence written: " + (Resolve-Path -LiteralPath $jsonPath).Path)
