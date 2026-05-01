Set-StrictMode -Version Latest

$script:TrustedDomains = @(
    'reuters.com',
    'apnews.com',
    'bbc.com',
    'bbc.co.uk',
    'nytimes.com',
    'theguardian.com',
    'washingtonpost.com',
    'nature.com',
    'science.org',
    'scientificamerican.com',
    'who.int',
    'cdc.gov',
    'nih.gov',
    'nasa.gov',
    'snopes.com',
    'factcheck.org',
    'politifact.com',
    'fullfact.org',
    'sciencedirect.com',
    'pubmed.ncbi.nlm.nih.gov',
    'britannica.com',
    'history.com'
)

$script:ClaimPrompt = @'
You are a fact checking assistant. Identify distinct, verifiable factual claims from the provided transcript text.
Exclude opinions, predictions, and rhetorical questions.
Return only a JSON array of claim strings.
'@

$script:VerdictPrompt = @'
You are a fact checking expert. Given one claim and a list of search results, return only JSON with these keys:
verdict, confidence, explanation, sources
Allowed verdict values are Supported, Contradicted, Disputed, and Unverified.
'@

function Write-YftLog {
    param(
        [Parameter(Mandatory)]
        [string]$Stage,
        [Parameter(Mandatory)]
        [string]$Status,
        [hashtable]$Fields = @{}
    )

    $payload = [ordered]@{
        stage  = $Stage
        status = $Status
    }

    foreach ($key in $Fields.Keys) {
        $payload[$key] = $Fields[$key]
    }

    Write-Information ($payload | ConvertTo-Json -Compress -Depth 10) -InformationAction Continue
}

function Get-YftRepoRoot {
    $root = Resolve-Path (Join-Path $PSScriptRoot '..')
    return $root.Path
}

function Get-YftSettings {
    $repoRoot = Get-YftRepoRoot
    $envPath = Join-Path $repoRoot '.env'
    $settings = [ordered]@{
        OpenAIApiKey             = ''
        OpenAIModel              = 'gpt-4o-mini'
        OpenAITranscriptionModel = 'whisper-1'
        MaxClaims                = 10
        ResearchMaxResults       = 5
    }

    if (Test-Path -LiteralPath $envPath) {
        foreach ($line in Get-Content -LiteralPath $envPath) {
            $trimmed = $line.Trim()
            if (-not $trimmed) { continue }
            if ($trimmed.StartsWith('#')) { continue }
            $parts = $trimmed -split '=', 2
            if ($parts.Count -ne 2) { continue }
            $name = $parts[0].Trim()
            $value = $parts[1].Trim()
            switch ($name) {
                'OPENAI_API_KEY' { $settings.OpenAIApiKey = $value }
                'OPENAI_MODEL' {
                    if ($value) { $settings.OpenAIModel = $value }
                }
                'OPENAI_TRANSCRIPTION_MODEL' {
                    if ($value) { $settings.OpenAITranscriptionModel = $value }
                }
                'MAX_CLAIMS' {
                    $parsed = 0
                    if ([int]::TryParse($value, [ref]$parsed) -and $parsed -gt 0) {
                        $settings.MaxClaims = $parsed
                    }
                }
                'RESEARCH_MAX_RESULTS' {
                    $parsed = 0
                    if ([int]::TryParse($value, [ref]$parsed) -and $parsed -gt 0) {
                        $settings.ResearchMaxResults = $parsed
                    }
                }
            }
        }
    }

    return [pscustomobject]$settings
}

function Test-YftYouTubeUrl {
    param(
        [Parameter(Mandatory)]
        [string]$Url
    )

    return ($Url -match 'youtube\.com' -or $Url -match 'youtu\.be')
}

