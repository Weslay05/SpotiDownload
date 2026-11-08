

logging.getLogger("musicbrainzngs").setLevel(logging.WARNING)



def embed_metadata(wav_file, output_file, cover_path, data):
    MAX_COVER_SIZE = 1024
    if data["cover_url"] == "https://None":
        cover_data = ""
        img = Image.new("RGB", (1, 1), (255, 255, 255))
        img.save(cover_path, "JPEG")
        logging.critical("No Real Cover, using decoy jpg")
    else:
        cover_data = requests.get(data["cover_url"]).content
        try:
            img = Image.open(io.BytesIO(cover_data)).convert("RGB")
            #with open(cover_path, "wb") as f:
            #    f.write(cover_data)
            img.thumbnail((MAX_COVER_SIZE, MAX_COVER_SIZE))
            img.save(cover_path, format="JPEG", quality=80)
            logging.debug("wrote cover.jpg natively")
        except Exception as e:
            logging.debug("cover data: %s", str(e))
            logging.warning("Invalid Cover Data falling back secondary cover")
            cover_data = requests.get(data["cover_url_fallback"]).content
            try: # TODO: Add another API as fallback instead of other url
                img = Image.open(io.BytesIO(cover_data)).convert("RGB")
                #with open(cover_path, "wb") as f:
                #    f.write(cover_data)
                img.thumbnail((MAX_COVER_SIZE, MAX_COVER_SIZE))
                img.save(cover_path, format="JPEG", quality=80)
                logging.debug("wrote cover.jpg natively though had to use fallback")
            except Exception as e2:
                logging.debug("cover data: %s", str(e2))
                logging.critical("Invalid Cover Data Creating decoy JPG to download and go on")
                img = Image.new("RGB", (1, 1), (255, 255, 255))
                img.save(cover_path, "JPEG")
                logging.debug("wrote cover.jpg using decoy file")

    genre_str = ", ".join(data["genres"])

    CODEC: str = output_file.rsplit(".", 1)[-1]
    # clean_album: str = "".join(ch for ch in data['album'] if ch.isprintable()).strip()
    if CODEC == "opus" or CODEC == "libopus":
        cmd = [
            "opusenc",
            "--bitrate", OPUS_FINAL_FILE_BITRATE, "--vbr",
            "--title", f"{data['title']}",
            "--artist", f"{data['artist']}",
            "--album", f"{data['album']}",
            "--date", f"{data['date']}",
            "--genre", f"{genre_str}",
            "--picture", f"3||Front Cover||{cover_path}",
            wav_file, f"{output_file.rsplit('.', 1)[0]}.opus"
        ]
    else:
        if CODEC == "flac":
            pass
        else:
            logging.warning("Codec not tested: falling back to ffmpeg auto conversion.")
        cmd = [
            "ffmpeg", 
            "-i", wav_file, "-i", cover_path,
            "-map", "0:a", "-map", "1:v",
            "-id3v2_version", "3",
            "-metadata:s:v", 'title="Album cover"',
            "-metadata:s:v", 'comment="Cover (Front)"',
            "-metadata:s:v:0", 'description="Front Cover"',
            "-metadata", f"title={data['title']}",
            "-metadata", f"artist={data['artist']}",
            "-metadata", f"album={data['album']}",
            "-metadata", f"date={data['date']}",
            "-metadata", f"genre={genre_str}",
            "-disposition:v", "attached_pic",
            output_file
        ]
    logging.debug("embedding metadata")
    subprocess.run(cmd, check=False)
    logging.debug("embedding metadata done")

def compress_audio(file: dict, output_path: str):
    if os.path.exists(file["path"]):
        if os.path.exists(output_path):
            logging.info("Overwriting: '%s'", output_path)
            os.remove(output_path)
    else:
        logging.error("'%s' doesn't exist: skipping compression", file["path"])
        return 1
    
    # Set Encoder
    if output_path.rsplit(".", 1)[-1] == "opus":
        encoder: str = "opusenc" # Options [ "opusenc", "ffmpeg-opus" ] # FIXME: ffmpeg-opus has no cover
    else:
        encoder: str = "ffmpeg" # Options [ "opusenc", "ffmpeg", "ffmpeg-opus" ]
    # Encoding
    if encoder == "opusenc":
        cmd = [
            "opusenc",
            "--bitrate", file["bitrate"], "--vbr",
            file["path"], output_path
        ]
    elif encoder == "ffmpeg-opus":
        cmd = [
            "ffmpeg",
            "-i", file["path"],
            "-c:a", file["codec"], "-b:a",
            file["bitrate"], output_path
        ]
    else:
        cmd = [
            "ffmpeg",
            "-i", file["path"],
            #"-map", "0:a", "-map", "0:v",
            "-c:a", file["codec"],
            "-b:a", file["bitrate"],
            "-c:v", "copy",# mjpeg
            #"-disposition:v", "attached_pic",
            output_path
        ]
    subprocess.run(cmd, check=False)
    return 0

