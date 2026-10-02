param(
    [Parameter(Mandatory = $true)]
    [string]$PayloadRoot,

    [switch]$NoLaunch,
    [switch]$NoShortcuts,
    [switch]$Uninstall
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Write-InstallLog([string]$Message) {
    $stamp = (Get-Date).ToUniversalTime().ToString("o")
    $line = $stamp + " " + $Message
    Write-Host "[AutoCompiler] $Message"
    if ($script:LogPath) {
        Add-Content -Path $script:LogPath -Value $line -Encoding UTF8
    }
}

function Stop-AutoCompilerOwnedProcesses([string]$Root) {
    if (-not (Test-Path $Root)) {
        return
    }

    $prefix = [System.IO.Path]::GetFullPath($Root).TrimEnd("\") + "\"
    $allowedNames = @("python.exe", "pythonw.exe", "AutoCompilerReadyBridge.exe")
    $stopped = @()

    $processes = Get-CimInstance Win32_Process -ErrorAction SilentlyContinue
    foreach ($proc in $processes) {
        $exe = $proc.ExecutablePath
        if (-not $exe) {
            continue
        }

        try {
            $full = [System.IO.Path]::GetFullPath($exe)
        } catch {
            continue
        }

        $name = [System.IO.Path]::GetFileName($full)
        $owned = $full.StartsWith($prefix, [System.StringComparison]::OrdinalIgnoreCase)
        if ($owned -and ($allowedNames -contains $name)) {
            try {
                Write-InstallLog ("Stopping running AutoCompiler process " + $proc.ProcessId + " (" + $name + ").")
                Stop-Process -Id $proc.ProcessId -Force -ErrorAction Stop
                $stopped += [int]$proc.ProcessId
            } catch {
                throw "Could not stop running AutoCompiler process $($proc.ProcessId): $($_.Exception.Message)"
            }
        }
    }

    foreach ($processId in $stopped) {
        for ($i = 0; $i -lt 50; $i++) {
            if (-not (Get-Process -Id $processId -ErrorAction SilentlyContinue)) {
                break
            }
            Start-Sleep -Milliseconds 100
        }

        if (Get-Process -Id $processId -ErrorAction SilentlyContinue) {
            throw "AutoCompiler process $processId did not stop before upgrade."
        }
    }
}

function New-Shortcut([string]$Path, [string]$Target, [string]$Arguments, [string]$WorkingDirectory, [string]$Description) {
    $shell = New-Object -ComObject WScript.Shell
    $shortcut = $shell.CreateShortcut($Path)
    $shortcut.TargetPath = $Target
    $shortcut.Arguments = $Arguments
    $shortcut.WorkingDirectory = $WorkingDirectory
    $shortcut.Description = $Description
    $shortcut.Save()
}

function Find-Browser([string]$Name) {
    $programFiles = [Environment]::GetFolderPath("ProgramFiles")
    $programFilesX86 = [Environment]::GetFolderPath("ProgramFilesX86")
    $candidates = @()
    if ($Name -eq "edge") {
        $candidates += (Join-Path $programFilesX86 "Microsoft\Edge\Application\msedge.exe")
        $candidates += (Join-Path $programFiles "Microsoft\Edge\Application\msedge.exe")
        $candidates += (Join-Path $env:LOCALAPPDATA "Microsoft\Edge\Application\msedge.exe")
    } elseif ($Name -eq "chrome") {
        $candidates += (Join-Path $programFiles "Google\Chrome\Application\chrome.exe")
        $candidates += (Join-Path $programFilesX86 "Google\Chrome\Application\chrome.exe")
        $candidates += (Join-Path $env:LOCALAPPDATA "Google\Chrome\Application\chrome.exe")
    }
    foreach ($candidate in $candidates) {
        if ($candidate -and (Test-Path $candidate)) {
            return $candidate
        }
    }
    return $null
}

$InstallRoot = [System.IO.Path]::GetFullPath((Join-Path $env:LOCALAPPDATA "AutoCompiler"))
$script:LogPath = $null

if ($Uninstall) {
    Stop-AutoCompilerOwnedProcesses $InstallRoot
    $Programs = [Environment]::GetFolderPath("Programs")
    foreach ($name in @("AutoCompiler.lnk", "AutoCompiler Edge.lnk", "AutoCompiler Chrome.lnk")) {
        $shortcut = Join-Path $Programs $name
        if (Test-Path $shortcut) {
            Remove-Item -Force $shortcut
        }
    }

    foreach ($key in @(
        "HKCU:\Software\Google\Chrome\NativeMessagingHosts\com.autocompiler.ready_bridge",
        "HKCU:\Software\Microsoft\Edge\NativeMessagingHosts\com.autocompiler.ready_bridge",
        "HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\AutoCompiler"
    )) {
        if (Test-Path $key) {
            Remove-Item -Recurse -Force $key
        }
    }

    foreach ($name in @(
        "app", "runtime", "tools", "state", "generated", "browser",
        "app.next", "runtime.next", "tools.next"
    )) {
        $path = Join-Path $InstallRoot $name
        if (Test-Path $path) {
            Remove-Item -Recurse -Force $path
        }
    }

    foreach ($name in @("install-manifest.json", "install.log")) {
        $path = Join-Path $InstallRoot $name
        if (Test-Path $path) {
            Remove-Item -Force $path
        }
    }
    exit 0
}

New-Item -ItemType Directory -Force -Path $InstallRoot | Out-Null
$script:LogPath = Join-Path $InstallRoot "install.log"
Write-InstallLog "Starting installation."
Stop-AutoCompilerOwnedProcesses $InstallRoot

$PayloadManifestPath = Join-Path $PayloadRoot "payload-manifest.json"
if (-not (Test-Path $PayloadManifestPath)) {
    throw "Invalid AutoCompiler payload: payload-manifest.json is missing."
}
$PayloadManifest = Get-Content $PayloadManifestPath -Raw -Encoding UTF8 | ConvertFrom-Json

$AppSource = Join-Path $PayloadRoot "app"
$RuntimeSource = Join-Path $PayloadRoot "runtime"
$ToolsSource = Join-Path $PayloadRoot "tools"

$AppTarget = Join-Path $InstallRoot "app"
$RuntimeTarget = Join-Path $InstallRoot "runtime"
$ToolsTarget = Join-Path $InstallRoot "tools"
$StateTarget = Join-Path $InstallRoot "state"
$GeneratedTarget = Join-Path $InstallRoot "generated"
$BrowserTarget = Join-Path $InstallRoot "browser"

foreach ($path in @($StateTarget, $GeneratedTarget, $BrowserTarget)) {
    New-Item -ItemType Directory -Force -Path $path | Out-Null
}

foreach ($name in @("app.next", "runtime.next", "tools.next")) {
    $path = Join-Path $InstallRoot $name
    if (Test-Path $path) {
        Remove-Item -Recurse -Force $path
    }
}

$AppNext = Join-Path $InstallRoot "app.next"
$RuntimeNext = Join-Path $InstallRoot "runtime.next"
$ToolsNext = Join-Path $InstallRoot "tools.next"
Copy-Item -Recurse -Force $AppSource $AppNext
Copy-Item -Recurse -Force $RuntimeSource $RuntimeNext
Copy-Item -Recurse -Force $ToolsSource $ToolsNext

$PythonNext = Join-Path $RuntimeNext "python.exe"
if (-not (Test-Path $PythonNext)) {
    throw "Bundled Python runtime is missing."
}

$env:AUTOCOMPILER_HOME = $InstallRoot
$env:AUTOCOMPILER_STATE_ROOT = $StateTarget
$env:AUTOCOMPILER_GENERATED_ROOT = $GeneratedTarget

foreach ($pair in @(
    @($AppTarget, $AppNext),
    @($RuntimeTarget, $RuntimeNext),
    @($ToolsTarget, $ToolsNext)
)) {
    $current = $pair[0]
    $next = $pair[1]
    if (Test-Path $current) {
        Remove-Item -Recurse -Force $current
    }
    Move-Item -Path $next -Destination $current
}

$Python = Join-Path $RuntimeTarget "python.exe"
$PythonW = Join-Path $RuntimeTarget "pythonw.exe"
if (-not (Test-Path $PythonW)) {
    $PythonW = $Python
}

Write-InstallLog "Verifying private Python runtime and AutoCompiler imports."
Push-Location $AppTarget
try {
    & $Python -c "import sys; import autocompiler; import autocompiler.local_canvas; import autocompiler.workflow_lifecycle; print(sys.version)"
    if ($LASTEXITCODE -ne 0) {
        throw "Private runtime verification failed."
    }
} finally {
    Pop-Location
}

$BridgeExe = Join-Path $ToolsTarget "AutoCompilerReadyBridge.exe"
if (-not (Test-Path $BridgeExe)) {
    throw "Ready Bridge executable is missing."
}
& $BridgeExe --self-test | Out-Null
if ($LASTEXITCODE -ne 0) {
    throw "Ready Bridge self-test failed."
}

$ExtensionSource = Join-Path $AppTarget "web\ready-automations\browser-selection-powershell"
$ExtensionTarget = Join-Path $BrowserTarget "extension"
if (Test-Path $ExtensionTarget) {
    Remove-Item -Recurse -Force $ExtensionTarget
}
Copy-Item -Recurse -Force $ExtensionSource $ExtensionTarget

$NativeTemplate = Join-Path $ExtensionTarget "native-host-manifest.template.json"
$NativeManifestPath = Join-Path $BrowserTarget "com.autocompiler.ready_bridge.json"
$NativeManifest = Get-Content $NativeTemplate -Raw -Encoding UTF8 | ConvertFrom-Json
$NativeManifest.path = $BridgeExe
$NativeManifest | ConvertTo-Json -Depth 8 | Set-Content -Path $NativeManifestPath -Encoding UTF8

foreach ($key in @(
    "HKCU:\Software\Google\Chrome\NativeMessagingHosts\com.autocompiler.ready_bridge",
    "HKCU:\Software\Microsoft\Edge\NativeMessagingHosts\com.autocompiler.ready_bridge"
)) {
    New-Item -Path $key -Force | Out-Null
    Set-Item -Path $key -Value $NativeManifestPath
}

Write-InstallLog "Running Windows Automation Base preflight."
$PreflightScript = Join-Path $StateTarget "install_preflight.py"
$PreflightOutput = Join-Path $StateTarget "install-preflight.json"
$PreflightSource = @'
import json
import os
from pathlib import Path
from autocompiler.first_run import build_machine_preflight

state_root = Path(os.environ["AUTOCOMPILER_STATE_ROOT"])
preflight, _ = build_machine_preflight(local_catalog_path=state_root / "capabilities.json")
target = Path(os.environ["AUTOCOMPILER_PREFLIGHT_OUTPUT"])
target.write_text(json.dumps(preflight, indent=2, ensure_ascii=False), encoding="utf-8")
print(json.dumps({
    "supported_platform": preflight.get("supported_platform"),
    "automation_ready": preflight.get("automation_ready"),
    "phase": preflight.get("phase"),
    "missing_required": preflight.get("missing_required", [])
}, ensure_ascii=False))
'@
Set-Content -Path $PreflightScript -Value $PreflightSource -Encoding UTF8
$env:AUTOCOMPILER_PREFLIGHT_OUTPUT = $PreflightOutput
Push-Location $AppTarget
try {
    & $Python $PreflightScript
    if ($LASTEXITCODE -ne 0) {
        throw "Automation Base preflight failed."
    }
} finally {
    Pop-Location
    Remove-Item -Force $PreflightScript -ErrorAction SilentlyContinue
}

$Programs = [Environment]::GetFolderPath("Programs")
if (-not $NoShortcuts) {
    $MainShortcut = Join-Path $Programs "AutoCompiler.lnk"
    New-Shortcut $MainShortcut $PythonW "-m autocompiler.desktop_launcher" $AppTarget "Open AutoCompiler"

    $Edge = Find-Browser "edge"
    if ($Edge) {
        $EdgeProfile = Join-Path $BrowserTarget "edge-profile"
        New-Item -ItemType Directory -Force -Path $EdgeProfile | Out-Null
        $EdgeArgs = "--user-data-dir=" + [char]34 + $EdgeProfile + [char]34 + " --load-extension=" + [char]34 + $ExtensionTarget + [char]34
        New-Shortcut (Join-Path $Programs "AutoCompiler Edge.lnk") $Edge $EdgeArgs $InstallRoot "Edge with AutoCompiler Ready Actions"
    }

    $Chrome = Find-Browser "chrome"
    if ($Chrome) {
        $ChromeProfile = Join-Path $BrowserTarget "chrome-profile"
        New-Item -ItemType Directory -Force -Path $ChromeProfile | Out-Null
        $ChromeArgs = "--user-data-dir=" + [char]34 + $ChromeProfile + [char]34 + " --load-extension=" + [char]34 + $ExtensionTarget + [char]34
        New-Shortcut (Join-Path $Programs "AutoCompiler Chrome.lnk") $Chrome $ChromeArgs $InstallRoot "Chrome with AutoCompiler Ready Actions"
    }
}

$SetupSource = $env:AUTOCOMPILER_SETUP_SOURCE
if ($SetupSource -and (Test-Path $SetupSource)) {
    Copy-Item -Force $SetupSource (Join-Path $InstallRoot "AutoCompilerSetup.exe")
}

$UninstallExe = Join-Path $InstallRoot "AutoCompilerSetup.exe"
$UninstallKey = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\AutoCompiler"
New-Item -Path $UninstallKey -Force | Out-Null
Set-ItemProperty -Path $UninstallKey -Name "DisplayName" -Value "AutoCompiler"
Set-ItemProperty -Path $UninstallKey -Name "DisplayVersion" -Value ([string]$PayloadManifest.version)
Set-ItemProperty -Path $UninstallKey -Name "Publisher" -Value "AutoCompiler"
Set-ItemProperty -Path $UninstallKey -Name "InstallLocation" -Value $InstallRoot
if (Test-Path $UninstallExe) {
    $UninstallString = [char]34 + $UninstallExe + [char]34 + " --uninstall --no-launch --no-shortcuts"
    Set-ItemProperty -Path $UninstallKey -Name "UninstallString" -Value $UninstallString
}

$InstallManifest = [ordered]@{
    schema_version = "1.0"
    installed_at = (Get-Date).ToUniversalTime().ToString("o")
    version = [string]$PayloadManifest.version
    python_version = [string]$PayloadManifest.python_version
    install_root = $InstallRoot
    app_root = $AppTarget
    state_root = $StateTarget
    generated_root = $GeneratedTarget
    extension_id = "feadcfjinjckfhcdonlmajcdpfjimgmo"
    native_host = $NativeManifestPath
    preflight = $PreflightOutput
}
$InstallManifest | ConvertTo-Json -Depth 8 | Set-Content -Path (Join-Path $InstallRoot "install-manifest.json") -Encoding UTF8

Write-InstallLog "Installation completed."

if (-not $NoLaunch) {
    Start-Process -FilePath $PythonW -ArgumentList "-m","autocompiler.desktop_launcher" -WorkingDirectory $AppTarget
}

exit 0