function Get-YftVideoId {
    param(
        [Parameter(Mandatory)]
        [string]$Url
    )

    $uri = [System.Uri]$Url
    $host = $uri.Host.ToLowerInvariant()

    if ($host -eq 'youtu.be') {
        $candidate = $uri.AbsolutePath.Trim('/')
        if ($candidate) {
            return ($candidate -split '/')[0]
        }
    }

    if ($host -in @('www.youtube.com', 'youtube.com', 'm.youtube.com')) {
        if ($uri.AbsolutePath -eq '/watch') {
            $query = [System.Web.HttpUtility]::ParseQueryString($uri.Query)
            $videoId = $query['v']
            if ($videoId) {
                return $videoId
            }
        }

        $match = [regex]::Match($uri.AbsolutePath, '^/(embed|shorts|v)/([A-Za-z0-9_-]+)')
        if ($match.Success) {
            return $match.Groups[2].Value
        }
    }

    throw "Could not extract video ID from URL: $Url"
}

function Get-YftVideoMetadata {
    param(
        [Parameter(Mandatory)]
        [string]$Url
    )

    $videoId = Get-YftVideoId -Url $Url

    try {
        $json = & yt-dlp --dump-single-json --skip-download --no-warnings --quiet $Url 2>$null
        if (-not $json) {
            throw 'yt-dlp returned no metadata.'
        }

        $info = $json | ConvertFrom-Json
        $publishedAt = $null
        if ($info.upload_date -and $info.upload_date.Length -eq 8) {
            $publishedAt = '{0}-{1}-{2}' -f $info.upload_date.Substring(0, 4), $info.upload_date.Substring(4, 2), $info.upload_date.Substring(6, 2)
        }

        return [pscustomobject]@{
            video_id         = if ($info.id) { $info.id } else { $videoId }
            title            = if ($info.title) { $info.title } else { 'Unknown Title' }
            channel          = if ($info.channel) { $info.channel } elseif ($info.uploader) { $info.uploader } else { 'Unknown Channel' }
            published_at     = $publishedAt
            duration_seconds = if ($null -ne $info.duration) { [int]$info.duration } else { $null }
            url              = $Url
        }
    }
    catch {
        return [pscustomobject]@{
            video_id         = $videoId
            title            = 'Unknown Title'
            channel          = 'Unknown Channel'
            published_at     = $null
            duration_seconds = $null
            url              = $Url
        }
    }
}

function ConvertFrom-YftSubtitleText {
    param(
        [Parameter(Mandatory)]
        [string]$Text
    )

    $lines = $Text -split "`r?`n"
    $content = New-Object System.Collections.Generic.List[string]
    foreach ($line in $lines) {
        $trimmed = $line.Trim()
        if (-not $trimmed) { continue }
        if ($trimmed -match '^(WEBVTT|Kind:|Language:|NOTE)') { continue }
        if ($trimmed -match '^\d+$') { continue }
        if ($trimmed -match '^\d{2}:\d{2}:\d{2}\.\d{3}\s+-->\s+\d{2}:\d{2}:\d{2}\.\d{3}') { continue }
        if ($trimmed -match '^\d{2}:\d{2}\.\d{3}\s+-->\s+\d{2}:\d{2}\.\d{3}') { continue }
        if ($trimmed -match '^<\d{2}:\d{2}:\d{2}\.\d{3}>') {
            $trimmed = [regex]::Replace($trimmed, '<[^>]+>', ' ')
        }
        $trimmed = [regex]::Replace($trimmed, '<[^>]+>', ' ')
        $trimmed = [regex]::Replace($trimmed, '&nbsp;', ' ')
        $trimmed = [regex]::Replace($trimmed, '\s+', ' ').Trim()
        if ($trimmed) {
            [void]$content.Add($trimmed)
        }
    }

    return (($content | Select-Object -Unique) -join ' ').Trim()
}

