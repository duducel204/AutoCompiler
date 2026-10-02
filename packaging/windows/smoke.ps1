param(
    [Parameter(Mandatory = $true)]
    [string]$SetupExe
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$SetupExe = (Resolve-Path $SetupExe).Path
$InstallRoot = Join-Path $env:LOCALAPPDATA "AutoCompiler"
$ChromeHostKey = "HKCU:\Software\Google\Chrome\NativeMessagingHosts\com.autocompiler.ready_bridge"
$EdgeHostKey = "HKCU:\Software\Microsoft\Edge\NativeMessagingHosts\com.autocompiler.ready_bridge"

function Invoke-Setup([string[]]$Arguments) {
    $process = Start-Process -FilePath $SetupExe -ArgumentList $Arguments -Wait -PassThru
    if ($process.ExitCode -ne 0) {
        throw "Setup failed with exit code $($process.ExitCode): $($Arguments -join ' ')"
    }
}

function Wait-Canvas() {
    for ($i = 0; $i -lt 80; $i++) {
        try {
            $response = Invoke-RestMethod -Uri "http://127.0.0.1:8765/api/templates" -TimeoutSec 1
            if ($response.ok -and $response.templates.Count -ge 5) {
                return $response
            }
        } catch { }
        Start-Sleep -Milliseconds 250
    }
    throw "Installed Local Canvas did not become reachable."
}

try {
    Write-Host "[smoke] Installing into clean root: $InstallRoot"
    if (Test-Path $InstallRoot) {
        Remove-Item -Recurse -Force $InstallRoot
    }

    Invoke-Setup @("--no-launch", "--no-shortcuts")

    $Python = Join-Path $InstallRoot "runtime\python.exe"
    $App = Join-Path $InstallRoot "app"
    $Bridge = Join-Path $InstallRoot "tools\AutoCompilerReadyBridge.exe"
    $Preflight = Join-Path $InstallRoot "state\install-preflight.json"
    $InstallManifest = Join-Path $InstallRoot "install-manifest.json"

    foreach ($Required in @($Python, $Bridge, $Preflight, $InstallManifest)) {
        if (-not (Test-Path $Required)) {
            throw "Installed product is missing: $Required"
        }
    }

    & $Bridge --self-test | Out-Null
    if ($LASTEXITCODE -ne 0) {
        throw "Installed Ready Bridge failed self-test."
    }

    $PreflightData = Get-Content $Preflight -Raw -Encoding UTF8 | ConvertFrom-Json
    if (-not $PreflightData.supported_platform) {
        throw "Installed AutoCompiler did not recognize the Windows host."
    }

    if (-not (Test-Path $ChromeHostKey) -or -not (Test-Path $EdgeHostKey)) {
        throw "Native Messaging host registration is incomplete."
    }

    $env:AUTOCOMPILER_HOME = $InstallRoot
    $env:AUTOCOMPILER_STATE_ROOT = Join-Path $InstallRoot "state"
    $env:AUTOCOMPILER_GENERATED_ROOT = Join-Path $InstallRoot "generated"

    $StateSentinel = Join-Path $env:AUTOCOMPILER_STATE_ROOT "upgrade-sentinel.txt"
    $GeneratedSentinel = Join-Path $env:AUTOCOMPILER_GENERATED_ROOT "upgrade-sentinel.txt"
    "preserve-state" | Set-Content -Path $StateSentinel -Encoding UTF8
    "preserve-generated" | Set-Content -Path $GeneratedSentinel -Encoding UTF8

    Write-Host "[smoke] Starting installed Local Canvas and keeping it running during upgrade"
    $Process = Start-Process -FilePath $Python -ArgumentList "-m","autocompiler.local_canvas" -WorkingDirectory $App -PassThru
    $Response = Wait-Canvas

    $ReadyUtilities = @($Response.templates | Where-Object { $_.status -eq "ready" })
    if ($ReadyUtilities.Count -lt 5) {
        throw "Installed product does not expose all five W-01 through W-05 ready utilities."
    }

    Write-Host "[smoke] Upgrading in place while Canvas owns the private Python runtime"
    Invoke-Setup @("--no-launch", "--no-shortcuts")

    for ($i = 0; $i -lt 50 -and (-not $Process.HasExited); $i++) {
        $Process.Refresh()
        Start-Sleep -Milliseconds 100
    }
    $Process.Refresh()
    if (-not $Process.HasExited) {
        throw "Old Canvas process remained alive after in-place upgrade."
    }

    if (-not (Test-Path $StateSentinel)) {
        throw "State directory was not preserved across in-place upgrade."
    }
    if (-not (Test-Path $GeneratedSentinel)) {
        throw "Generated directory was not preserved across in-place upgrade."
    }

    $Python = Join-Path $InstallRoot "runtime\python.exe"
    $App = Join-Path $InstallRoot "app"
    if (-not (Test-Path $Python)) {
        throw "Private runtime disappeared during in-place upgrade."
    }

    Write-Host "[smoke] Starting upgraded Canvas"
    $UpgradedProcess = Start-Process -FilePath $Python -ArgumentList "-m","autocompiler.local_canvas" -WorkingDirectory $App -PassThru
    $Response = Wait-Canvas

    Write-Host "[smoke] Uninstalling while upgraded Canvas is still running"
    Invoke-Setup @("--uninstall", "--no-launch", "--no-shortcuts")

    for ($i = 0; $i -lt 40 -and (Test-Path $InstallRoot); $i++) {
        Start-Sleep -Milliseconds 250
    }
    if (Test-Path $InstallRoot) {
        throw "Install root remained after uninstall."
    }

    if ((Test-Path $ChromeHostKey) -or (Test-Path $EdgeHostKey)) {
        throw "Native Messaging registration remained after uninstall."
    }

    $UpgradedProcess.Refresh()
    if (-not $UpgradedProcess.HasExited) {
        throw "Canvas process remained alive after uninstall."
    }

    Write-Host "WINDOWS_PACKAGE_SMOKE_OK"
} finally {
    foreach ($candidate in @($Process, $UpgradedProcess)) {
        if ($candidate) {
            try {
                $candidate.Refresh()
                if (-not $candidate.HasExited) {
                    Stop-Process -Id $candidate.Id -Force -ErrorAction SilentlyContinue
                }
            } catch { }
        }
    }
    if (Test-Path $InstallRoot) {
        Remove-Item -Recurse -Force $InstallRoot -ErrorAction SilentlyContinue
    }
}
