import logging
from pathlib import Path
import colorlog
import json

from handler.download import Youtube


# Configure logging
if not Path("assets/song_downloader.log").exists():
    Path("assets").mkdir(exist_ok=True)
    Path("assets/song_downloader.log").write_text("", "UTF-8")

logger = logging.getLogger()
logging.basicConfig(
    filename="assets/song_downloader.log",     # log file name
    filemode="a",
    encoding="utf-8",
    level=logging.INFO,                 # log level: DEBUG, INFO, WARNING, ERROR
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# beautiful horses color to logging
formatter = colorlog.ColoredFormatter(
    "%(log_color)s%(levelname)-8s%(reset)s %(blue)s%(message)s",
    datefmt=None,
    reset=True,
    log_colors={
        'DEBUG':    'cyan',
        'INFO':     'green',
        'WARNING':  'yellow',
        'ERROR':    'red',
        'CRITICAL': 'red,bg_white',  # Red text on a white background
    },
    secondary_log_colors={},
    style='%'
)
handler = colorlog.StreamHandler() # Output to Terminal too
handler.setFormatter(formatter)
logger.addHandler(handler) # add handler for color format

yt = Youtube(logger=logger)

rating = yt.youtube_search(song_title="under the stars", song_artist="project aer", does_case_matter=False)#, song_duration_ms=((2*60 +3) *1000))

print(json.dumps(rating, indent=4))
