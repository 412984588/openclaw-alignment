param(
  [switch]$Phase3,
  [switch]$Dev,
  [switch]$Editable
)

$Root = Split-Path -Parent $PSScriptRoot
$Args = @()
if ($Phase3) { $Args += "--phase3" }
if ($Dev) { $Args += "--dev" }
if ($Editable) { $Args += "--editable" }

python "$Root/scripts/install.py" @Args
