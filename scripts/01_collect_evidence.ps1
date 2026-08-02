<#
CodexTune - 01_collect_evidence.ps1
Read-only diagnostic collector. Does not modify any data.
Writes an evidence package (JSON) under ./reports/<timestamp>/.
#>
param(
    [string]$OutDir = "reports"
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
$skills = @()
foreach ($r in $skillRoots) {
    if (Test-Path -LiteralPath $r) {
        $md = @(Get-ChildItem -LiteralPath $r -Filter 'SKILL.md' -File -Recurse -Force -ErrorAction SilentlyContinue)
        $skills += [pscustomobject]@{ root = $r; skill_count = $md.Count }
    }
}
$report.skills = $skills

# 3. Plugin staging directories
$pluginDirs = @(
    "$env:USERPROFILE\.codex\.tmp\plugins\plugins",
    "$env:USERPROFILE\.codex\plugins\cache"
)
$plugins = @()
foreach ($p in $pluginDirs) {
    if (Test-Path -LiteralPath $p) {
        $dirs = @(Get-ChildItem -LiteralPath $p -Directory -Force -ErrorAction SilentlyContinue)
        $plugins += [pscustomobject]@{ path = $p; plugin_dir_count = $dirs.Count }
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
}

# 6. Write evidence package
$json = $report | ConvertTo-Json -Depth 6
$jsonPath = Join-Path $dir 'evidence.json'
Set-Content -LiteralPath $jsonPath -Value $json -Encoding utf8
Write-Output ("Evidence written: " + (Resolve-Path -LiteralPath $jsonPath).Path)
