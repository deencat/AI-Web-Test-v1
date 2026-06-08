<#
.SYNOPSIS
  One-way sync from the private dev repo to the customer export folder.

.DESCRIPTION
  Mirrors source code into Agentic_QA_v1, excludes internal tooling and docs,
  applies the customer overlay, scans for obvious secrets, and optionally
  initializes git with the andrewchw no-reply identity.

.EXAMPLE
  .\sync-customer-package.ps1 -DryRun

.EXAMPLE
  .\sync-customer-package.ps1 -InitGit

.EXAMPLE
  .\sync-customer-package.ps1 -SkipSecretScan
#>
param(
    [switch]$DryRun,
    [switch]$SkipSecretScan,
    [switch]$InitGit,
    [switch]$Force,
    [string]$ConfigPath = "$PSScriptRoot\export-config.json"
)

$ErrorActionPreference = "Stop"

function Write-Step([string]$Message) {
    Write-Host "`n=== $Message ===" -ForegroundColor Cyan
}

function Normalize-RelativePath([string]$Path) {
    return $Path.Replace("/", "\").TrimStart("\")
}

function Remove-PathSafe([string]$TargetPath) {
    if (-not (Test-Path $TargetPath)) {
        return $true
    }

    try {
        Remove-Item $TargetPath -Recurse -Force -ErrorAction Stop
        return $true
    } catch {
        # Fallback: robocopy empty-dir mirror often works on locked Windows files
        $emptyDir = Join-Path $env:TEMP ("customer-export-empty-" + [guid]::NewGuid().ToString())
        try {
            New-Item -ItemType Directory -Force -Path $emptyDir | Out-Null
            & robocopy $emptyDir $TargetPath /MIR /NFL /NDL /NJH /NJS /NP /R:0 /W:0 | Out-Null
            Remove-Item $emptyDir -Force -ErrorAction SilentlyContinue
            if (Test-Path $TargetPath) {
                Remove-Item $TargetPath -Recurse -Force -ErrorAction Stop
            }
            return $true
        } catch {
            Remove-Item $emptyDir -Force -ErrorAction SilentlyContinue
            Write-Host "  WARNING: Could not remove (file may be in use): $TargetPath" -ForegroundColor Yellow
            Write-Host "           Stop 'npm run dev' or other processes using this folder, then re-run." -ForegroundColor Yellow
            return $false
        }
    }
}

if (-not (Test-Path $ConfigPath)) {
    throw "Config not found: $ConfigPath"
}

$config = Get-Content $ConfigPath -Raw | ConvertFrom-Json

$source = $config.sourceRoot
$dest = $config.destRoot
$overlay = $config.overlayDir

if (-not (Test-Path $source)) {
    throw "Source not found: $source"
}

Write-Host "Customer export sync" -ForegroundColor Green
Write-Host "  Source:  $source"
Write-Host "  Dest:    $dest"
Write-Host "  Overlay: $overlay"
Write-Host "  Remote:  $($config.customerRepoUrl)"
if ($DryRun) {
    Write-Host "  Mode:    DRY RUN (no files changed)" -ForegroundColor Yellow
}

New-Item -ItemType Directory -Force -Path $dest | Out-Null

Write-Step "Step 1: Mirror source code"
$robocopyArgs = @(
    $source,
    $dest,
    "/MIR",
    "/NFL", "/NDL", "/NJH", "/NJS", "/NP",
    "/XD", ".git"
)

foreach ($dir in $config.excludeDirs) {
    $robocopyArgs += "/XD"
    $robocopyArgs += $dir
}

foreach ($file in $config.excludeFiles) {
    $robocopyArgs += "/XF"
    $robocopyArgs += $file
}

if ($DryRun) {
    $robocopyArgs += "/L"
}

& robocopy @robocopyArgs | Out-Null
if ($LASTEXITCODE -gt 7) {
    throw "Robocopy failed with exit code $LASTEXITCODE"
}

Write-Step "Step 2: Remove sensitive and dev-only files from export"
$sensitiveFiles = @(
    (Join-Path $dest ".env"),
    (Join-Path $dest ".env.local"),
    (Join-Path $dest "backend\.env"),
    (Join-Path $dest "backend\.env.local"),
    (Join-Path $dest "frontend\.env"),
    (Join-Path $dest "frontend\.env.local"),
    (Join-Path $dest "stagehand-service\.env")
)
$purgeWarnings = @()

foreach ($file in $sensitiveFiles) {
    if (Test-Path $file) {
        Write-Host "  Remove sensitive file: $file"
        if (-not $DryRun) {
            Remove-Item $file -Force -ErrorAction SilentlyContinue
        }
    }
}

$devOnlyDirs = @(
    (Join-Path $dest "scripts"),
    (Join-Path $dest "backend\artifacts")
)
$purgeDirNames = @(
    "node_modules", "venv", "env", "__pycache__", ".pytest_cache",
    "dist", "build", "coverage", ".mypy_cache"
)
foreach ($dir in $devOnlyDirs) {
    if (Test-Path $dir) {
        Write-Host "  Remove dev-only dir: $dir"
        if (-not $DryRun) {
            if (-not (Remove-PathSafe $dir)) {
                $purgeWarnings += $dir
            }
        }
    }
}
foreach ($dirName in $purgeDirNames) {
    Get-ChildItem -Path $dest -Directory -Recurse -Filter $dirName -ErrorAction SilentlyContinue |
        Sort-Object { $_.FullName.Length } -Descending |
        ForEach-Object {
            Write-Host "  Remove build/cache dir: $($_.FullName)"
            if (-not $DryRun) {
                if (-not (Remove-PathSafe $_.FullName)) {
                    $purgeWarnings += $_.FullName
                }
            }
        }
}

if ($purgeWarnings.Count -gt 0 -and -not $DryRun) {
    Write-Host ""
    Write-Host "  $($purgeWarnings.Count) folder(s) could not be removed (likely in use by a dev server)." -ForegroundColor Yellow
    Write-Host "  Export will continue. node_modules is in .gitignore and will not be pushed to GitHub." -ForegroundColor Yellow
}

Write-Step "Step 3: Prune documentation to whitelist"
$docDest = Join-Path $dest "documentation"
if (Test-Path $docDest) {
    $whitelist = @($config.includeDocWhitelist | ForEach-Object { Normalize-RelativePath $_ })
    Get-ChildItem $docDest -Recurse -File | ForEach-Object {
        $rel = Normalize-RelativePath $_.FullName.Substring($dest.Length + 1)
        if ($whitelist -notcontains $rel) {
            Write-Host "  Remove doc: $rel"
            if (-not $DryRun) {
                Remove-Item $_.FullName -Force
            }
        }
    }

    if (-not $DryRun) {
        Get-ChildItem $docDest -Recurse -Directory |
            Sort-Object { $_.FullName.Length } -Descending |
            ForEach-Object {
                if (-not (Get-ChildItem $_.FullName -Force -ErrorAction SilentlyContinue)) {
                    Remove-Item $_.FullName -Force
                }
            }

        if (-not (Get-ChildItem $docDest -Force -ErrorAction SilentlyContinue)) {
            Remove-Item $docDest -Force
        }
    }
}

Write-Step "Step 4: Apply customer overlay"
if (-not (Test-Path $overlay)) {
    Write-Host "  Overlay folder not found, skipping." -ForegroundColor Yellow
} else {
    $overlayArgs = @(
        $overlay,
        $dest,
        "/E",
        "/NFL", "/NDL", "/NJH", "/NJS", "/NP"
    )
    if ($DryRun) {
        $overlayArgs += "/L"
    }
    & robocopy @overlayArgs | Out-Null
    if ($LASTEXITCODE -gt 7) {
        throw "Overlay robocopy failed with exit code $LASTEXITCODE"
    }
}

Write-Step "Step 5: Secret and personal-info scan"
if (-not $SkipSecretScan) {
    $textExtensions = @(
        ".py", ".ts", ".tsx", ".js", ".jsx", ".json", ".md", ".html",
        ".yml", ".yaml", ".txt", ".sh", ".ps1", ".bat", ".env"
    )
    $scanExcludeFiles = @()
    if ($config.scanExcludeFiles) {
        $scanExcludeFiles = @($config.scanExcludeFiles)
    }
    $scanRoots = @(
        (Join-Path $dest "backend"),
        (Join-Path $dest "frontend"),
        (Join-Path $dest "stagehand-service"),
        (Join-Path $dest "tests"),
        (Join-Path $dest "documentation"),
        (Join-Path $dest "README.md"),
        (Join-Path $dest "LICENSE")
    ) | Where-Object { Test-Path $_ }

    $filesToScan = @()
    foreach ($root in $scanRoots) {
        if (Test-Path $root -PathType Leaf) {
            $filesToScan += Get-Item $root
        } else {
            $filesToScan += Get-ChildItem -Path $root -Recurse -File -ErrorAction SilentlyContinue |
                Where-Object {
                    $textExtensions -contains $_.Extension -and
                    $scanExcludeFiles -notcontains $_.Name -and
                    $_.FullName -notmatch '\\node_modules\\|\\venv\\|\\env\\|\\__pycache__\\|\\dist\\|\\build\\|\\coverage\\'
                }
        }
    }
    $filesToScan = $filesToScan | Select-Object -Unique FullName

    Write-Host "  Scanning $($filesToScan.Count) text files..." -ForegroundColor Gray

    $hits = @()
    $combinedPattern = ($config.secretScanPatterns | ForEach-Object { "($_)" }) -join "|"
    foreach ($file in $filesToScan) {
        $matches = Select-String -Path $file.FullName -Pattern $combinedPattern -ErrorAction SilentlyContinue
        if ($matches) {
            $hits += $matches
        }
    }

    $envFiles = @(
        (Join-Path $dest "backend\.env"),
        (Join-Path $dest "frontend\.env"),
        (Join-Path $dest ".env")
    ) | Where-Object { Test-Path $_ }

    if ($envFiles.Count -gt 0) {
        throw "Export blocked: .env file(s) still present in customer package: $($envFiles -join ', ')"
    }

    if ($hits.Count -gt 0) {
        Write-Host "WARNING: Possible secrets or internal references found ($($hits.Count) matches):" -ForegroundColor Red
        $hits |
            Select-Object -Unique Path, LineNumber, Line |
            Select-Object -First 25 |
            ForEach-Object {
                Write-Host "  $($_.Path):$($_.LineNumber)  $($_.Line.Trim())"
            }

        if (-not $DryRun -and -not $Force) {
            Write-Host ""
            Write-Host ">>> WAITING FOR INPUT: Type y and press Enter to continue, or N / Ctrl+C to abort <<<" -ForegroundColor Yellow
            Write-Host "    (Or re-run with -Force to skip this prompt)" -ForegroundColor Yellow
            $confirm = Read-Host "Continue anyway? (y/N)"
            if ($confirm -ne "y") {
                throw "Export aborted due to secret scan hits. Use -Force to skip this prompt."
            }
        }
    } else {
        Write-Host "  No obvious secret patterns found." -ForegroundColor Green
    }
}

Write-Step "Step 6: Git setup in customer folder"
if ($InitGit -and -not $DryRun) {
    Push-Location $dest
    try {
        git config user.name $config.gitUserName
        git config user.email $config.gitUserEmail

        if (-not (Test-Path ".git")) {
            git init
            git branch -M main
        }

        $remotes = git remote 2>$null
        if ($remotes -notcontains "origin") {
            git remote add origin $config.customerRepoUrl
        } else {
            git remote set-url origin $config.customerRepoUrl
        }

        git add -A
        $status = git status --porcelain
        if ($status) {
            git commit -m "Release - Agentic QA v1"
            Write-Host "  Created commit in customer folder." -ForegroundColor Green
        } else {
            Write-Host "  No changes to commit." -ForegroundColor Yellow
        }

        Write-Host "  Next: cd `"$dest`" && git push -u origin main" -ForegroundColor Cyan
    } finally {
        Pop-Location
    }
}

Write-Host "`nDone. Customer package: $dest" -ForegroundColor Green
if ($DryRun) {
    Write-Host "(Dry run - no files were changed)" -ForegroundColor Yellow
}