function Get-YftYouTubeCaptions {
    param(
        [Parameter(Mandatory)]
        [string]$Url
    )

    $tempDir = Join-Path ([System.IO.Path]::GetTempPath()) ("yft_subs_" + [guid]::NewGuid().ToString('N'))
    [System.IO.Directory]::CreateDirectory($tempDir) | Out-Null

    try {
        $outputTemplate = Join-Path $tempDir 'subtitle'
        & yt-dlp `
            --skip-download `
            --write-subs `
            --write-auto-subs `
            --sub-langs 'en,en-US,en-GB' `
            --convert-subs vtt `
            --output $outputTemplate `
            --no-warnings `
            --quiet `
            $Url 2>$null | Out-Null

        $subtitleFile = Get-ChildItem -LiteralPath $tempDir -File | Where-Object {
            $_.Extension -in @('.vtt', '.srv1', '.srv2', '.srv3', '.ttml')
        } | Select-Object -First 1

        if (-not $subtitleFile) {
            return $null
        }

        $subtitleText = Get-Content -LiteralPath $subtitleFile.FullName -Raw
        $plainText = ConvertFrom-YftSubtitleText -Text $subtitleText
        if (-not $plainText) {
            return $null
        }

        return [pscustomobject]@{
            text     = $plainText
            source   = 'youtube_captions'
            language = 'en'
        }
    }
    finally {
        if (Test-Path -LiteralPath $tempDir) {
            Remove-Item -LiteralPath $tempDir -Recurse -Force
        }
    }
}

function Invoke-YftAudioTranscription {
    param(
        [Parameter(Mandatory)]
        [string]$AudioPath,
        [Parameter(Mandatory)]
        [string]$ApiKey,
        [Parameter(Mandatory)]
        [string]$Model
    )

    $handler = New-Object System.Net.Http.HttpClientHandler
    $client = New-Object System.Net.Http.HttpClient($handler)
    try {
        $client.DefaultRequestHeaders.Authorization = New-Object System.Net.Http.Headers.AuthenticationHeaderValue('Bearer', $ApiKey)
        $content = New-Object System.Net.Http.MultipartFormDataContent
        $content.Add((New-Object System.Net.Http.StringContent($Model)), 'model')
        $fileBytes = [System.IO.File]::ReadAllBytes($AudioPath)
        $fileContent = New-Object System.Net.Http.ByteArrayContent($fileBytes)
        $fileContent.Headers.ContentType = New-Object System.Net.Http.Headers.MediaTypeHeaderValue('audio/mpeg')
        $content.Add($fileContent, 'file', [System.IO.Path]::GetFileName($AudioPath))

        $response = $client.PostAsync('https://api.openai.com/v1/audio/transcriptions', $content).GetAwaiter().GetResult()
        $body = $response.Content.ReadAsStringAsync().GetAwaiter().GetResult()
        if (-not $response.IsSuccessStatusCode) {
            throw "OpenAI transcription request failed: $($response.StatusCode) $body"
        }

        $data = $body | ConvertFrom-Json
        return [pscustomobject]@{
            text     = [string]$data.text
            source   = 'audio_transcription'
            language = if ($data.language) { [string]$data.language } else { 'en' }
        }
    }
    finally {
        $client.Dispose()
        $handler.Dispose()
    }
}

function Get-YftAudioTranscript {
    param(
        [Parameter(Mandatory)]
        [string]$Url,
        [Parameter(Mandatory)]
        [pscustomobject]$Settings
    )

    if (-not $Settings.OpenAIApiKey) {
        return $null
    }

    $tempDir = Join-Path ([System.IO.Path]::GetTempPath()) ("yft_audio_" + [guid]::NewGuid().ToString('N'))
    [System.IO.Directory]::CreateDirectory($tempDir) | Out-Null

    try {
        $outputTemplate = Join-Path $tempDir 'audio.%(ext)s'
        & yt-dlp `
            --extract-audio `
            --audio-format mp3 `
            --audio-quality 5 `
            --output $outputTemplate `
            --no-warnings `
            --quiet `
            $Url 2>$null | Out-Null

        $audioFile = Get-ChildItem -LiteralPath $tempDir -File | Where-Object {
            $_.Extension -eq '.mp3'
        } | Select-Object -First 1

        if (-not $audioFile) {
            return $null
        }

        return Invoke-YftAudioTranscription -AudioPath $audioFile.FullName -ApiKey $Settings.OpenAIApiKey -Model $Settings.OpenAITranscriptionModel
    }
    catch {
        return $null
    }
    finally {
        if (Test-Path -LiteralPath $tempDir) {
            Remove-Item -LiteralPath $tempDir -Recurse -Force
        }
    }
}

