"""
Electronic-Records-Classification.ps1 - Legacy PowerShell CLI for records classification

Forwards to the Python CLI for modern, robust classification.

Usage:
    powershell.exe -ExecutionPolicy Bypass -File Electronic-Records-Classification.ps1 -FolderPath <path> [-OutputPath <csv>]

Author: Pierce County IT
Date: 2025-05-27
"""

function Start-RecordsClassification {
    [CmdletBinding()]
    param (
        [Parameter(Mandatory = $true)]
        [ValidateScript({Test-Path -Path $_ -PathType Container})]
        [string]$FolderPath,

        [Parameter()]
        [string]$OutputPath = 'C:\Temp',

        [Parameter()]
        [int]$LinesPerFile = 100,

        [Parameter()]
        [string]$Model = "gemma3:1b",

        [Parameter()]
        [switch]$SkipAnalysis,

        [Parameter()]
        [int]$MaxParallelJobs = 0,

        [Parameter()]
        [string[]]$ExcludeExtension = @('.tmp','.log','.bak','.old','.zip','.rar','.tar','.gz','.7z','.exe','.dll','.sys','.iso','.dmg','.apk','.msi','.ps1','.psd1','.psm1','.json','.xml','.db','.mdb','.accdb'),

        [Parameter()]
        [string[]]$IncludeExtension = @('.txt','.csv','.docx','.xlsx','.pptx','.pdf','.html','.htm','.md','.rtf','.odt','.xml','.json','.yaml','.yml','.log','.tsv'),

        [Parameter()]
        [string]$LogPath = 'C:\Temp\RecordsClassification.log',

        [Parameter()]
        [switch]$PassThru
    )

    begin {
        if (-not $SkipAnalysis -and -not (Get-Command "ollama" -ErrorAction SilentlyContinue)) {
            throw "Ollama CLI not found but required for analysis. Use -SkipAnalysis to only identify old files."
        }

        $logging = $false
        if ($LogPath) {
            try {
                $LogFolder = Split-Path -Path $LogPath -Parent
                if (-not (Test-Path -Path $LogFolder)) {
                    New-Item -Path $LogFolder -ItemType Directory -Force | Out-Null
                }
                $timestamp = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
                $logFile = Join-Path -Path $LogFolder -ChildPath "$timestamp`_file_analysis.log"
                "File analysis started at $(Get-Date)" | Out-File -FilePath $logFile
                $logging = $true
            }
            catch {
                Write-Warning "Failed to initialize logging: $_"
            }
        }
        function Write-Log {
            param([string]$Message, [string]$Level = "INFO")
            if ($logging) {
                "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') [$Level] $Message" | Out-File -FilePath $logFile -Append
            }
        }

        # Initial file discovery
        Write-Verbose "Starting file analysis" 
        Write-Log "Starting file analysis" "INFO"
        $results = [System.Collections.Concurrent.ConcurrentBag[PSCustomObject]]::new()
        $timer = [System.Diagnostics.Stopwatch]::StartNew()
        # Determine optimal parallel jobs if not set: oversubscribe I/O-bound tasks (~2.5× cores)
        if ($MaxParallelJobs -le 0) {
            $MaxParallelJobs = [math]::Ceiling([Environment]::ProcessorCount * 2.5)
        }
        Write-Verbose "MaxParallelJobs set to $MaxParallelJobs (logical cores: $([Environment]::ProcessorCount))"
        # Continue on errors and warnings, trap unexpected exceptions
        $ErrorActionPreference = 'Continue'
        $WarningPreference = 'Continue'
        trap {
            Write-Error "Unexpected error: $_"
            Continue
        }
    }

    process {
        try {
            # Retrieve all files under root recursively
            $fileItems = Get-ChildItem -Path $FolderPath -Recurse -File -ErrorAction Stop
         
             # Auto-DESTROY any files older than 6 years (skip model)
             $sixYearDate = (Get-Date).AddYears(-6)
            $destroyItems = $fileItems | Where-Object { $_.LastWriteTime -lt $sixYearDate }
            foreach ($old in $destroyItems) {
                $r = [PSCustomObject]@{
                    FileName           = $old.Name
                    Extension          = $old.Extension
                    FullPath           = $old.FullName
                    LastModified       = $old.LastWriteTime
                    SizeKB             = [math]::Round($old.Length / 1KB, 2)
                    ModelDetermination = 'DESTROY'
                    ConfidenceScore    = 100
                    ContextualInsights = 'LastMofified date greater than 6 years: automatically DESTROY as per policy.'
                }
                $results.Add($r)
                if ($PassThru) { $r }
            }
            # Filter out auto-destroyed files from further analysis
            $fileItems = $fileItems | Where-Object { $_.LastWriteTime -ge $sixYearDate }

            # Separate supported and unsupported files for indexing
            $supportedItems = $fileItems | Where-Object { $_.Extension -in $IncludeExtension -and $_.Extension -notin $ExcludeExtension }
            $unsupportedItems = $fileItems | Where-Object { $_.Extension -notin $IncludeExtension -or $_.Extension -in $ExcludeExtension }

            foreach ($ui in $unsupportedItems) {
                $r = [PSCustomObject]@{
                    FileName           = $ui.Name
                    Extension          = $ui.Extension
                    FullPath           = $ui.FullName
                    LastModified       = $ui.LastWriteTime
                    SizeKB             = [math]::Round($ui.Length/1KB,2)
                    ModelDetermination = "SKIPPED"
                    ConfidenceScore    = 0
                    ContextualInsights = "Unsupported file type: $($ui.Extension)"
                }
                $results.Add($r)
                if ($PassThru) { $r }
                if ($logging) { Write-Log "Skipping unsupported file: $($ui.FullName)" "INFO" }
            }

            # Only process supported files through the model
            $fileItems = $supportedItems

            $totalFiles = $fileItems.Count
            Write-Verbose "Found $totalFiles files to process."
            Write-Log "Found $totalFiles files to process." "INFO"

            if (-not $totalFiles) { return }

            if ($SkipAnalysis) {
                $fileItems | ForEach-Object {
                    $r = [PSCustomObject]@{
                        FileName           = $_.Name
                        Extension          = $_.Extension
                        FullPath           = $_.FullName
                        LastModified       = $_.LastWriteTime
                        SizeKB             = [math]::Round($_.Length / 1KB, 2)
                        ModelDetermination = "Not Analyzed"
                        ConfidenceScore    = 0
                        ContextualInsights = "Analysis skipped"
                    }
                    $results.Add($r)
                    if ($PassThru) { $r }
                }
                return $results.ToArray()
            }

            # Define LLM prompt and schema for analysis
            $instructions = @"
You are "$($Model)" – a highly specialized Washington State Records Classification Assistant 
specializing in government content for Pierce County. Your primary function is to generate a single, precise JSON 
object adhering to the defined schema.

**Output Format:** Produce *only* this JSON object. Do not exceed $($LinesPerFile) lines.
```json
{
  "modelDetermination": "TRANSITORY" | "DESTROY" | "KEEP",
  "confidenceScore": integer (1–100),
  "contextualInsights": string
}
```

**Core Requirements:**

1.  **Confidence Assessment:** Estimate a confidence score (1-100) for your classification based 
    *exclusively* on the text within the provided file. Justify this score with *direct textual 
    references* to the relevant passages.

2.  **Contextual Justification:** When generating contextual insights, you *must* cite key text 
    snippets directly supporting your classification decision, avoiding interpretive commentary.

3. **JSON Schema Adherence:** Strictly adhere to the defined JSON schema.

4.  **Prioritize Accuracy & Compliance:** Ensure your output directly addresses the legal 
    requirements of WA Schedule 6.

**Instructions:**

*   Read the first $($LinesPerFile) lines of the input file.
*   Identify the most relevant legal classification (e.g., 'KEEP', 'DESTROY', 'TRANSITORY').
*   Assign a confidence score (1-100) justifying your determination.
*   Quote *exactly* one relevant text snippet to support your classification.

**Example:**  '[Quote relevant text]' and '[Quote relevant text]'
"@

            $jsonSchema = @{
                type       = "object"
                properties = @{
                    modelDetermination = @{ type = "string"; enum = @("TRANSITORY","DESTROY","KEEP") }
                    confidenceScore    = @{ type = "integer"; minimum = 1; maximum = 100 }
                    contextualInsights = @{ type = "string" }
                }
                required = @("modelDetermination","confidenceScore","contextualInsights")
            } | ConvertTo-Json -Depth 10 -Compress

            $jobs = @()
            # enforce dynamic throttling of background jobs
            $maxParallel = $MaxParallelJobs
            Write-Verbose "Throttle to $maxParallel concurrent jobs"

            foreach ($file in $fileItems) {
                try {
                    # throttle and start job
                    while ((Get-Job -State Running).Count -ge $maxParallel) { Start-Sleep -Milliseconds 200 }
                    $job = Start-Job -ScriptBlock {
                        param($f,$lp,$mdl,$sch,$ins)
                        try {
                            $fileInfo = Get-Item $f -ErrorAction Stop
                            $content = $null
                            try {
                                # Read up to $linesPerFile lines, with special handling for .docx files
                                switch ($fileInfo.Extension.ToLower()) {
                                    '.docx' {
                                        try {
                                            $word = New-Object -ComObject Word.Application
                                            $doc = $word.Documents.Open($f, [ref]$false, [ref]$true)
                                            $fullText = $doc.Content.Text
                                            $doc.Close()
                                            $word.Quit()
                                            $lines = $fullText -split '\r?\n' | Select-Object -First $lp
                                        } catch {
                                            throw "Unable to extract text from Word document: $_"
                                        }
                                    }
                                    default {
                                        $lines = Get-Content -Path $f -TotalCount $lp -ErrorAction Stop
                                    }
                                }
                                $content = $lines -join "`n"
                            } catch {
                                return [PSCustomObject]@{
                                    FileName           = $fileInfo.Name
                                    Extension          = $fileInfo.Extension
                                    FullPath           = $fileInfo.FullName
                                    LastModified       = $fileInfo.LastWriteTime
                                    SizeKB             = [math]::Round($fileInfo.Length / 1KB, 2)
                                    ModelDetermination = "ERROR"
                                    ConfidenceScore    = 0
                                    ContextualInsights = "Unable to read file: $_"
                                }
                            }

                            if ([string]::IsNullOrWhiteSpace($content)) {
                                return [PSCustomObject]@{
                                    FileName           = $fileInfo.Name
                                    Extension          = $fileInfo.Extension
                                    FullPath           = $fileInfo.FullName
                                    LastModified       = $fileInfo.LastWriteTime
                                    SizeKB             = [math]::Round($fileInfo.Length / 1KB, 2)
                                    ModelDetermination = "TRANSITORY"
                                    ConfidenceScore    = 80
                                    ContextualInsights = "File is empty or unreadable"
                                }
                            }

                            $tempFile = [System.IO.Path]::GetTempFileName()
                            $content | Out-File -FilePath $tempFile -Encoding utf8

                            try {
                                # Run Ollama CLI without unsupported --json flag
                                $res = & ollama run $mdl --no-stream --schema $sch --prompt $ins --file $tempFile
                                Remove-Item $tempFile -Force -ErrorAction SilentlyContinue
                                if ([string]::IsNullOrWhiteSpace($res)) { throw 'Empty response from model' }
                                $parsed = $res | ConvertFrom-Json -ErrorAction Stop

                                return [PSCustomObject]@{
                                    FileName           = $fileInfo.Name
                                    Extension          = $fileInfo.Extension
                                    FullPath           = $fileInfo.FullName
                                    LastModified       = $fileInfo.LastWriteTime
                                    SizeKB             = [math]::Round($fileInfo.Length / 1KB, 2)
                                    ModelDetermination = $parsed.modelDetermination
                                    ConfidenceScore    = [int]$parsed.confidenceScore
                                    ContextualInsights = $parsed.contextualInsights
                                }
                            }
                            catch {
                                $errMsg = $_.Exception.Message
                                Remove-Item $tempFile -Force -ErrorAction SilentlyContinue
                                return [PSCustomObject]@{
                                    FileName           = $fileInfo.Name
                                    Extension          = $fileInfo.Extension
                                    FullPath           = $fileInfo.FullName
                                    LastModified       = $fileInfo.LastWriteTime
                                    SizeKB             = [math]::Round($fileInfo.Length / 1KB, 2)
                                    ModelDetermination = "KEEP"
                                    ConfidenceScore    = 0
                                    ContextualInsights = "Error analyzing file: $errMsg"
                                }
                            }
                        }
                        catch {
                            return [PSCustomObject]@{
                                FileName           = [System.IO.Path]::GetFileName($f)
                                Extension          = [System.IO.Path]::GetExtension($f)
                                FullPath           = $f
                                LastModified       = $null
                                SizeKB             = 0
                                ModelDetermination = "ERROR"
                                ConfidenceScore    = 0
                                ContextualInsights = "Unhandled job error: $_"
                            }
                        }
                    } -ArgumentList $file.FullName, $LinesPerFile, $Model, $jsonSchema, $instructions

                    $jobs += [PSCustomObject]@{ Job = $job; FilePath = $file.FullName }
                } catch {
                    # Fallback on start-job failure: record error and continue
                    Write-Warning "Failed to start job for $($file.FullName): $_"
                    $errRecord = [PSCustomObject]@{
                        FileName = $file.Name; Extension = $file.Extension; FullPath = $file.FullName
                        LastModified = $file.LastWriteTime; SizeKB = [math]::Round($file.Length/1KB,2)
                        ModelDetermination = 'ERROR'; ConfidenceScore = 0
                        ContextualInsights = "Job launch failed: $_"
                    }
                    $results.Add($errRecord)
                }
            }

            $processedCount = 0
            while ($jobs.Count -gt 0) {
                $finished = $jobs | Where-Object { $_.Job.State -ne 'Running' }
                foreach ($f in $finished) {
                    try {
                        $r = Receive-Job -Job $f.Job -ErrorAction Stop
                        $results.Add($r)
                        $processedCount++
                        Write-Progress -Activity 'Classifying files' -Status "Processing file $processedCount of $totalFiles" -PercentComplete (($processedCount/$totalFiles)*100)
                        Write-Host "Processed $processedCount of $totalFiles : $($r.FileName)"
                        if ($PassThru) { $r }
                        if ($logging) {
                            Write-Log "[$($r.ModelDetermination)] $($r.FullPath) ($($r.ConfidenceScore)%)"
                        }
                    }
                    catch {
                        Write-Warning "Job for $($f.FilePath) failed: $_"
                        Write-Log "Job for $($f.FilePath) failed: $_" "ERROR"
                    }
                    finally {
                        Remove-Job -Job $f.Job -Force
                    }
                }
                $jobs = $jobs | Where-Object { $_.Job.State -eq 'Running' }
                if ($jobs.Count -gt 0) {
                    Start-Sleep -Milliseconds 300
                }
            }
        }
        catch {
            Write-Error "File enumeration failed: $_"
            Write-Log "File enumeration failed: $_" "ERROR"
        }
    }

    end {
        $timer.Stop()
        Write-Verbose "Completed in $($timer.Elapsed.ToString('hh\:mm\:ss'))"
        Write-Log "Completed in $($timer.Elapsed.ToString('hh\:mm\:ss'))"

        if (${OutputPath} -and (Test-Path -Path ${OutputPath} -PathType Container)) {
            try {
                $results.ToArray() | Export-Csv -Path $csvFile -NoTypeInformation
                Write-Verbose "Saved results to $csvFile"
            } catch {
                Write-Warning "Failed to write CSV to ${csvFile}: $_"
            }
        }
        else {
            try {
                $results.ToArray() | Export-Csv -Path $OutputPath -NoTypeInformation
                Write-Verbose "Saved results to $OutputPath"
            } catch {
                Write-Warning "Failed to write CSV to ${OutputPath}: $_"
            }
        }

        if (-not $PassThru) {
            $results.ToArray()
        }
    }
}
