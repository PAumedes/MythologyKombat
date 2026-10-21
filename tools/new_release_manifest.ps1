<#
.SYNOPSIS
  Writes manifest.json (path, size, SHA-256 of every file) into a release folder (T3.21). Deterministic:
  sorted ordinally, LF line endings, no timestamps. manifest.json does not list itself.
  Used by tools\release.ps1 and tools\test_updater.ps1. Windows PowerShell 5.1.
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$Dir,
    [Parameter(Mandatory = $true)][string]$Version
)
$ErrorActionPreference = 'Stop'
$base = (Resolve-Path -LiteralPath $Dir).Path.TrimEnd('\')
$out = Join-Path $base 'manifest.json'
if (Test-Path -LiteralPath $out) { Remove-Item -LiteralPath $out -Force }

function Esc([string]$s) {
    $sb = New-Object Text.StringBuilder
    foreach ($c in $s.ToCharArray()) {
        $n = [int]$c
        if ($c -eq '"') { [void]$sb.Append('\"') }
        elseif ($c -eq '\') { [void]$sb.Append('\\') }
        elseif ($n -lt 32 -or $n -gt 126) { [void]$sb.Append(('\u{0:x4}' -f $n)) }
        else { [void]$sb.Append($c) }
    }
    return $sb.ToString()
}

$rels = New-Object System.Collections.Generic.List[string]
foreach ($f in Get-ChildItem -LiteralPath $base -Recurse -File) { $rels.Add($f.FullName.Substring($base.Length + 1).Replace('\', '/')) }
$rels.Sort([StringComparer]::Ordinal)
$sha = [Security.Cryptography.SHA256]::Create()
$lines = New-Object System.Collections.Generic.List[string]
foreach ($rel in $rels) {
    $full = Join-Path $base ($rel.Replace('/', '\'))
    $fs = [IO.File]::OpenRead($full)
    try { $h = $sha.ComputeHash($fs); $len = $fs.Length } finally { $fs.Dispose() }
    $hex = ($h | ForEach-Object { $_.ToString('x2') }) -join ''
    $lines.Add(('    {{"path": "{0}", "size": {1}, "sha256": "{2}"}}' -f (Esc $rel), $len, $hex))
}
$text = "{`n  `"manifest_version`": 1,`n  `"product`": `"MythologyKombat`",`n  `"version`": `"" + (Esc $Version) + "`",`n  `"files`": [`n" + ($lines -join ",`n") + "`n  ]`n}`n"
[IO.File]::WriteAllText($out, $text, (New-Object Text.UTF8Encoding($false)))
Write-Host ("manifest.json: {0} files" -f $rels.Count)
