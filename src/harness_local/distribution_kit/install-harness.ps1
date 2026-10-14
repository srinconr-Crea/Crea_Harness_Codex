param(
    [string]$Kit = $PSScriptRoot,
    [string]$InstallRoot = (Join-Path $env:LOCALAPPDATA 'LocalHarness/installations/0.1.0'),
    [string]$SkillRoot = (Join-Path $env:USERPROFILE '.agents/skills'),
    [string]$Python,
    [string]$KitUrl,
    [string]$KitSha256,
    [string]$ManifestSha256,
    [string[]]$Tools = @(),
    [switch]$Preview, [switch]$Apply, [switch]$Recover, [switch]$Update
)
$ErrorActionPreference = 'Stop'
function Fail([string]$Reason, [int]$Code=4) {
    @{schema_version=1; command='install'; status='blocked'; reason=$Reason; certified=$false; release_allowed=$false} | ConvertTo-Json -Compress
    exit $Code
}
function SafePath([string]$Value) {
    if ($Value -match '(^|[\\/])\.\.([\\/]|$)' -or $Value.StartsWith('\\')) { Fail 'invalid_input' 2 }
    $full=[IO.Path]::GetFullPath($Value)
    $probe=$full
    while ($probe) {
        if ([IO.File]::Exists($probe) -or [IO.Directory]::Exists($probe)) {
            if ([IO.File]::GetAttributes($probe) -band [IO.FileAttributes]::ReparsePoint) { Fail 'owned_resource_conflict' }
        }
        $parent=[IO.Directory]::GetParent($probe)
        if ($null -eq $parent) { break }; $probe=$parent.FullName
    }
    return $full
}
function ProbeVersion([string]$Binary,[string]$Arguments='--version') {
    $info=New-Object Diagnostics.ProcessStartInfo
    $info.FileName=$Binary; $info.Arguments=$Arguments
    $info.WorkingDirectory=[IO.Path]::GetDirectoryName($Binary)
    $info.UseShellExecute=$false; $info.CreateNoWindow=$true
    $info.RedirectStandardOutput=$true; $info.RedirectStandardError=$true
    $info.EnvironmentVariables['OPENSPEC_TELEMETRY']='0'
    $process=New-Object Diagnostics.Process
    $process.StartInfo=$info
    try {
        if (-not $process.Start()) { Fail 'tool_unavailable' 3 }
        $out=$process.StandardOutput.ReadToEndAsync(); $err=$process.StandardError.ReadToEndAsync()
        if (-not $process.WaitForExit(30000)) { $process.Kill(); Fail 'tool_unavailable' 3 }
        if ($process.ExitCode -ne 0) { Fail 'tool_unavailable' 3 }
        return $out.Result
    } finally { $process.Dispose() }
}
function Relative([string]$Value) {
    if (-not $Value -or $Value -match '[\\:<>|?*\x00-\x1f]' -or $Value.StartsWith('/')) { Fail 'invalid_input' 2 }
    foreach ($part in $Value.Split('/')) {
        if ($part -in @('', '.', '..') -or $part -match '[. ]$|^(?i:con|prn|aux|nul|com[0-9]|lpt[0-9])(?:\.|$)') { Fail 'invalid_input' 2 }
    }
}
function Hash([string]$Path) {
    $algorithm=[Security.Cryptography.SHA256]::Create(); $stream=[IO.File]::OpenRead((SafePath $Path))
    try { return ([BitConverter]::ToString($algorithm.ComputeHash($stream))).Replace('-','').ToLowerInvariant() }
    finally { $stream.Dispose(); $algorithm.Dispose() }
}
function NewFile([string]$Path,[byte[]]$Bytes) {
    $Path=SafePath $Path
    $stream=[IO.File]::Open($Path,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::None)
    try { $stream.Write($Bytes,0,$Bytes.Length); $stream.Flush($true) } finally { $stream.Dispose() }
}
function JsonFile([string]$Path,$Value) {
    NewFile $Path ([Text.Encoding]::UTF8.GetBytes(($Value | ConvertTo-Json -Depth 30 -Compress)))
}
$pins=New-Object 'Collections.Generic.List[IDisposable]'
$pinned=@{}
function PinParents([string]$Path) {
    $paths=New-Object 'Collections.Generic.List[string]'; $probe=[IO.Path]::GetFullPath($Path)
    while ($probe) {
        $paths.Insert(0,$probe); $parent=[IO.Directory]::GetParent($probe)
        if ($null -eq $parent) { break }; $probe=$parent.FullName
    }
    foreach ($path in $paths) {
        if (-not $pinned.ContainsKey($path)) { $pins.Add([LocalHarness.FileGuard]::PinDirectory($path)); $pinned[$path]=$true }
    }
}
function EnsureDir([string]$Path) {
    $Path=SafePath $Path
    if ([IO.Directory]::Exists($Path)) { PinParents $Path; return }
    EnsureDir ([IO.Path]::GetDirectoryName($Path))
    [LocalHarness.FileGuard]::CreateDirectory($Path); PinParents $Path
}
function Extract([string]$Archive,[string]$Destination) {
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    $zip=[IO.Compression.ZipFile]::OpenRead((SafePath $Archive))
    try {
        $total=0L
        foreach ($entry in $zip.Entries) {
            if ($entry.FullName.EndsWith('/')) { continue }
            Relative $entry.FullName
            $total+=$entry.Length
            if ($total -gt 1073741824 -or (($entry.ExternalAttributes -shr 16) -band 61440) -eq 40960) { Fail 'download_integrity_failed' 5 }
            $out=SafePath (Join-Path $Destination $entry.FullName)
            if (-not $out.StartsWith($Destination.TrimEnd('\')+'\',[StringComparison]::OrdinalIgnoreCase)) { Fail 'invalid_input' 2 }
            EnsureDir ([IO.Path]::GetDirectoryName($out))
            $source=$entry.Open(); $target=[IO.File]::Open($out,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::None)
            try { $source.CopyTo($target); $target.Flush($true) } finally { $source.Dispose(); $target.Dispose() }
        }
    } finally { $zip.Dispose() }
}
$root=SafePath $InstallRoot; $skillBase=SafePath $SkillRoot; $kitRoot=SafePath $Kit
if (-not [Environment]::Is64BitOperatingSystem -or $env:PROCESSOR_ARCHITECTURE -eq 'ARM64') { Fail 'tool_unavailable' 3 }
if (@($Tools | Where-Object { $_ -notin @('git','node','openspec','databricks') }).Count) { Fail 'invalid_input' 2 }
if ($KitUrl) {
    $uri=[Uri]$KitUrl
    if ($uri.Scheme -ne 'https' -or $uri.UserInfo -or $uri.Query -or $KitSha256 -notmatch '^[a-f0-9]{64}$') { Fail 'invalid_input' 2 }
    $cache=SafePath (Join-Path $env:TEMP ('LocalHarness/kit-'+$KitSha256))
    $kitRoot=Join-Path $cache 'kit'
    if (-not $Apply -and -not $Recover) {
        @{schema_version=1; command='install'; status='prepared'; source=$KitUrl; sha256=$KitSha256; cache=$cache; install_root=$root; skill_root=$skillBase; tools=$Tools; certified=$false; release_allowed=$false} | ConvertTo-Json -Depth 10
        exit 0
    }
    $bootstrapGuard=Join-Path $PSScriptRoot 'fs-guard.dll'
    $bootstrapBytes=[IO.File]::ReadAllBytes($bootstrapGuard)
    $bootstrapHasher=[Security.Cryptography.SHA256]::Create()
    try { $bootstrapHash=[BitConverter]::ToString($bootstrapHasher.ComputeHash($bootstrapBytes)).Replace('-','').ToLowerInvariant() }
    finally { $bootstrapHasher.Dispose() }
    if ($bootstrapHash -ne '__FS_GUARD_SHA256__') { Fail 'download_integrity_failed' 5 }
    [Reflection.Assembly]::Load($bootstrapBytes) | Out-Null
    if (-not (Test-Path -LiteralPath $cache)) {
        EnsureDir $cache
        JsonFile (Join-Path $cache 'download-journal.json') @{source=$KitUrl; sha256=$KitSha256; state='download_pending'}
        try {
            $response=Invoke-WebRequest -Uri $KitUrl -UseBasicParsing
            if ($response.RawContentLength -gt 1073741824) { Fail 'download_integrity_failed' 5 }
            $memory=New-Object IO.MemoryStream
            try {
                $buffer=New-Object byte[] 65536
                while (($count=$response.RawContentStream.Read($buffer,0,$buffer.Length)) -gt 0) {
                    if ($memory.Length+$count -gt 1073741824) { Fail 'download_integrity_failed' 5 }
                    $memory.Write($buffer,0,$count)
                }
                NewFile (Join-Path $cache 'kit.zip') $memory.ToArray()
            } finally { $memory.Dispose() }
        } catch { Fail 'tool_unavailable' 3 }
        if ((Hash (Join-Path $cache 'kit.zip')) -ne $KitSha256) { Fail 'download_integrity_failed' 5 }
        Extract (Join-Path $cache 'kit.zip') $kitRoot
    }
}
$manifestPath=Join-Path $kitRoot 'install-manifest.json'
if (-not (Test-Path -LiteralPath $manifestPath)) {
    if (-not $Apply -and -not $Recover) {
        @{schema_version=1; command='install'; status='blocked'; reason='tool_unavailable'; offline_kit_required=$true; install_root=$root; skill_root=$skillBase; certified=$false; release_allowed=$false} | ConvertTo-Json -Compress
        exit 0
    }; Fail 'tool_unavailable' 3
}
try {
    $manifestBytes=[IO.File]::ReadAllBytes($manifestPath)
    $manifestHasher=[Security.Cryptography.SHA256]::Create()
    try { $manifestDigest=[BitConverter]::ToString($manifestHasher.ComputeHash($manifestBytes)).Replace('-','').ToLowerInvariant() }
    finally { $manifestHasher.Dispose() }
    $manifest=[Text.Encoding]::UTF8.GetString($manifestBytes) | ConvertFrom-Json
} catch { Fail 'invalid_input' 2 }
if ($manifest.schema_version -ne 1 -or $manifest.version -ne '0.1.0' -or $manifest.platform -ne 'windows-amd64' -or -not $manifest.files -or -not $manifest.wheel -or -not $manifest.skill) { Fail 'invalid_input' 2 }
if ($Apply -and ($ManifestSha256 -notmatch '^[a-f0-9]{64}$' -or $manifestDigest -ne $ManifestSha256)) { Fail 'plan_stale' }
$seen=@{}
foreach ($file in $manifest.files.PSObject.Properties) {
    Relative $file.Name
    if ($seen.ContainsKey($file.Name.ToLowerInvariant()) -or $file.Value -notmatch '^[a-f0-9]{64}$') { Fail 'invalid_input' 2 }
    $seen[$file.Name.ToLowerInvariant()]=$true
    $artifact=SafePath (Join-Path $kitRoot $file.Name)
    if (-not (Test-Path -LiteralPath $artifact) -or (Hash $artifact) -ne $file.Value) { Fail 'download_integrity_failed' 5 }
}
Relative $manifest.wheel; Relative $manifest.skill
if (-not $manifest.files.PSObject.Properties[$manifest.wheel] -or -not $manifest.files.PSObject.Properties[$manifest.skill]) { Fail 'download_integrity_failed' 5 }
$runtimeNames=@($manifest.runtime_dependencies | ForEach-Object { $_.name.ToLowerInvariant().Replace('_','-') } | Sort-Object)
if (($runtimeNames -join ',') -ne 'annotated-types,pydantic,pydantic-core,pyyaml,typing-extensions,typing-inspection') { Fail 'download_integrity_failed' 5 }
foreach ($dep in $manifest.runtime_dependencies) {
    Relative ('wheelhouse/'+$dep.artifact)
    if (-not $dep.version -or -not $dep.license -or $dep.sha256 -ne $manifest.files.PSObject.Properties[('wheelhouse/'+$dep.artifact)].Value) { Fail 'download_integrity_failed' 5 }
}
# This allowlist is part of the reviewed entry point, independent of kit JSON.
$official=@{
    python=@{version='3.13.7'; sha256='b12e2e82461ac8e51fc43289050bc8eb937a32d84ce4d242e2c88258c37cf2bb'}
    git=@{version='2.51.0'; sha256='a09b275d51ed3e829128e04cf4168fb54896cf6234bb30fecb8dc96a2bd321fa'}
    node=@{version='22.20.0'; sha256='bb819d6eb8f5bfda294bbc83a7e4ec6539da67c4233d54b0d655b9248b15e29d'}
    databricks=@{version='0.292.0'; sha256='14de87368dad80892ec793494877a59317e7fb4522c87cd7cf4e093b09aa2fb2'}
    openspec=@{version='1.13.2'; sha256='__OPENSPEC_ZIP_SHA256__'}
}
if (@($manifest.tools.PSObject.Properties).Count -ne 5) { Fail 'download_integrity_failed' 5 }
foreach ($name in $official.Keys) {
    $tool=$manifest.tools.PSObject.Properties[$name].Value
    if (-not $tool -or $tool.version -ne $official[$name].version -or $tool.sha256 -ne $official[$name].sha256) { Fail 'download_integrity_failed' 5 }
}
$skillDir=Join-Path $skillBase 'harness-setup'; $skillPath=Join-Path $skillDir 'SKILL.md'
$effects=@('runtime aislado','registro de instalación','Skill de usuario')
if (-not $Python) { $effects+= 'Python oficial per-user si falta: registro HKCU, sin PATH ni asociaciones' }
if (-not $Apply -and -not $Recover) {
    @{schema_version=1; command='install'; status='prepared'; install_root=$root; skill_path=$skillPath; tools=$Tools; effects=$effects; source=$kitRoot; manifest_sha256=$manifestDigest; conflict=(Test-Path -LiteralPath $skillPath); certified=$false; release_allowed=$false} | ConvertTo-Json -Depth 10
    exit 0
}
$recordPath=Join-Path $root 'installation.json'
if (Test-Path -LiteralPath $recordPath) {
    try { $record=Get-Content -LiteralPath $recordPath -Raw | ConvertFrom-Json } catch { Fail 'owned_resource_conflict' }
    if ($record.product_sha256 -ne $manifestDigest -or $record.installation_root -ne $root -or $record.skill_path -ne $skillPath) { Fail 'owned_resource_conflict' }
    foreach ($file in $record.owned_files.PSObject.Properties) {
        Relative $file.Name
        if ((Hash (Join-Path $root $file.Name)) -ne $file.Value) { Fail 'owned_resource_conflict' }
    }
    if ((Hash $skillPath) -ne $record.skill_sha256) { Fail 'owned_resource_conflict' }
    foreach ($file in $record.skill_files.PSObject.Properties) {
        Relative $file.Name
        if ((Hash (Join-Path $skillDir $file.Name)) -ne $file.Value) { Fail 'owned_resource_conflict' }
    }
    @{schema_version=1; command='install'; status='prepared'; idempotent=$true; reason='skill_discovery_pending'; record=$record; certified=$false; release_allowed=$false} | ConvertTo-Json -Depth 20
    exit 0
}
$guardPath=SafePath (Join-Path $kitRoot 'fs-guard.dll')
$guardBytes=[IO.File]::ReadAllBytes($guardPath)
$guardHasher=[Security.Cryptography.SHA256]::Create()
try { $guardDigest=[BitConverter]::ToString($guardHasher.ComputeHash($guardBytes)).Replace('-','').ToLowerInvariant() }
finally { $guardHasher.Dispose() }
if ($guardDigest -ne $manifest.files.PSObject.Properties['fs-guard.dll'].Value) { Fail 'download_integrity_failed' 5 }
[Reflection.Assembly]::Load($guardBytes) | Out-Null
foreach ($name in @('install-manifest.json')+@($manifest.files.PSObject.Properties.Name)) {
    $artifact=SafePath (Join-Path $kitRoot $name)
    PinParents ([IO.Path]::GetDirectoryName($artifact))
    $stream=[IO.File]::Open($artifact,[IO.FileMode]::Open,[IO.FileAccess]::Read,[IO.FileShare]::Read)
    $pins.Add($stream)
    # Fixed artifacts are read-only leases, so a cache hard link is safe;
    # FileShare.Read prevents writing through any link while the lease exists.
    [LocalHarness.FileGuard]::Validate($stream.SafeFileHandle,$artifact,$true)
    $hasher=[Security.Cryptography.SHA256]::Create()
    try { $actual=[BitConverter]::ToString($hasher.ComputeHash($stream)).Replace('-','').ToLowerInvariant(); $stream.Position=0 }
    finally { $hasher.Dispose() }
    $expected=if ($name -eq 'install-manifest.json') { $manifestDigest } else { $manifest.files.PSObject.Properties[$name].Value }
    if ($actual -ne $expected) { Fail 'download_integrity_failed' 5 }
}
$resuming=$Recover -and (Test-Path -LiteralPath $root)
$attempt=if ($resuming) { 'recover-'+[Guid]::NewGuid().ToString('N') } else { 'initial' }
$previousSkill=$null
if (Test-Path -LiteralPath $skillDir) {
    if (-not $Update -and -not $resuming) { Fail 'owned_resource_conflict' }
    $registration=Get-Content -LiteralPath (Join-Path $skillDir 'runtime.json') -Raw | ConvertFrom-Json
    if (Test-Path -LiteralPath $registration.installation_record) {
        $previousSkill=Get-Content -LiteralPath $registration.installation_record -Raw | ConvertFrom-Json
        foreach ($file in $previousSkill.skill_files.PSObject.Properties) {
            if ((Hash (Join-Path $skillDir $file.Name)) -ne $file.Value) { Fail 'owned_resource_conflict' }
        }
    } else {
        $skillJournal=Join-Path $root 'journal-skill-initial.json'
        if (-not $resuming -or -not (Test-Path -LiteralPath $skillJournal)) { Fail 'owned_resource_conflict' }
        $previousSkill=Get-Content -LiteralPath $skillJournal -Raw | ConvertFrom-Json
        foreach ($file in $previousSkill.skill_files.PSObject.Properties) {
            $candidate=Join-Path $skillDir $file.Name
            if ((Test-Path -LiteralPath $candidate) -and (Hash $candidate) -ne $file.Value) { Fail 'owned_resource_conflict' }
        }
    }
}
if ((Test-Path -LiteralPath $root) -and -not $resuming) { Fail 'owned_resource_conflict' }
if ($resuming) {
    $marker=Get-Content -LiteralPath (Join-Path $root 'journal-00-initial.json') -Raw | ConvertFrom-Json
    if ($marker.product_sha256 -ne $manifestDigest) { Fail 'owned_resource_conflict' }
    PinParents $root
    if ([LocalHarness.FileGuard]::Identity($pins[$pins.Count-1]) -ne $marker.root_identity) { Fail 'owned_resource_conflict' }
} else { EnsureDir ([IO.Path]::GetDirectoryName($root)); [LocalHarness.FileGuard]::CreateDirectory($root); PinParents $root }
$lock=$null
try {
    $lock=[IO.File]::Open((Join-Path $root 'install.lock'),$(if ($resuming) {[IO.FileMode]::Open} else {[IO.FileMode]::CreateNew}),[IO.FileAccess]::ReadWrite,[IO.FileShare]::None)
    $rootIdentity=[LocalHarness.FileGuard]::Identity($pins[$pins.Count-1])
    JsonFile (Join-Path $root ('journal-00-'+$attempt+'.json')) @{state='prepared'; root_identity=$rootIdentity; product_sha256=$manifestDigest; effects=$effects}
    if ($Python) {
        $Python=SafePath $Python
        & $Python -I -c "import sys; assert sys.version_info[:2] == (3,13)"
        if ($LASTEXITCODE -ne 0) { Fail 'tool_unavailable' 3 }
    } else {
        $detected=Get-Command python.exe -ErrorAction SilentlyContinue
        if ($detected -and $detected.Source -notmatch 'WindowsApps') {
            $compatible=& $detected.Source -I -S -c "import sys; print(sys.version_info[:2] == (3,13))"
            if ($LASTEXITCODE -eq 0 -and $compatible -eq 'True') { $Python=SafePath $detected.Source }
        }
    }
    if (-not $Python) {
        $official=$manifest.tools.python
        $installer=SafePath (Join-Path $kitRoot $official.artifact)
        if ((Hash $installer) -ne $official.sha256) { Fail 'download_integrity_failed' 5 }
        $pythonRoot=Join-Path $root 'python'
        JsonFile (Join-Path $root ('journal-01-'+$attempt+'.json')) @{state='installing_python'; destination=$pythonRoot; native_recovery='Usar Repair del instalador fijado; no borrar registro HKCU manualmente'}
        $process=Start-Process -FilePath $installer -ArgumentList @('/quiet','InstallAllUsers=0',('TargetDir="'+$pythonRoot+'"'),'PrependPath=0','AssociateFiles=0','Include_launcher=0','Include_test=0','Shortcuts=0') -Wait -PassThru -WindowStyle Hidden
        if ($process.ExitCode -ne 0) { Fail 'recovery_required' 6 }
        $Python=Join-Path $pythonRoot 'python.exe'
    }
    $venv=Join-Path $root $(if ($resuming) {'r'+[Guid]::NewGuid().ToString('N').Substring(0,8)} else {'runtime'})
    JsonFile (Join-Path $root ('journal-02-'+$attempt+'.json')) @{state='creating_runtime'; python=$Python; destination=$venv}
    & $Python -I -m venv $venv
    if ($LASTEXITCODE -ne 0) { Fail 'recovery_required' 6 }
    $runtime=Join-Path $venv 'Scripts/python.exe'
    & $runtime -I -m pip install --no-index --no-compile --require-hashes --find-links (Join-Path $kitRoot 'wheelhouse') -r (Join-Path $kitRoot 'runtime-lock.txt') | Out-Null
    if ($LASTEXITCODE -ne 0) { Fail 'recovery_required' 6 }
    & $runtime -I -m pip install --no-index --no-compile --no-deps (Join-Path $kitRoot $manifest.wheel) | Out-Null
    if ($LASTEXITCODE -ne 0) { Fail 'recovery_required' 6 }
    & $runtime -I -c "from harness_local.installation import validate_kit; import sys; validate_kit(sys.argv[1])" $kitRoot
    if ($LASTEXITCODE -ne 0) { Fail 'download_integrity_failed' 5 }
    $installedTools=@()
    $selected=@($Tools)
    if ('openspec' -in $selected -and 'node' -notin $selected) { $selected+='node' }
    foreach ($name in $selected) {
        $tool=$manifest.tools.PSObject.Properties[$name].Value
        if (-not $tool -or (Hash (Join-Path $kitRoot $tool.artifact)) -ne $tool.sha256) { Fail 'download_integrity_failed' 5 }
        $destination=Join-Path $root $(if ($resuming) {$attempt+'/'+$name} else {$name})
        JsonFile (Join-Path $root ('journal-tool-'+$name+'-'+$attempt+'.json')) @{state='installing_tool'; destination=$destination; sha256=$tool.sha256}
        if ($name -eq 'git') {
            $process=Start-Process -FilePath (Join-Path $kitRoot $tool.artifact) -ArgumentList @('-y',('-o"'+$destination+'"')) -Wait -PassThru -WindowStyle Hidden
            if ($process.ExitCode -ne 0) { Fail 'recovery_required' 6 }
        } else { Extract (Join-Path $kitRoot $tool.artifact) $destination }
        $binary=SafePath (Join-Path $destination $tool.binary)
        if (-not (Test-Path -LiteralPath $binary)) { Fail 'tool_unavailable' 3 }
        $installedTools+=@{schema_version=1; name=$name; version=$tool.version; path=$binary; sha256=(Hash $binary); license=$tool.license}
    }
    foreach ($tool in $installedTools) {
        if ($tool.name -eq 'openspec') {
            $nodeTool=@($installedTools | Where-Object { $_.name -eq 'node' })[0]
            $observed=ProbeVersion $nodeTool.path ('"'+$tool.path+'" --version')
        } else { $observed=ProbeVersion $tool.path }
        if ($observed -notmatch [Regex]::Escape($tool.version)) { Fail 'tool_unavailable' 3 }
    }
    EnsureDir $skillDir
    $registration=@{schema_version=1; runtime_path=$runtime; installation_record=$recordPath; runtime_sha256=(Hash $runtime)}
    $skillBytes=@{'SKILL.md'=[IO.File]::ReadAllBytes((Join-Path $kitRoot $manifest.skill)); 'invoke-setup.ps1'=[IO.File]::ReadAllBytes((Join-Path $kitRoot 'invoke-setup.ps1')); 'fs-guard.dll'=[IO.File]::ReadAllBytes((Join-Path $kitRoot 'fs-guard.dll')); 'runtime.json'=[Text.Encoding]::UTF8.GetBytes(($registration | ConvertTo-Json -Compress))}
    $plannedSkill=@{}
    foreach ($name in $skillBytes.Keys) {
        $algorithm=[Security.Cryptography.SHA256]::Create()
        try { $plannedSkill[$name]=([BitConverter]::ToString($algorithm.ComputeHash($skillBytes[$name]))).Replace('-','').ToLowerInvariant() } finally { $algorithm.Dispose() }
    }
    JsonFile (Join-Path $root ('journal-skill-'+$attempt+'.json')) @{state='registering_skill'; skill_files=$plannedSkill}
    foreach ($name in $skillBytes.Keys) {
        $destination=Join-Path $skillDir $name
        if (Test-Path -LiteralPath $destination) {
            if (-not $previousSkill -or (Hash $destination) -ne $previousSkill.skill_files.PSObject.Properties[$name].Value) { Fail 'owned_resource_conflict' }
            NewFile (Join-Path $root ('backup-'+$name+'-'+$attempt)) ([IO.File]::ReadAllBytes($destination))
            $stream=[IO.File]::Open($destination,[IO.FileMode]::Open,[IO.FileAccess]::Write,[IO.FileShare]::None)
            try { $stream.SetLength(0); $stream.Write($skillBytes[$name],0,$skillBytes[$name].Length); $stream.Flush($true) } finally { $stream.Dispose() }
        } else { NewFile $destination $skillBytes[$name] }
    }
    $owned=@{}
    foreach ($file in Get-ChildItem -LiteralPath $root -Recurse -File) {
        SafePath $file.FullName | Out-Null
        $relative=$file.FullName.Substring($root.Length+1).Replace('\','/')
        $runtimeRelative=$venv.Substring($root.Length+1).Replace('\','/')+'/'
        if ($file.Name -ne 'install.lock' -and (-not $resuming -or $relative.StartsWith($runtimeRelative) -or $relative.StartsWith($attempt+'/') -or $file.Name.Contains($attempt))) { $owned[$relative]=Hash $file.FullName }
    }
    $skillFiles=@{}
    foreach ($name in @('SKILL.md','runtime.json','invoke-setup.ps1','fs-guard.dll')) { $skillFiles[$name]=Hash (Join-Path $skillDir $name) }
    $record=@{schema_version=1; kind='installation_record'; version=$manifest.version; product_sha256=$manifestDigest; installation_root=$root; runtime_path=$runtime; kit_path=$kitRoot; skill_path=$skillPath; skill_sha256=(Hash $skillPath); skill_files=$skillFiles; tools=$installedTools; owned_files=$owned; resource_installed=$true; skill_discovered=$false; certified=$false; release_allowed=$false}
    JsonFile $recordPath $record
    @{schema_version=1; command='install'; status='prepared'; reason='skill_discovery_pending'; record=$record; certified=$false; release_allowed=$false} | ConvertTo-Json -Depth 30
} catch { Fail 'recovery_required' 6 } finally { if ($lock) { $lock.Dispose() }; foreach ($pin in $pins) { $pin.Dispose() } }
