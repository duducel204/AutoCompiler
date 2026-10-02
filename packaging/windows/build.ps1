param(
    [string]$PythonVersion = "3.12.10",
    [string]$PythonSha256 = "156c7eea90d58cd7e91a23f28a0056616b13e9f4cf4901b7b99b837b7848c6da"
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$Repo = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$BuildRoot = Join-Path $Repo ".build\windows-package"
$Payload = Join-Path $BuildRoot "payload"
$App = Join-Path $Payload "app"
$Runtime = Join-Path $Payload "runtime"
$Tools = Join-Path $Payload "tools"
$Dist = Join-Path $Repo "dist"
$PythonZip = Join-Path $BuildRoot "python-embeddable.zip"
$PayloadZip = Join-Path $BuildRoot "AutoCompilerPayload.zip"

if (Test-Path $BuildRoot) {
    Remove-Item -Recurse -Force $BuildRoot
}
New-Item -ItemType Directory -Force -Path $App, $Runtime, $Tools, $Dist | Out-Null

$PythonUrl = "https://www.python.org/ftp/python/$PythonVersion/python-$PythonVersion-embeddable-amd64.zip"
Write-Host "[build] Downloading pinned Python $PythonVersion embeddable runtime"
Invoke-WebRequest -UseBasicParsing -Uri $PythonUrl -OutFile $PythonZip

$ActualHash = (Get-FileHash -Algorithm SHA256 $PythonZip).Hash.ToLowerInvariant()
if ($ActualHash -ne $PythonSha256.ToLowerInvariant()) {
    throw "Python runtime hash mismatch. Expected $PythonSha256, got $ActualHash"
}

Expand-Archive -Path $PythonZip -DestinationPath $Runtime -Force

$PythonMajorMinor = ($PythonVersion.Split(".")[0..1] -join "")
$Pth = Join-Path $Runtime ("python" + $PythonMajorMinor + "._pth")
if (-not (Test-Path $Pth)) {
    throw "Embedded Python _pth file was not found: $Pth"
}
$PthLines = @(Get-Content $Pth | Where-Object { $_ -ne "..\app\src" })
$PthLines += "..\app\src"
Set-Content -Path $Pth -Value $PthLines -Encoding ASCII

Write-Host "[build] Copying full AutoCompiler product payload"
$Directories = @("src", "web", "data", "schemas", "examples", "skills", "docs", "scripts")
foreach ($Directory in $Directories) {
    $Source = Join-Path $Repo $Directory
    if (-not (Test-Path $Source)) {
        throw "Required product directory missing: $Directory"
    }
    Copy-Item -Recurse -Force $Source (Join-Path $App $Directory)
}
foreach ($File in @("README.md", "AGENTS.md", "CONTRIBUTING.md")) {
    $Source = Join-Path $Repo $File
    if (Test-Path $Source) {
        Copy-Item -Force $Source (Join-Path $App $File)
    }
}

$CscCandidates = @(
    (Join-Path $env:WINDIR "Microsoft.NET\Framework64\v4.0.30319\csc.exe"),
    (Join-Path $env:WINDIR "Microsoft.NET\Framework\v4.0.30319\csc.exe")
)
$Csc = $CscCandidates | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $Csc) {
    throw "Windows .NET Framework C# compiler was not found."
}

Write-Host "[build] Compiling native Ready Bridge"
$BridgeExe = Join-Path $Tools "AutoCompilerReadyBridge.exe"
$BridgeArgs = @(
    "/nologo",
    "/target:winexe",
    "/optimize+",
    "/out:$BridgeExe",
    "/reference:System.Windows.Forms.dll",
    "/reference:System.Web.Extensions.dll",
    (Join-Path $PSScriptRoot "AutoCompilerReadyBridge.cs")
)
& $Csc $BridgeArgs
if ($LASTEXITCODE -ne 0 -or -not (Test-Path $BridgeExe)) {
    throw "Ready Bridge compilation failed."
}

& $BridgeExe --self-test | Out-Null
if ($LASTEXITCODE -ne 0) {
    throw "Ready Bridge self-test failed during build."
}

Copy-Item -Force (Join-Path $PSScriptRoot "bootstrap.ps1") (Join-Path $Payload "bootstrap.ps1")

$GitVersion = "working-tree"
try {
    $GitVersion = (& git -C $Repo rev-parse --short HEAD).Trim()
} catch { }

$PayloadManifest = [ordered]@{
    schema_version = "1.0"
    version = $GitVersion
    built_at = (Get-Date).ToUniversalTime().ToString("o")
    target = "windows-x64"
    python_version = $PythonVersion
    python_sha256 = $PythonSha256
    product = @(
        "AutoCompiler Canvas",
        "Automation Base",
        "Ready Automations",
        "private Python runtime",
        "Windows deployment adapters",
        "native browser bridge"
    )
}
$PayloadManifest | ConvertTo-Json -Depth 8 | Set-Content (Join-Path $Payload "payload-manifest.json") -Encoding UTF8

if (Test-Path $PayloadZip) {
    Remove-Item -Force $PayloadZip
}
Compress-Archive -Path (Join-Path $Payload "*") -DestinationPath $PayloadZip -CompressionLevel Optimal

$SetupExe = Join-Path $Dist "AutoCompilerSetup.exe"
if (Test-Path $SetupExe) {
    Remove-Item -Force $SetupExe
}

Write-Host "[build] Compiling single-file AutoCompilerSetup.exe"
$SetupArgs = @(
    "/nologo",
    "/target:winexe",
    "/optimize+",
    "/out:$SetupExe",
    "/reference:System.IO.Compression.dll",
    "/reference:System.IO.Compression.FileSystem.dll",
    "/reference:System.Windows.Forms.dll",
    "/resource:$PayloadZip,AutoCompiler.Payload",
    (Join-Path $PSScriptRoot "AutoCompilerSetup.cs")
)
& $Csc $SetupArgs
if ($LASTEXITCODE -ne 0 -or -not (Test-Path $SetupExe)) {
    throw "AutoCompilerSetup.exe compilation failed."
}

$PackageHash = (Get-FileHash -Algorithm SHA256 $SetupExe).Hash.ToLowerInvariant()
$BuildManifest = [ordered]@{
    schema_version = "1.0"
    setup = "AutoCompilerSetup.exe"
    sha256 = $PackageHash
    size_bytes = (Get-Item $SetupExe).Length
    python = @{
        version = $PythonVersion
        source = $PythonUrl
        sha256 = $PythonSha256
    }
    payload_version = $GitVersion
}
$BuildManifest | ConvertTo-Json -Depth 8 | Set-Content (Join-Path $Dist "AutoCompilerSetup.manifest.json") -Encoding UTF8

Write-Host "[build] COMPLETE"
Write-Host ("[build] Setup: " + $SetupExe)
Write-Host ("[build] SHA256: " + $PackageHash)
