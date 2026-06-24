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
