param(
    [switch]$Console
)

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$driveName = @("Z", "Y", "X", "W", "V", "U", "T", "S", "R") |
    Where-Object { -not (Get-PSDrive -Name $_ -ErrorAction SilentlyContinue) } |
    Select-Object -First 1

if (-not $driveName) {
    throw "No unused drive letter is available for a short build path."
}

$drive = "{0}:" -f $driveName
$originalLocation = Get-Location
$originalConsoleSetting = $env:SPC_CONSOLE
$mapped = $false

try {
    & subst $drive $projectRoot
    if ($LASTEXITCODE -ne 0) {
        throw "Could not create a temporary drive mapping for the project."
    }
    $mapped = $true
    Set-Location "$drive\"

    $python = "$drive\.venv\Scripts\python.exe"
    if (-not (Test-Path $python)) {
        throw "The project virtual environment was not found at $python."
    }
    $mediapipeModules = "$drive\.venv\Lib\site-packages\mediapipe\modules"
    foreach ($assetDirectory in @("hand_landmark", "palm_detection")) {
        if (-not (Test-Path (Join-Path $mediapipeModules $assetDirectory))) {
            throw "MediaPipe model assets were not found: $mediapipeModules\$assetDirectory"
        }
    }

    if ($Console) {
        $env:SPC_CONSOLE = "1"
    }
    else {
        $env:SPC_CONSOLE = "0"
    }

    $specPath = Join-Path $drive "SmartPresentationController.spec"
    & $python -m PyInstaller --noconfirm --clean `
        --distpath "$drive\dist" `
        --workpath "$drive\build\onefile" `
        --log-level WARN $specPath

    if ($LASTEXITCODE -ne 0) {
        throw "PyInstaller failed with exit code $LASTEXITCODE."
    }

    $exePath = Join-Path $projectRoot "dist\SmartPresentationController.exe"
    if (-not (Test-Path $exePath)) {
        throw "PyInstaller finished without creating the expected executable: $exePath"
    }
    Write-Output "One-file executable created: $exePath"
    Get-Item $exePath | Select-Object FullName, Length, LastWriteTime
}
finally {
    Set-Location $originalLocation
    if ($null -eq $originalConsoleSetting) {
        Remove-Item Env:\SPC_CONSOLE -ErrorAction SilentlyContinue
    }
    else {
        $env:SPC_CONSOLE = $originalConsoleSetting
    }
    if ($mapped) {
        & subst $drive /d
    }
}