function Get-YftTranscript {
    param(
        [Parameter(Mandatory)]
        [string]$Url,
        [Parameter(Mandatory)]
        [pscustomobject]$Settings
    )

    $captionResult = Get-YftYouTubeCaptions -Url $Url
    if ($captionResult) {
        Write-YftLog -Stage 'transcript_fetch' -Status 'complete' -Fields @{
            transcript_source = $captionResult.source
            transcript_length = $captionResult.text.Length
            language          = $captionResult.language
        }
        return $captionResult
    }

    $audioResult = Get-YftAudioTranscript -Url $Url -Settings $Settings
    if ($audioResult) {
        Write-YftLog -Stage 'transcript_fetch' -Status 'complete' -Fields @{
            transcript_source = $audioResult.source
            transcript_length = $audioResult.text.Length
            language          = $audioResult.language
        }
        return $audioResult
    }

    Write-YftLog -Stage 'transcript_fetch' -Status 'complete' -Fields @{
        transcript_source = 'unavailable'
        transcript_length = 0
        language          = $null
    }

    return [pscustomobject]@{
        text     = ''
        source   = 'unavailable'
        language = $null
    }
}

function Get-YftHeuristicClaims {
    param(
        [Parameter(Mandatory)]
        [string]$TranscriptText,
        [Parameter(Mandatory)]
        [int]$MaxClaims
    )

    $sentences = [regex]::Split($TranscriptText, '(?<=[.!?])\s+')
    $claims = New-Object System.Collections.Generic.List[object]
    $index = 1

    foreach ($sentence in $sentences) {
        $trimmed = $sentence.Trim()
        if (-not $trimmed) { continue }
        if ([regex]::Matches($trimmed, '\S+').Count -lt 6) { continue }
        if ($trimmed -notmatch '(?i)\b(percent|%|million|billion|trillion|founded|born|died|invented|discovered|according|research|study|studies|scientists|proved|proven|fact|evidence|data|statistics|statistic|report|reported|published|recorded|measured|largest|smallest|first|last|oldest|newest|highest|lowest)\b') { continue }
        $claims.Add([pscustomobject]@{
            id   = "claim_$index"
            text = $trimmed
        })
        $index++
        if ($claims.Count -ge $MaxClaims) {
            break
        }
    }

    return $claims.ToArray()
}

function Invoke-YftChatCompletion {
    param(
        [Parameter(Mandatory)]
        [string]$ApiKey,
        [Parameter(Mandatory)]
        [string]$Model,
        [Parameter(Mandatory)]
        [object[]]$Messages,
        [double]$Temperature = 0.2,
        [int]$MaxTokens = 1024
    )

    $headers = @{
        Authorization = "Bearer $ApiKey"
        'Content-Type' = 'application/json'
    }

    $body = @{
        model       = $Model
        messages    = $Messages
        temperature = $Temperature
        max_tokens  = $MaxTokens
    } | ConvertTo-Json -Depth 10

    $response = Invoke-RestMethod -Method Post -Uri 'https://api.openai.com/v1/chat/completions' -Headers $headers -Body $body
    return [string]$response.choices[0].message.content
}

function ConvertFrom-YftJsonFragment {
    param(
        [Parameter(Mandatory)]
        [string]$Text,
        [Parameter(Mandatory)]
        [string]$Kind
    )

    $raw = $Text.Trim()
    $raw = [regex]::Replace($raw, '^```(?:json)?\s*', '', 'IgnoreCase')
    $raw = [regex]::Replace($raw, '```$', '')

    if ($Kind -eq 'array') {
        try {
            return ($raw | ConvertFrom-Json)
        }
        catch {
            $match = [regex]::Match($raw, '\[.*\]', 'Singleline')
            if ($match.Success) {
                return ($match.Value | ConvertFrom-Json)
            }
        }
    }

    if ($Kind -eq 'object') {
        try {
            return ($raw | ConvertFrom-Json)
        }
        catch {
            $match = [regex]::Match($raw, '\{.*\}', 'Singleline')
            if ($match.Success) {
                return ($match.Value | ConvertFrom-Json)
            }
        }
    }

    return $null
}

