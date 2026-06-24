# FIXME: Entire loop
cd ../../
call ./env/scripts/activate.bat

title SongDownloader

REM Loop through each line in tracks.txt
powershell -NoProfile -Command ^
    "Get-Content -Encoding UTF8 assets/tracks.txt | ForEach-Object { ^
        Write-Host ('Processing ' + $_); ^
        python main.py --song $_ ^
    }"

echo done
pause
