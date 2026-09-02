param(
    [Parameter(Mandatory = $true)]
    [string]$Vault
)
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$py = Get-Command py -ErrorAction SilentlyContinue
if ($py) {
    & py -3 (Join-Path $here 'deploy.py') --vault $Vault
} else {
    & python (Join-Path $here 'deploy.py') --vault $Vault
}