function Get-YftClaims {
    param(
        [Parameter(Mandatory)]
        [string]$TranscriptText,
        [Parameter(Mandatory)]
        [pscustomobject]$Settings
    )

    if (-not $TranscriptText.Trim()) {
        Write-YftLog -Stage 'claim_extraction' -Status 'complete' -Fields @{
            claim_count = 0
            provider    = 'none'
        }
        return @()
    }

    if ($Settings.OpenAIApiKey) {
        try {
            $truncated = if ($TranscriptText.Length -gt 12000) { $TranscriptText.Substring(0, 12000) } else { $TranscriptText }
            $messages = @(
                @{ role = 'system'; content = $script:ClaimPrompt }
                @{ role = 'user'; content = "Extract up to $($Settings.MaxClaims) key factual claims from this transcript:`n`n$truncated" }
            )
            $raw = Invoke-YftChatCompletion -ApiKey $Settings.OpenAIApiKey -Model $Settings.OpenAIModel -Messages $messages -Temperature 0.2 -MaxTokens 1024
            $claimTexts = ConvertFrom-YftJsonFragment -Text $raw -Kind 'array'
            if ($claimTexts) {
                $claims = New-Object System.Collections.Generic.List[object]
                $index = 1
                foreach ($claimText in $claimTexts) {
                    $value = [string]$claimText
                    if (-not $value.Trim()) { continue }
                    $claims.Add([pscustomobject]@{
                        id   = "claim_$index"
                        text = $value.Trim()
                    })
                    $index++
                    if ($claims.Count -ge $Settings.MaxClaims) {
                        break
                    }
                }
                if ($claims.Count -gt 0) {
                    Write-YftLog -Stage 'claim_extraction' -Status 'complete' -Fields @{
                        claim_count = $claims.Count
                        provider    = 'openai'
                    }
                    return $claims.ToArray()
                }
            }
        }
        catch {
        }
    }

    $heuristicClaims = @(Get-YftHeuristicClaims -TranscriptText $TranscriptText -MaxClaims $Settings.MaxClaims)
    Write-YftLog -Stage 'claim_extraction' -Status 'complete' -Fields @{
        claim_count = $heuristicClaims.Count
        provider    = 'heuristic'
    }
    return $heuristicClaims
}

function Test-YftTrustedUrl {
    param(
        [Parameter(Mandatory)]
        [string]$Url
    )

    $lower = $Url.ToLowerInvariant()
    foreach ($domain in $script:TrustedDomains) {
        if ($lower.Contains($domain)) {
            return $true
        }
    }

    return $false
}

function Get-YftSearchResults {
    param(
        [Parameter(Mandatory)]
        [string]$Query,
        [Parameter(Mandatory)]
        [int]$MaxResults
    )

    $encoded = [System.Uri]::EscapeDataString($Query)
    $uri = "https://html.duckduckgo.com/html/?q=$encoded"

    try {
        $response = Invoke-WebRequest -Uri $uri -Headers @{ 'User-Agent' = 'Mozilla/5.0' } -UseBasicParsing
    }
    catch {
        return @()
    }

    $matches = [regex]::Matches($response.Content, '<a[^>]+class="[^"]*result__a[^"]*"[^>]+href="(?<url>[^"]+)"[^>]*>(?<title>.*?)</a>.*?<a[^>]+class="[^"]*result__snippet[^"]*"[^>]*>(?<snippet>.*?)</a>', 'Singleline')
    $results = New-Object System.Collections.Generic.List[object]

    foreach ($match in $matches) {
        $title = [System.Net.WebUtility]::HtmlDecode(([regex]::Replace($match.Groups['title'].Value, '<[^>]+>', ' '))).Trim()
        $snippet = [System.Net.WebUtility]::HtmlDecode(([regex]::Replace($match.Groups['snippet'].Value, '<[^>]+>', ' '))).Trim()
        $url = [System.Net.WebUtility]::HtmlDecode($match.Groups['url'].Value)

        if (-not $url -or -not $title) { continue }
        $results.Add([pscustomobject]@{
            title   = $title
            url     = $url
            snippet = $snippet
        })
    }

    $trusted = @($results | Where-Object { Test-YftTrustedUrl -Url $_.url })
    $others = @($results | Where-Object { -not (Test-YftTrustedUrl -Url $_.url) })
    return @($trusted + $others | Select-Object -First $MaxResults)
}

