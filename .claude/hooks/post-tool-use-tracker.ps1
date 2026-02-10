# Post-tool-use hook that tracks edited files and their modules
# This runs after Edit, MultiEdit, or Write tools complete successfully

$ErrorActionPreference = "SilentlyContinue"

# Read tool information from stdin
$toolInfo = $input | Out-String | ConvertFrom-Json

# Extract relevant data
$toolName = $toolInfo.tool_name
$filePath = $toolInfo.tool_input.file_path
$sessionId = $toolInfo.session_id

# Skip if not an edit tool or no file path
if ($toolName -notmatch "^(Edit|MultiEdit|Write)$" -or [string]::IsNullOrEmpty($filePath)) {
    exit 0
}

# Skip markdown files
if ($filePath -match "\.(md|markdown)$") {
    exit 0
}

# Get project directory
$projectDir = $env:CLAUDE_PROJECT_DIR
if ([string]::IsNullOrEmpty($projectDir)) {
    $projectDir = (Get-Location).Path
}

# Create cache directory
$cacheDir = Join-Path $projectDir ".claude\cache\$sessionId"
if (-not (Test-Path $cacheDir)) {
    New-Item -ItemType Directory -Path $cacheDir -Force | Out-Null
}

# Function to detect module from file path
function Get-ModuleFromPath {
    param([string]$file)

    $relativePath = $file.Replace($projectDir, "").TrimStart("\", "/")
    $firstDir = ($relativePath -split "[/\\]")[0]

    switch ($firstDir) {
        # Stock Dashboard project structure
        "collector"       { return "collector" }
        "research_engine" { return "research_engine" }
        "api"             { return "api" }
        "dashboard"       { return "dashboard" }
        "tools"           { return "tools" }
        "docs"            { return "docs" }
        "tests"           { return "tests" }
        "config"          { return "config" }
        default {
            if ($relativePath -notmatch "[/\\]") {
                return "root"
            }
            return $firstDir
        }
    }
}

# Function to get test command for Python modules
function Get-TestCommand {
    param([string]$module)

    $modulePath = Join-Path $projectDir $module

    switch ($module) {
        "collector"       { return "python -m pytest tests/test_collector/ -v" }
        "research_engine" { return "python -m pytest tests/test_research_engine/ -v" }
        "api"             { return "python -m pytest tests/test_api/ -v" }
        default           { return "" }
    }
}

# Function to get lint command
function Get-LintCommand {
    param([string]$module)

    if ($module -in @("collector", "research_engine", "api", "tools")) {
        return "ruff check $module/"
    }
    return ""
}

# Detect module
$module = Get-ModuleFromPath $filePath

# Skip if unknown or empty
if ([string]::IsNullOrEmpty($module)) {
    exit 0
}

# Log edited file
$timestamp = [DateTimeOffset]::Now.ToUnixTimeSeconds()
$logEntry = "${timestamp}:${filePath}:${module}"
$logFile = Join-Path $cacheDir "edited-files.log"
Add-Content -Path $logFile -Value $logEntry

# Update affected modules list
$affectedFile = Join-Path $cacheDir "affected-modules.txt"
$existingModules = @()
if (Test-Path $affectedFile) {
    $existingModules = Get-Content $affectedFile
}
if ($module -notin $existingModules) {
    Add-Content -Path $affectedFile -Value $module
}

# Store test/lint commands
$commandsFile = Join-Path $cacheDir "commands.txt"
$testCmd = Get-TestCommand $module
$lintCmd = Get-LintCommand $module

$commands = @()
if (Test-Path $commandsFile) {
    $commands = Get-Content $commandsFile
}

if ($testCmd -and "${module}:test:${testCmd}" -notin $commands) {
    Add-Content -Path $commandsFile -Value "${module}:test:${testCmd}"
}
if ($lintCmd -and "${module}:lint:${lintCmd}" -notin $commands) {
    Add-Content -Path $commandsFile -Value "${module}:lint:${lintCmd}"
}

exit 0
