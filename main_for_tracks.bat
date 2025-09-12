call activate ./conda-windows

REM Loop through each line in tracks.txt
for /f "usebackq delims=" %%a in ("assets/tracks.txt") do (
    echo Processing %%a
    python main.py --spotify_url "%%a"
)

echo done
pause