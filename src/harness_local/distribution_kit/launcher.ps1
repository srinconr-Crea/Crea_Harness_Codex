param([string]$Python = 'python', [string]$ProjectRoot, [string]$Wheelhouse, [string]$Venv, [string]$Lock, [string]$Wheel, [string]$WheelSha256, [switch]$Apply)
$ErrorActionPreference = 'Stop'
# Preview is read-only, including on Windows without Python.
$tools = @('python', 'git', 'node', 'openspec', 'databricks')
$steps = foreach ($tool in $tools) {
    @{tool=$tool; detected=[bool](Get-Command $tool -ErrorAction SilentlyContinue); review_required=$true}
}
if (-not $Apply) {
    @{schema_version=1; command='launcher'; status='partial'; steps=@($steps); login='pending'; trust='pending'; plugin='unsupported'; certified=$false; release_allowed=$false} | ConvertTo-Json -Depth 5
    exit 0
}
# Explicit local installation only. No download, login, policy change or global activation.
if (-not $ProjectRoot -or -not $Wheelhouse -or -not $Venv -or -not $Lock -or -not $Wheel -or $WheelSha256 -notmatch '^[a-f0-9]{64}$') { throw 'Review project root, wheelhouse, lock, wheel hash and an absent local venv first.' }
function Assert-NoReparse([string]$Path) {
    $probe = [IO.Path]::GetFullPath($Path)
    while ($probe) {
        if (Test-Path -LiteralPath $probe) {
            $item = Get-Item -LiteralPath $probe -Force
            if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'Linked path rejected.' }
        }
        $parent = [IO.Directory]::GetParent($probe)
        if ($null -eq $parent) { break }
        $probe = $parent.FullName
    }
}
$candidateProject = [IO.Path]::GetFullPath($ProjectRoot).TrimEnd('\','/')
$candidateVenv = [IO.Path]::GetFullPath($Venv)
Assert-NoReparse $candidateProject
Assert-NoReparse $candidateVenv
if (-not (Test-Path -LiteralPath (Join-Path $candidateProject '.git'))) { throw 'Project must be a reviewed Git checkout.' }
if (-not $candidateVenv.StartsWith($candidateProject + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) { throw 'Venv must stay within the selected project.' }
foreach ($globalRoot in @($env:CODEX_HOME, (Join-Path $env:USERPROFILE '.codex'))) {
    if ($globalRoot) {
        $globalPath = [IO.Path]::GetFullPath($globalRoot).TrimEnd('\','/')
        if ($candidateVenv.Equals($globalPath, [StringComparison]::OrdinalIgnoreCase) -or $candidateVenv.StartsWith($globalPath + '\', [StringComparison]::OrdinalIgnoreCase)) { throw 'Global Codex configuration rejected.' }
    }
}
if (Test-Path -LiteralPath $candidateVenv) { throw 'Venv already exists; refusing to modify it.' }
foreach ($inputPath in @($Wheel, $Wheelhouse, $Lock)) { Assert-NoReparse $inputPath }
$wheelPath = (Resolve-Path -LiteralPath $Wheel).Path
$wheelhousePath = (Resolve-Path -LiteralPath $Wheelhouse).Path
$lockPath = (Resolve-Path -LiteralPath $Lock).Path
if ((Get-FileHash -LiteralPath $wheelPath -Algorithm SHA256).Hash.ToLowerInvariant() -ne $WheelSha256) { throw 'Wheel hash mismatch.' }
& $Python -c "import sys; assert sys.version_info[:2] == (3,13), 'Python 3.13 required'"
if ($LASTEXITCODE -ne 0) { throw 'Unsupported Python.' }
& $Python -m venv $candidateVenv
if ($LASTEXITCODE -ne 0) { throw 'Venv creation failed.' }
$venvPython = Join-Path $candidateVenv 'Scripts/python.exe'
& $venvPython -m pip install --no-index --no-compile --find-links $wheelhousePath --require-hashes -r $lockPath
if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed; keep local evidence for review.' }
& $venvPython -m pip install --no-index --no-compile --no-deps $wheelPath
if ($LASTEXITCODE -ne 0) { throw 'Candidate installation failed.' }
& $venvPython -m harness_local bootstrap --json
exit $LASTEXITCODE