function Get-YftResearchResults {
    param(
        [AllowEmptyCollection()]
        [Parameter(Mandatory)]
        [object[]]$Claims,
        [Parameter(Mandatory)]
        [pscustomobject]$Settings
    )

    $results = New-Object System.Collections.Generic.List[object]
    foreach ($claim in $Claims) {
        $query = "fact check: `"$($claim.text)`""
        $searchResults = @(Get-YftSearchResults -Query $query -MaxResults $Settings.ResearchMaxResults)
        $results.Add([pscustomobject]@{
            claim_id       = $claim.id
            claim_text     = $claim.text
            search_results = $searchResults
        })
    }

    $searchResultCount = 0
    foreach ($result in $results) {
        $searchResultCount += @($result.search_results).Count
    }
    Write-YftLog -Stage 'research' -Status 'complete' -Fields @{
        claim_count         = $results.Count
        search_result_count = $searchResultCount
    }

    return $results.ToArray()
}

function Get-YftHeuristicVerdict {
    param(
        [Parameter(Mandatory)]
        [pscustomobject]$ResearchResult
    )

    $parts = foreach ($item in $ResearchResult.search_results) {
        '{0} {1}' -f $item.title, $item.snippet
    }
    $allText = ($parts -join ' ')

    $positive = [regex]::Matches($allText, '(?i)\b(confirm|confirmed|true|accurate|correct|verified|fact|evidence|proven|support|supported|valid|agree|agrees|agreed|yes|right)\b').Count
    $negative = [regex]::Matches($allText, '(?i)\b(false|incorrect|wrong|debunked|myth|misleading|inaccurate|refuted|disproven|contradict|contradicts|contradicted|fake|hoax)\b|no evidence').Count
    $total = $positive + $negative

    if ($total -eq 0) {
        $verdict = 'Unverified'
        $confidence = 0.3
        $explanation = 'No relevant evidence was found in the search results.'
    }
    elseif ($positive -gt ($negative * 2)) {
        $verdict = 'Supported'
        $confidence = [math]::Min(0.5 + ($positive / ($total * 2)), 0.85)
        $explanation = "Search results contain mostly supportive language ($positive positive vs $negative negative signals)."
    }
    elseif ($negative -gt ($positive * 2)) {
        $verdict = 'Contradicted'
        $confidence = [math]::Min(0.5 + ($negative / ($total * 2)), 0.85)
        $explanation = "Search results contain mostly contradictory language ($negative negative vs $positive positive signals)."
    }
    else {
        $verdict = 'Disputed'
        $confidence = 0.4
        $explanation = "Search results contain mixed signals ($positive positive, $negative negative)."
    }

    return [pscustomobject]@{
        id          = $ResearchResult.claim_id
        text        = $ResearchResult.claim_text
        verdict     = $verdict
        confidence  = [math]::Round($confidence, 2)
        explanation = $explanation
        sources     = @($ResearchResult.search_results | Select-Object -First 3 | ForEach-Object { $_.url })
    }
}

function Get-YftScoredClaims {
    param(
        [AllowEmptyCollection()]
        [Parameter(Mandatory)]
        [object[]]$ResearchResults,
        [Parameter(Mandatory)]
        [pscustomobject]$Settings
    )

    $scored = New-Object System.Collections.Generic.List[object]
    foreach ($result in $ResearchResults) {
        if ($Settings.OpenAIApiKey) {
            try {
                $formattedResults = if ($result.search_results.Count -gt 0) {
                    ($result.search_results | ForEach-Object -Begin { $i = 1 } -Process {
                        $line = "[{0}] {1}`nURL: {2}`nSnippet: {3}" -f $i, $_.title, $_.url, ($_.snippet.Substring(0, [Math]::Min($_.snippet.Length, 300)))
                        $i++
                        $line
                    }) -join "`n`n"
                }
                else {
                    'No results found.'
                }

                $messages = @(
                    @{ role = 'system'; content = $script:VerdictPrompt }
                    @{ role = 'user'; content = "Claim: $($result.claim_text)`n`nSearch Results:`n$formattedResults" }
                )

                $raw = Invoke-YftChatCompletion -ApiKey $Settings.OpenAIApiKey -Model $Settings.OpenAIModel -Messages $messages -Temperature 0.1 -MaxTokens 512
                $data = ConvertFrom-YftJsonFragment -Text $raw -Kind 'object'
                if ($data) {
                    $confidence = 0.5
                    if ($data.confidence -ne $null) {
                        $confidence = [double]$data.confidence
                    }
                    $confidence = [math]::Max(0.0, [math]::Min(1.0, $confidence))
                    $sources = @()
                    if ($data.sources -is [System.Collections.IEnumerable]) {
                        foreach ($source in $data.sources) {
                            $sources += [string]$source
                        }
                    }

                    $scored.Add([pscustomobject]@{
                        id          = $result.claim_id
                        text        = $result.claim_text
                        verdict     = if ($data.verdict) { [string]$data.verdict } else { 'Unverified' }
                        confidence  = $confidence
                        explanation = if ($data.explanation) { [string]$data.explanation } else { '' }
                        sources     = $sources
                    })
                    continue
                }
            }
            catch {
            }
        }

        $scored.Add((Get-YftHeuristicVerdict -ResearchResult $result))
    }

    $provider = if ($Settings.OpenAIApiKey) { 'mixed_or_openai' } else { 'heuristic' }
    Write-YftLog -Stage 'verdict_scoring' -Status 'complete' -Fields @{
        scored_claim_count = $scored.Count
        provider           = $provider
    }

    return $scored.ToArray()
}

