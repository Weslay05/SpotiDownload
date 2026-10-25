# SpotiDownload

Downloads songs from YouTube using metadata from third-party sources.

## Quick Start

### Standard Installation (All Systems)

```bash
cd /path/to/project
pip install --upgrade -r requirements.txt
python src/main.py "artist song"
```

### NixOS / Recommended Development Environment

```bash
nix develop
python src/main.py "artist song"
# No pip install needed! All dependencies included.
```

## System Requirements

- **ffmpeg** (system package) - Audio/video processing
- **opus-tools/opusenc** (system package) - Opus format handling

### Windows Setup

```powershell
winget install --silent -e --id="Mozilla.opus-tools" --id="Gyan.FFmpeg"
```

## Usage

### Basic Command

```bash
python src/main.py "song name - artist" # Works better with the dash
```

Arguments:

- Search query (required)
- Additional flags as supported by the script

### Batch Processing from `assets/tracks.txt`

**Windows Example:**

```powershell
Get-Content -LiteralPath 'assets\tracks.txt' | ForEach-Object {
    $song = $_.Trim()
    if ($song) {
        Write-Host "Processing $song"
        & python 'src/main.py' --song "$song"
    }
}
```

**Linux/Mac Example:**

```bash
xargs -I {} python src/main.py --song {} < assets/tracks.txt
```

---

## Development with Nix (Recommended)

The project includes a `flake.nix` for reproducible development environments.

### Features

- ✅ Zero setup - all Python packages pre-installed
- ✅ Cross-platform (x86_64, ARM64, etc.)
- ✅ Includes system dependencies (ffmpeg, opus-tools)
- ✅ Isolates environment from host system

### Usage on NixOS/Nix

```bash
# Start development shell
nix develop

# Run the application
python src/main.py "artist song"

# Access tools installed in flake.nix
uv --version        # Python package manager
direnv allow        # Environment variable management
```

**Note:** When using `nix develop`, `requirements.txt` aren't needed anymore, since it already contains all requirements.

## Output Directory

Processed songs are saved to `output/`.

### Post-Processing Tip (Windows)

Compress all downloaded files (**OPUS, FLAC**) into an organized folder:

```powershell
$outDir = Join-Path $PWD 'output/compressed-ohio-impressed/'
New-Item -ItemType Directory -Force -Path $outDir | Out-Null

Get-ChildItem -File | Where-Object { $_.Extension -in '.opus', '.flac' } | ForEach-Object {
    $outFile = Join-Path $outDir ($_.BaseName + '.mp3')
    Write-Host "Converting $($_.Name)"
    ffmpeg -i $_.FullName -codec:a libmp3lame -q:a 2 $outFile
}
```
