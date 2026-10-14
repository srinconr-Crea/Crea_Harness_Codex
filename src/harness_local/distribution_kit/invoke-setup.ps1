param([Parameter(ValueFromRemainingArguments=$true)][string[]]$HarnessArguments)
$ErrorActionPreference='Stop'
$registration=Join-Path $PSScriptRoot 'runtime.json'
$held=New-Object 'Collections.Generic.List[IDisposable]'
$pinnedDirectories=@{}
function FileHash([string]$Path) {
    $algorithm=[Security.Cryptography.SHA256]::Create()
    $stream=[IO.File]::OpenRead($Path)
    try { return ([BitConverter]::ToString($algorithm.ComputeHash($stream))).Replace('-','').ToLowerInvariant() }
    finally { $stream.Dispose(); $algorithm.Dispose() }
}
try {
    $entry=Get-Content -LiteralPath $registration -Raw | ConvertFrom-Json
    $receiptPath=[IO.Path]::GetFullPath($entry.installation_record)
    $receipt=([IO.File]::ReadAllText($receiptPath,[Text.Encoding]::UTF8)) | ConvertFrom-Json
    if ($receipt.schema_version -ne 1 -or $receipt.kind -ne 'installation_record' -or $receipt.skill_path -ne (Join-Path $PSScriptRoot 'SKILL.md')) { throw 'Invalid record' }
    $guardPath=Join-Path $PSScriptRoot 'fs-guard.dll'
    if ([IO.File]::GetAttributes($guardPath) -band [IO.FileAttributes]::ReparsePoint) { throw 'Invalid guard' }
    $guardBytes=[IO.File]::ReadAllBytes($guardPath)
    $algorithm=[Security.Cryptography.SHA256]::Create()
    try { $guardHash=[BitConverter]::ToString($algorithm.ComputeHash($guardBytes)).Replace('-','').ToLowerInvariant() }
    finally { $algorithm.Dispose() }
    if ($guardHash -ne $receipt.skill_files.'fs-guard.dll') { throw 'Invalid guard' }
    [Reflection.Assembly]::Load($guardBytes) | Out-Null
    function PinParents([string]$Path) {
        $paths=New-Object 'Collections.Generic.List[string]'
        $probe=[IO.Path]::GetFullPath($Path)
        while ($probe) {
            $paths.Insert(0,$probe); $parent=[IO.Directory]::GetParent($probe)
            if ($null -eq $parent) { break }; $probe=$parent.FullName
        }
        foreach ($path in $paths) {
            if (-not $pinnedDirectories.ContainsKey($path)) {
                $held.Add([LocalHarness.FileGuard]::PinDirectory($path)); $pinnedDirectories[$path]=$true
            }
        }
    }
    function PinFile([string]$Path,[string]$Expected,[bool]$Tool=$false) {
        $stream=[IO.File]::Open($Path,[IO.FileMode]::Open,[IO.FileAccess]::Read,[IO.FileShare]::Read)
        $held.Add($stream)
        [LocalHarness.FileGuard]::Validate($stream.SafeFileHandle,$Path,$Tool)
        if ($stream.Length -gt 268435456 -or $Expected -notmatch '^[a-f0-9]{64}$') { throw 'Invalid resource' }
        $algorithm=[Security.Cryptography.SHA256]::Create()
        try { $actual=([BitConverter]::ToString($algorithm.ComputeHash($stream))).Replace('-','').ToLowerInvariant() }
        finally { $algorithm.Dispose() }
        if ($actual -ne $Expected) { throw 'Modified resource' }
    }
    $installationRoot=[IO.Path]::GetFullPath($receipt.installation_root)
    if ($receiptPath -ne (Join-Path $installationRoot 'installation.json') -or $receipt.runtime_path -ne $entry.runtime_path) { throw 'Invalid selection' }
    PinParents $installationRoot; PinParents $PSScriptRoot
    $runtimeDir=[IO.Directory]::GetParent($entry.runtime_path).Parent.FullName
    $packageKey=$runtimeDir.Substring($installationRoot.Length+1).Replace('\','/')+'/Lib/site-packages/harness_local/cli.py'
    if (-not $receipt.owned_files.PSObject.Properties[$packageKey]) { throw 'Missing package ownership' }
    foreach ($file in $receipt.owned_files.PSObject.Properties) {
        if ($file.Name -match '(^|/)\.\.?(/|$)|[\\:]|^/' -or $file.Name -match '(^|/)(?i:con|prn|aux|nul|com[0-9]|lpt[0-9])(?:\.|/|$)') { throw 'Invalid ownership path' }
        $path=[IO.Path]::GetFullPath((Join-Path $installationRoot $file.Name))
        PinParents ([IO.Path]::GetDirectoryName($path))
        PinFile $path $file.Value (@($receipt.tools | Where-Object { $_.path -eq $path }).Count -gt 0)
    }
    foreach ($file in $receipt.skill_files.PSObject.Properties) {
        if ($file.Name -match '[\\:/]|^\.\.?$') { throw 'Invalid skill ownership' }
        PinFile (Join-Path $PSScriptRoot $file.Name) $file.Value
    }
    $runtime=[IO.Path]::GetFullPath($entry.runtime_path)
    if ($runtime -ne $entry.runtime_path -or (FileHash $runtime) -ne $entry.runtime_sha256) { throw 'Invalid runtime' }
    # A fresh nonexistent cache namespace plus -B prevents unowned .pyc files
    # from shadowing the pinned package and never writes a bytecode cache.
    $cacheArgument='pycache_prefix='+(Join-Path $installationRoot ('no-cache-'+[Guid]::NewGuid().ToString('N')))
    & $runtime -I -B -X $cacheArgument -c "import sys; from harness_core.onboarding_plan import load_json; from harness_core.setup import InstallationRecord; r=load_json(sys.argv[1],InstallationRecord,limit=8*1024*1024); assert r.runtime_path==sys.executable" $entry.installation_record
    if ($LASTEXITCODE -ne 0) { throw 'Invalid installation record' }
    & $runtime -I -B -X $cacheArgument -m harness_local setup @HarnessArguments
    exit $LASTEXITCODE
} catch { Write-Output '{"status":"blocked","reason":"owned_resource_conflict"}'; exit 4 }
finally { foreach ($handle in $held) { $handle.Dispose() } }