function Get-YftOverallCredibilityScore {
    param(
        [AllowEmptyCollection()]
        [Parameter(Mandatory)]
        [object[]]$Claims
    )

    if ($Claims.Count -eq 0) {
        return 0.5
    }

    $weights = @{
        Supported    = 1.0
        Unverified   = 0.5
        Disputed     = 0.25
        Contradicted = 0.0
    }

    $totalWeight = 0.0
    $weightedScore = 0.0
    foreach ($claim in $Claims) {
        $weight = [double]$claim.confidence
        $totalWeight += $weight
        $weightedScore += ($weights[[string]$claim.verdict] * $weight)
    }

    if ($totalWeight -eq 0) {
        return 0.5
    }

    return [math]::Round(($weightedScore / $totalWeight), 2)
}

function Get-YftSummary {
    param(
        [AllowEmptyCollection()]
        [Parameter(Mandatory)]
        [object[]]$Claims,
        [Parameter(Mandatory)]
        [double]$OverallScore
    )

    if ($Claims.Count -eq 0) {
        return 'No factual claims could be extracted from this video.'
    }

    $counts = [ordered]@{}
    foreach ($claim in $Claims) {
        $label = [string]$claim.verdict
        if (-not $counts.Contains($label)) {
            $counts[$label] = 0
        }
        $counts[$label]++
    }

    $breakdown = ($counts.GetEnumerator() | ForEach-Object { '{0}: {1}' -f $_.Key, $_.Value }) -join ', '
    $pct = [int]($OverallScore * 100)

    if ($OverallScore -ge 0.75) {
        $assessment = 'The content appears to be largely credible.'
    }
    elseif ($OverallScore -ge 0.5) {
        $assessment = 'The content has mixed credibility.'
    }
    elseif ($OverallScore -ge 0.25) {
        $assessment = 'The content contains significant inaccuracies or unverified claims.'
    }
    else {
        $assessment = 'The content is largely inaccurate or contradicted by evidence.'
    }

    return "Analysed $($Claims.Count) claim(s) from this video ($breakdown). Overall credibility score: $pct%. $assessment"
}

