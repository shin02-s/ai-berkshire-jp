<#
.SYNOPSIS
Sets EDINET_API_KEY for this PowerShell session and the current Windows user.

.DESCRIPTION
The key is not printed or saved in the repository. New terminals inherit it.
#>
[CmdletBinding()]
param(
    [SecureString]$ApiKey
)

if (-not $ApiKey) {
    $ApiKey = Read-Host 'EDINET API key' -AsSecureString
}

$bstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($ApiKey)
try {
    $plainTextKey = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($bstr).Trim()
    if ([string]::IsNullOrWhiteSpace($plainTextKey)) {
        throw 'EDINET API key is empty.'
    }
    [Environment]::SetEnvironmentVariable('EDINET_API_KEY', $plainTextKey, 'User')
    $env:EDINET_API_KEY = $plainTextKey
    Write-Host 'EDINET_API_KEY is set for this session and the current Windows user.' -ForegroundColor Green
}
finally {
    if ($bstr -ne [IntPtr]::Zero) {
        [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr)
    }
    Remove-Variable plainTextKey -ErrorAction SilentlyContinue
}
