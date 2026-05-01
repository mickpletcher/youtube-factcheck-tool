param(
    [Parameter(Mandatory)]
    [string]$Url,
    [string]$JsonOutputPath,
    [string]$MarkdownOutputPath
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

Import-Module (Join-Path $PSScriptRoot 'YouTubeFactCheck.psm1') -Force

$result = Invoke-YftFactCheck -Url $Url

if ($JsonOutputPath) {
    $result | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $JsonOutputPath -Encoding UTF8
}

if ($MarkdownOutputPath) {
    $result.report_markdown | Set-Content -LiteralPath $MarkdownOutputPath -Encoding UTF8
}

$result | ConvertTo-Json -Depth 10
