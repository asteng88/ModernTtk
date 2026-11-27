<#
.SYNOPSIS
    Captures screenshots, cleans cached bytecode, commits, tags, and publishes ModernTtk to GitHub.
.EXAMPLE
    powershell -ExecutionPolicy Bypass -File scripts/publish_github.ps1
#>

[CmdletBinding()]
param(
    [string]$Version = "v0.2.0",
    [string]$Repo = "asteng88/ModernTtk",
    [switch]$SkipScreenshots
)

$ErrorActionPreference = "Stop"
$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $RepoRoot

Write-Host "==> Working in $RepoRoot" -ForegroundColor Cyan

# 1. Capture live showcase screenshots
if (-not $SkipScreenshots) {
    Write-Host "==> Capturing showcase screenshots..." -ForegroundColor Cyan
    python scripts/capture_screenshots.py
}

# 2. Remove tracked __pycache__ / *.pyc / *.egg-info from git index if present
Write-Host "==> Cleaning bytecode and build artifacts from git index..." -ForegroundColor Cyan
$prevEAP = $ErrorActionPreference
$ErrorActionPreference = "Continue"
git rm -r --cached --ignore-unmatch __pycache__ modernttk/__pycache__ modernttk/widgets/__pycache__ modernttk.egg-info *> $null
$ErrorActionPreference = $prevEAP

# 3. Stage and commit
Write-Host "==> Staging and committing files..." -ForegroundColor Cyan
git add .
$status = git status --porcelain
if ($status) {
    git commit -m "Release ${Version}: Gauges suite, DataStream animation, docs & screenshots"
} else {
    Write-Host "Nothing new to commit." -ForegroundColor Yellow
}

# 4. Ensure GitHub repo exists and is public, with description and topics
$Description = "Hybrid modern Tkinter & ttk UI library blending Windows 11 Fluent Design (sv_ttk) and ttkbootstrap with 4x supersampled widgets, gauges, and animations."
$Topics = @(
    "python",
    "tkinter",
    "ttk",
    "gui",
    "fluent-design",
    "ttkbootstrap",
    "sv-ttk",
    "dark-mode",
    "widgets",
    "gauges",
    "ui-library",
    "pillow"
)

if (Get-Command gh -ErrorAction SilentlyContinue) {
    Write-Host "==> Configuring GitHub repository ($Repo)..." -ForegroundColor Cyan
    $prevEAP = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    gh repo view $Repo *> $null
    $repoExists = ($LASTEXITCODE -eq 0)
    $ErrorActionPreference = $prevEAP

    if (-not $repoExists) {
        gh repo create $Repo --public --description $Description --source . --remote origin --push
    } else {
        gh repo edit $Repo --visibility public --accept-visibility-change-consequences --description $Description
        git push -u origin main
    }

    foreach ($topic in $Topics) {
        gh repo edit $Repo --add-topic $topic | Out-Null
    }

    # 5. Create annotated git tag & GitHub Release
    $existingTag = git tag -l $Version
    if (-not $existingTag) {
        git tag -a $Version -m "ModernTtk $Version"
    }
    git push origin $Version

    $prevEAP = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    gh release view $Version --repo $Repo *> $null
    $releaseExists = ($LASTEXITCODE -eq 0)
    $ErrorActionPreference = $prevEAP

    if (-not $releaseExists) {
        gh release create $Version --repo $Repo --title "ModernTtk $Version" --notes-file CHANGELOG.md
    }
    Write-Host "==> Published https://github.com/$Repo ($Version)!" -ForegroundColor Green
} else {
    Write-Host "GitHub CLI (gh) not found. Pushing branch and tag via git..." -ForegroundColor Yellow
    git push -u origin main
    $existingTag = git tag -l $Version
    if (-not $existingTag) {
        git tag -a $Version -m "ModernTtk $Version"
    }
    git push origin $Version
    Write-Host "Pushed! Set repository visibility, description, and topics on https://github.com/$Repo/settings" -ForegroundColor Green
}