if __name__ == "__main__":
    # Argument Parser
    parser = argparse.ArgumentParser(description="Spotify ↔ YouTube helper")
    parser.add_argument("--song", default="", help="Search for ...")
    parser.add_argument("--youtube", default="", help="YouTube video URL")
    parser.add_argument("--cover", default="", help="Cover URL")
    # TODO: Explicit Mode / Custom Filename
    args = parser.parse_args()

    # Main Variables
    logging.info("Starting to download a new Track with given data")
    if not args.song and not args.youtube:
        logging.debug('Using in-script values')
        song = ""
        youtube = ""
    else:
        logging.debug('Using given Arguments')
        song = args.song
        youtube = args.youtube

    # Secondary Variables
    tolerance_sec = 2 # TODO: Music Fingerprint analysis for downloaded works
    max_results_ytsearch = 10
    # TODO: specific tmp files for parallel works
    input_file = "output/tmp_downloaded.wav"
    tmp_file = "output/tmp_normalized.wav"
    tmp_cover = "output/tmp_cover_data.jpg"
    COMPRESSION_OPT_PATH = "output/compressed (ohio-impressed)"

    if os.path.exists(input_file):
        os.remove(input_file)
        logging.warning("Overwriting tmp_downloaded file")
    if os.path.exists(tmp_file):
        os.remove(tmp_file)
        logging.warning("Overwriting tmp_normalized file")
    if os.path.exists(tmp_cover):
        os.remove(tmp_cover)
        logging.warning("Overwriting tmp_cover_data file")

    # Validate Important Args
    if not song and not youtube :
        logging.error("No Song name or Youtube URL\n")
        sys.exit(1)
    else:
        if song and youtube:
            logging.info(
                "... Processing: '%s' (%s) ---",
                song,
                youtube
            )
            song_data = sanitize_filename(song)
            METADATA = get_metadata_musicbrainz(song_data['title'], song_data['artist'])
            filename_data = sanitize_filename(f"{METADATA['title']} - {METADATA['artist']}")
            opt_filename: str = f"{filename_data['title']} - {filename_data['artist']}"
            logging.info("Song name is: (%s)", song)
            logging.info("Youtube_URL is: (%s)", youtube)
        if not song:
            logging.info("... Processing: (%s)", youtube)
            # TODO: Derive song from youtube url
            logging.info("No Song name given, generated one is: (%s)", song)
        if not youtube:
            logging.info("... Processing: '%s'", song)
            song_data = sanitize_filename(song)
            METADATA = get_metadata_musicbrainz(song_data['title'], song_data['artist'])
            filename_data = sanitize_filename(f"{METADATA['title']} - {METADATA['artist']}")
            opt_filename: str = f"{filename_data['title']} - {filename_data['artist']}"

    # smaller optional args
    if args.cover:
        logging.info("Cover_URL is: (%s)", args.cover)
        METADATA['cover_url'] = f"{args.cover}"

    # Correct File Name
    Path("output").mkdir(exist_ok=True)
    final_file = {
        "path": f"output/{opt_filename}.opus", # Opus is natively supported
        "compress": False,
        "codec": "libopus",
        "container": "opus",
        "bitrate": "128k"
    }
    FILE_COMPRESSED = f"{COMPRESSION_OPT_PATH}/{opt_filename}.{final_file["container"]}"

    match check_filepaths(final_file["path"], final_file["compress"]):
        case 1: # All files already there
            logging.info("File '%s' already exists & compression deactivated: closing\n", final_file["path"])
            sys.exit(0)
        case 2: # Skipping to compression
            logging.info("File '%s' already exists & compression activated: skipping to compression", final_file["path"])
        case 0: # No initial file there, downloading audio
            if not youtube: # Fetch Youtube URL
                # QUERY = f"{METADATA['title']} - {METADATA['artist']}"
                QUERY = opt_filename
                youtube = get_youtube_link(QUERY, tolerance_sec, max_results_ytsearch, METADATA)
                if youtube is None:
                    # Fallback to user Input
                    USER_INPUT = f"{song_data['title']} - {song_data['artist']}"

                    # Redefining/Revalidating Things
                    QUERY = USER_INPUT
                    final_file["path"] = f"output/{USER_INPUT}.flac"
                    FILE_COMPRESSED = f"{COMPRESSION_OPT_PATH}/{USER_INPUT}.{final_file["container"]}"

                    # Running loop again
                    match check_filepaths(final_file["path"], final_file["compress"]):
                        case 1: # All files already there
                            logging.info("File '%s' already exists & compression deactivated: closing\n", final_file["path"])
                            sys.exit(0)
                        case 2: # Skipping to compression
                            logging.info("File '%s' already exists & compression activated: skipping to compression", final_file["path"])
                        case 0: # No initial file there, downloading audio
                            logging.critical("Fetching Youtube_URL failed, falling back to user input query: '%s'", QUERY)
                            youtube = get_youtube_link(QUERY, tolerance_sec, max_results_ytsearch, METADATA)
                            if youtube is None:
                                logging.error("Fetching Youtube_URL failed for all Queries\n")
                                sys.exit(1)
                logging.info("No Youtube_URL given, generated one is: (%s)", youtube)

            download_audio(input_file, youtube)

            measured = analyze_audio(input_file)
            normalize_audio(input_file, tmp_file, measured)

            embed_metadata(tmp_file, final_file["path"], tmp_cover, METADATA)

            # Delete Temp Files
            logging.debug("removing temp files")
            os.remove(tmp_file)
            os.remove(input_file)
            os.remove(tmp_cover)

    # Compress Audio
    if check_filepaths(final_file["path"], final_file["compress"]) == 0:
        logging.error("`%s` was never written\n", final_file["path"])
        sys.exit(1)
    elif final_file["compress"] is True:
        Path(COMPRESSION_OPT_PATH).mkdir(exist_ok=True)
        compress_audio(final_file, FILE_COMPRESSED)
        # os.remove(final_file["path"]) # Delete large file
        logging.info("✅ Compressed: '%s'", FILE_COMPRESSED)
    elif final_file["compress"] is False:
        logging.info("Compression Deactivated: Skipping")
    else:
        logging.error("something at compress audio went wrong, though not sure what")

    if song["score"] < 20.0:
        logging.warning("✅‼️ SCORE UNDER 20 PLEASE CHECK / Downloaded: '%s'\n", final_file["path"])
    else:
        logging.info("✅ Downloaded: '%s'\n", final_file["path"])
    sys.exit(0)
