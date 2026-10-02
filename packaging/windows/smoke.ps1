param(
    [Parameter(Mandatory = $true)]
    [string]$SetupExe
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$SetupExe = (Resolve-Path $SetupExe).Path
$InstallRoot = Join-Path $env:RUNNER_TEMP ("AutoCompiler-Smoke-" + [Guid]::NewGuid().ToString("N"))

try {
    Write-Host "[smoke] Installing into clean root: $InstallRoot"
    $InstallProcess = Start-Process -FilePath $SetupExe -ArgumentList @(
        "--install-root", $InstallRoot, "--no-launch", "--no-shortcuts"
    ) -Wait -PassThru
    if ($InstallProcess.ExitCode -ne 0) {
        throw "Setup failed with exit code $($InstallProcess.ExitCode)"
    }

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

    $ChromeHostKey = "HKCU:\Software\Google\Chrome\NativeMessagingHosts\com.autocompiler.ready_bridge"
    $EdgeHostKey = "HKCU:\Software\Microsoft\Edge\NativeMessagingHosts\com.autocompiler.ready_bridge"
    if (-not (Test-Path $ChromeHostKey) -or -not (Test-Path $EdgeHostKey)) {
        throw "Native Messaging host registration is incomplete."
    }

    $env:AUTOCOMPILER_HOME = $InstallRoot
    $env:AUTOCOMPILER_STATE_ROOT = Join-Path $InstallRoot "state"
    $env:AUTOCOMPILER_GENERATED_ROOT = Join-Path $InstallRoot "generated"

    Write-Host "[smoke] Starting installed Local Canvas"
    $Process = Start-Process -FilePath $Python -ArgumentList "-m","autocompiler.local_canvas" -WorkingDirectory $App -PassThru
    try {
        $Ready = $false
        for ($i = 0; $i -lt 80; $i++) {
            try {
                $Response = Invoke-RestMethod -Uri "http://127.0.0.1:8765/api/templates" -TimeoutSec 1
                if ($Response.ok -and $Response.templates.Count -ge 5) {
                    $Ready = $true
                    break
                }
            } catch { }
            Start-Sleep -Milliseconds 250
        }
        if (-not $Ready) {
            throw "Installed Local Canvas did not become reachable."
        }

        $ReadyUtilities = @($Response.templates | Where-Object { $_.status -eq "ready" })
        if ($ReadyUtilities.Count -lt 5) {
            throw "Installed product does not expose all five W-01 through W-05 ready utilities."
        }
    } finally {
        if ($Process -and -not $Process.HasExited) {
            Stop-Process -Id $Process.Id -Force
        }
    }

    Write-Host "[smoke] Uninstalling"
    $UninstallProcess = Start-Process -FilePath $SetupExe -ArgumentList @(
        "--install-root", $InstallRoot, "--uninstall", "--no-launch", "--no-shortcuts"
    ) -Wait -PassThru
    if ($UninstallProcess.ExitCode -ne 0) {
        throw "Uninstall failed with exit code $($UninstallProcess.ExitCode)"
    }

    for ($i = 0; $i -lt 40 -and (Test-Path $InstallRoot); $i++) {
        Start-Sleep -Milliseconds 250
    }
    if (Test-Path $InstallRoot) {
        throw "Install root remained after uninstall."
    }

    if ((Test-Path $ChromeHostKey) -or (Test-Path $EdgeHostKey)) {
        throw "Native Messaging registration remained after uninstall."
    }

    Write-Host "WINDOWS_PACKAGE_SMOKE_OK"
} finally {
    if (Test-Path $InstallRoot) {
        Remove-Item -Recurse -Force $InstallRoot -ErrorAction SilentlyContinue
    }
}