function New-YftMarkdownReport {
    param(
        [Parameter(Mandatory)]
        [pscustomobject]$Video,
        [Parameter(Mandatory)]
        [string]$TranscriptSource,
        [AllowEmptyCollection()]
        [Parameter(Mandatory)]
        [object[]]$Claims,
        [Parameter(Mandatory)]
        [string]$Summary,
        [Parameter(Mandatory)]
        [double]$OverallScore
    )

    $lines = New-Object System.Collections.Generic.List[string]
    $lines.Add('# Fact Check Report')
    $lines.Add('')
    $lines.Add('## Video Information')
    $lines.Add('')
    $lines.Add("* Title: $($Video.title)")
    $lines.Add("* Channel: $($Video.channel)")
    if ($Video.published_at) {
        $lines.Add("* Published: $($Video.published_at)")
    }
    if ($null -ne $Video.duration_seconds) {
        $minutes = [math]::Floor([int]$Video.duration_seconds / 60)
        $seconds = [int]$Video.duration_seconds % 60
        $lines.Add("* Duration: $minutes m $seconds s")
    }
    $lines.Add("* URL: $($Video.url)")
    $lines.Add("* Transcript source: $($TranscriptSource.Replace('_', ' '))")
    $lines.Add('')
    $lines.Add('## Summary')
    $lines.Add('')
    $lines.Add($Summary)
    $lines.Add('')
    $lines.Add("Overall Credibility Score: $([int]($OverallScore * 100))%")
    $lines.Add('')

    if ($Claims.Count -gt 0) {
        $lines.Add('## Claim by Claim Analysis')
        $lines.Add('')
        foreach ($claim in $Claims) {
            $lines.Add("### $($claim.id): $($claim.verdict) ($([int]([double]$claim.confidence * 100))% confidence)")
            $lines.Add('')
            $lines.Add("> $($claim.text)")
            $lines.Add('')
            $lines.Add("Explanation: $($claim.explanation)")
            if ($claim.sources.Count -gt 0) {
                $lines.Add('')
                $lines.Add('Sources:')
                foreach ($source in $claim.sources) {
                    $lines.Add("* $source")
                }
            }
            $lines.Add('')
        }
    }

    return ($lines -join "`n")
}

function New-YftReport {
    param(
        [Parameter(Mandatory)]
        [pscustomobject]$Video,
        [Parameter(Mandatory)]
        [pscustomobject]$Transcript,
        [AllowEmptyCollection()]
        [Parameter(Mandatory)]
        [object[]]$ScoredClaims
    )

    $overall = Get-YftOverallCredibilityScore -Claims $ScoredClaims
    $summary = Get-YftSummary -Claims $ScoredClaims -OverallScore $overall
    $markdown = New-YftMarkdownReport -Video $Video -TranscriptSource $Transcript.source -Claims $ScoredClaims -Summary $summary -OverallScore $overall

    return [pscustomobject]@{
        video                     = $Video
        transcript_source         = $Transcript.source
        claims                    = @($ScoredClaims)
        summary                   = $summary
        overall_credibility_score = $overall
        report_markdown           = $markdown
    }
}

function Invoke-YftFactCheck {
    param(
        [Parameter(Mandatory)]
        [string]$Url
    )

    if (-not (Test-YftYouTubeUrl -Url $Url)) {
        throw 'URL must be a YouTube link (youtube.com or youtu.be).'
    }

    $settings = Get-YftSettings
    $video = Get-YftVideoMetadata -Url $Url
    Write-YftLog -Stage 'metadata' -Status 'complete' -Fields @{
        video_id = $video.video_id
        title    = $video.title
        channel  = $video.channel
    }
    $transcript = Get-YftTranscript -Url $Url -Settings $settings
    $claims = @(Get-YftClaims -TranscriptText $transcript.text -Settings $settings)
    $research = @(Get-YftResearchResults -Claims $claims -Settings $settings)
    $scored = @(Get-YftScoredClaims -ResearchResults $research -Settings $settings)
    $report = New-YftReport -Video $video -Transcript $transcript -ScoredClaims $scored
    Write-YftLog -Stage 'report_generation' -Status 'complete' -Fields @{
        overall_credibility_score = $report.overall_credibility_score
        claim_count               = @($report.claims).Count
    }
    return $report
}

Export-ModuleMember -Function @(
    'Get-YftSettings',
    'Test-YftYouTubeUrl',
    'Get-YftVideoId',
    'Get-YftVideoMetadata',
    'Get-YftTranscript',
    'Get-YftClaims',
    'Get-YftResearchResults',
    'Get-YftScoredClaims',
    'New-YftReport',
    'Invoke-YftFactCheck'
)
