param([Parameter(ValueFromRemainingArguments=$true)][string[]]$InstallerArgs)
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
python scripts/install.py --install @InstallerArgs
exit $LASTEXITCODE
