Import-Module (Join-Path $PSScriptRoot '..\powershell_app\YouTubeFactCheck.psm1') -Force

Describe 'YouTubeFactCheck module' {
    InModuleScope YouTubeFactCheck {
        It 'extracts a video id from a watch url' {
            Get-YftVideoId -Url 'https://www.youtube.com/watch?v=dQw4w9WgXcQ' | Should -Be 'dQw4w9WgXcQ'
        }

        It 'extracts a video id from a short url' {
            Get-YftVideoId -Url 'https://youtu.be/dQw4w9WgXcQ' | Should -Be 'dQw4w9WgXcQ'
        }

        It 'rejects a non youtube url' {
            Test-YftYouTubeUrl -Url 'https://vimeo.com/123' | Should -BeFalse
        }

        It 'creates heuristic claims from factual text' {
            $settings = [pscustomobject]@{
                OpenAIApiKey       = ''
                OpenAIModel        = 'gpt-4o-mini'
                MaxClaims          = 5
                ResearchMaxResults = 5
            }

            $claims = Get-YftClaims -TranscriptText 'According to scientists, the Moon is 384,400 km from Earth. I like pizza.' -Settings $settings
            $claims.Count | Should -Be 1
            $claims[0].id | Should -Be 'claim_1'
        }

        It 'builds a report with the expected shape' {
            $video = [pscustomobject]@{
                video_id         = 'dQw4w9WgXcQ'
                title            = 'Test Video'
                channel          = 'Test Channel'
                published_at     = '2026-05-01'
                duration_seconds = 120
                url              = 'https://www.youtube.com/watch?v=dQw4w9WgXcQ'
            }

            $transcript = [pscustomobject]@{
                text     = 'Transcript'
                source   = 'youtube_captions'
                language = 'en'
            }

            $claims = @(
                [pscustomobject]@{
                    id          = 'claim_1'
                    text        = 'The Earth is 4.5 billion years old.'
                    verdict     = 'Supported'
                    confidence  = 0.9
                    explanation = 'Multiple sources support the claim.'
                    sources     = @('https://britannica.com/example')
                }
            )

            $report = New-YftReport -Video $video -Transcript $transcript -ScoredClaims $claims

            $report.video.video_id | Should -Be 'dQw4w9WgXcQ'
            $report.transcript_source | Should -Be 'youtube_captions'
            $report.claims.Count | Should -Be 1
            $report.report_markdown | Should -Match 'Fact Check Report'
        }

        It 'runs the full pipeline with mocks' {
            Mock Get-YftSettings {
                [pscustomobject]@{
                    OpenAIApiKey             = ''
                    OpenAIModel              = 'gpt-4o-mini'
                    OpenAITranscriptionModel = 'whisper-1'
                    MaxClaims                = 5
                    ResearchMaxResults       = 3
                }
            }

            Mock Get-YftVideoMetadata {
                [pscustomobject]@{
                    video_id         = 'dQw4w9WgXcQ'
                    title            = 'Test Video'
                    channel          = 'Test Channel'
                    published_at     = '2026-05-01'
                    duration_seconds = 120
                    url              = 'https://www.youtube.com/watch?v=dQw4w9WgXcQ'
                }
            }

            Mock Get-YftTranscript {
                [pscustomobject]@{
                    text     = 'According to scientists, the Moon is 384,400 km from Earth.'
                    source   = 'youtube_captions'
                    language = 'en'
                }
            }

            Mock Get-YftClaims {
                @(
                    [pscustomobject]@{
                        id   = 'claim_1'
                        text = 'The Moon is 384,400 km from Earth.'
                    }
                )
            }

            Mock Get-YftResearchResults {
                @(
                    [pscustomobject]@{
                        claim_id   = 'claim_1'
                        claim_text = 'The Moon is 384,400 km from Earth.'
                        search_results = @(
                            [pscustomobject]@{
                                title   = 'NASA'
                                url     = 'https://nasa.gov/moon'
                                snippet = 'The average distance is about 384,400 km.'
                            }
                        )
                    }
                )
            }

            Mock Get-YftScoredClaims {
                @(
                    [pscustomobject]@{
                        id          = 'claim_1'
                        text        = 'The Moon is 384,400 km from Earth.'
                        verdict     = 'Supported'
                        confidence  = 0.85
                        explanation = 'NASA supports the claim.'
                        sources     = @('https://nasa.gov/moon')
                    }
                )
            }

            $result = Invoke-YftFactCheck -Url 'https://www.youtube.com/watch?v=dQw4w9WgXcQ'

            $result.video.title | Should -Be 'Test Video'
            $result.claims[0].verdict | Should -Be 'Supported'
            $result.overall_credibility_score | Should -Be 1
        }
    }
}
