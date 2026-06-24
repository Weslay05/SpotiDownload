# Song Downloader

Downloads Songs from youtube using metadata from third party sites.

## Requirements

- ffmpeg

## Usage: `main.py`

1. Cd into project root
2. Activate Python environment
3. update/install requirements `pip install --upgrade -r requirements.txt`

Either run `python main.py` directly with arguments like `--song` or

If `assets/tracks.txt` should be used

**Windows** Example

```pwsh
Get-Content assets\tracks.txt | ForEach-Object {
    Write-Host "Processing $_"
    python main.py --song $_
}
```

**Linux** Example

```bash
xargs -I {} python main.py --song {} < assets/tracks.txt
```

### Useful Hacks

**Windows** convert `output/*.flac` -> `output/compresssed (ohio-impressed mp3-version)/*.mp3` *(cd into `output`)*

```powershell
New-Item -ItemType Directory -Force -Path ".\compresssed (ohio-impressed mp3-version)" | Out-Null

Get-ChildItem -Path . -Filter *.flac | ForEach-Object {
    $output_file = Join-Path ".\compresssed (ohio-impressed mp3-version)" ($_.BaseName)

    Write-Host "Converting $($_.Name)"
    ffmpeg -i $_ -codec:a libmp3lame -q:a 2 "${output_file}.mp3"
}
```
